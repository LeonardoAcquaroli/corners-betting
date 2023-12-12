# Web scraping libraries
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import shutil
from get_aggregated_data import *
# Data
import pandas as pd
# Web app
import streamlit as st

# Driver initialization
@st.cache_resource(show_spinner=False)
def get_chromedriver_path():
    return shutil.which('chromedriver')

@st.cache_resource(show_spinner=False)
def init_driver(driver_headless=True, driver_loglevel3=True, driver_noImg=True):
    #### options
    chrome_options = Options()
    if driver_headless == True:
        chrome_options.add_argument('--headless')
    if driver_loglevel3 == True:
        chrome_options.add_argument('log-level=3')
    if driver_noImg == True:
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    #### service
    chrome_service = webdriver.ChromeService(executable_path=get_chromedriver_path())
    #### webdriver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    return driver

driver = init_driver()

while True:
    try:
        driver.get('https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures')
        fixtures_table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="sched_2023-2024_11_1"]')))
        break
    except Exception as error:
        st.write(error)

fixtures =  pd.read_html((fixtures_table.get_attribute('outerHTML')))[0]