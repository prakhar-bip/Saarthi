import urllib.request
import urllib.error
import json

if __name__ == "__main__":
    req = urllib.request.Request('http://127.0.0.1:8000/api/chats/test-chat/messages', method='OPTIONS')
    req.add_header('Origin', 'http://127.0.0.1:3000')
    req.add_header('Access-Control-Request-Method', 'POST')
    
    try:
        res = urllib.request.urlopen(req)
        print("OPTIONS headers:", res.headers)
    except urllib.error.HTTPError as e:
        print("OPTIONS Status:", e.code)
    
    req2 = urllib.request.Request('http://127.0.0.1:8000/api/chats/test-chat/messages', method='POST')
    req2.add_header('Content-Type', 'application/json')
    req2.add_header('Origin', 'http://127.0.0.1:3000')
    
    try:
        res = urllib.request.urlopen(req2, data=b'{"text": "hello"}')
        print("POST Status:", res.status)
        print("POST headers:", res.headers)
    except urllib.error.HTTPError as e:
        print("POST Status:", e.code)
        print("POST headers:", e.headers)
