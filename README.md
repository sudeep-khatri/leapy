# leapy

A full-stack script and language support app for working with Nepal Bhasa, Nepali, and historical scripts. The project combines a Python backend for AI-assisted translation and OCR-style analysis with a React frontend for chatting, conversion, and script rendering.

This project is built around a simple idea: make it easier to read, translate, and convert text between Devanagari, Newa, and Ranjana script while keeping the experience lightweight and approachable.

## What this project does

- Chat with an LLM in Nepal Bhasa or Nepali
- Convert text between Devanagari and traditional scripts such as Newa and Ranjana
- Translate between Nepali and Nepal Bhasa
- Analyze inscription-like images and return a translation plus summary
- Serve a modern frontend UI for experimentation and practical use

## Project structure

```text
leapy/
├── backend/           # Flask API and AI service logic
├── frontend/          # Vite + React app
├── ml/                # ML/training and OCR-related code
├── checkpoints/       # Model checkpoints
├── data_splits/       # Dataset split files
├── LICENSE.md         # Project license
├── .env.example       # Root environment template
├── .gitignore
└── README.md          # Project overview
```

## Tech stack

- Backend: Python, Flask
- AI: Google Gemini
- Translation: deep-translator
- Frontend: React, Vite, TypeScript, Tailwind
- Script conversion: aksharamukha

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/sudeep-khatri/leapy.git
cd leapy
```

### 2. Set up the backend

```bash
cd backend
copy .env.example .env
```

Then update `.env` with your Gemini API key:

```env
GEMINI_API_KEY=your_key_here
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
python app.py
```

The API runs at:

```text
http://localhost:5001
```

### 3. Set up the frontend

```bash
cd ../frontend
copy .env.example .env
```

Example frontend environment values:

```env
VITE_LIPIAI_CHAT_URL=http://localhost:5001
VITE_LIPIAI_ANALYSIS_URL=http://localhost:5001/api/analyze
```

Install frontend dependencies:

```bash
npm install
```

Run the frontend:

```bash
npm run dev
```

Open the app in a browser at:

```text
http://localhost:3000
```

## Main backend endpoints

### `POST /api/chat`
Used for chat responses in the selected script and language mode.

### `POST /api/convert`
Converts text to the requested script target, such as Newa or Ranjana.

### `POST /api/translate`
Translates text between supported language codes.

### `POST /api/analyze`
Accepts an uploaded image and returns a translation and summary.

### `GET /health`
Health check endpoint for verifying the backend is running.

## Features

- Script-aware conversation flow
- Script conversion between Devanagari and traditional scripts
- Translation support for Nepal Bhasa and Nepali
- Image-based text analysis pipeline
- Clean frontend with conversational UX

## Notes

This project is intended as a practical research and app prototype for multilingual and script-preserving text workflows. The backend especially focuses on Nepal Bhasa and historical script rendering.

## License

This project is licensed under the MIT License. See [LICENSE.md](LICENSE.md) for details.

## Contributing

Contributions are welcome. If you want to improve the translation logic, add new script conversions, or improve the frontend UX, feel free to open a pull request or start a discussion.
