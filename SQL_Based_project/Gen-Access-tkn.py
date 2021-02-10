from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import traceback
from selenium import webdriver
from time import sleep

request_tkn = ''
access_tkn = ''


def parse_url_string(url):
    params = url.split('?')[1].split('&')
    car = {}
    for param in params:
        car[param.split('=')[0]] = param.split('=')[1]
    return car


def get_key(url):
    global request_tkn
    try:
        chrome_driver = webdriver.Chrome()
        chrome_driver.get(url)
        chrome_driver.maximize_window()

        sleep(2)
        chrome_driver.find_element_by_id("userid").send_keys("DG0619")
        chrome_driver.find_element_by_id("password").send_keys("millionaire1")
        chrome_driver.find_element_by_css_selector(
            "#container > div > div > div.login-form > form > div.actions > button").click()
        sleep(2)
        chrome_driver.find_element_by_id("pin").send_keys("171188")
        chrome_driver.find_element_by_css_selector(
            "#container > div > div > div.login-form > form > div.actions > button").click()
        sleep(3)
        final_url = chrome_driver.current_url
        splitted_url = parse_url_string(final_url)
        request_tkn = splitted_url['request_token']
        chrome_driver.close()
    except Exception as e:
        traceback.print_exc(e)


# get_key("https://kite.zerodha.com/connect/login?api_key=dysoztj41hntm1ma")

kws = ""
kite = ""


def get_login(api, apisecret):  # log in to zerodha API panel
    global kws, kite, request_tkn, access_tkn
    kite = KiteConnect(api_key=api)

    # print("[*] Generate access Token : ", kite.login_url())
    get_key(kite.login_url())

    data = kite.generate_session(request_tkn, api_secret=apisecret)
    kite.set_access_token(data["access_token"])
    kws = KiteTicker(api, data["access_token"])
    access_tkn = data["access_token"]


api_k = "dysoztj41hntm1ma"  # api_key
api_s = "e9u4vp3t8jx9opnmg7rkyuwhpghgim6c"  # api_secret

get_login(api_k, api_s)  # function that used to get connected with API

file_object = open("access-token.txt", "w+")
file_object.write(access_tkn)
file_object.close()

ngrok_file = open("postback.txt", "r")
postback_url = ngrok_file.read() + str("/post")


def ngrok_postback_url_update():
    global postback_url
    ngrok_driver = webdriver.Chrome()
    ngrok_driver.get("https://developers.kite.trade/login")
    ngrok_driver.maximize_window()

    sleep(1)
    ngrok_driver.find_element_by_id("id_email").send_keys("karanam.goutham@gmail.com")
    sleep(1)
    ngrok_driver.find_element_by_id("id_password").send_keys("IITIIT1!")
    sleep(1)
    ngrok_driver.find_element_by_css_selector("#main > div > form > p:nth-child(4) > input").click()
    sleep(1)
    ngrok_driver.find_element_by_xpath("/html/body/div/div/div/div/table/tbody/tr").click()
    sleep(1)
    ngrok_driver.find_element_by_id("id_postback_url").clear()
    ngrok_driver.find_element_by_id("id_postback_url").send_keys(postback_url)
    sleep(1)
    ngrok_driver.find_element_by_css_selector("#main > div > div > div.seven.columns > form > p:nth-child(8) > input").click()
    sleep(20)


ngrok_postback_url_update()
