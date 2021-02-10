from pyngrok import ngrok

ngrok.set_auth_token("1nwBBRjIAdTBbejioEh6aFA8Tfy_87pqmB1vui6bShgMay73b")
# ngrok.kill()
http_tunnel = ngrok.connect()
# print(http_tunnel)


tunnels = ngrok.get_tunnels()
print(tunnels)
https_tunnel = tunnels[0]
# print(address)
url = https_tunnel.public_url
print(url)

file_object = open("postback.txt", "w+")
file_object.write(url)
file_object.close()