# Web scraping libraries
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import shutil
from get_aggregated_data import *
from SingleTeam import SingleTeamCorners
# Data
import pandas as pd
from t_test import *
# Web app
import streamlit as st
# Strings handling
#from io import StringIO

# -----------------------------------

# Driver initialization
@st.cache_resource(show_spinner=False)
def get_chromedriver_path():
    return shutil.which('chromedriver')

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

# 1
st.markdown("### Team-wise aggregated data")
st.dataframe(get_aggregated_data(driver=driver))

# 2
# Single teams tables
team_codes = pd.read_csv("https://raw.githubusercontent.com/LeonardoAcquaroli/corners-betting/main/team_codes/teams_23-24.csv")

st.markdown("### Match-by-match data")
team = st.selectbox("Choose the team", pd.Series(team_codes['team_name']))
if team != "":
    code = team_codes.team_code[team_codes.team_name == team].reset_index(drop=True)[0]

stc = SingleTeamCorners(driver=driver)

if team != "":
    c = 0
    while True:
        try:
            team_corners = stc.single_team(code, team)
            break
        except Exception as error:
            st.write(error)
    
    mean_for = round(team_corners["Corners for"].mean(),2)
    sd_for = round(team_corners["Corners for"].std(),2)
    mean_against = round(team_corners["Corners against"].mean(),2)
    sd_against = round(team_corners["Corners against"].std(),2)
    st.dataframe(team_corners)
    st.write(f"Average number of corners for {team}: {mean_for}, Standard deviation of corners for {team}: {sd_for}")
    st.write(f"Average number of corners against {team}: {mean_against}, Standard deviation of corners against {team}: {sd_against}")

# 3
st.markdown("### Corners average comparison and match prediction")
# Significance level based on the number of corners draws in Serie A 22/23: alpha = 90.81%

def t_test_predictions(teamA, teamB, alpha = 90.81):
    if ((teamA != "") & (teamB != "")):
        codeA = team_codes.team_code[team_codes.team_name == teamA].reset_index(drop=True)[0]
        codeB = team_codes.team_code[team_codes.team_name == teamB].reset_index(drop=True)[0]
        cornersA = stc.single_team(code=codeA, team=teamA)['Corners difference']
        cornersB = stc.single_team(code=codeB, team=teamB)['Corners difference']
        p_value = t_test().t_test(a=cornersA, b=cornersB)*100
        if p_value <= (alpha/2): # Reject hypotesis of equality in corners average. Righ/Left most tail of the t distribution
            if np.mean(cornersA) >= np.mean(cornersB):
                corners_winning_team = teamA
            else:
                corners_winning_team = teamB
            return (corners_winning_team, p_value)
        else:
            return ('X', p_value)

driver.get('https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures')

v = 0
while True:
    try:
        fixtures_table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="sched_2023-2024_11_1"]')))
        break
    except:
        v += 1
        st.write(v) 



fixtures =  pd.read_html((fixtures_table.get_attribute('outerHTML')))[0]
fixtures = fixtures[fixtures.Wk.isna() == False] # delete the grey blank rows to separate gameweeks
fixtures = fixtures[fixtures.Score.isna()] # drop the played matches
fixtures = fixtures.reset_index(drop=True) # reset index
next_fixtures = fixtures[["Wk","Day","Date","Time","Home","Away"]][fixtures.Wk == fixtures.Wk[0]].reset_index(drop=True)
corners_outcome = next_fixtures.apply(lambda row: t_test_predictions(teamA = row['Home'], teamB = row['Away']), axis=1) # return winning team name and p_value
next_fixtures['Corners outcome'] = [outcome[0] for outcome in corners_outcome] # Team name
p_values = [outcome[1] for outcome in corners_outcome] # p values

# Transform into 1X2 with np.where
conditions = [
    (next_fixtures['Corners outcome'] == 'X'),
    (next_fixtures['Corners outcome'] == next_fixtures['Home']),
    (next_fixtures['Corners outcome'] == next_fixtures['Away'])]
next_fixtures['Corners outcome'] = np.where(conditions[0], 'X', np.where(conditions[1], '1', '2'))

# Add forecast reliability calculated as the difference between the significance threshold (45.405 or 50) and the p_value for each game
sign_level = 90.81
reliabilities = [round( ((sign_level/2 - p) / sign_level/2)*100, 2 ) if p <= sign_level/2 else round( ((50 - p) / 50)*100, 2 ) for p in p_values]
next_fixtures['Reliability of the forecast'] = reliabilities
next_fixtures.set_index('Wk', inplace=True)
st.dataframe(next_fixtures)
# pred_file = next_fixtures.to_csv('SerieA_corners_predictions.csv')
# st.download_button(label="Download the predictions", data=pred_file, file_name='SerieA_corners_predictions.csv')