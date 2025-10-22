#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo "🔹 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Ensure GROQ_API_KEY is set
if [ -z "$GROQ_API_KEY" ]; then
    echo "❌ Error: GROQ_API_KEY is not set in the environment or .env file."
    echo "Please add it to .env or run: export GROQ_API_KEY=your_api_key_here"
    exit 1
fi

# Run the Dolphin launcher with environment variable
python launch_dolphin.py \
    --model openai/gpt-oss-120b \
    --code_model openai/gpt-oss-120b \
    --experiment point_classification_modelnet \
    --topic "novel attention mechanisms for point cloud classification" \
    --rag \
    --num-ideas 3 \
    --round 0 \
    --check_similarity \
    --embedding_model sentence-transformers/all-roberta-large-v1 \
    --save_name groq_test_run \
    | tee launch_dolphin.txt
