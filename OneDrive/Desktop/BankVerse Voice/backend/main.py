import asyncio
import json
import os
from dotenv import load_dotenv
from groq import AsyncGroq
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import db_manager

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

    async def generate_guidance(self, english_text: str, chat_history: list = None, session_state: dict = None) -> dict:
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

CUSTOMER AUTHENTICATION RULES:
1. If the customer is NOT authenticated (the system will provide auth status), they must be authenticated before checking balance, viewing transactions, loan inquiries, or transferring funds.
2. To authenticate, they must first state their name or customer ID (intent: 'request_auth', entities: 'customer_name' or 'customer_id').
3. Once we find the customer, they must state their 4-digit verification code (intent: 'verify_auth', entities: 'verification_code').
4. If they try to check balance, transfer funds, or view transactions without being logged in, tell them they need to authenticate first.

AVAILABLE INTENTS:
- 'request_auth': Stating name/ID to log in. Entities: 'customer_name', 'customer_id'.
- 'verify_auth': Speaking 4-digit verification code. Entities: 'verification_code'.
- 'check_balance': Checking account balance. Entities: 'account_type' (savings, current, loan, fixed_deposit).
- 'view_transactions': Listing recent transactions. Entities: 'account_type'.
- 'view_loans': Inquiring about outstanding loans.
- 'transfer_funds': Sending money. Entities: 'recipient_name' (str) and 'amount' (number).
- 'policy_inquiry': General bank guidelines. Entities: 'policy_topic' (loan, card, close).

