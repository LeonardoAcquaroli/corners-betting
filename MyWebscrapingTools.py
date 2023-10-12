<<<<<<< HEAD
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class MyWsTools():
    
    # Initialization arguments
    def __init__(self, driver_headless=True, driver_loglevel3=True, driver_noImg=True):
        def init_driver():
            #### options
            chrome_options = Options()
            if driver_headless == True:
                chrome_options.add_argument('--headless')
            if driver_loglevel3 == True:
                chrome_options.add_argument('log-level=3')
            if driver_noImg == True:
                chrome_options.add_argument('--blink-settings=imagesEnabled=false')
            #### service
            # chrome_service = webdriver.ChromeService(ChromeDriverManager().install())
            chrome_service = Service(ChromeDriverManager().install())
            #### webdriver
            driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
            return driver
        self.driver = init_driver()

    def cookies_handler(self, xpath: str):
        accept_button = WebDriverWait(self.driver,3).until(
                        EC.presence_of_element_located((By.XPATH,xpath))
                        )
        accept_button.click()

    def first_result_click(self, xpath='//*[@class="LC20lb MBeuO DKV0Md"]'):
        """
        :param xpath: the xpath of the list of results in the current google search page
        """
        # xpath is valid for Google Chrome
        first_result = WebDriverWait(self.driver,7).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )                                           
        first_result.click()

    def nth_result_click(self, n: int, xpath='//*[@class="LC20lb MBeuO DKV0Md"]'):
        """
        :param xpath: the xpath of the list of results in the current google search page
        :param n: the result number to click
        """
        # xpath is valid for Google Chrome
        nth_result = WebDriverWait(self.driver,5).until(
                EC.presence_of_all_elements_located((By.XPATH, xpath))
            )                                           
        nth_result[n-1].click() # n-1 since python starts counting from 0

    def login_form(self, xpath_mail: str, email_address: str, xpath_password: str, password: str, xpath_login_button: str):
        #email/username
        mail_box = WebDriverWait(self.driver,10).until(
                EC.presence_of_element_located((By.XPATH, xpath_mail))
            )
        ActionChains(self.driver).send_keys_to_element(mail_box,email_address).perform()
        #password
        pwd_box = WebDriverWait(self.driver,10).until(
                EC.presence_of_element_located((By.XPATH, xpath_password))
            )      
        ActionChains(self.driver).send_keys_to_element(pwd_box,password).perform()
        # click login button
        login_button = WebDriverWait(self.driver,10).until(
                EC.presence_of_element_located((By.XPATH, xpath_login_button))
            )      
        login_button.click()


    def click(self, xpath):
        element = WebDriverWait(self.driver,10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )                                           
        element.click()


    def elements(self,xpath: str,timeout: float = 10,text: bool = False):
        elements = WebDriverWait(self.driver,timeout).until(
            EC.presence_of_all_elements_located((By.XPATH,xpath))
        )
        if text == True:
            return [e.text for e in elements]
        else:
            return elements

    def element(self,xpath: str,timeout: float = 10,text: bool = False):
        element = WebDriverWait(self.driver,timeout).until(
            EC.presence_of_element_located((By.XPATH,xpath))
        )
        if text == True:
            return element.text
        else:
            return element


    ### INVESTMENTS DISPLAY ###
    # text_to_int function definition
    def textprice_to_int(string: str): 
        comma_position = str.find(string,',') 
        dot_position = str.find(string,'.')
        if string.count(',') > 1: # if there are more than one comma
            string = string.replace(',',"") # remove them since it should be bilions, millions and thousands separators
        if comma_position < dot_position: # if comma comes before (more at the left) the dot
            string = string.replace(',',"") # replace comma with nothing because it is the thousands separator
        elif dot_position == -1: # if dot is not present
            string = string.replace(',','.') # replace comma with dot because it is the decimal separator
        elif dot_position < comma_position: # if dot comes before (more at the left) the comma
            string = string.replace(".","").replace(",",".") # replace the dot with nothing and then the comma with a dot
        return float(string)

    # get_price function definition
    def get_price(self, source: str, ticker: str):
        """
        Retrieve the last prices from a specified web-source
        :param source: the web-source of the price (supported are: Investing.com, Borsa Italiana, Yahoo finance)
        :param tickers: a list of the tickers of the instruments to monitor
        """
        self.driver.get(f'https://www.google.com/search?q={source}+{ticker}')
        try:
            self.cookies_handler(self.driver,'//*[@id="W0wltc"]/div') # google cookies handler
        except:
            pass
        self.first_result_click(self.driver)
        if "investing" in source:
            # investing cookies handler
            try:
                self.cookies_handler(self.driver,'//*[@id="onetrust-accept-btn-handler"]')
            except:
                pass
            # get price
            last_price = self.element(self.driver,'//*[@data-test="instrument-price-last"]',text=True)
            return self.textprice_to_int(last_price)
        elif "borsa italiana" in source:
            last_price = self.element(self.driver,'//*[@class="t-text -black-warm-60 -formatPrice"]',text=True)
            return self.textprice_to_int(last_price)
        elif "yahoo" in source:
            # yahoo cookies handler
            try:
                self.cookies_handler(self.driver,'//*[@id="consent-page"]/div/div/div/form/div[2]/div[2]/button[1]')
            except:
                pass
            # get price
            last_price = self.element(self.driver,'//*[@class="Fw(b) Fz(36px) Mb(-4px) D(ib)"]',text=True)
            return self.textprice_to_int(last_price)
    ### END OF INVESTMENTS DISPLAY ###    

    #PHONE REGEX
    indicatori_del_numero = '(tel|telefono|numero|centralino|contatto|fisso)'
    spazi_e_caratteri_nonwords_dopo_indicatore = '[^(a-zA-Z0-9)](.*)'
    prefisso = '(0[0-9])'
    iteration_num_space = "([^(a-zA-Z0-9)]?)([0-9]+[^(a-zA-Z0-9\&\<\>\(\)\;)]?)+"
    PHONE_REGEX_specific = indicatori_del_numero + spazi_e_caratteri_nonwords_dopo_indicatore + prefisso + iteration_num_space
    phone_regex = "^(?:\+39\s)?\d{2,3}[\s.-]?\d{6,7}$"

    #EMAIL REGEX
    EMAIL_REGEX = "[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
