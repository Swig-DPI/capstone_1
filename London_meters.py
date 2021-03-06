import numpy as np
import pandas as pd
import missingno as msno
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import plotly.plotly as py
import seaborn as sns

from sklearn.metrics import mean_squared_error #, cross_val_score
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LassoCV, LinearRegression, RidgeCV, Ridge
from fancyimpute import SimpleFill, KNN,  IterativeSVD, IterativeImputer
from plotly.graph_objs import *
from sklearn.preprocessing import scale
from statsmodels.stats.outliers_influence import variance_inflation_factor



## Data Scrubber
def data_scrubber(income_df, percent_good):
    '''Simple data scrubber that fills the NAN columns with the mean
        of the data in the columns'''
    if(income_df.isna().sum().count() >= income_df.shape[0]*percent_good):
        print('Erroronious Data.  Look to fix')
        return(income_df.fillna(income_df.mean()))
    else:
        return(income_df.fillna(income_df.mean()))

def join_df_weather(dfmeter_hh, dfweather_h):
        '''dfmeter_hh =  half hour data from meters
        dfweather_h = hourly data from London
        Returns a merged list on date and time'''

        dfmeter_hh['date_start_time'] = pd.to_datetime(dfmeter_hh['tstp']) ## standardizes date and time for merge
        dfweather_h['date_start_time'] = pd.to_datetime(dfweather_h['time']) ## standardizes date and time for merge
        extradata = ['energy(kWh/hh)','time', 'tstp']

        ## Would be nice to return df with hour and half hour meter data with same weather database
            ## currently only returns hour incremented data
        merg = pd.merge(dfmeter_hh,dfweather_h, how = 'inner', left_on='date_start_time', right_on='date_start_time')
        # merg['energy'] = pd.to_numeric(merg['energy(kWh/hh)'])  ## converts exisitng energy colum to correct numeric values
        return merg # .drop(columns = extradata, inplace = True)


def break_by_meter(df, unique_meters):
    '''df = weather and meter data combined
        Splits data by meter'''
    meter_df_list = []
    for meter_name in unique_meters:
        meter_df_list.append(df[df['LCLid'] == meter_name])

    return meter_df_list

## plot Scatter_matrix()
    ## Discuss corollations
def plot_scatter_matrix(df):
    plot1 = pd.plotting.scatter_matrix(df)
    plt.savefig('images/Scatter_matrix_of_{}.png'.format(df['LCLid'][0]))


## Mean energy by by block
    ## build function
    ## Plot heat map of blocks

## Mean energy by meter in each block
def mean_meter_all(meter_df_list):  ### Need to fixxx
    mean = []
    name = []
    for meter in meter_df_list:
        mean.append(meter['energy'].mean())
        name.append(meter['LCLid'].unique()[0]) ## this gets the unique name of the meter itself
    return mean, name


### Only use if you want to compute all blocks.
    ## Takes ~ 10 mins to run for 111 blocks
def means_of_all_blocks(number_of_blocks):
    '''This function will find the means of the n blocks in the data base'''
    dfweather_h = pd.read_csv("data/smart_meters_london/weather_hourly_darksky.csv")
    df_pass = pd.DataFrame({'A' : []})
    for i in range(number_of_blocks):
        print('block_{}'.format(i))
        string = "data/smart_meters_london/halfhourly_dataset/block_{}.csv".format(i)
        dfmeter_hh = pd.read_csv(string)
        df_meter_weather_hourly = join_df_weather(dfmeter_hh, dfweather_h) ## joins the two data frames on hour of time. Removes all non matching half hour data
        unique_meters = df_meter_weather_hourly['LCLid'].unique() ## Breaks into individual meter names
        meter_df_list = break_by_meter(df_meter_weather_hourly, unique_meters)  # See def
        mean_meter_enengy, mean_meter_enengy_name = mean_meter_all(meter_df_list) # see Def

        # This is to keep the mean lengths consistant
            ## should create a better way to implenment and add NAN instead of adding 0
                    # this will shift the mean down
        if len(mean_meter_enengy) == 50 :
            df_pass['block_{}'.format(i)] = mean_meter_enengy
        elif len(mean_meter_enengy) < 50:
            len_param = len(mean_meter_enengy)
            mean_meter_enengy = mean_meter_enengy + [0]*(50 -len_param)
            df_pass['block_{}'.format(i)] = mean_meter_enengy
        else:
            df_pass['block_{}'.format(i)] = mean_meter_enengy[0:50]

    df_pass.to_csv('data/smart_meters_london/meterAVGS.csv', encoding='utf-8', index=False)
    return df_pass.drop(labels = 'A', axis = 1)

