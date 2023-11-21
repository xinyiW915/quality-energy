# Test 1
# t-test for dependent samples
from math import sqrt
from numpy.random import seed
from numpy.random import randn
from numpy import mean
from scipy.stats import t
import pandas as pd

power_log = pd.read_csv("../metrics/energy_log/power_log_2023-04-13.csv", names=['time_stamp', 'power'])
power_log['time_stamp'] = pd.to_datetime(power_log['time_stamp'])
print(power_log.head())


# function for calculating the t-test for two dependent samples
def dependent_ttest(data1, data2, alpha):
    # calculate means
    mean1, mean2 = mean(data1), mean(data2)
    # number of paired samples
    n = len(data1)
    # sum squared difference between observations
    d1 = sum([(data1[i] - data2[i]) ** 2 for i in range(n)])
    # sum difference between observations
    d2 = sum([data1[i] - data2[i] for i in range(n)])
    # standard deviation of the difference between means
    sd = sqrt((d1 - (d2 ** 2 / n)) / (n - 1))
    # standard error of the difference between the means
    sed = sd / sqrt(n)
    # calculate the t statistic
    t_stat = (mean1 - mean2) / sed
    # degrees of freedom
    df = n - 1
    # calculate the critical value
    cv = t.ppf(1.0 - alpha, df)
    # calculate the p-value
    p = (1.0 - t.cdf(abs(t_stat), df)) * 2.0
    # return everything
    return t_stat, df, cv, p

print("-------------------------------")
print("Test 1")
# seed the random number generator
seed(1)
# generate two independent samples (pretend they are dependent)
data1 = 5 * randn(100) + 50
data2 = 5 * randn(100) + 51
# calculate the t test
alpha = 0.05
t_stat, df, cv, p = dependent_ttest(data1, data2, alpha)
print('t=%.3f, df=%d, cv=%.3f, p=%.3f' % (t_stat, df, cv, p))
# interpret via critical value
if abs(t_stat) <= cv:
    print('Accept null hypothesis that the means are equal.')
else:
    print('Reject the null hypothesis that the means are equal.')
# interpret via p-value
if p > alpha:
    print('Accept null hypothesis that the means are equal.')
else:
    print('Reject the null hypothesis that the means are equal.')


print("-------------------------------")
print("Test 2")
# Test 2
# two sample student t test
import numpy as np
from scipy import stats

data1 = 5 * randn(100) + 50
data2 = 5 * randn(100) + 51
mean1 = np.mean(data1)
mean2 = np.mean(data2)

std1 = np.std(data1)
std2 = np.std(data2)

nobs1 = 100  # sample count
nobs2 = 100

modified_std1 = np.sqrt(np.float32(nobs1) / np.float32(nobs1 - 1)) * std1
modified_std2 = np.sqrt(np.float32(nobs2) / np.float32(nobs2 - 1)) * std2

(statistic, pvalue) = stats.ttest_ind_from_stats(mean1=mean1, std1=modified_std1, nobs1=10, mean2=mean2,
                                                 std2=modified_std2, nobs2=10)

print(f't statistic is: {statistic}')
print(f'pvalue is: {pvalue}')


# Test 3
power_log = pd.read_csv("../metrics/energy_log/power_log_2023-04-13.csv", names=['time_stamp', 'power'])
power_log['time_stamp'] = pd.to_datetime(power_log['time_stamp'])
df2 = power_log['power'][0:10]
print(df2)

t,p=stats.ttest_1samp(df2, popmean = 145)   #One-sample t-test performed
print("t-values=",t)  #Output t-statistic
print("p-values=",p) #Output probability P
if p < 0.05:    #Comparison of probability P and significance level α
       print("Significant differences")
else:
       print("Non-significant difference")
