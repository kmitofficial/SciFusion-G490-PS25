# Using InternAgent with Ollama and DeepSeek-V2:16B

This guide helps you set up and run InternAgent using a local Ollama deployment with the DeepSeek-V2:16B model.

## Prerequisites

1. **Install Ollama**: Download from [ollama.com](https://ollama.com/download)
2. **Ensure sufficient disk space**: DeepSeek-V2:16B requires ~8.9GB of storage
3. **RAM requirements**: At least 16GB RAM recommended for smooth operation

## Quick Setup

### Option 1: Automated Setup (Recommended)

**For Windows (PowerShell):**
```powershell
# Start Ollama server first
ollama serve

# In a new PowerShell window, run the setup script
.\setup_ollama.ps1
```

**For Linux/macOS:**
```bash
# Start Ollama server first
ollama serve &

# Run the setup script
chmod +x setup_ollama.sh
./setup_ollama.sh
```

### Option 2: Manual Setup

1. **Start Ollama server:**
   ```bash
   ollama serve
   ```

2. **Pull the DeepSeek-V2:16B model:**
   ```bash
   ollama pull deepseek-v2:16b
   ```

3. **Create optimized model with extended context:**
   ```bash
   ollama create deepseek-v2:16b-32k -f deepseek-v2-16b-32k-modelfile
   ```

4. **Test the model:**
   ```bash
   ollama run deepseek-v2:16b-32k
   ```

## Running InternAgent

Once setup is complete, you can run InternAgent with Ollama:

### Basic Usage
```bash
python launch_dolphin.py \
  --model localhost-deepseek-v2-16b \
  --code_model localhost-deepseek-v2-16b \
  --experiment point_classification_modelnet
```

### With Custom Parameters
```bash
python launch_dolphin.py \
  --model localhost-deepseek-v2-16b \
  --code_model localhost-deepseek-v2-16b \
  --experiment image_classification_cifar100 \
  --num-ideas 10 \
  --parallel 2 \
  --gpus "0,1"
```

### Available Experiments
- `point_classification_modelnet`
- `image_classification_cifar100` 
- `sentiment_classification_sst2`

## Configuration Details

### Model Configuration
The `deepseek-v2-16b-32k-modelfile` contains optimized parameters:
- **Context Length**: 32,768 tokens (extended from default)
- **Max Generation**: 8,192 tokens
- **Temperature**: 0.7 (balanced creativity/consistency)
- **Top-K**: 40, Top-P: 0.9 (sampling parameters)

### Performance Tips

1. **Memory Management**: The model requires ~16GB RAM. Close other applications if needed.
2. **GPU Acceleration**: Ollama automatically uses GPU if available (NVIDIA/AMD).
3. **Concurrent Usage**: Avoid running multiple heavy models simultaneously.

### Troubleshooting

**Model not found error:**
```bash
# Check available models
ollama list

# Recreate if missing
ollama create deepseek-v2:16b-32k -f deepseek-v2-16b-32k-modelfile
```

**Connection refused:**
```bash
# Ensure Ollama server is running
ollama serve

# Check server status
curl http://localhost:11434/api/tags
```

**Out of memory:**
```bash
# Reduce concurrent processes
python launch_dolphin.py --parallel 1

# Or use smaller batch size in experiments
```

## Advanced Configuration

### Custom Model Parameters
Edit `deepseek-v2-16b-32k-modelfile` to adjust:
- `num_ctx`: Context window size
- `num_predict`: Maximum generation length  
- `temperature`: Response randomness (0.0-1.0)
- `repeat_penalty`: Repetition control

### Multiple Models
You can set up multiple model variants:
```bash
# Creative variant
ollama create deepseek-v2:16b-creative -f creative-modelfile

# Conservative variant  
ollama create deepseek-v2:16b-conservative -f conservative-modelfile
```

### Integration with Aider
The system automatically configures Aider (the coding assistant) to use your Ollama model. The model name `ollama/deepseek-v2:16b-32k` is registered for code generation tasks.

## Cost Benefits

Using Ollama with local models provides:
- **Zero API costs** after initial setup
- **Complete privacy** - no data sent to external services  
- **Offline capability** - works without internet connection
- **Customizable parameters** - fine-tune for your specific needs

## Next Steps

After successful setup:
1. Try different experiments to find your preferred workflow
2. Adjust model parameters based on your hardware capabilities
3. Explore the various InternAgent features with your local setup
4. Consider setting up multiple model variants for different use cases