import backoff
import openai
import groq
import json
from transformers import AutoModelForCausalLM, AutoTokenizer
import tiktoken


def count_tokens(text, model="gpt-4"):
    """Count tokens in text using tiktoken"""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def truncate_text_to_token_limit(text, max_tokens=4000, model="gpt-4"):
    """Truncate text to fit within token limit"""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    
    # Truncate and add indicator
    truncated_tokens = tokens[:max_tokens]
    truncated_text = encoding.decode(truncated_tokens)
    return truncated_text + "\n\n[... Content truncated due to length ...]"


def cal_price(model, usage):
    if model == "gpt-4o-2024-08-06" or model == "gpt-4o-2024-11-20":
        return (0.0025 * usage.prompt_tokens + 0.01 * usage.completion_tokens) / 1000.0
    elif model == "gpt-4o-2024-05-13":
        return (0.005 * usage.prompt_tokens + 0.015 * usage.completion_tokens) / 1000.0
    elif model == 'claude-3-7-sonnet-20250219':
        return (0.003 * usage.prompt_tokens + 0.015 * usage.completion_tokens) / 1000.0
    elif model == 'Intern-S1':
        return 0
    elif "localhost" in model:
        return 0
    # Groq pricing (as of 2025)
    elif model == "openai/gpt-oss-120b":
        return (0.005 * usage.prompt_tokens + 0.005 * usage.completion_tokens) / 1000.0
    elif model == "openai/gpt-oss-20b":
        return (0.001 * usage.prompt_tokens + 0.002 * usage.completion_tokens) / 1000.0
    elif "groq" in model.lower():
        # Default Groq pricing for unknown models
        return (0.001 * usage.prompt_tokens + 0.002 * usage.completion_tokens) / 1000.0
    else:
        print(f"!Warning: Cannot calculate price for model: {model}. Ignore this if you are using locally deployed model.")
        return 0

@backoff.on_exception(backoff.expo, (openai.RateLimitError, openai.APITimeoutError, groq.RateLimitError, groq.APITimeoutError))
def get_response_from_llm(
    msg,
    client,
    model,
    system_message,
    print_debug=False,
    msg_history=None,
    max_tokens=4096,
    temperature=0.7,
):
    if msg_history is None:
        msg_history = []
    
    # Initialize response and content variables to avoid UnboundLocalError
    response = None
    content = ""
    new_msg_history = []

    if "claude" in model:
        new_msg_history = msg_history + [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": msg,
                    }
                ],
            }
        ]
        response = client.messages.create(
            model=model,
            max_tokens=3000,
            temperature=temperature,
            system=system_message,
            messages=new_msg_history,
        )
        price = cal_price(model, response.usage)
        content = response.content[0].text
        new_msg_history = new_msg_history + [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": content,
                    }
                ],
            }
        ]
    elif "gpt" in model:
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    *new_msg_history,
                ],
                temperature=temperature,
                max_tokens=3000,
                n=1,
                stop=None,
                seed=0,
            )
        except Exception as e:
            print(e)
        price = cal_price(model, response.usage)
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
    elif "deepseek" in model:
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=3000,
            n=1,
            stop=None,
        )
        price = cal_price(model, response.usage)
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
    # Locally deployed models
    elif "localhost" in model:
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model='-'.join(model.split("-")[1:]),
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=3000,
            n=1,
            stop=None,
        )
        price = cal_price(model, response.usage)
        content = response.choices[0].message.content
        new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
    
    elif model == "Intern-S1":
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        response = client.chat.completions.create(
            model="intern-latest",
            messages=[
                {"role": "system", "content": system_message},
                *new_msg_history,
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stop=None
        )
        price = cal_price(model, response.usage)
        content = response.choices[0].message.content
        # remove thinking content
        if "</think>" in content:
            content = content.split("</think>", 1)[1].strip()
        else:
            content = content
    # Groq API (GPT-OSS models)
    elif model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"] or "groq" in model.lower():
        # Groq has strict token limits - be VERY aggressive with truncation
        # For gpt-oss-120b: 8000 token limit on input (including system + all messages)
        
        # Truncate system message very aggressively
        system_token_count = count_tokens(system_message)
        max_system_tokens = 800  # Very small limit for system message
        if system_token_count > max_system_tokens:
            print(f"Warning: Truncating system message from {system_token_count} tokens to {max_system_tokens}")
            system_message = truncate_text_to_token_limit(system_message, max_system_tokens)
        
        # Truncate message history - keep only last message if exists
        if len(msg_history) > 2:
            print(f"Warning: Truncating message history from {len(msg_history)} messages to last 2")
            msg_history = msg_history[-2:]
        
        # Truncate user message aggressively
        msg_token_count = count_tokens(msg)
        max_msg_tokens = 1200  # Very small limit for user message
        if msg_token_count > max_msg_tokens:
            print(f"Warning: Truncating user message from {msg_token_count} tokens to {max_msg_tokens}")
            msg = truncate_text_to_token_limit(msg, max_msg_tokens)
        
        new_msg_history = msg_history + [{"role": "user", "content": msg}]
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    *new_msg_history,
                ],
                temperature=temperature,
                max_tokens=min(max_tokens, 3000),  # Limit output tokens too
            )
            price = cal_price(model, response.usage)
            content = response.choices[0].message.content
            new_msg_history = new_msg_history + [{"role": "assistant", "content": content}]
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            # Return error gracefully
            return "", msg_history, 0
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            raise
    else:
        raise ValueError(f"Model {model} not supported.")

    if print_debug:
        print()
        print("*" * 20 + " LLM START " + "*" * 20)
        for j, msg in enumerate(new_msg_history):
            print(f'{j}, {msg["role"]}: {msg["content"]}')
        print(content)
        print("*" * 21 + " LLM END " + "*" * 21)
        print()

    return content, new_msg_history, price


def extract_json_between_markers(llm_output):
    json_start_marker = "```json"
    json_end_marker = "```"

    # Find the start and end indices of the JSON string
    start_index = llm_output.find(json_start_marker)
    if start_index != -1:
        start_index += len(json_start_marker)  # Move past the marker
        end_index = llm_output.find(json_end_marker, start_index)
    else:
        return None  # JSON markers not found

    if end_index == -1:
        return None  # End marker not found

    # Extract the JSON string
    json_string = llm_output[start_index:end_index].strip()
    try:
        parsed_json = json.loads(json_string)
        return parsed_json
    except json.JSONDecodeError:
        return None  # Invalid JSON format
