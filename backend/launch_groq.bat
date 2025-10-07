@echo off
echo Activating Python 3.12 virtual environment...
call .\venv312\Scripts\activate.bat

echo Loading environment variables from .env file...
for /f "tokens=1,2 delims==" %%a in (.env) do set %%a=%%b
echo Loaded GROQ_API_KEY

echo.
echo Starting InternAgent with Groq GPT-OSS 120B model...
echo Experiment: Point Classification on ModelNet40
echo Model: openai/gpt-oss-120b (Groq's most powerful model)
echo Topic: Novel attention mechanisms for point cloud classification
echo Ideas to generate: 3
echo RAG enabled for better research ideas
echo ================================================================================

python launch_dolphin.py ^
    --model "openai/gpt-oss-120b" ^
    --code_model "openai/gpt-oss-120b" ^
    --experiment "point_classification_modelnet" ^
    --topic "novel attention mechanisms for point cloud classification" ^
    --rag ^
    --num-ideas 3 ^
    --round 0 ^
    --check_similarity ^
    --embedding_model "sentence-transformers/all-roberta-large-v1" ^
    --save_name "groq_point_classification"

echo.
echo ================================================================================
echo InternAgent execution completed!
echo Output displayed in console
echo Results saved to: results/groq_point_classification/
echo You can now review the generated research ideas and experimental results!
pause