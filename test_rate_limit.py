import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
HEADERS = {"X-API-KEY": API_KEY}
QUERY_URL = "http://127.0.0.1:8000/api/v1/query"

def test_limit():
    """
    Tests the rate limit for the synchronous /query endpoint.
    """
    if not API_KEY:
        print("Error: API_KEY not found in environment. Please set it in your .env file.")
        return

    print("Sending 6 requests to /api/v1/query to test the 5/minute limit...")
    
    with requests.Session() as session:
        session.headers.update(HEADERS)
        
        for i in range(1, 7):
            try:
                response = session.post(QUERY_URL, json={"question": f"test {i}"})
                print(f"Request {i}: Status Code {response.status_code}")
                
                if response.status_code == 429:
                    print("  -> Successfully received 429 Too Many Requests!")
                    print(f"  -> Retry-After header: {response.headers.get('Retry-After')}")
            
            except requests.exceptions.RequestException as e:
                print(f"Request {i}: Failed to connect. Is the server running? Error: {e}")
                break

            time.sleep(0.1)

if __name__ == "__main__":
    test_limit()