# Web scraping libraries
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import shutil
# Data
import pandas as pd
import numpy as np
import requests
from io import StringIO
import math
# Web app
import streamlit as st
# Plot
import plotly.graph_objects as go

# Recreate the SingleTeam class
class SingleTeamCorners():
    def __init__(self, driver):
        self.driver = driver

    def corners_for(self):
        corners_for_team_table = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'matchlogs_for')))
        corners_for_team = pd.read_html((corners_for_team_table.get_attribute('outerHTML')))[0]
        columns = corners_for_team.columns.droplevel(0) # cut out the first header of the multi Index
        corners_for_team.columns = columns
        corners_for_team = corners_for_team[["Date","Round","Venue","Result","GF","GA","Opponent","CK"]] # select only the important columns
        corners_for_team.rename({"CK": "Corners for"}, axis = 1, inplace=True) # change the corners for column name
        corners_for_team = corners_for_team.loc[0:len(corners_for_team)-2] # delete the total row
        return corners_for_team

    def corners_against(self):
        corners_against_team_table = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'matchlogs_against')))
        corners_against_team = pd.read_html((corners_against_team_table.get_attribute('outerHTML')))[0]
        columns = corners_against_team.columns.droplevel(0) # cut out the first header of the multi Index
        corners_against_team.columns = columns
        corners_against_team = corners_against_team[["Date","Round","Venue","Result","GF","GA","Opponent","CK"]] # select only the important columns
        corners_against_team.rename({"CK": "Corners against"}, axis = 1, inplace=True) # change the corners for column name
        corners_against_team = corners_against_team.loc[0:len(corners_against_team)-2] # delete the total row
        return corners_against_team

    def single_team(self, code, team):
        self.driver.get(f"https://fbref.com/en/squads/{code}/2023-2024/matchlogs/c11/passing_types/{team}-Match-Logs-Serie-A")
        team_corners_table = pd.merge(self.corners_for(), self.corners_against(), left_index=True, right_index=True, suffixes=('', '_y'))
        team_corners_table = team_corners_table.loc[:, ~team_corners_table.columns.isin(["Date_y","Round_y","Venue_y","Result_y","GF_y","GA_y","Opponent_y"])]
        team_corners_table["Outcome"] = team_corners_table.apply(lambda row: 'Win' if row['Corners for'] > row['Corners against'] else ('Draw' if row['Corners for'] == row['Corners against'] else 'Defeat'), axis=1) # create 1X2 column
        team_corners_table["Corners difference"] = team_corners_table["Corners for"] - team_corners_table["Corners against"]
        team_corners_table.set_index("Round", inplace = True)
        return team_corners_table

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

# Get fixtures
driver.get('https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures')
fixtures_table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="sched_2023-2024_11_1"]')))
fixtures =  pd.read_html((fixtures_table.get_attribute('outerHTML')))[0]
fixtures = fixtures[(fixtures.Wk.isna() == False) & (fixtures.Wk != "Wk") & (fixtures.Score.isna() == False)] # delete grey blank rows, repeated headers and taken only played games
fixtures = fixtures[["Wk","Home","Away"]]

# Get teams code
try:
    team_codes = pd.read_csv("https://raw.githubusercontent.com/LeonardoAcquaroli/corners-betting/main/team_codes/teams_23-24.csv", sep=',')
except:
    team_codes = pd.read_csv("https://raw.githubusercontent.com/LeonardoAcquaroli/corners-betting/main/team_codes/teams_23-24.csv", sep=';')

# Initialize stc
stc = SingleTeamCorners(driver=driver)

@st.cache_resource(show_spinner=False)
def corners_result(game_data):
    homeTeam = game_data["Home"]
    awayTeam = game_data["Away"]
    homeCode = team_codes.team_code[team_codes.team_name == homeTeam].reset_index(drop=True)[0]
    # awayCode = team_codes.team_code[team_codes.team_name == awayTeam]
    driver.get(f"https://fbref.com/en/squads/{homeCode}/2023-2024/matchlogs/c11/passing_types/{homeTeam}-Match-Logs-Serie-A")
    cornersHome = stc.corners_for()
    cornersHome = cornersHome["Corners for"][cornersHome["Opponent"] == awayTeam]
    cornersAway = stc.corners_against()
    cornersAway = cornersAway["Corners against"][cornersAway["Opponent"] == awayTeam]
    return pd.concat((cornersHome, cornersAway), axis=1)

