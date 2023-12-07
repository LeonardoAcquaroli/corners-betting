from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import streamlit as st

@st.cache_data(show_spinner=False)
def get_aggregated_data(_driver):
    '''Data fetching from FBref Passing types pages'''
    # Get the page
    _driver.get("https://fbref.com/en/comps/11/passing_types/Serie-A-Stats")
    # Wait for the two tables to load
    table_for = WebDriverWait(_driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="stats_squads_passing_types_for"]')))
    table_against = WebDriverWait(_driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="stats_squads_passing_types_against"]')))
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