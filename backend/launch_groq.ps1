# InternAgent Launch Script with Groq GPT-OSS 120B
# PowerShell version of launch_dolphin.sh for Windows

# Activate virtual environment first
Write-Host "Activating Python 3.12 virtual environment..." -ForegroundColor Cyan
& ".\venv312\Scripts\Activate.ps1"

# Set environment variables (using .env file)
Write-Host "Loading environment variables from .env file..." -ForegroundColor Cyan

# Load .env file
if (Test-Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -match "^([^=]+)=(.*)$") {
            $name = $matches[1]
            $value = $matches[2]
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
            Write-Host "Loaded $name" -ForegroundColor Green
        }
    }
} else {
    Write-Host "ERROR: .env file not found! Please make sure GROQ_API_KEY is set." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting InternAgent with Groq GPT-OSS 120B model..." -ForegroundColor Green
Write-Host "Experiment: Point Classification on ModelNet40" -ForegroundColor Yellow
Write-Host "Model: openai/gpt-oss-120b (Groq's most powerful model)" -ForegroundColor Cyan
Write-Host "Topic: Novel attention mechanisms for point cloud classification" -ForegroundColor Magenta
Write-Host "Ideas to generate: 3" -ForegroundColor Blue
Write-Host "RAG enabled for better research ideas" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor White

# Run InternAgent with Groq 120B model (from your launch_dolphin.sh)
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
    | Tee-Object -FilePath "groq_launch.txt"

Write-Host ""
Write-Host "================================================================================" -ForegroundColor White
Write-Host "InternAgent execution completed!" -ForegroundColor Green
Write-Host "Log saved to: groq_launch.txt" -ForegroundColor Blue
Write-Host "Results saved to: results/groq_point_classification/" -ForegroundColor Blue
Write-Host "You can now review the generated research ideas and experimental results!" -ForegroundColor Yellow