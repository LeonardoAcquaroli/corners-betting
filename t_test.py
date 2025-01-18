import numpy as np
import scipy.stats

class t_test():
    def __init__(self) -> None:
        pass
    
    def F_test(self, a, b):
        '''
        F test is used to compare the variances of two independent samples.

        Parameters:
        - a (pandas.DataFrame): One of the two independent groups
        - b (pandas.DataFrame): One of the two independent groups

        Returns:
        (float, float): A tuple (F, p_value) of the F statistic and p_value 
        '''
        F = np.var(a,ddof=1)/np.var(b,ddof=1)
        df1 = np.array(a).size - 1
        df2 = np.array(b).size - 1
        if np.var(a,ddof=1) >= np.var(b,ddof=1):
            p_value = 1 - scipy.stats.f.cdf(F,df1,df2)
        else: 
            p_value = scipy.stats.f.cdf(F,df1,df2)
        return F, p_value
    
    def _ttest_ind(self, a, b, equal_var: bool):
        # values
        n = np.array(a).size
        m = np.array(b).size
        S_a = np.var(a,ddof=1)
        S_b = np.var(b,ddof=1)
        S_pool = ((n-1)*S_a + (m-1)*S_b) / (n+m-2)
        k = (  ((S_a/n + S_b/m)**2) / ( (1/(n-1))*((S_a/n)**2) + (1/(m-1))*((S_b/m)**2) )  )
        # t statistic
        if equal_var == True:
            t = ((np.mean(a) - np.mean(b)) - 0) / np.sqrt( S_pool*( (1/n) + (1/m) ) )
            # degrees of freedom
            degrees_of_freedom = (n+m-2)
        else:
            t = ((np.mean(a) - np.mean(b)) - 0) / np.sqrt( (S_a/n) + (S_b/m) )
            # degrees of freedom
            degrees_of_freedom = k

        if np.mean(a) >= np.mean(b):
            p_value = 1 - scipy.stats.t.cdf(t, df=degrees_of_freedom)
        else: 
            p_value = scipy.stats.t.cdf(t, df=degrees_of_freedom)
        return t, p_value

    def t_test(self, a, b):
        '''
        t-test is used to compare the mean of two independent samples.

        Parameters:
        - a (pandas.DataFrame): One of the two independent groups
        - b (pandas.DataFrame): One of the two independent groups

        Returns:
        (float, float): A tuple (t, p_value) of the t statistic and p_value 
        '''
        # Variances equality check
        F_p_value = self.F_test(a, b)[1]
        if F_p_value >= 0.05: # F-TEST --> H0: variances are equal
            t_p_value = self._ttest_ind(a, b, equal_var=True)[1]
        else: # F-TEST --> H1: variances are different
            t_p_value = self._ttest_ind(a, b, equal_var=False)[1]
        return t_p_value