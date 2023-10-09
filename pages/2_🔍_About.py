import streamlit as st

# Header
st.markdown("# Serie A Corner kicks stats🚩")

# Description
st.markdown(
    """
    ## Description:
    This Streamlit web app provides aggregated and granular data about corner kicks and 1X2 predictions for the next Serie A matchweek about corners number (basically who will gain more corners) that can be used to catch valuable bets or just to study italian teams play styles.

    ### Data Source:
    Data come from [FBref](https://www.fbref.com/).

    ### Features:
    1. **Team-wise aggregated data:** View the average number of corner kicks taken by each Serie A team and their opponents in the current season. 👕
    2. **Match-by-match data:** See the numbers of corner kicks (for and against) for each game and their Mean and Standard deviation. 📆
    3. **Corners 1X2 predictions:** 1X2 predictions for the next Serie A matchweek with a reliability measure. 🔮
    """,
    unsafe_allow_html=True)


prediction_desc = r'''
The predictions are computed through a hypothesis test (a t-test on independent samples) over the mean difference between corners for and corners against. In other words, n steps are performed:\\
  1. Compute **average difference between corners for and against (ACD: Average Corners Difference)** for each team (see Team-wise aggregated data)
  2. Calculate the adequate significance level ($\alpha$). This is done based on the fraction of games that ended with a draw in corners in '22/'23 Serie A. It was found that $9.19\%$ of games ended in a draw in corners and so $\alpha = 100 - 9.19 = 90.81\%$  
  3. For each game of the next matchweek, perform a \textbf{bilateral t-test} on independent samples, which in this case are the records of the average corners difference of the two teams, with the above-computed significance level $\alpha = 90.81\%$ and so with each tail comprising $90.81/2 = 45.405\%$ of the probability under the t distribution
  4. If the **ACD of the two teams are statistically different** ($p < 45.405\%$), **1 or 2** is output based on who has the highest corners mean. If, instead, **ACD of the teams are not statistically different** ($p > 45.405\%$) **X** is the output
  5. Finally, a reliability measure is built. It goes from 0 to 100 since $$p \in [0, 50]$$:
'''

# add the image of the equations
st.markdown(prediction_desc)
st.image(r"C:\Immagini\Catture di schermata\Screenshot 2023-10-09 230523.png")