def means_of_all_blocks_plot():
    df = pd.read_csv('data/smart_meters_london/meterAVGS.csv')
    df.drop(columns = ['A'],inplace=True)
    ax = sns.heatmap(df.values)
    plt.xlabel('Blocks')
    plt.ylabel('Blocks')
    plt.title('Average Energy for all Blocks (24/7)')
    plt.show()

def energy_by_hour_plot(meter_df_list):
    pass



def split_data_multimeter(df_in):
    ## Split and clean Data
    df_in.dropna(inplace = True)
    df = df_in.copy(deep = True)
    y = df['energy']
    X = df.drop(columns = ['energy','energy(kWh/hh)','time', 'tstp', 'date_start_time'], inplace = True)  ## removed time and tstp because i have a time_date object thats contains that data
    X = pd.get_dummies(df,columns = ['precipType', 'icon','summary', 'LCLid'])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25)
    return X_train, X_test, y_train, y_test

def split_data_single_meter(single_meter_df):
    ## Split and clean Data
    single_meter_df.dropna(inplace = True)
    df = single_meter_df.copy(deep = True)
    y = df['energy']
    X = df.drop(columns = ['energy','energy(kWh/hh)','time', 'tstp', 'date_start_time', 'LCLid'], inplace = True)  ## removed time and tstp because i have a time_date object thats contains that data
    X = pd.get_dummies(df,columns = ['precipType', 'icon','summary'])
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25)
    return X_train, X_test, y_train, y_test


def linear_reg_all(df):
    ## Split and clean Data
    X_train, X_test, y_train, y_test = split_data_multimeter(df)

    # Fit your model using the training set
    linear = LinearRegression()
    lasso_cv = LassoCV(cv=5, random_state=0)
    ridge_cv = RidgeCV(alphas=(0.1, 1.0, 10.0))
    linear.fit(X_train, y_train)
    lasso_cv.fit(X_train, y_train)
    ridge_cv.fit(X_train, y_train)
    print('Linear regression score on train set with all parameters: {}'.format(linear.score(X_train, y_train)))
    print('Linear regression score on test set with all parameters: {}'.format(linear.score(X_test, y_test)))
    print('Linear regression crossVal score on train set with all parameters: {}'.format(linear.score(X_train, y_train)))
    print('Linear regression crossVal score on test set with all parameters: {}'.format(linear.score(X_test, y_test)))

    print('LassoCV regression score on train set with all parameters: {}'.format(lasso_cv.score(X_train, y_train)))
    print('LassoCV regression score on test set with all parameters: {}'.format(lasso_cv.score(X_test, y_test)))
    print('LassoCV regression crossVal score on train set with all parameters: {}'.format(lasso_cv.score(X_train, y_train)))
    print('LassoCV regression crossVal score on test set with all parameters: {}'.format(lasso_cv.score(X_test, y_test)))

    print('RidgeCV regression score on train set with all parameters: {}'.format(ridge_cv.score(X_train, y_train)))
    print('RidgeCV regression score on test set with all parameters: {}'.format(ridge_cv.score(X_test, y_test)))
    print('RidgeCV regression crossVal score on train set with all parameters: {}'.format(ridge_cv.score(X_train, y_train)))
    print('RidgeCV regression crossVal score on test set with all parameters: {}'.format(ridge_cv.score(X_test, y_test)))

    return ridge_cv, lasso_cv, linear, X_train, X_test, y_train, y_test

def linear_reg_single_meter(single_meter_df):

    X_train, X_test, y_train, y_test = split_data_single_meter(single_meter_df)
    # Fit your model using the training set
    linear = LinearRegression()
    lasso_cv = LassoCV(cv=5, random_state=0)
    ridge_cv = RidgeCV(alphas=(0.1, 1.0, 10.0))
    linear.fit(X_train, y_train)
    lasso_cv.fit(X_train, y_train)
    ridge_cv.fit(X_train, y_train)
    print('Linear regression score on train set with all parameters: {}'.format(linear.score(X_train, y_train)))
    print('Linear regression score on test set with all parameters: {}'.format(linear.score(X_test, y_test)))
    print('Linear regression crossVal score on train set with all parameters: {}'.format(linear.score(X_train, y_train)))
    print('Linear regression crossVal score on test set with all parameters: {}'.format(linear.score(X_test, y_test)))

    print('LassoCV regression score on train set with all parameters: {}'.format(lasso_cv.score(X_train, y_train)))
    print('LassoCV regression score on test set with all parameters: {}'.format(lasso_cv.score(X_test, y_test)))
    print('LassoCV regression crossVal score on train set with all parameters: {}'.format(lasso_cv.score(X_train, y_train)))
    print('LassoCV regression crossVal score on test set with all parameters: {}'.format(lasso_cv.score(X_test, y_test)))

    print('RidgeCV regression score on train set with all parameters: {}'.format(ridge_cv.score(X_train, y_train)))
    print('RidgeCV regression score on test set with all parameters: {}'.format(ridge_cv.score(X_test, y_test)))
    print('RidgeCV regression crossVal score on train set with all parameters: {}'.format(ridge_cv.score(X_train, y_train)))
    print('RidgeCV regression crossVal score on test set with all parameters: {}'.format(ridge_cv.score(X_test, y_test)))

    return ridge_cv, lasso_cv, linear, X_train, X_test, y_train, y_test

