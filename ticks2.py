import selenium
from selenium import webdriver

driver = webdriver.Chrome(executable_path=r"C:\Users\gkaranam\Downloads\chromedriver.exe")
driver.get('https://kite.zerodha.com/connect/login?sess_id=oBImlEqZ9iEFTVRe5B0B7wg2WtMpe5PJ')

driver.find_element_by_xpath("//input[@placeholder='User ID']").send_keys("DG0619")
driver.find_element_by_xpath("//input[@placeholder='Password']").send_keys("mahalakshmi2")

#//*[@id="u_0_8"]    #u_0_8

#driver.find_element_by_css_selector("input#pass").send_keys(Keys.ENTER)
driver.find_element_by_xpath("//button[@class='button-orange wide']").click()
