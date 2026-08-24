import os
import sys
from dotenv import load_dotenv
from google import genai

# Load env variables from root or parent directory
load_dotenv()
load_dotenv("../.env")

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[-] Error: GEMINI_API_KEY environment variable is not set in .env.")
        sys.exit(1)
        
    print(f"[+] Found GEMINI_API_KEY: {api_key[:6]}...{api_key[-4:] if len(api_key) > 10 else ''}")
    
    try:
        print("[+] Initializing Gemini client...")
        # Initialize genai Client; it picks up GEMINI_API_KEY from environment automatically.
        client = genai.Client()
        
        print("[+] Listing available models from Gemini API...")
        models = client.models.list()
        for m in models:
            print(f"  - {m.name}")
        
        # Use the model recommended by the API
        model_name = "gemini-3.6-flash"
        print(f"[+] Sending test request to {model_name}...")
        response = client.models.generate_content(
            model=model_name,
            contents="Say 'Gemini API connectivity test successful!' and give a one-sentence fun fact about cryptography.",
        )
        
        print("\n[+] Response received from Gemini:")
        print("-" * 50)
        print(response.text.strip())
        print("-" * 50)
        print("[+] Test completed successfully!")
        
    except Exception as e:
        print(f"[-] Error during Gemini connectivity test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
