import logging
from kiteconnect import KiteConnect
from kiteconnect import KiteTicker

import datetime,time,os,random;


kws = "";
kite = "";

def get_login(api_k,api_s): # log in to zerodha API panel
	global kws,kite;
	kite = KiteConnect(api_key=api_k)

	print("[*] Generate access Token : ",kite.login_url())
	request_tkn = input("[*] Enter Your Request Token Here : ");

	data = kite.generate_session(request_tkn, api_secret=api_s)
	kite.set_access_token(data["access_token"])
	print(data["access_token"])
	kws = KiteTicker(api_k, data["access_token"])

api_k = "dysoztj41hntm1ma"; #api_key
api_s = "rzgyg4edlvcurw4vp83jl5io9b610x94"; #api_secret

get_login(api_k,api_s); #function that used to get connected with API