corners_homeAway = fixtures.apply(lambda game_data: corners_result(game_data), axis=1)
fixtures[["Corners home", "Corners away"]] = pd.concat(corners_homeAway.tolist(), ignore_index=True).values
fixtures["Corners outcome"] = np.where(fixtures['Corners home'] > fixtures['Corners away'], '1', 
                                 np.where(fixtures['Corners home'] < fixtures['Corners away'], '2', 'X'))
fixtures.Wk = fixtures.Wk.astype(int)
# Get only the matches after the 12th Gameweek
fixtures_evaluated = fixtures[fixtures.Wk >= 12]

# Construct the GitHub API URL for the contents of the folder
api_url = f"https://api.github.com/repos/LeonardoAcquaroli/corners-betting/contents/evaluation"
# Fetch the content of the folder index using the GitHub API
response = requests.get(api_url)
# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the JSON response
    files = response.json()
    csv_files = [file["name"] for file in files if file["type"] == "file" and file["name"].endswith(".csv")]
    concatenated_data = pd.DataFrame()
    for csv_file in csv_files:
        # Get the raw content URL for the CSV file
        raw_url = files[csv_files.index(csv_file)]["download_url"]
        # Read the CSV content into a DataFrame
        content = requests.get(raw_url).text
        df = pd.read_csv(StringIO(content), sep=';')
        if len(df.columns) < 7: # Because if the csv is separated by ',' it does not split it in a 7 columns df
            df = pd.read_csv(StringIO(content), sep=',')
        concatenated_data = pd.concat((concatenated_data, df), ignore_index=True)
concatenated_data.drop(["Day","Date","Time"], inplace=True, axis=1)

evaluation = pd.merge(fixtures_evaluated, concatenated_data, how='outer', on=('Wk','Home','Away'))
# Transform the outcome and predictions in strings
evaluation["Corners outcome"] = evaluation["Corners outcome"].astype('str')
evaluation["Corners predictions"] = evaluation["Corners predictions"].astype('str')
# Unlist the .apply() results
successful_bets = evaluation.apply(lambda game: [1 if game["Corners outcome"] == game["Corners predictions"] else 0], axis=1) # is a nested list
successful_bets = [item for sublist in successful_bets for item in sublist]
evaluation["Succesful bet"] = successful_bets
st.dataframe(evaluation)


def evaluate_predictions(evaluation_df, thr = 20, printout=False):
    filtered_data = evaluation_df[evaluation_df['Reliability of the forecast'] >= thr]
    correct_pred = filtered_data["Succesful bet"].sum()
    all_pred = len(filtered_data)
    perc_correct = round((correct_pred)/all_pred*100,2)
    if printout:
        st.write(f"{correct_pred}/{all_pred} ({perc_correct}%) correctly predicted games with reliability greater than {thr}%.")
    return (correct_pred, perc_correct)

# Print the accuracy based on the chosen level of reliability
thr_chosen = st.number_input("Reliability threshold", min_value=0, max_value=100, value=20, help="Select a threshold for the reliability of the prediction")
evaluate_predictions(evaluation_df=evaluation, thr=thr_chosen, printout=True)

perc_list = []
for threshold in range(math.ceil((evaluation['Reliability of the forecast'].max()))):
    perc = evaluate_predictions(evaluation_df=evaluation, thr=threshold)[1]
    perc_list.append(perc)

# Create a trace for the line plot
trace = go.Scatter(x=list(range(math.ceil((evaluation['Reliability of the forecast'].max())))), y=perc_list, mode='lines', name='Line Plot')
# Create a layout for the plot
layout = go.Layout(title='Percentual of succesful bets for different thresholds', xaxis=dict(title='Reliability threshold'), yaxis=dict(title='Percentual of succesful bets'))
# Create a figure and add the trace to it
fig = go.Figure(data=[trace], layout=layout)
st.plotly_chart(fig)