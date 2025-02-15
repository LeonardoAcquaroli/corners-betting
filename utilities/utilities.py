from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from typing import Tuple, Union
import numpy as np
import scipy.stats
import pandas as pd
import matplotlib.pyplot as plt
import numpy.typing as npt
import shutil
import time
import streamlit as st
from io import StringIO

class WebDriverUtility:
    @staticmethod
    @st.cache_resource(show_spinner=False)
    def get_chromedriver_path():
        return shutil.which('chromedriver')

    @staticmethod
    @st.cache_resource(show_spinner=False)
    def init_driver(headless=True, log_level=3, no_images=True):
        #### options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        if log_level not in [0, 1, 2, 3]:
            raise ValueError("log_level must be one of the following: 0, 1, 2, 3")
        else:
            chrome_options.add_argument(f'log-level={log_level}')
        if no_images:
            chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        #### service
        chrome_service = webdriver.ChromeService(
            executable_path=WebDriverUtility.get_chromedriver_path()
        )
        #### webdriver
        driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
        return driver

class SingleTeamCornersUtility():
    def __init__(self, driver):
        self.driver = driver

    def corners_for(self):
        corners_for_team_table = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'matchlogs_for')))
        corners_for_team = pd.read_html(StringIO(corners_for_team_table.get_attribute('outerHTML')))[0]
        columns = corners_for_team.columns.droplevel(0) # cut out the first header of the multi Index
        corners_for_team.columns = columns
        corners_for_team = corners_for_team[["Date","Round","Venue","Result","GF","GA","Opponent","CK"]] # select only the important columns
        corners_for_team.rename({"CK": "Corners for"}, axis = 1, inplace=True) # change the corners for column name
        corners_for_team = corners_for_team.dropna(how='all') # drop the grey separator rows where all the entries in the row are nan 
        corners_for_team = corners_for_team[~corners_for_team['Result'].str.contains(r'\d', na=False)] # Drop the total row: rows where the 'Result' column contains at least one digit
        corners_for_team['GF'] = pd.to_numeric(corners_for_team['GF'], errors='coerce')
        corners_for_team = corners_for_team.dropna(subset=['GF'])
        # Force Corners for column to int
        corners_for_team['Corners for'] = pd.to_numeric(corners_for_team['Corners for'], errors='coerce')
        corners_for_team = corners_for_team.reset_index(drop=True)
        return corners_for_team

    def corners_against(self):
        corners_against_team_table = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, 'matchlogs_against')))
        corners_against_team = pd.read_html(StringIO(corners_against_team_table.get_attribute('outerHTML')))[0]
        columns = corners_against_team.columns.droplevel(0) # cut out the first header of the multi Index
        corners_against_team.columns = columns
        corners_against_team = corners_against_team[["Date","Round","Venue","Result","GF","GA","Opponent","CK"]] # select only the important columns
        corners_against_team.rename({"CK": "Corners against"}, axis = 1, inplace=True) # change the corners for column name
        corners_against_team = corners_against_team.dropna(how='all') # drop the grey separator rows where all the entries in the row are nan 
        corners_against_team = corners_against_team[~corners_against_team['Result'].str.contains(r'\d', na=False)] # Drop the total row: rows where the 'Result' column contains at least one digit
        # Force Corners against column to int
        corners_against_team['Corners against'] = pd.to_numeric(corners_against_team['Corners against'], errors='coerce')
        corners_against_team = corners_against_team.reset_index(drop=True)
        return corners_against_team

    def single_team(self, code, team, season):
        '''
        Parameters:
            code (str): The team's unique identifier code used in fbref.com URLs
            team (str): The team's name
            season (int): The starting year of the season (e.g., 2023 for 2023-24 season)
        ''' 
        self.driver.get(f"https://fbref.com/en/squads/{str(code)}/{str(season+2000)}-{str(season+1+2000)}/matchlogs/c11/passing_types/{team}-Match-Logs-Serie-A")
        team_corners_table = pd.merge(self.corners_for(), self.corners_against(), left_index=True, right_index=True, suffixes=('', '_y'))
        team_corners_table = team_corners_table.loc[:, ~team_corners_table.columns.isin(["Date_y","Round_y","Venue_y","Result_y","GF_y","GA_y","Opponent_y"])]
        team_corners_table["Outcome"] = team_corners_table.apply(lambda row: 'Win' if int(row['Corners for']) > int(row['Corners against']) else ('Draw' if int(row['Corners for']) == int(row['Corners against']) else 'Defeat'), axis=1) # create 1X2 column
        team_corners_table["Corners difference"] = team_corners_table["Corners for"].astype(int) - team_corners_table["Corners against"].astype(int)
        team_corners_table.set_index("Round", inplace = True)
        return team_corners_table
    
