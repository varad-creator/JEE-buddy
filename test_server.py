import requests
import sys

def test_chat():
    url = "http://127.0.0.1:8000/chat"
    
    payload = {
        "user_id": "test_user_001",
        "message": "bhai physics me lag gayi hai",
        "history": []
    }
    
    try:
        print(f"Sending request to {url}...")
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            print("Success!")
            print("Response:", response.json())
        else:
            print("Error:", response.status_code)
            print(response.text)
            
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    test_chat()
