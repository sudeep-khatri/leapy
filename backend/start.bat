@echo off
echo Starting LipiAI backend...

if not exist ".env" (
    echo ERROR: .env file not found.
    echo Copy .env.example to .env and set your GEMINI_API_KEY.
    pause
    exit /b 1
)

python app.py
pause
