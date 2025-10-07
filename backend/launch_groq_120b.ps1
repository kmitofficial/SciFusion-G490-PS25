# InternAgent Launch Script for Windows PowerShell with Groq 120B
# Make sure you're in the InternAgent directory and have activated venv312

Write-Host "🚀 Starting InternAgent with Groq GPT-OSS 120B model..." -ForegroundColor Green
Write-Host "📍 Experiment: Point Classification on ModelNet40" -ForegroundColor Yellow
Write-Host "🤖 Model: openai/gpt-oss-120b (Groq's most powerful model)" -ForegroundColor Cyan

# Run InternAgent with Groq 120B model
python launch_dolphin.py `
    --model "openai/gpt-oss-120b" `
    --code_model "openai/gpt-oss-120b" `
    --experiment "point_classification_modelnet" `
    --topic "novel attention mechanisms for point cloud classification" `
    --rag `
    --num-ideas 3 `
    --round 0 `
    --check_similarity `
    --embedding_model "sentence-transformers/all-roberta-large-v1" `
    --save_name "groq_point_classification" `
    | Tee-Object -FilePath "groq_launch_log.txt"

Write-Host "✅ InternAgent execution completed!" -ForegroundColor Green
Write-Host "📄 Log saved to: groq_launch_log.txt" -ForegroundColor Blue
Write-Host "📁 Results saved to: results/groq_point_classification/" -ForegroundColor Blue