ALWAYS output a final JSON containing exactly these keys: "intent", "entities" (dict), "prompt", and "suggested_response"."""

            current_status = "UNAUTHENTICATED"
            if session_state and session_state.get("authenticated_customer"):
                cust = session_state["authenticated_customer"]
                current_status = f"AUTHENTICATED as ID: {cust['customer_id']}, Name: {cust['name']}, Credit Score: {cust['credit_score']}"
            elif session_state and session_state.get("auth_pending_customer"):
                cust = session_state["auth_pending_customer"]
                current_status = f"AUTH_PENDING (Verification code requested for Name: {cust['name']})"

            system_prompt_with_state = f"{system_prompt}\n\nCurrent Session Auth Status: {current_status}"

            messages = [{"role": "system", "content": system_prompt_with_state}]
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
            
            # --- Intent Execution Block ---
            
            # Customer Authentication Request
            if result.get("intent") == "request_auth":
                name = result.get("entities", {}).get("customer_name")
                cust_id = result.get("entities", {}).get("customer_id")
                
                customer = None
                if cust_id:
                    customer = db_manager.get_customer_by_id(cust_id)
                elif name:
                    customer = db_manager.get_customer_by_name(name)
                    
                if customer:
                    if session_state is not None:
                        session_state["auth_pending_customer"] = customer
                    sys_msg = f"System Auth Result: Customer found: {customer['name']} (ID: {customer['customer_id']}). State to user that we found their profile and ask for their 4-digit verification code."
                else:
                    sys_msg = "System Auth Result: Customer not found. Prompt the customer to repeat their name or ID."
                    
                messages.append({"role": "assistant", "content": result_str})
                messages.append({"role": "user", "content": sys_msg})
                
                final_completion = await self.client.chat.completions.create(
                    messages=messages,
                    model="llama-3.1-8b-instant",
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                return json.loads(final_completion.choices[0].message.content)

            # Customer Verification Code
            if result.get("intent") == "verify_auth":
                code = result.get("entities", {}).get("verification_code")
                pending_cust = session_state.get("auth_pending_customer") if session_state else None
                
                if not pending_cust:
                    sys_msg = "System Verification Result: No authentication request is pending. Ask the customer to state their name first."
                else:
                    is_valid = db_manager.verify_customer_code(pending_cust["customer_id"], str(code))
                    if is_valid:
                        if session_state is not None:
                            session_state["authenticated_customer"] = pending_cust
                            session_state["auth_pending_customer"] = None
                        sys_msg = f"System Verification Result: Success. The customer {pending_cust['name']} is now logged in. Thank them and ask how to help."
                    else:
                        sys_msg = "System Verification Result: Failed. The verification code is incorrect. Ask them to speak the code again."
                        
                messages.append({"role": "assistant", "content": result_str})
                messages.append({"role": "user", "content": sys_msg})
                
                final_completion = await self.client.chat.completions.create(
                    messages=messages,
                    model="llama-3.1-8b-instant",
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                return json.loads(final_completion.choices[0].message.content)
            
            # Formally execute the mock function manually if requested by the LLM
            if result.get("intent") == "check_balance":
                acc_type = result.get("entities", {}).get("account_type", "savings")
                if isinstance(acc_type, str):
                    acc_type = acc_type.lower()
                else:
                    acc_type = "savings"
                    
                cust = session_state.get("authenticated_customer") if session_state else None
                if not cust:
                    sys_msg = "System Action Result: Access Denied. The customer is not authenticated. They must identify themselves and verify their 4-digit code first."
                else:
                    accounts = db_manager.get_customer_accounts(cust["customer_id"])
                    matching_acc = next((a for a in accounts if a["account_type"] == acc_type), None)
                    if matching_acc:
                        bal = f"₹{matching_acc['balance']:,.2f}"
                        sys_msg = f"System Action Result: The customer {cust['name']}'s {acc_type} account ({matching_acc['account_number']}) balance is {bal}. Update your JSON. The 'prompt' MUST state this exact balance to the staff."
                    else:
                        available_accs = ", ".join([f"{a['account_type']} ({a['account_number']})" for a in accounts])
                        sys_msg = f"System Action Result: The customer {cust['name']} does not have a {acc_type} account. They have: {available_accs}. State this and ask if they wish to check another account."
                
                messages.append({"role": "assistant", "content": result_str})
                messages.append({"role": "user", "content": sys_msg})
                
                final_completion = await self.client.chat.completions.create(
                    messages=messages,
                    model="llama-3.1-8b-instant",
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                return json.loads(final_completion.choices[0].message.content)

            # View transactions intent handler
            if result.get("intent") == "view_transactions":
                acc_type = result.get("entities", {}).get("account_type", "savings")
                if isinstance(acc_type, str):
                    acc_type = acc_type.lower()
                else:
                    acc_type = "savings"
                    
                cust = session_state.get("authenticated_customer") if session_state else None
                if not cust:
                    sys_msg = "System Action Result: Access Denied. The customer is not authenticated. They must identify themselves and verify their 4-digit code first."
                else:
                    accounts = db_manager.get_customer_accounts(cust["customer_id"])
                    matching_acc = next((a for a in accounts if a["account_type"] == acc_type), None)
                    if matching_acc:
                        txs = db_manager.get_recent_transactions(matching_acc['account_number'], limit=5)
                        if txs:
                            txs_str = "\n".join([f"- {t['type'].upper()} of ₹{t['amount']:,.2f}: {t['description']}" for t in txs])
                            sys_msg = f"System Action Result: The recent transactions for {cust['name']}'s {acc_type} account ({matching_acc['account_number']}) are:\n{txs_str}\nUpdate your JSON. The 'prompt' MUST summarize these transactions clearly for the staff to read."
                        else:
                            sys_msg = f"System Action Result: No transaction history found for {cust['name']}'s {acc_type} account ({matching_acc['account_number']}). Inform the staff."
                    else:
                        available_accs = ", ".join([f"{a['account_type']} ({a['account_number']})" for a in accounts])
                        sys_msg = f"System Action Result: The customer {cust['name']} does not have a {acc_type} account. They have: {available_accs}. Inform the staff."
                
                messages.append({"role": "assistant", "content": result_str})
                messages.append({"role": "user", "content": sys_msg})
                
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
    session_state = {
        "authenticated_customer": None,
        "auth_pending_customer": None
    }
    try:
        while True:
            message = await websocket.receive()
            
            if "text" in message:
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
                
                original_transcript = await asr.transcribe(audio_data)
                english_transcript = await translator.translate_to_english(original_transcript)
                
                llm_result = await llm.generate_guidance(english_transcript, chat_history, session_state)
                
                chat_history.append({"role": "user", "content": f"Customer: {english_transcript}"})
                chat_history.append({"role": "assistant", "content": f"Agent Guidance: {llm_result.get('prompt')} | Reccomended Reply: {llm_result.get('suggested_response')}"})
                
                regional_response = await translator.translate_to_regional(llm_result["suggested_response"])
                cloud_audio_b64 = await tts.synthesize(regional_response)
                
                accounts_info = None
                if session_state["authenticated_customer"]:
                    cust_id = session_state["authenticated_customer"]["customer_id"]
                    accounts_info = db_manager.get_customer_accounts(cust_id)
                
                response_payload = {
                    "type": "message",
                    "transcript": original_transcript,
                    "translation": english_transcript,
                    "speaker": "Customer",
                    "prompt": llm_result["prompt"],
                    "suggested_response": llm_result["suggested_response"],
                    "regional_response": regional_response,
                    "audio_base64": cloud_audio_b64,
                    "customer": session_state["authenticated_customer"],
                    "accounts": accounts_info
                }
                await websocket.send_text(json.dumps(response_payload))
                
    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"Error in WebSocket pipeline: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
