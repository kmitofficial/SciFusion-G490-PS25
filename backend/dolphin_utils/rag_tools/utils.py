import os
import json
import random
import google.generativeai as genai  # <-- 1. ADD THIS IMPORT
from dolphin_utils.llm_utils import cal_price, truncate_text_to_token_limit, count_tokens


def call_api(client, model, prompt_messages, temperature=1.0, max_tokens=100, seed=2024, json_output=False):
    # For Groq models, truncate messages to stay within limits
    if model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"] or "groq" in model.lower():
        for msg in prompt_messages:
            if "content" in msg and isinstance(msg["content"], str):
                token_count = count_tokens(msg["content"])
                if token_count > 3000:
                    print(f"Warning: Truncating message from {token_count} tokens to 3000")
                    msg["content"] = truncate_text_to_token_limit(msg["content"], max_tokens=3000)

    # --- 2. ADD THIS ENTIRE BLOCK FOR GEMINI ---
    if isinstance(client, genai.GenerativeModel):
        try:
            config_args = {}
            if max_tokens:
                config_args['max_output_tokens'] = max_tokens
            if temperature is not None:
                config_args['temperature'] = temperature

            # Convert OpenAI/Claude message format to Gemini format
            gemini_messages = []
            for msg in prompt_messages:
                role = 'user' if msg['role'] == 'user' else 'model'
                gemini_messages.append({'role': role, 'parts': [msg['content']]})

            # Handle JSON output for Gemini via prompting
            if json_output:
                last_message = gemini_messages[-1]['parts'][0]
                last_message += "\n\nRespond ONLY with a valid JSON object. Do not include any other text or markdown formatting (like ```json)."
                gemini_messages[-1]['parts'][0] = last_message

            completion = client.generate_content(
                gemini_messages,
                generation_config=genai.types.GenerationConfig(**config_args)
            )
            response = completion.text
            cost = 0  # Placeholder: Add Gemini cost calculation if needed

            if json_output:
                # Clean up potential markdown formatting
                response = response.strip()
                if response.startswith("```json"):
                    response = response[len("```json"):].strip()
                if response.endswith("```"):
                    response = response[:-len("```")].strip()

        except Exception as e:
            print(f"Error in Gemini API call: {e}")
            raise

    # --- CHANGE THIS `if` to `elif` ---
    elif "claude" in model:
        if json_output:
            prompt = prompt_messages[0][
                         "content"] + " Directly output the JSON dict with no additional text (avoid the presence of newline characters (\"\n\") and unescaped double quotes within the string so that we can call json.loads() on the output later)."
            prompt_messages = [{"role": "user", "content": prompt}]
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=prompt_messages
        )
        cost = cal_price(model, message.usage)
        response = message.content[0].text
    else:
        response_format = {"type": "json_object"} if json_output else {"type": "text"}
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=prompt_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                seed=seed,
                response_format=response_format
            )
            cost = cal_price(model, completion.usage)
            response = completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in call_api: {e}")
            raise

    return response, cost


def call_api_claude(client, model, prompt_messages, temperature=1.0, max_tokens=100):
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=prompt_messages
    )
    cost = cal_price(model, message.usage)
    response = message.content[0].text

    return response, cost


def cache_output(output, file_name):
    if file_name.endswith(".txt"):
        ## store GPT4 output into a txt file
        with open(file_name, "w") as f:
            f.write(output)
    elif file_name.endswith(".json"):
        ## store GPT4 output into a json file
        with open(file_name, "w") as f:
            json.dump(output, f, indent=4)
    return


def print_idea_json(filename):
    with open(filename, "r") as f:
        idea_json = json.load(f)
    idea = idea_json["final_plan_json"]
    name = idea_json["idea_name"]
    print(name)
    for k, v in idea.items():
        if len(v) > 5:
            print('- ' + k)
            print(v.strip() + '\n')


def format_plan_json(experiment_plan_json, indent_level=0, skip_test_cases=True, skip_fallback=True):
    try:
        # Check if the input is a string, if so, return it directly
        if isinstance(experiment_plan_json, str):
            return experiment_plan_json

        output_str = ""
        indent = "  " * indent_level
        for k, v in experiment_plan_json.items():
            if k == "score":
                continue
            if skip_test_cases and k == "Test Case Examples":
                continue
            if skip_fallback and k == "Fallback Plan":
                continue
            if isinstance(v, (str, int, float)):
                output_str += f"{indent}{k}: {v}\n"
            elif isinstance(v, list):
                output_str += f"{indent}{k}:\n"
                for item in v:
                    if isinstance(item, dict):
                        output_str += format_plan_json(item, indent_level + 1)
                    else:
                        output_str += f"{indent}  - {item}\n"
            elif isinstance(v, dict):
                output_str += f"{indent}{k}:\n"
                output_str += format_plan_json(v, indent_level + 1)
        return output_str
    except Exception as e:
        print("Error in formatting experiment plan json: ", e)
        return ""


def shuffle_dict_and_convert_to_string(input_dict):
    # Convert dict items to a list and shuffle
    items = list(input_dict.items())
    random.shuffle(items)

    # Convert back to dict and then to a JSON-formatted string
    shuffled_dict = dict(items)
    json_str = json.dumps(shuffled_dict, indent=4)

    return json_str


def clean_code_output(code_output):
    code_output = code_output.strip()
    if code_output.startswith("```python"):
        code_output = code_output[len("```python"):].strip()
    if code_output.endswith("```"):
        code_output = code_output[:-len("```")].strip()
    return code_output


def concat_reviews(paper_json):
    review_str = ""
    meta_review = paper_json["meta_review"]
    all_reviews = paper_json["reviews"]

    review_str += "Meta Review:\n" + meta_review + "\n\n"
    for idx, review in enumerate(all_reviews):
        review_str += "Reviewer #{}:\n".format(idx + 1) + "\n"
        for key, value in review.items():
            if key in ["summary", "soundness", "contribution", "strengths", "weaknesse", "questions", "rating",
                       "confidence"]:
                review_str += key + ": " + value["value"] + "\n"
        review_str += "\n"

    return review_str


def avg_score(scores):
    scores = [int(s[0]) for s in scores]
    return sum(scores) / len(scores)


def max_score(scores):
    scores = [int(s[0]) for s in scores]
    return max(scores)


def min_score(scores):
    scores = [int(s[0]) for s in scores]
    return min(scores)