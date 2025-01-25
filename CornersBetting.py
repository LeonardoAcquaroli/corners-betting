# Web scraping libraries
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import shutil
import time
# from get_aggregated_data import *
# from SingleTeam import SingleTeamCorners
# Data
import pandas as pd
import numpy as npr
from utilities.utilities import *
# Web app
import streamlit as st
# Strings handling
from io import StringIO

# -----------------------------------
driver = WebDriverUtility.init_driver()

# 1
st.markdown("### Team-wise aggregated data")
preprocessing_utility = PreprocessingUtility()
st.dataframe(preprocessing_utility.get_aggregated_data(_driver=driver))

# 2
# Single teams tables
team_codes = pd.read_csv("https://raw.githubusercontent.com/LeonardoAcquaroli/corners-betting/main/team_codes/teams_24-25.csv")

st.markdown("### Match-by-match data")
team = st.selectbox("Choose the team", pd.Series(team_codes['team_name']))
if team != "":
    code = team_codes.team_code[team_codes.team_name == team].reset_index(drop=True)[0]

stc = SingleTeamCornersUtility(driver=driver)

if team != "":
    while True:
        try:
            team_corners = stc.single_team(code, team)
            break
        except:
            pass
    
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

@st.cache_data(show_spinner=False)
def t_test_predictions(teamA, teamB, alpha = 90.81):
    if ((teamA != "") & (teamB != "")):
        codeA = team_codes.team_code[team_codes.team_name == teamA].reset_index(drop=True)[0]
        codeB = team_codes.team_code[team_codes.team_name == teamB].reset_index(drop=True)[0]
        time.sleep(1)
        cornersA = stc.single_team(code=codeA, team=teamA)['Corners difference']
        time.sleep(1)
        cornersB = stc.single_team(code=codeB, team=teamB)['Corners difference']
        p_value = TTestUtility(alpha=0.05).t_test(sample1=cornersA, sample2=cornersB)*100
        if p_value <= (alpha/2): # Reject hypotesis of equality in corners average. Righ/Left most tail of the t distribution
            if np.mean(cornersA) >= np.mean(cornersB):
                corners_winning_team = teamA
            else:
                corners_winning_team = teamB
            return (corners_winning_team, p_value)
        else:
            return ('X', p_value)

# Try multiple times (because it does not work in deployment)
while True:
    try:
        driver.get('https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures')
        fixtures_table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f'//*[@id="sched_{stc.season}-{stc.season+1}_11_1"]')))
        break
    except Exception as error:
        st.write(error)

fixtures = pd.read_html(StringIO(fixtures_table.get_attribute('outerHTML')))[0]
fixtures = fixtures[fixtures.Wk.isna() == False] # delete the grey blank rows to separate gameweeks
fixtures = fixtures[fixtures.Score.isna()] # drop the played matches
fixtures = fixtures.reset_index(drop=True) # reset index
current_Wk = fixtures.Wk[:10].mode()[0]
next_fixtures = fixtures[["Wk","Day","Date","Time","Home","Away"]][fixtures.Wk <= current_Wk].reset_index(drop=True)
corners_outcome = next_fixtures.apply(lambda row: t_test_predictions(teamA = row['Home'], teamB = row['Away']), axis=1) # return winning team name and p_value
next_fixtures['Corners predictions'] = [outcome[0] for outcome in corners_outcome] # Team name
p_values = [outcome[1] for outcome in corners_outcome] # p values

# Transform into 1X2 with np.where
conditions = [
    (next_fixtures['Corners predictions'] == 'X'),
    (next_fixtures['Corners predictions'] == next_fixtures['Home']),
    (next_fixtures['Corners predictions'] == next_fixtures['Away'])]
next_fixtures['Corners predictions'] = np.where(conditions[0], 'X', np.where(conditions[1], '1', '2'))

# Add forecast reliability calculated as the difference between the significance threshold (45.405 or 50) and the p_value for each game
sign_level = 90.81
reliabilities = [round( ((sign_level/2 - p) / sign_level/2)*100, 2 ) if p <= sign_level/2 else round( ((50 - p) / 50)*100, 2 ) for p in p_values]
next_fixtures['Reliability of the forecast'] = reliabilities
next_fixtures.set_index('Wk', inplace=True)
st.dataframe(next_fixtures)