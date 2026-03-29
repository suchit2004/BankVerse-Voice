import asyncio
import json
import os
from dotenv import load_dotenv
from groq import AsyncGroq
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

load_dotenv(override=True)
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="BankVerse Voice API - Phase 2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AI Pipeline Modules ---

class ASRModule:
    """ Speech-to-Text Module """
    def __init__(self):
        self.client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

    async def transcribe(self, audio_bytes: bytes) -> str:
        if not self.client:
            await asyncio.sleep(0.3)
            return "Namaskar, mala mazya account chi mahiti havi ahe."
            
        try:
            # Pass the webm binary payload to Groq Whisper v3 Turbo
            file_tuple = ("audio.webm", audio_bytes)
            transcription = await self.client.audio.transcriptions.create(
              file=file_tuple,
              model="whisper-large-v3-turbo",
              response_format="json"
            )
            return transcription.text
        except Exception as e:
            print(f"ASR Error: {e}")
            return f"[Voice transcription failed: {e}]"

class TranslationModule:
    """ Neural Machine Translation Module """
    def __init__(self):
        self.client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

    async def translate_to_english(self, text: str, source_lang="Marathi") -> str:
        try:
            system_prompt = f"You are a professional translator. Translate the following text from {source_lang} to English. Provide ONLY the translated English text. Do not add any conversational filler, explanations, or quotes around the output."
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.1
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Translation Error (to English): {e}")
            return "Hello, I need information about my account."
    
    async def translate_to_regional(self, text: str, target_lang="Marathi") -> str:
        try:
            system_prompt = f"You are a professional translator. Translate the following English text to {target_lang}. Provide ONLY the translated {target_lang} text. Do not add any conversational filler, explanations, or quotes around the output."
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.1
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Translation Error (to Regional): {e}")
            return "Namaskar, tumhala kontya account chi mahiti havi ahe?" # "Hello, which account info do you need?"

class TTSModule:
    """ Cloud TTS Integration """
    def __init__(self):
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        
    async def synthesize(self, text: str) -> str:
        if not self.openai_key:
            return None
        try:
            import httpx
            import base64
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={"Authorization": f"Bearer {self.openai_key}"},
                    json={"model": "tts-1", "input": text, "voice": "nova"}
                )
                if response.status_code == 200:
                    return base64.b64encode(response.content).decode("utf-8")
        except Exception as e:
            print(f"Cloud TTS Error: {e}")
        return None