class PreprocessingUtility:
    @staticmethod
    def preprocessing(df):
        columns = df.columns.droplevel(0) # cut out the first header of the multi Index
        df.columns = columns
        df = df[["Squad","90s","CK"]] # select only the important columns
        df.loc[:, 'CK'] = round(df['CK']/df['90s'], 2) # get the mean number of corners instead of the total
        return df
    
    @staticmethod
    @st.cache_data(show_spinner=False)
    def get_aggregated_data(_driver):
        '''Data fetching from FBref Passing types pages'''
        # Get the page
        _driver.get("https://fbref.com/en/comps/11/passing_types/Serie-A-Stats")
        # Wait for the two tables to load
        table_for = WebDriverWait(_driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="stats_squads_passing_types_for"]')))
        table_against = WebDriverWait(_driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="stats_squads_passing_types_against"]')))
        # Parse the HTML table using Pandas
        corners_for_aggregated = pd.read_html(StringIO(table_for.get_attribute('outerHTML')))[0]
        corners_against_aggregated = pd.read_html(StringIO(table_against.get_attribute('outerHTML')))[0]

        corners_for_aggregated = PreprocessingUtility.preprocessing(corners_for_aggregated)
        corners_against_aggregated = PreprocessingUtility.preprocessing(corners_against_aggregated)
        corners_for_aggregated.rename({"CK": "Corners for", "90s": "Games played"}, axis = 1, inplace=True) # change the corners for column name
        corners_against_aggregated.rename({"CK": "Corners against", "90s": "Games played"}, axis = 1, inplace=True) # change the corners against column name
        corners_against_aggregated.Squad = corners_for_aggregated.Squad
        corners_aggregated = pd.merge(corners_for_aggregated, corners_against_aggregated, how="inner", on='Squad', suffixes=['','_y'])
        corners_aggregated.drop('Games played_y', inplace=True, axis=1)
        corners_aggregated['Total per match'] = corners_aggregated['Corners for'] + corners_aggregated['Corners against']
        corners_aggregated['Corners average difference'] = corners_aggregated['Corners for'] - corners_aggregated['Corners against']
        return corners_aggregated

class TTestUtility:
    """A class for performing statistical tests on independent samples."""
    
    def __init__(self, alpha):
        """
        Initialize the statistical testing class.
        
        Args:
            alpha: Significance level for hypothesis testing
        """
        self.alpha = alpha

    def _calculate_variance(self, data: Union[pd.DataFrame, npt.ArrayLike]) -> Tuple[float, int]:
        """
        Calculate variance and degrees of freedom for a sample.
        
        Args:
            data: Input data array or DataFrame
            
        Returns:
            Tuple containing (variance, degrees of freedom)
        """
        array_data = np.array(data)
        return np.var(array_data, ddof=1), array_data.size - 1

    def f_test(self, sample1: Union[pd.DataFrame, npt.ArrayLike], 
               sample2: Union[pd.DataFrame, npt.ArrayLike]) -> Tuple[float, float]:
        """
        Perform F-test to compare variances of two independent samples.
        
        Args:
            sample1: First sample data
            sample2: Second sample data
            
        Returns:
            Tuple containing (F statistic, p-value)
        """
        var1, df1 = self._calculate_variance(sample1)
        var2, df2 = self._calculate_variance(sample2)
        
        f_statistic = var1 / var2
        
        # Calculate one-tailed p-value
        if var1 >= var2:
            p_value = 1 - scipy.stats.f.cdf(f_statistic, df1, df2)
        else:
            p_value = scipy.stats.f.cdf(f_statistic, df1, df2)
            
        return f_statistic, p_value

    def _perform_ttest(self, sample1: Union[pd.DataFrame, npt.ArrayLike], 
                      sample2: Union[pd.DataFrame, npt.ArrayLike], 
                      equal_var: bool) -> Tuple[float, float]:
        """
        Perform t-test calculation with or without equal variance assumption.
        
        Args:
            sample1: First sample data
            sample2: Second sample data
            equal_var: Whether to assume equal variances
            
        Returns:
            Tuple containing (t statistic, p-value)
        """
        # Convert inputs to numpy arrays and calculate basic statistics
        arr1, arr2 = np.array(sample1), np.array(sample2)
        n1, n2 = arr1.size, arr2.size
        mean1, mean2 = np.mean(arr1), np.mean(arr2)
        var1, var2 = np.var(arr1, ddof=1), np.var(arr2, ddof=1)
        
        if equal_var:
            # Pooled variance t-test
            pooled_var = ((n1-1)*var1 + (n2-1)*var2) / (n1 + n2 - 2)
            std_err = np.sqrt(pooled_var * (1/n1 + 1/n2))
            df = n1 + n2 - 2
        else:
            # Welch's t-test
            std_err = np.sqrt(var1/n1 + var2/n2)
            # Welch–Satterthwaite equation for degrees of freedom
            df = ((var1/n1 + var2/n2)**2) / (
                (var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1)
            )
        
        t_stat = (mean1 - mean2) / std_err
        
        # Calculate one-tailed p-value
        p_value = 1 - scipy.stats.t.cdf(t_stat, df) if mean1 >= mean2 else scipy.stats.t.cdf(t_stat, df)
        
        return t_stat, p_value

    def t_test(self, sample1: Union[pd.DataFrame, npt.ArrayLike],
                     sample2: Union[pd.DataFrame, npt.ArrayLike]) -> float:
        """
        Perform appropriate t-test based on F-test results.
        
        Args:
            sample1: First sample data
            sample2: Second sample data
            
        Returns:
            p-value from the t-test
        """
        # First perform F-test to check variance equality
        _, f_test_pvalue = self.f_test(sample1, sample2)
        
        # Choose appropriate t-test based on F-test result
        equal_variances = f_test_pvalue >= 0.05
        _, t_test_pvalue = self._perform_ttest(sample1, sample2, equal_var=equal_variances)
        
        return t_test_pvalue
        
    @st.cache_data(show_spinner=False)
    def t_test_predictions(_self, _stc, team_codes, teamA, teamB, season, alpha):
        if ((teamA != "") & (teamB != "")):
            codeA = team_codes.team_code[team_codes.team_name == teamA].reset_index(drop=True)[0]
            codeB = team_codes.team_code[team_codes.team_name == teamB].reset_index(drop=True)[0]
            time.sleep(1)
            cornersA = _stc.single_team(code=codeA, team=teamA, season=season)['Corners difference']
            time.sleep(1)
            cornersB = _stc.single_team(code=codeB, team=teamB, season=season)['Corners difference']
            p_value = _self.t_test(sample1=cornersA, sample2=cornersB)*100
            if p_value <= (alpha/2): # Reject hypotesis of equality in corners average. Righ/Left most tail of the t distribution
                if np.mean(cornersA) >= np.mean(cornersB):
                    corners_winning_team = teamA
                else:
                    corners_winning_team = teamB
                return (corners_winning_team, p_value)
            else:
                return ('X', p_value)
            
