import sys
sys.path.append('..')
from utilities.utilities import *
import time
import os
import tempfile
import pandas as pd
import subprocess

games = pd.DataFrame()
driver = WebDriverUtility.init_driver(headless=False)
stc = SingleTeamCornersUtility(driver=driver)

for season in [22, 23, 24]:
    team_codes = pd.read_csv(fr"C:\Users\leoac\OneDrive - Università degli Studi di Milano\Data science\Football\Betting\Corners\corners-betting\team_codes\teams_{season}-{season+1}.csv")
    for i, (team, code) in team_codes.iterrows():
        print(team, code, season)
        time.sleep(1)
        team_df = stc.single_team(code=code, team=team, season=season)
        team_df['season'] = f"{season}-{season+1}"
        games = pd.concat((games, team_df),axis=0)

# Number of matches ended with corners draw
corners_draw = games.Outcome.value_counts()['Draw']/2 # games are duplicated
# Percentual of matches ended with corners draw.
perc_corners_draw = corners_draw/(len(games)/2)*100
# Significance level to perform hypotesis testing
alpha = round(100 - perc_corners_draw,2)

# Create a temporary directory with the txt file
tmp_dir = tempfile.mkdtemp()
tmp_file_path = os.path.join(tmp_dir, 'alpha.txt')
with open(tmp_file_path, 'w') as file:
    file.write(str(alpha))

# Push the file to the repository
subprocess.run(['git', 'add', tmp_file_path])
subprocess.run(['git', 'commit', '-m', 'Update significance level (alpha)'])
subprocess.run(['git', 'push'])

# Clean up: remove the file and directory
os.remove(tmp_file_path)
os.rmdir(tmp_dir)