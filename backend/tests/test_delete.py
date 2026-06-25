import requests

if __name__ == "__main__":
    url = "http://127.0.0.1:8000/api/chats/fake-id"
    headers = {"Authorization": "Bearer fake-token"}
    r = requests.delete(url, headers=headers)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
