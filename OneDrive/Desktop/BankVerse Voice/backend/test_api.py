import json
import asyncio
from fastapi.testclient import TestClient
import main
from main import app

# Create a test client
client = TestClient(app)

# Helper mock classes to bypass network calls in tests
class MockASR:
    async def transcribe(self, audio_bytes: bytes) -> str:
        # Return a simulated transcript based on test input bytes
        if audio_bytes == b"test_name":
            return "Rajesh Kumar"
        elif audio_bytes == b"test_code":
            return "1234"
        elif audio_bytes == b"test_balance":
            return "Check balance of savings"
        return "Hello"

class MockTranslation:
    async def translate_to_english(self, text: str, source_lang="Marathi") -> str:
        return text  # Bypass translation for tests
        
    async def translate_to_regional(self, text: str, target_lang="Marathi") -> str:
        return text  # Bypass translation for tests

class MockTTS:
    async def synthesize(self, text: str) -> str:
        return "mock_base64_audio"

def test_websocket_flow():
    # Patch main API modules with mocks
    original_asr = main.asr
    original_translator = main.translator
    original_tts = main.tts
    
    main.asr = MockASR()
    main.translator = MockTranslation()
    main.tts = MockTTS()
    
    try:
        with client.websocket_connect("/ws/audio") as websocket:
            print("[OK] Connected to WebSocket endpoint")
            
            # Test 1: Change language to Hindi
            websocket.send_text(json.dumps({"action": "set_language", "language": "Hindi"}))
            response = websocket.receive_text()
            data = json.loads(response)
            assert data["type"] == "language_changed"
            assert data["language"] == "Hindi"
            print("[OK] Test 1: set_language passed")
            
            # Test 2: Identify Rajesh Kumar (request_auth)
            # Send name as mock bytes
            websocket.send_bytes(b"test_name")
            response = websocket.receive_text()
            data = json.loads(response)
            assert data["type"] == "message"
            assert data["customer"] is None  # Should not be authenticated yet
            print("[OK] Test 2: request_auth recognized profile")
            
            # Test 3: Authenticate with code (verify_auth)
            websocket.send_bytes(b"test_code")
            response = websocket.receive_text()
            data = json.loads(response)
            assert data["type"] == "message"
            assert data["customer"] is not None
            assert data["customer"]["name"] == "Rajesh Kumar"
            assert data["customer"]["kyc_status"] == "Verified"
            print("[OK] Test 3: verify_auth successfully logged in")
            
            # Test 4: Check balance
            websocket.send_bytes(b"test_balance")
            response = websocket.receive_text()
            data = json.loads(response)
            assert data["type"] == "message"
            assert data["customer"]["customer_id"] == "C1001"
            assert len(data["accounts"]) == 2
            print("[OK] Test 4: check_balance returned accounts")
            
            # Test 5: End and Summarize
            websocket.send_text(json.dumps({"action": "summarize"}))
            response = websocket.receive_text()
            data = json.loads(response)
            assert data["type"] == "summary"
            assert len(data["content"]) > 0
            print("[OK] Test 5: summarize returned session summary")
            
            print("ALL API INTEGRATION TESTS PASSED SUCCESSFULLY!")
            
    finally:
        # Restore original modules
        main.asr = original_asr
        main.translator = original_translator
        main.tts = original_tts

if __name__ == "__main__":
    test_websocket_flow()
