import requests
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'
}
with requests.session() as s:
    url = "https://kite.zerodha.com/connect/login?api_key=dysoztj41hntm1ma"
    r = s.get(url, headers=headers)
    print(r.content)