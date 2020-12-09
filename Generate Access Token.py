from kiteconnect import KiteConnect
from kiteconnect import KiteTicker

kws = ""
kite = ""


def get_login(api, apisecret):  # log in to zerodha API panel
	global kws, kite
	kite = KiteConnect(api_key=api)

	print("[*] Generate access Token : ", kite.login_url())
	request_tkn = input("[*] Enter Your Request Token Here : ")

	data = kite.generate_session(request_tkn, api_secret=apisecret)
	kite.set_access_token(data["access_token"])
	print(data["access_token"])
	kws = KiteTicker(api, data["access_token"])


api_k = "dysoztj41hntm1ma"  # api_key
api_s = "e9u4vp3t8jx9opnmg7rkyuwhpghgim6c"  # api_secret

get_login(api_k, api_s)  # function that used to get connected with API