class BankingLLM:
    """ Banking Domain Context & Agentic Logic """
    def __init__(self):
        self.client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

    async def generate_guidance(self, english_text: str, chat_history: list = None) -> dict:
        if not self.client:
            await asyncio.sleep(0.5)
            return {
                "intent": "account_inquiry",
                "entities": {"account_type": None},
                "prompt": "Client missing.",
                "suggested_response": "Hello"
            }
            
        try:
            system_prompt = """You are BankVerse Voice, an AI assistant for frontline bank branch staff in India.
Your goal is to guide the staff on how to assist the customer based on the live translated transcript.
If the customer asks for a balance, set intent to 'check_balance' and extract the 'account_type' entity (savings, current, or loan).
If the customer asks about bank procedures (loans, cards, account closure), set intent to 'policy_inquiry' and extract 'policy_topic'.
ALWAYS output a final JSON containing exactly these keys: "intent", "entities" (dict), "prompt", and "suggested_response"."""

            messages = [{"role": "system", "content": system_prompt}]
            if chat_history:
                messages.extend(chat_history[-10:])
            messages.append({"role": "user", "content": f"Customer transcript: {english_text}"})

            chat_completion = await self.client.chat.completions.create(
                messages=messages,
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result_str = chat_completion.choices[0].message.content
            result = json.loads(result_str)
            
            # Formally execute the mock function manually if requested by the LLM
            if result.get("intent") == "check_balance":
                acc_type = result.get("entities", {}).get("account_type", "savings")
                if isinstance(acc_type, str):
                    acc_type = acc_type.lower()
                else:
                    acc_type = "savings"
                    
                import sqlite3, os
                db_path = os.path.join(os.path.dirname(__file__), "bank_data.db")
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT balance FROM accounts WHERE account_type = ?", (acc_type,))
                    row = cursor.fetchone()
                    conn.close()
                    bal = f"₹{row[0]:,.2f}" if row else "₹0.00"
                except Exception as e:
                    print(f"DB Error: {e}")
                    bal = "Error fetching balance"
                
                messages.append({"role": "assistant", "content": result_str})
                messages.append({"role": "user", "content": f"System Action Result: The {acc_type} account balance is {bal}. Now update your JSON. The 'prompt' MUST state the exact balance to the staff."})
                
                final_completion = await self.client.chat.completions.create(
                    messages=messages,
                    model="llama-3.1-8b-instant",
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                return json.loads(final_completion.choices[0].message.content)

            # RAG Document Retrieval block
            if result.get("intent") == "policy_inquiry":
                topic = result.get("entities", {}).get("policy_topic", "")
                topic_lower = str(topic).lower()
                
                if "loan" in topic_lower:
                    policy_text = "BankVerse Home Loan Policy: Require Proof of identity (Aadhar/PAN), Last 6 months bank statements, Last 3 months salary slips. Interest rate 8.5% p.a. minimum."
                elif "card" in topic_lower:
                    policy_text = "BankVerse Credit Card Policy: Minimum credit score of 750 required. Zero joining fee for the first year."
                elif "close" in topic_lower or "closure" in topic_lower:
                    policy_text = "BankVerse Account Closure Policy: Customer must visit their home branch in-person with original passbook and checkbook."
                else:
                    policy_text = "No exact policy retrieved for this topic. Ask customer to contact general support on 1800-BANK-VERSE."
                
                messages.append({"role": "assistant", "content": result_str})
                messages.append({"role": "user", "content": f"System RAG Result: Retrieved policy snippet: '{policy_text}'. Update your JSON. The 'prompt' MUST summarize this exact policy for the staff to read."})
                
                final_completion = await self.client.chat.completions.create(
                    messages=messages,
                    model="llama-3.1-8b-instant",
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                return json.loads(final_completion.choices[0].message.content)
                
            return result
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "intent": "error",
                "entities": {},
                "prompt": f"System error generating response: {e}",
                "suggested_response": "I apologize, our internal systems are momentarily facing issues."
            }

    async def generate_summary(self, chat_history: list) -> str:
        if not self.client or not chat_history:
            return "No conversation history available to summarize."
        try:
            history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
            system_prompt = "You are a bilingual (English and Marathi) banking CRM summarizer. Create a brief, professional summary of the customer interaction below for the bank's records. Output the summary as a string."
            comp = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Interaction Log:\n{history_text}"}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.2
            )
            return comp.choices[0].message.content.strip()
        except Exception as e:
            return f"Failed to generate summary: {e}"

# Instantiate global pipeline modules
asr = ASRModule()
translator = TranslationModule()
llm = BankingLLM()
tts = TTSModule()

@app.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected via WebSocket.")
    chat_history = []
    try:
        while True:
            # 1. Receive data (text or bytes)
            message = await websocket.receive()
            
            if "text" in message:
                # Check for UI Commands like summarize
                try:
                    text_data = json.loads(message["text"])
                    if text_data.get("action") == "summarize":
                        summary = await llm.generate_summary(chat_history)
                        await websocket.send_text(json.dumps({"type": "summary", "content": summary}))
                except:
                    pass
                continue
                
            if "bytes" in message:
                audio_data = message["bytes"]
                
                # Step 1: Speech to Text
                original_transcript = await asr.transcribe(audio_data)
                english_transcript = await translator.translate_to_english(original_transcript)
                
                # Step 3: LLM Intent Extraction & Staff Guidance Generation
                llm_result = await llm.generate_guidance(english_transcript, chat_history)
                
                # Update Context Memory
                chat_history.append({"role": "user", "content": f"Customer: {english_transcript}"})
                chat_history.append({"role": "assistant", "content": f"Agent Guidance: {llm_result.get('prompt')} | Reccomended Reply: {llm_result.get('suggested_response')}"})
                
                # Step 4: Translation and TTS
                regional_response = await translator.translate_to_regional(llm_result["suggested_response"])
                cloud_audio_b64 = await tts.synthesize(regional_response)
                
                # Step 5: Send payload
                response_payload = {
                    "type": "message",
                    "transcript": original_transcript,
                    "translation": english_transcript,
                    "speaker": "Customer",
                    "prompt": llm_result["prompt"],
                    "suggested_response": llm_result["suggested_response"],
                    "regional_response": regional_response,
                    "audio_base64": cloud_audio_b64
                }
                await websocket.send_text(json.dumps(response_payload))
                
    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"Error in WebSocket pipeline: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