class PlottingUtility:
    def __init__(self):
        pass

    @staticmethod
    def plot_corners_distributions(mean_for: float, sd_for: float,
                                   mean_against: float, sd_against: float,
                                   mode: str = 'single_team',
                                   home_team: str = None, away_team: str = None):
        # Create the data points for x-axis
        left_lim = min(mean_for, mean_against) - 3*max(sd_for, sd_against)
        right_lim = max(mean_for, mean_against) + 3*max(sd_for, sd_against)
        x = np.linspace(left_lim, right_lim, 200)
        
        # Calculate normal distributions
        y_for = (1/(sd_for * np.sqrt(2*np.pi))) * np.exp(-0.5*((x-mean_for)/sd_for)**2)
        y_against = (1/(sd_against * np.sqrt(2*np.pi))) * np.exp(-0.5*((x-mean_against)/sd_against)**2)
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 3))
        
        # Create masks for standard deviation ranges
        mask_for = (x >= mean_for - sd_for) & (x <= mean_for + sd_for)
        mask_against = (x >= mean_against - sd_against) & (x <= mean_against + sd_against)
        
        # Plot the shadows for standard deviation ranges
        ax.fill_between(x, y_for, where=mask_for, color='black', alpha=0.1)
        ax.fill_between(x, y_against, where=mask_against, color='black', alpha=0.1)
        
        # Plot distributions
        ax.fill_between(x, y_against, alpha=0.3, color='red', label='Corners Against' if mode == 'single_team' else away_team)
        ax.plot(x, y_against, color='red', linewidth=2)
        
        ax.fill_between(x, y_for, alpha=0.3, color='blue', label='Corners For' if mode == 'single_team' else home_team)
        ax.plot(x, y_for, color='blue', linewidth=2)
        
        # Find the maximum height of both distributions
        y_max = max(max(y_for), max(y_against))
        
        # Add vertical lines for means (extending to the curve)
        # Get y-values at means
        y_at_mean_for = (1/(sd_for * np.sqrt(2*np.pi)))
        y_at_mean_against = (1/(sd_against * np.sqrt(2*np.pi)))
        
        ax.vlines(x=mean_for, ymin=0, ymax=y_at_mean_for, color='blue', linestyle='--', alpha=0.5)
        ax.vlines(x=mean_against, ymin=0, ymax=y_at_mean_against, color='red', linestyle='--', alpha=0.5)
        
        # Customize plot
        ax.set_title(f'''Distribution of Corners{" For and Against" if mode == "single_team" else f": {home_team} - {away_team}"}''', pad=20)
        ax.set_xlabel('Number of Corners' if mode == 'single_team' else 'Corners number difference')
        ax.set_ylabel('Density')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.set_xlim(-max(abs(left_lim), abs(right_lim)), max(abs(left_lim), abs(right_lim)))
        
        return fig