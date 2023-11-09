# %%
# Web scraping libraries
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import shutil
# Web scraping proprietary library
from import_MyWebScrapingTools import *
# # Data
import pandas as pd
from t_test import *
# Web app
import streamlit as st
# Strings handling
# from io import StringIO

# -----------------------------------

@st.cache_resource(show_spinner=False)
def get_chromedriver_path():
    return shutil.which('chromedriver')
mws = import_MyWebScrapingTools().MyWsTools(chromedriver_executable_path=get_chromedriver_path(), driver_headless=True, driver_loglevel3=True, driver_noImg=True)
# mws = import_MyWebScrapingTools().MyWsTools(chromedriver_executable_path=r"C:\Users\leoac\OneDrive - Università degli Studi di Milano\Data science\Football\Betting\Corners\corners-betting\chromedriver.exe", driver_headless=True, driver_loglevel3=True, driver_noImg=True)
# mws = import_MyWebScrapingTools().MyWsTools()
driver = mws.driver
#%%
####### wait utility
wait = WebDriverWait(driver, 10)
# %%
# @st.cache_resource() # FIXXXX
def get_aggregated_data(driver):
    driver.get("https://fbref.com/en/comps/11/passing_types/Serie-A-Stats")
    # Wait for the two tables to load
    table_for = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="stats_squads_passing_types_for"]')))
    table_against = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="stats_squads_passing_types_against"]')))
    # Parse the HTML table using Pandas
    corners_for_aggregated = pd.read_html((table_for.get_attribute('outerHTML')))[0]
    corners_against_aggregated = pd.read_html((table_against.get_attribute('outerHTML')))[0]
    # Process the data
    # I should use a function the preprocess both in the same way
    def preprocessing(df):
        columns = df.columns.droplevel(0) # cut out the first header of the multi Index
        df.columns = columns
        df = df[["Squad","90s","CK"]] # select only the important columns
        df['CK'] = round(df['CK']/df['90s'], 2) # get the mean number of corners instead of the total
        return df
    corners_for_aggregated = preprocessing(corners_for_aggregated)
    corners_against_aggregated = preprocessing(corners_against_aggregated)
    corners_for_aggregated.rename({"CK": "Corners for", "90s": "Games played"}, axis = 1, inplace=True) # change the corners for column name
    corners_against_aggregated.rename({"CK": "Corners against", "90s": "Games played"}, axis = 1, inplace=True) # change the corners against column name
    corners_against_aggregated.Squad = corners_for_aggregated.Squad
    corners_aggregated = pd.merge(corners_for_aggregated, corners_against_aggregated, how="inner", on='Squad', suffixes=['','_y'])
    corners_aggregated.drop('Games played_y', inplace=True, axis=1)
    corners_aggregated['Total per match'] = corners_aggregated['Corners for'] + corners_aggregated['Corners against']
    corners_aggregated['Corners average difference'] = corners_aggregated['Corners for'] - corners_aggregated['Corners against']
    return corners_aggregated
# 1
st.markdown("### Team-wise aggregated data")
st.dataframe(get_aggregated_data(driver=driver))

# 2
# Single teams tables
# %%
team_codes = pd.read_csv("https://raw.githubusercontent.com/LeonardoAcquaroli/corners-betting/main/team_codes/teams_23-24.csv")

# %%
def corners_for():
    corners_for_team_table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'matchlogs_for')))
    corners_for_team_table = wait.until(EC.presence_of_element_located((By.ID, 'matchlogs_for')))
    corners_for_team = pd.read_html((corners_for_team_table.get_attribute('outerHTML')))[0]
    columns = corners_for_team.columns.droplevel(0) # cut out the first header of the multi Index
    corners_for_team.columns = columns
    corners_for_team = corners_for_team[["Date","Round","Venue","Result","GF","GA","Opponent","CK"]] # select only the important columns
    corners_for_team.rename({"CK": "Corners for"}, axis = 1, inplace=True) # change the corners for column name
    corners_for_team = corners_for_team.loc[0:len(corners_for_team)-2] # delete the total row
    return corners_for_team

def corners_against():
    corners_against_team_table = wait.until(EC.presence_of_element_located((By.ID, 'matchlogs_against')))
    corners_against_team = pd.read_html((corners_against_team_table.get_attribute('outerHTML')))[0]
    columns = corners_against_team.columns.droplevel(0) # cut out the first header of the multi Index
    corners_against_team.columns = columns
    corners_against_team = corners_against_team[["Date","Round","Venue","Result","GF","GA","Opponent","CK"]] # select only the important columns
    corners_against_team.rename({"CK": "Corners against"}, axis = 1, inplace=True) # change the corners for column name
    corners_against_team = corners_against_team.loc[0:len(corners_against_team)-2] # delete the total row
    return corners_against_team

st.markdown("### Match-by-match data")
team = st.selectbox("Choose the team", pd.Series(team_codes['team_name']))
if team != "":
    code = team_codes.team_code[team_codes.team_name == team].reset_index(drop=True)[0]
def single_team(code, team):
    driver.get(f"https://fbref.com/en/squads/{code}/2023-2024/matchlogs/c11/passing_types/{team}-Match-Logs-Serie-A")
    team_corners_table = pd.merge(corners_for(), corners_against(), left_index=True, right_index=True, suffixes=('', '_y'))
    team_corners_table = team_corners_table.loc[:, ~team_corners_table.columns.isin(["Date_y","Round_y","Venue_y","Result_y","GF_y","GA_y","Opponent_y"])]
    team_corners_table["Outcome"] = team_corners_table.apply(lambda row: 'Win' if row['Corners for'] > row['Corners against'] else ('Draw' if row['Corners for'] == row['Corners against'] else 'Defeat'), axis=1) # create 1X2 column
    team_corners_table["Corners difference"] = team_corners_table["Corners for"] - team_corners_table["Corners against"]
    team_corners_table.set_index("Round", inplace = True)
    return team_corners_table
# %%
if team != "":
    team_corners = single_team(code, team)
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
# %%
def t_test_predictions(teamA, teamB, alpha = 90.81):
    if ((teamA != "") & (teamB != "")):
        codeA = team_codes.team_code[team_codes.team_name == teamA].reset_index(drop=True)[0]
        codeB = team_codes.team_code[team_codes.team_name == teamB].reset_index(drop=True)[0]
        cornersA = single_team(code=codeA, team=teamA)['Corners difference']
        cornersB = single_team(code=codeB, team=teamB)['Corners difference']
        p_value = t_test().t_test(a=cornersA, b=cornersB)*100
        if p_value <= (alpha/2): # Reject hypotesis of equality in corners average. Righ/Left most tail of the t distribution
            if np.mean(cornersA) >= np.mean(cornersB):
                corners_winning_team = teamA
            else:
                corners_winning_team = teamB
            return (corners_winning_team, p_value)
        else:
            return ('X', p_value)

# %%
driver.get('https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures')
fixtures_table = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="sched_2023-2024_11_1"]')))
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