=======
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class MyWsTools():
    
    # Initialization arguments
    def __init__(self, chromedriver_executable_path, driver_headless=True, driver_loglevel3=True, driver_noImg=True):
        def init_driver(executable_path=chromedriver_executable_path):
            #### options
            chrome_options = Options()
            if driver_headless == True:
                chrome_options.add_argument('--headless')
            if driver_loglevel3 == True:
                chrome_options.add_argument('log-level=3')
            if driver_noImg == True:
                chrome_options.add_argument('--blink-settings=imagesEnabled=false')
            #### service
            chrome_service = webdriver.ChromeService(executable_path=executable_path)
            #### webdriver
            driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
            return driver
        self.driver = init_driver()

    def cookies_handler(self, xpath: str):
        accept_button = WebDriverWait(self.driver,3).until(
                        EC.presence_of_element_located((By.XPATH,xpath))
                        )
        accept_button.click()

    def first_result_click(self, xpath='//*[@class="LC20lb MBeuO DKV0Md"]'):
        """
        :param xpath: the xpath of the list of results in the current google search page
        """
        # xpath is valid for Google Chrome
        first_result = WebDriverWait(self.driver,7).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )                                           
        first_result.click()

    def nth_result_click(self, n: int, xpath='//*[@class="LC20lb MBeuO DKV0Md"]'):
        """
        :param xpath: the xpath of the list of results in the current google search page
        :param n: the result number to click
        """
        # xpath is valid for Google Chrome
        nth_result = WebDriverWait(self.driver,5).until(
                EC.presence_of_all_elements_located((By.XPATH, xpath))
            )                                           
        nth_result[n-1].click() # n-1 since python starts counting from 0

    def login_form(self, xpath_mail: str, email_address: str, xpath_password: str, password: str, xpath_login_button: str):
        #email/username
        mail_box = WebDriverWait(self.driver,10).until(
                EC.presence_of_element_located((By.XPATH, xpath_mail))
            )
        ActionChains(self.driver).send_keys_to_element(mail_box,email_address).perform()
        #password
        pwd_box = WebDriverWait(self.driver,10).until(
                EC.presence_of_element_located((By.XPATH, xpath_password))
            )      
        ActionChains(self.driver).send_keys_to_element(pwd_box,password).perform()
        # click login button
        login_button = WebDriverWait(self.driver,10).until(
                EC.presence_of_element_located((By.XPATH, xpath_login_button))
            )      
        login_button.click()


    def click(self, xpath):
        element = WebDriverWait(self.driver,10).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )                                           
        element.click()


    def elements(self,xpath: str,timeout: float = 10,text: bool = False):
        elements = WebDriverWait(self.driver,timeout).until(
            EC.presence_of_all_elements_located((By.XPATH,xpath))
        )
        if text == True:
            return [e.text for e in elements]
        else:
            return elements

    def element(self,xpath: str,timeout: float = 10,text: bool = False):
        element = WebDriverWait(self.driver,timeout).until(
            EC.presence_of_element_located((By.XPATH,xpath))
        )
        if text == True:
            return element.text
        else:
            return element


    ### INVESTMENTS DISPLAY ###
    # text_to_int function definition
    def textprice_to_int(string: str): 
        comma_position = str.find(string,',') 
        dot_position = str.find(string,'.')
        if string.count(',') > 1: # if there are more than one comma
            string = string.replace(',',"") # remove them since it should be bilions, millions and thousands separators
        if comma_position < dot_position: # if comma comes before (more at the left) the dot
            string = string.replace(',',"") # replace comma with nothing because it is the thousands separator
        elif dot_position == -1: # if dot is not present
            string = string.replace(',','.') # replace comma with dot because it is the decimal separator
        elif dot_position < comma_position: # if dot comes before (more at the left) the comma
            string = string.replace(".","").replace(",",".") # replace the dot with nothing and then the comma with a dot
        return float(string)

    # get_price function definition
    def get_price(self, source: str, ticker: str):
        """
        Retrieve the last prices from a specified web-source
        :param source: the web-source of the price (supported are: Investing.com, Borsa Italiana, Yahoo finance)
        :param tickers: a list of the tickers of the instruments to monitor
        """
        self.driver.get(f'https://www.google.com/search?q={source}+{ticker}')
        try:
            self.cookies_handler(self.driver,'//*[@id="W0wltc"]/div') # google cookies handler
        except:
            pass
        self.first_result_click(self.driver)
        if "investing" in source:
            # investing cookies handler
            try:
                self.cookies_handler(self.driver,'//*[@id="onetrust-accept-btn-handler"]')
            except:
                pass
            # get price
            last_price = self.element(self.driver,'//*[@data-test="instrument-price-last"]',text=True)
            return self.textprice_to_int(last_price)
        elif "borsa italiana" in source:
            last_price = self.element(self.driver,'//*[@class="t-text -black-warm-60 -formatPrice"]',text=True)
            return self.textprice_to_int(last_price)
        elif "yahoo" in source:
            # yahoo cookies handler
            try:
                self.cookies_handler(self.driver,'//*[@id="consent-page"]/div/div/div/form/div[2]/div[2]/button[1]')
            except:
                pass
            # get price
            last_price = self.element(self.driver,'//*[@class="Fw(b) Fz(36px) Mb(-4px) D(ib)"]',text=True)
            return self.textprice_to_int(last_price)
    ### END OF INVESTMENTS DISPLAY ###    

    #PHONE REGEX
    indicatori_del_numero = '(tel|telefono|numero|centralino|contatto|fisso)'
    spazi_e_caratteri_nonwords_dopo_indicatore = '[^(a-zA-Z0-9)](.*)'
    prefisso = '(0[0-9])'
    iteration_num_space = "([^(a-zA-Z0-9)]?)([0-9]+[^(a-zA-Z0-9\&\<\>\(\)\;)]?)+"
    PHONE_REGEX_specific = indicatori_del_numero + spazi_e_caratteri_nonwords_dopo_indicatore + prefisso + iteration_num_space
    phone_regex = "^(?:\+39\s)?\d{2,3}[\s.-]?\d{6,7}$"

    #EMAIL REGEX
    EMAIL_REGEX = "[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
