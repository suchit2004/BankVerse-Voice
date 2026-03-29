# BankVerse Voice 🎙️

A real-time, multilingual Gen-AI Banking Voice Assistant built with React, FastAPI, Llama-3, and WebSockets. Designed to empower frontline bank staff in India by automatically translating Marathi/English interactions, extracting banking intents, looking up live account data, and maintaining dual-language context memory.

## 🚀 Features
- **Live Multilingual Translation**: Instantly captures audio, transcribes it, and routes regional dialects (Marathi) into English using near-zero latency Groq Llama-3 inference.
- **Agentic Intent Routing**: Autonomous AI decision loop that parses user semantics ("What is my balance?") and directly hooks into an SQLite Database (`bank_data.db`) via simulated function calling.
- **Policy RAG**: Retrieves strict internal banking guidelines (loans, credit scores, account closures) on demand to ensure perfect procedural compliance without AI hallucinations.
- **Contextual Memory**: Persistently remembers session context across the WebSocket stream so complex follow-up questions work fluidly.
- **Cloud Text-to-Speech (TTS)**: Synthesizes ultra-realistic OpenAI audio and pipes it back to the UI, seamlessly degrading to the browser's Native Speech synthesis if offline.
- **CRM Summaries**: One-click generation of fully structured, dual-language interaction summaries for immediate bank ticket filing.

## 🛠️ Stack Architecture
- **Frontend**: React.js (Vite), TailwindCSS, Native MediaRecorder API, WebSocket API
- **Backend**: Python, FastAPI, Uvicorn, SQLite3, HTTPX
- **AI Engine**: Groq (`llama-3.1-8b-instant`), OpenAI TTS (`tts-1-nova`)

## ⚡ Local Quickstart

### 1. Backend API Hub
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

*Required: Create a `.env` file inside `/backend` with your keys:*
```env
GROQ_API_KEY=gsk_your_key_here
OPENAI_API_KEY=optional_key_here
```

*Seed the Database and Boot the Server:*
```bash
python init_db.py
python main.py
```
> The API will bind to `ws://localhost:8000/ws/audio` for voice streaming.

### 2. Frontend Dashboard
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
> The React dashboard will be live at `http://localhost:5173`. Grant microphone permissions and speak!
