#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo "🔹 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Ensure GOOGLE_API_KEY is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ Error: GOOGLE_API_KEY is not set in the environment or .env file."
    echo "Please add it to .env or run: export GOOGLE_API_KEY=your_api_key_here"
    echo "Get your key from: https://aistudio.google.com/app/apikey"
    exit 1
fi

# Run the Dolphin launcher with environment variable
python launch_dolphin.py \
    --model gemini-2.5-flash-lite \
    --code_model gemini-2.5-flash-lite \
    --experiment Chem_LLM \
    --topic "Predicting Chemical Properties of Compounds Using Large Language Models (LLMs)" \
    --rag \
    --max_papers 10 \
    --num-ideas 2 \
    --round 0 \
    --check_similarity \
    --embedding_model sentence-transformers/all-roberta-large-v1 \
    --save_name chem_test \
    | tee launch_dolphin.txt