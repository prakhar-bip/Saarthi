import urllib.request
import urllib.error

if __name__ == "__main__":
    req = urllib.request.Request('http://127.0.0.1:8000/api/chats/test/messages', method='OPTIONS')
    req.add_header('Origin', 'http://127.0.0.1:3000')
    req.add_header('Access-Control-Request-Method', 'POST')
    
    try:
        res = urllib.request.urlopen(req)
        print(res.status)
        print(res.headers)
    except urllib.error.HTTPError as e:
        print(e.code)
        print(e.headers)
