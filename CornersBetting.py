# Web scraping libraries
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Data
import pandas as pd
import numpy as np
from datetime import date
from utilities.utilities import *
# Web app
import streamlit as st
# Strings handling
from io import StringIO

# -----------------------------------
driver = WebDriverUtility.init_driver()
season = (date.today().year if (7 <= date.today().month <= 12) else date.today().year - 1) - 2000
with open(r'C:\Users\leoac\OneDrive - Università degli Studi di Milano\Data science\Football\Betting\Corners\corners-betting\significance_level\alpha.txt', 'r') as file:
    # Read alpha from the txt update by the notebook
    alpha = float(file.read().strip())

# 1
st.markdown("### Team-wise aggregated data")
preprocessing_utility = PreprocessingUtility()
aggregated_data = preprocessing_utility.get_aggregated_data(_driver=driver)
st.dataframe(aggregated_data)

# 2
# Single teams tables
team_codes = pd.read_csv(f"https://raw.githubusercontent.com/LeonardoAcquaroli/corners-betting/main/team_codes/teams_{season}-{season+1}.csv")

st.markdown("### Match-by-match data")
team = st.selectbox("Choose the team", pd.Series(team_codes['team_name']))
if team != "":
    code = team_codes.team_code[team_codes.team_name == team].reset_index(drop=True)[0]

stc = SingleTeamCornersUtility(driver=driver)

if team != "":
    while True:
        try:
            team_corners = stc.single_team(code, team, season)
            break
        except:
            print('Trying to get the single team again')
            pass
    
    mean_for = team_corners["Corners for"].mean()
    sd_for = team_corners["Corners for"].std()
    mean_against = team_corners["Corners against"].mean()
    sd_against = team_corners["Corners against"].std()
    st.dataframe(team_corners)
    # Create and display a plot of the distributions of corners for and against
    fig = PlottingUtility.plot_corners_distributions(mean_for, sd_for, mean_against, sd_against)
    st.pyplot(fig)
    st.write(f"""
    - Corners For {team}: Mean = {round(mean_for, 2)}, SD = {round(sd_for, 2)}
    - Corners Against {team}: Mean = {round(mean_against, 2)}, SD = {round(sd_against, 2)}
    """)

# 3
st.markdown("### Corners average comparison and match prediction")
# Try multiple times (because it does not work in deployment)
while True:
    try:
        driver.get('https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures')
        fixtures_table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f'//*[@id="sched_{season+2000}-{season+2000+1}_11_1"]')))
        break
    except Exception as error:
        st.write(error)

fixtures = pd.read_html(StringIO(fixtures_table.get_attribute('outerHTML')))[0]
fixtures = fixtures[fixtures.Wk.isna() == False] # delete the grey blank rows to separate gameweeks
fixtures = fixtures[fixtures.Score.isna()] # drop the played matches
fixtures = fixtures.reset_index(drop=True) # reset index
current_Wk = fixtures.Wk[:10].mode()[0]
next_fixtures = fixtures[["Wk","Day","Date","Time","Home","Away"]][fixtures.Wk <= current_Wk].reset_index(drop=True)
# Significance level for t-test based on the number of corners draws in Serie A last years from 22/23: (100-pct_corners_draws)
corners_outcome = next_fixtures.apply(lambda row:
                                      TTestUtility(alpha=alpha).t_test_predictions(
                                                                    team_codes=team_codes,
                                                                    _stc = stc,
                                                                    teamA = row['Home'],
                                                                     teamB = row['Away'],
                                                                     season = season,
                                                                     alpha = alpha
                                                                     ),
                                                        axis=1) # return winning team name and p_value
next_fixtures['Corners predictions'] = [outcome[0] for outcome in corners_outcome] # Team name
p_values = [outcome[1] for outcome in corners_outcome] # p values

# Transform into 1X2 with np.where
conditions = [
    (next_fixtures['Corners predictions'] == 'X'),
    (next_fixtures['Corners predictions'] == next_fixtures['Home']),
    (next_fixtures['Corners predictions'] == next_fixtures['Away'])]
next_fixtures['Corners predictions'] = np.where(conditions[0], 'X', np.where(conditions[1], '1', '2'))

# Add forecast reliability calculated as the difference between the significance threshold (45.405 or 50) and the p_value for each game
sign_level = alpha
reliabilities = [round( ((sign_level/2 - p) / sign_level/2)*100, 2 ) if p <= sign_level/2 else round( ((50 - p) / 50)*100, 2 ) for p in p_values]
next_fixtures['Reliability of the forecast'] = reliabilities
next_fixtures.set_index('Wk', inplace=True)
st.dataframe(next_fixtures)

# Plot a single game's normal distributions
games_tuples = [(game['Home'],game['Away']) for _, game in next_fixtures[['Home', 'Away']].iterrows()]
games = [f"{game[0]} - {game[1]}" for game in games_tuples]
tuples_to_str = dict(zip(games, games_tuples))
selected_game = st.selectbox("Plot the prediction curves", games, index=None, placeholder='Select a game')
if selected_game is not None:
    home_team, away_team = tuples_to_str[selected_game]

    mean_home = aggregated_data[aggregated_data['Squad'] == home_team]['Corners average difference'].values[0]
    sd_home = stc.single_team(team_codes[team_codes['team_name'] == home_team]['team_code'].values[0],
                                home_team,
                                season)["Corners difference"].std()
    mean_away = aggregated_data[aggregated_data['Squad'] == away_team]['Corners average difference'].values[0]
    sd_away = stc.single_team(team_codes[team_codes['team_name'] == away_team]['team_code'].values[0],
                                away_team,
                                season)["Corners difference"].std()
    fig_t_test = PlottingUtility.plot_corners_distributions(mean_home, sd_home,
                                                            mean_away, sd_away,
                                                            mode='prediction', # useless to specify, it only needs to be != 'single_team'
                                                            home_team=home_team,
                                                            away_team=away_team
                                                            )
    st.pyplot(fig_t_test)