## This needs to be fixed.  Log issue??
def Ridge_plot(X_train, X_test, y_train, y_test):
    plot_y = []
    plot_y_test = []
    plot_x = np.arange(0.1,10,0.1)
    for val in np.arange(0.1,10,0.1):
        ridge = Ridge(alpha=val)
        ridge.fit(X_train.values, y_train.values)
        plot_y.append(ridge.score(X_train.values, y_train.values))
        plot_y_test.append(ridge.score(X_test.values, y_test.values))

    plt.scatter(plot_x, plot_y, c = 'r')
    plt.scatter(plot_x, plot_y_test, c = 'b')
    plt.show()
    return plot_x, plot_y, plot_y_test

## Not working on the data ?? need to fix
def OLS_model(X_train,y_train):
    ols_model = sm.OLS(endog=y_train, exog=X_train).fit()
    print(ols_model.summary())
    energy_cons = ols_model.outlier_test()['energy']
    plt.figure(1)
    plt.scatter(ols_model.fittedvalues, energy_cons)
    plt.xlabel('Fitted values of AVGEXP')
    plt.ylabel('Studentized Residuals')
    plt.figure(2)
    sm.graphics.qqplot(energy_cons, line='45', fit=True)
    plt.show()


## Split all data into train and test.  Only  test on test
    ## Need function to read and write new files to split data
    ## Place in train and test file sets for easyc iterations
        ## should probably build a database (SQL) with tables by block number

## Add cost benifit matrix from confuion matrix see this: /Documents/galvanize/Lectures/lecture_profit-curve-imbal-classes

## For each block test data
    ## Set x and y values
    ## X is average meter data
    ## Y will be the weather and time (month and day) data

    ## split into train and test data

    ## Do LinearRegression with Kfolds
        ## QQ plot

    ## do logisticRegression with X above or below average use
        ## ROC plot

    #return linear errors

if __name__ == '__main__':
    dfmeter = pd.read_csv("data/smart_meters_london/daily_dataset/block_0.csv")
    dfweather = pd.read_csv("data/smart_meters_london/weather_daily_darksky.csv")

    dfmeter_hh = pd.read_csv("data/smart_meters_london/halfhourly_dataset/block_0.csv")##, dtype={'energy(kWh/hh)': float} )
    dfweather_h = pd.read_csv("data/smart_meters_london/weather_hourly_darksky.csv")


    df_meter_weather_hourly = join_df_weather(dfmeter_hh, dfweather_h) ## joins the two data frames on hour of time. Removes all non matching half hour data
    df_meter_weather_hourly['energy'] = pd.to_numeric(df_meter_weather_hourly['energy(kWh/hh)'])  ## converts exisitng energy colum to correct numeric values

    unique_meters = df_meter_weather_hourly['LCLid'].unique() ## gets unique meters in block
    meter_df_list = break_by_meter(df_meter_weather_hourly, unique_meters)

    ## plot_scatter_matrix(meter_df_list[0]) ## Initial scatter plot of a single meter at a single block
    ridge_cv, lasso_cv, linear, X_train, X_test, y_train, y_test = linear_reg_all(df_meter_weather_hourly)
    ridge_cv_meter, lasso_cv_meter, linear_meter, X_train_meter, X_test_meter, y_train_meter, y_test_meter = linear_reg_single_meter(meter_df_list[0])
    #plot_x_alphas, plot_y, plot_y_test = ridgeCV_plot(X_train, X_test, y_train, y_test)
    mean_meter_enengy, mean_meter_enengy_name = mean_meter_all(meter_df_list)
    #heat_map_plot(mean_meter_enengy, mean_meter_enengy_name)
    #plt.show()
