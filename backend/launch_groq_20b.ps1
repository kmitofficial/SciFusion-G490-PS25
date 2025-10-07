# InternAgent Launch Script with Groq GPT-OSS 20B
# PowerShell version for efficient model

# Set environment variables (using .env file)
Write-Host "🔑 Loading environment variables from .env file..." -ForegroundColor Cyan

# Load .env file
if (Test-Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            $name = $matches[1]
            $value = $matches[2]
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
            Write-Host "✓ Loaded $name" -ForegroundColor Green
        }
    }
} else {
    Write-Host "❌ .env file not found! Please make sure GROQ_API_KEY is set." -ForegroundColor Red
    exit 1
}

Write-Host "`n🚀 Starting InternAgent with Groq GPT-OSS 20B model..." -ForegroundColor Green
Write-Host "📍 Experiment: Image Classification on CIFAR-100" -ForegroundColor Yellow
Write-Host "🤖 Model: openai/gpt-oss-20b (Groq's efficient model)" -ForegroundColor Cyan

# Run InternAgent with Groq 20B model
python launch_dolphin.py `
    --model "openai/gpt-oss-20b" `
    --code_model "openai/gpt-oss-20b" `
    --experiment "image_classification_cifar100" `
    --topic "efficient convolutional architectures for resource-constrained devices" `
    --rag `
    --num-ideas 5 `
    --round 0 `
    --check_similarity `
    --embedding_model "sentence-transformers/all-roberta-large-v1" `
    --save_name "groq_efficient_cnns" `
    | Tee-Object -FilePath "groq_20b_launch_log.txt"

Write-Host "✅ InternAgent execution completed!" -ForegroundColor Green
Write-Host "📄 Log saved to: groq_20b_launch_log.txt" -ForegroundColor Blue
Write-Host "📁 Results saved to: results/groq_efficient_cnns/" -ForegroundColor Blue