from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import date

class SingleTeamCorners():
    def __init__(self, driver):
        self.driver = driver
        self.season = date.today().year if (7 <= date.today().month <= 12) else date.today().year - 1

    def corners_for(self):
        corners_for_team_table = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'matchlogs_for')))
        corners_for_team = pd.read_html((corners_for_team_table.get_attribute('outerHTML')))[0]
        columns = corners_for_team.columns.droplevel(0) # cut out the first header of the multi Index
        corners_for_team.columns = columns
        corners_for_team = corners_for_team[["Date","Round","Venue","Result","GF","GA","Opponent","CK"]] # select only the important columns
        corners_for_team.rename({"CK": "Corners for"}, axis = 1, inplace=True) # change the corners for column name
        corners_for_team = corners_for_team.loc[0:len(corners_for_team)-2] # delete the total row
        # Convert 'GF' column to numeric and drop rows with NaN values in 'GF'
        corners_for_team['GF'] = pd.to_numeric(corners_for_team['GF'], errors='coerce')
        corners_for_team = corners_for_team.dropna(subset=['GF'])
        # Force Corners for column to int
        corners_for_team['Corners for'] = corners_for_team['Corners for'].astype(int, errors='raise')
        corners_for_team = corners_for_team.reset_index(drop=True)
        return corners_for_team

    def corners_against(self):
        corners_against_team_table = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'matchlogs_against')))
        corners_against_team = pd.read_html((corners_against_team_table.get_attribute('outerHTML')))[0]
        columns = corners_against_team.columns.droplevel(0) # cut out the first header of the multi Index
        corners_against_team.columns = columns
        corners_against_team = corners_against_team[["Date","Round","Venue","Result","GF","GA","Opponent","CK"]] # select only the important columns
        corners_against_team.rename({"CK": "Corners against"}, axis = 1, inplace=True) # change the corners for column name
        corners_against_team = corners_against_team.loc[0:len(corners_against_team)-2] # delete the total row
        # Force Corners against column to int
        corners_against_team['Corners against'] = corners_against_team['Corners against'].astype(int, errors='raise')
        corners_against_team = corners_against_team.reset_index(drop=True)
        return corners_against_team

    def single_team(self, code, team):
        self.driver.get(f"https://fbref.com/en/squads/{code}/{self.season}-{self.season+1}/matchlogs/c11/passing_types/{team}-Match-Logs-Serie-A")
        team_corners_table = pd.merge(self.corners_for(), self.corners_against(), left_index=True, right_index=True, suffixes=('', '_y'))
        team_corners_table = team_corners_table.loc[:, ~team_corners_table.columns.isin(["Date_y","Round_y","Venue_y","Result_y","GF_y","GA_y","Opponent_y"])]
        team_corners_table["Outcome"] = team_corners_table.apply(lambda row: 'Win' if int(row['Corners for']) > int(row['Corners against']) else ('Draw' if int(row['Corners for']) == int(row['Corners against']) else 'Defeat'), axis=1) # create 1X2 column
        team_corners_table["Corners difference"] = team_corners_table["Corners for"].astype(int) - team_corners_table["Corners against"].astype(int)
        team_corners_table.set_index("Round", inplace = True)
        return team_corners_table