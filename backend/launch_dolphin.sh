#!/bin/bash

export OPENAI_API_KEY={your_openai_key}
export S2_API_KEY={your_semantic_scholar_key}
export INS1_API_KEY={your_intern-s1_key}
export GROQ_API_KEY={your_groq_key}
export DEEPSEEK_API_KEY={your_deepseek_key}

python launch_dolphin.py \
    --model gpt-4o-2024-11-20 \
    --code_model gpt-4o-2024-11-20 \
    --experiment exp_name (e.g., point_classification_modelnet) \
    --topic "your topic" \
    --rag \
    --num-ideas 3 \
    --round 0 \
    --check_similarity \
    --embedding_model sentence-transformers/all-roberta-large-v1 \
    --save_name {your_save_name} \
    | tee launch_dolphin.txt

# Generate ideas using Groq's most powerful model (120B parameters)
# python launch_dolphin.py \
#     --model openai/gpt-oss-120b \
#     --code_model openai/gpt-oss-120b \
#     --experiment point_classification_modelnet \
#     --topic "novel attention mechanisms for point cloud classification" \
#     --rag \
#     --num-ideas 3 \
#     --round 0 \
#     --check_similarity \
#     --embedding_model sentence-transformers/all-roberta-large-v1 \
#     --save_name groq_point_classification \
#     | tee groq_launch.txt

# Generate ideas using Groq's smaller model (20B parameters)
# python launch_dolphin.py \
#     --model openai/gpt-oss-20b \
#     --code_model openai/gpt-oss-20b \
#     --experiment image_classification_cifar100 \
#     --topic "efficient convolutional architectures for resource-constrained devices" \
#     --rag \
#     --num-ideas 5 \
#     --round 0 \
#     --save_name groq_efficient_cnns \
#     | tee groq_coding.txt

# Generate ideas using Intern-S1
# python launch_dolphin.py \
#     --model Intern-S1 \
#     --code_model gpt-4o-2024-11-20 \
#     --experiment exp_name (e.g., point_classification_modelnet) \
#     --topic "your topic" \
#     --rag \
#     --num-ideas 3 \
#     --round 0 \
#     --check_similarity \
#     --embedding_model sentence-transformers/all-roberta-large-v1 \
#     --save_name {your_save_name} \
#     | tee launch_dolphin.txt