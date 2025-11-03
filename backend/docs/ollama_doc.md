```

## Deploy LLMs using [ollama](https://ollama.com/) (Optional)

1. Download ollama following the [instructions](https://ollama.com/download) on the website.
2. (Optional) Run `export OLLAMA_MODELS=path/to/models` to specify the model storage path of ollama.
3. Run `ollama serve`.
4. Run `ollama run model_name`, for example, `ollama run deepseek-v2.5`. More model information can be found [here](https://ollama.com/library).

### Recommended Best Models (2025):

**Large Scale Models (120B+ parameters):**
- `gpt-oss:20b` - Already installed, excellent general-purpose model
- For true 120B+ models, consider using Groq API or other cloud providers as they exceed typical local hardware limits

**Best Local Models:**
- `llama3.1:8b` - Best overall performance/size ratio, excellent reasoning
- `mixtral:8x7b` - Outstanding for coding and complex reasoning tasks  
- `codellama:13b` - Specialized for code generation and programming tasks
- `deepseek-coder:6.7b` - Excellent coding capabilities, fast inference
- `llava:7b` - Vision-language model (already installed)

**Quick Setup:**
```bash
# Pull recommended models
ollama pull llama3.1:8b
ollama pull mixtral:8x7b  
ollama pull codellama:13b
ollama pull deepseek-coder:6.7b

# Or use the setup script
python setup_ollama_models.py
```

**Note that you need to modify the modelfile of ollama for more tokens**. For example,

1. Create a new file by `vim deepseek-v2.5-32k-modelfile`.
2. Modify the `num_ctx`, `num_predict` ... in the modelfile.
    ```
    FROM deepseek-v2.5
    PARAMETER num_ctx 24576
    PARAMETER num_predict 8192
    ```
3. Run `ollama create deepseek-v2.5-32k -f deepseek-v2.5-32k-modelfile`.
4. After that, you can run `ollama run deepseek-v2.5-32k`.

**Make aider support your own LLMs.**. For example,

1. **Ollama Local Models** - Use OpenAI-compatible API:

    ```python
    import openai
    client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="na")
    
    # Test any local model
    response = client.chat.completions.create(
        model="llama3.1-32k",  # or any custom model name
        messages=[{"role": "user", "content": "Hello!"}]
    )
    ```

2. **Groq Cloud API** - For large 120B+ models:

    ```python
    import openai
    client = openai.OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key="your-groq-api-key"  # Get from https://console.groq.com/
    )
    
    # Use Groq's latest models (Llama 3.1 405B, Mixtral 8x22B)
    response = client.chat.completions.create(
        model="llama-3.1-405b-reasoning",  # Latest 120B+ model
        messages=[{"role": "user", "content": "Complex reasoning task"}]
    )
    ```

3. **Aider Configuration** - Add model settings:

    In `/Path/to/env/lib/python3.x/site-packages/aider/models.py`
    
    ```python
    # Local Ollama models
    ModelSettings(
        "ollama/llama3.1-32k",
        "diff",
        use_repo_map=True,
        send_undo_reply=True,
        examples_as_sys_msg=True,
        reminder_as_sys_msg=True,
    ),
    
    ModelSettings(
        "ollama/mixtral-32k",
        "diff", 
        use_repo_map=True,
        send_undo_reply=True,
        examples_as_sys_msg=True,
        reminder_as_sys_msg=True,
    ),
    
    # Groq cloud models
    ModelSettings(
        "groq/llama-3.1-405b-reasoning", 
        "diff",
        use_repo_map=True,
        send_undo_reply=True,
        examples_as_sys_msg=True,
        reminder_as_sys_msg=True,
    ),
    ```

### Groq Setup (for 120B+ models):

1. Sign up at [https://console.groq.com/](https://console.groq.com/)
2. Get your API key from the dashboard
3. Set environment variable: `export GROQ_API_KEY=your-key-here`
4. Available large models:
   - `openai/gpt-oss-120b` (120B parameters - best reasoning and coding)
   - `openai/gpt-oss-20b` (20B parameters - fast and capable)

### Usage Examples:

**Basic Groq API usage:**
```python
import os
import openai

# Setup Groq client
client = openai.OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

# Use with InternAgent
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Explain neural attention mechanisms"}],
    max_tokens=1000,
    temperature=0.3
)
```

**Run InternAgent with Groq:**
```bash
# Use most powerful model for research ideas
python launch_dolphin.py \
    --model openai/gpt-oss-120b \
    --code_model openai/gpt-oss-120b \
    --experiment point_classification_modelnet \
    --topic "novel attention mechanisms for point cloud classification"

# Use smaller model for faster implementation
python launch_dolphin.py \
    --model openai/gpt-oss-20b \
    --experiment image_classification_cifar100 \
    --topic "efficient CNN architectures"
```

**Test Groq integration:**
```bash
python groq_examples.py
```




