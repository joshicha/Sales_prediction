# -*- coding: utf-8 -*-
"""Boots_drug_sales_prediction.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1RlfFSC3MM9P-wQdifqsDrw3Rq6DinTwc

**BOOTS DRUG SALES FORECASTING** 

Author: Dr Chaitanya Joshi

Data Science Campus


---




**In this notebook we:**

**(.) Create a dummy dataset for Boots sales data**

**(.) Use forcasting models for Drug Sales forecasting**

**(.) There is a separate notebook for Exploratory Data Analysis which checks for stationarity, regularity of the time series data**

**(.) Sales forecasting models will be built for different drug categories, assuming Sales of different drug items are not correlated**

**(.) We will sample the Sales data on a weekly basis and at Postcode level (we have ignored the OUTPUT_AREA feature in this consideration)**

**(.) (STILL) TO DO: one can make the mapping from OUTPUT_AREA/Postcode level to Upper Tier Local Authorities and can repeat the analysis at UTLA level**


---

We have tried a few prediction models:

Facebook Prophet (Linear and Logistic growth)

LinearRegression

BayesianRidge

LassoLars

DecisionTreeRegressor

RandomForestRegressor

KNeighborsRegressor

XGBRegressor

SGDRegressor
"""

# Commented out IPython magic to ensure Python compatibility.
# Install all the packages: only need this cell when running simulations on Google Colab

from google.colab import drive
drive.mount('/content/drive')

# %cd /content/drive/My Drive/Drug_sales_dataset

"""**Install Packages**"""

! pip install faker

! pip install fbprophet

! pip install holidays

! pip install pgeocode

! pip install geopy

! pip install xgboost

"""**Import packages**"""

# Commented out IPython magic to ensure Python compatibility.
import pandas as pd
import numpy as np
import math

from faker import Factory
import string 
from datetime import date
from datetime import datetime, timedelta
import holidays
import random
from random import randint




from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.graphics.tsaplots import plot_pacf
from statsmodels.tsa.stattools import kpss
import warnings
warnings.filterwarnings("ignore")


import matplotlib.pyplot as plt
import plotly.offline as py
py.init_notebook_mode()
import pgeocode
from geopy.geocoders import Nominatim
# %matplotlib inline
import seaborn as sns

from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error as MAE, mean_squared_error, r2_score
from sklearn.model_selection import cross_validate


from fbprophet import Prophet
from fbprophet.plot import plot_plotly
from fbprophet.plot import add_changepoints_to_plot
from fbprophet.diagnostics import cross_validation
from fbprophet.diagnostics import performance_metrics



from sklearn.linear_model import LinearRegression
from sklearn.linear_model import BayesianRidge
from sklearn.linear_model import LassoLars
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor
import xgboost as xgb
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import StandardScaler

pd.set_option('display.max_columns', None)

"""**Utility Functions**"""

def date_between(d1, d2):
    f = '%d-%m-%Y'
    return faker.date_time_between_dates(datetime.strptime(d1, f), datetime.strptime(d2, f))


# This function to be used when pgeocode fails to get region information
def get_cntry_name(post_cod):

  geolocator = Nominatim()
  
  location = geolocator.geocode(post_cod)
  
  if type(location)!=None.__class__:
    
    tmp_lst=[x.strip() for x in location.raw['display_name'].split(',')]

    if any("England" in s for s in tmp_lst):
      cntry_name='England'
    if any("Wales" in s for s in tmp_lst):
      cntry_name='Wales'
    if any("Scotland" in s for s in tmp_lst):
      cntry_name='Scotland'
    if any("Northern Ireland" in s for s in tmp_lst):
      cntry_name='Northern Ireland'
  else:
    cntry_name=float('United Kingdom')
    
  return cntry_name



def uk_holiday(df,colm_dat,colm_reg):
  holdiay_list=[]
  for x in range(len(df)):
    
    if df.loc[x,colm_reg]=='England':
      uk_holidays =holidays.England()
      holdy=int(df_pharma_sales_raw.loc[x,'DATE'] in uk_holidays)
    elif df.loc[x,colm_reg]=='Scotland':
      uk_holidays =holidays.Scotland()
      holdy=int(df_pharma_sales_raw.loc[x,'DATE'] in uk_holidays)
    elif df.loc[x,colm_reg]=='Wales':
      uk_holidays =holidays.Wales()
      holdy=int(df_pharma_sales_raw.loc[x,'DATE'] in uk_holidays)
    elif df.loc[x,colm_reg]=='Northern Ireland':
      uk_holidays =holidays.NorthernIreland()
      holdy=int(df_pharma_sales_raw.loc[x,'DATE'] in uk_holidays)
    else:
      uk_holidays =holidays.UnitedKingdom()
      holdy=int(df_pharma_sales_raw.loc[x,'DATE'] in uk_holidays)
    holdiay_list.append(holdy)
  return holdiay_list


def dayNameFromWeekday(weekday):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[weekday] if 0 <= weekday < len(days) else None


def monday_of_calenderweek(year, week):
    first = date(year, 1, 1)
    base = 1 if first.isocalendar()[1] == 1 else 8
    return first + timedelta(days=base - first.isocalendar()[2] + 7 * (week - 1))



class MultiColumnLabelEncoder:
    def __init__(self,columns = None):
        self.columns = columns # array of column names to encode

    def fit(self,X,y=None):
        return self # 

    def transform(self,X):
        '''
        Transforms columns of X specified in self.columns using
        LabelEncoder(). If no columns specified, transforms all
        columns in X.
        '''
        output = X.copy()
        if self.columns is not None:
            for col in self.columns:
                output[col] = LabelEncoder().fit_transform(output[col])
        else:
            for colname,col in output.iteritems():
                output[colname] = LabelEncoder().fit_transform(col)
        return output

    def fit_transform(self,X,y=None):
        return self.fit(X,y).transform(X)

"""**Part (a): Creating a dummy dataset (the following cell can be skipped if real dataset is available)**"""

# random list of drugs categories
otc_drug_catg=['ANTIFUNGAL','PAIN RELIEVER','SMOKING CESSATION','DIABETES/Insulin','DIGESTION','VITAMINS',\
               'EYE CARE','COUGH/COLD/ALLERGY','Hand Sanitiser']

otc_drug_catg=[x.lower() for x in otc_drug_catg]



# random list of postcodes
post_codes_random=['ML3 0EU','BN14 9NN','WA7 3JF','SR3 3NB','SW19 1UX','NG32 1HW','CO10 2TA','PA34 5JN',\
                   'RG42 3RD','S43 4JZ','BS31 1UT','LL309YX','CF10 1AF','G1 1EA','G1 1HF','E1 7AE','E1 6AN','BT1 1BW']

N=8 # Number of digits in OUTPUT_AREA variable: we have created dummy records for this variable.
# One has to make a mapping from OUTPUT_AREA to UTLA level to sample the data at UTLA level
str_output_areas=[''.join(random.choices(string.ascii_uppercase +string.digits, k = N)) for x in range(25)]

                   
# Map store number to their postcodes
store_number_dictnry={'ML3 0EU':1,'BN14 9NN':2,'WA7 3JF':3,'SR3 3NB':4,'SW19 1UX':5,'NG32 1HW':6,\
                      'CO10 2TA':7,'PA34 5JN':8,'RG42 3RD':9,'S43 4JZ':10,'BS31 1UT':11,\
                      'LL309YX':12,'CF10 1AF':13,'G1 1EA':14,'G1 1HF':15,'E1 7AE':16,'E1 6AN':17,'BT1 1BW':18}

# Initiate the raw dataset
df_pharma_sales_raw=pd.DataFrame()

df_pharma_sales_raw['STORE NUMBER']=""

df_pharma_sales_raw['STORE POSTCODE']=""
df_pharma_sales_raw['CATEGORY']=""
df_pharma_sales_raw['DATE']=""
df_pharma_sales_raw['TIME']=""
df_pharma_sales_raw['TRANSACTION COUNT']=""
df_pharma_sales_raw['UNITS']=""
df_pharma_sales_raw['OUTPUT AREA']=""


# Initiate the Faker module for creating dummy dataset
faker = Factory.create()


def fakerecord():
    return {'DATE': date_between('01-05-2018', '01-05-2020').date(),  # random date
            'TRANSACTION COUNT': faker.numerify('##'),# random count
            'UNITS': faker.numerify('#')}# random units

# Size of the dataset
num_rows=50000

df_pharma_sales_raw = pd.DataFrame([fakerecord() for _ in range(num_rows)])

df_pharma_sales_raw['STORE POSTCODE']=np.random.choice(a=post_codes_random,size=num_rows)
df_pharma_sales_raw['CATEGORY']=np.random.choice(a=otc_drug_catg,size=num_rows)
df_pharma_sales_raw['STORE NUMBER']=df_pharma_sales_raw['STORE POSTCODE'].map(store_number_dictnry) 
df_pharma_sales_raw['OUTPUT_AREA']=np.random.choice(a=str_output_areas,size=num_rows)

df_pharma_sales_raw['TIME']=np.random.choice(a=pd.date_range("09:00", "18:00", freq="05min").time,size=num_rows)
df_pharma_sales_raw.sample(5)



df_pharma_sales_raw['STORE NUMBER']=df_pharma_sales_raw['STORE NUMBER'].astype(int)
df_pharma_sales_raw['STORE POSTCODE']=df_pharma_sales_raw['STORE POSTCODE'].astype(str)
df_pharma_sales_raw['CATEGORY']=df_pharma_sales_raw['CATEGORY'].astype(str)
df_pharma_sales_raw['TRANSACTION COUNT']=df_pharma_sales_raw['TRANSACTION COUNT'].astype(int)
df_pharma_sales_raw['UNITS']=df_pharma_sales_raw['UNITS'].astype(int)
df_pharma_sales_raw['OUTPUT_AREA']=df_pharma_sales_raw['OUTPUT_AREA'].astype(str)



print(df_pharma_sales_raw.dtypes)

df_pharma_sales_raw=df_pharma_sales_raw.sort_values(by=['DATE','TIME']).reset_index(drop=True)
df_pharma_sales_raw.to_pickle('df_pharma_sales_raw.pkl')


df_pharma_sales_raw.head(5)

"""**Part (b): We next  manipulate the dataset to bring out some additional attributes**"""

# read the dataset

df_pharma_sales_raw=pd.read_pickle('df_pharma_sales_raw.pkl')


# Drug categories: number of unique drug items

# Option 1: consider all the drug categories
#drug_catgrs=list(np.unique(df_pharma_sales_raw['CATEGORY']))

# Option 2: consider most popular drug items
drug_catgrs=list(df_pharma_sales_raw['CATEGORY'].value_counts().nlargest(5).index)

# Option 3: hand-pick a few drug items relevant for epidemic growth indication.
#drug_catgrs=['paracetamol','sanitiser','vitamin']



df_pharma_sales_raw=df_pharma_sales_raw.loc[df_pharma_sales_raw['CATEGORY'].isin(drug_catgrs)].reset_index(drop=True)
# Visually checking if the imported data looks OK ?
print(df_pharma_sales_raw.head(5))


print(df_pharma_sales_raw.shape)

"""**1. Sample the sales every hour**"""

df_pharma_sales_raw['TIME']=pd.to_datetime(df_pharma_sales_raw['TIME'].astype(str)).dt.hour
df_pharma_sales_raw['DATE']=pd.to_datetime(df_pharma_sales_raw['DATE'].astype(str))

df_pharma_sales_raw=df_pharma_sales_raw.groupby(['DATE', 'TIME','STORE POSTCODE', 'CATEGORY', 'OUTPUT_AREA'])\
['TRANSACTION COUNT', 'UNITS'].mean().reset_index()

print(df_pharma_sales_raw.head(5))

print(df_pharma_sales_raw.shape)

"""**2. Add additional information on the dataset, including day of the week and week number**"""

df_pharma_sales_raw['DAY OF THE WEEK']=[x.weekday() for x in df_pharma_sales_raw.DATE]

df_pharma_sales_raw['DAY OF THE WEEK']=df_pharma_sales_raw['DAY OF THE WEEK'].apply(lambda x: dayNameFromWeekday(x))


df_pharma_sales_raw['WEEK NUMBER']=pd.to_datetime(df_pharma_sales_raw.DATE).dt.week


print(df_pharma_sales_raw.head(5))

print(df_pharma_sales_raw.shape)

"""**3. Sample the sales on a daily basis and ignoring the time variable**"""

df_pharma_sales_raw=df_pharma_sales_raw.groupby(['DATE','STORE POSTCODE','CATEGORY','OUTPUT_AREA','DAY OF THE WEEK','WEEK NUMBER'])\
['TRANSACTION COUNT','UNITS'].mean().reset_index()

print(df_pharma_sales_raw.head(5))

print(df_pharma_sales_raw.shape)

"""**4. Let us add regions based on the postcodes**"""

nomi = pgeocode.Nominatim('gb')

regions=[nomi.query_postal_code(x).state_name for x in list(df_pharma_sales_raw['STORE POSTCODE'].unique())]


# Sometimes pgeocode fails, geopy can be used then.

#regions=[get_cntry_name(z) for z in list(df_pharma_sales_raw['STORE POSTCODE'].unique())]

# Sometimes pgeocode fails, geopy can be used then.


region_dict=dict(zip(list(df_pharma_sales_raw['STORE POSTCODE'].unique()),regions))

df_pharma_sales_raw['REGION']=df_pharma_sales_raw['STORE POSTCODE'].map(region_dict) 


print(df_pharma_sales_raw.head(5))

print(df_pharma_sales_raw.shape)

"""**5. Let us add region specific holidays**"""

df_pharma_sales_raw['HOLIDAY']=uk_holiday(df_pharma_sales_raw,'DATE','REGION')


print(df_pharma_sales_raw.head(5))

print(df_pharma_sales_raw.shape)

"""**6. If the data is sparse, one can sample the data at a weekly rate- we first have to convert the dates to weekly interval**"""

df_pharma_sales_raw['YEAR']=pd.to_datetime(df_pharma_sales_raw['DATE'].astype(str)).dt.year

df_pharma_sales_raw['MONTH']=pd.to_datetime(df_pharma_sales_raw['DATE'].astype(str)).dt.month

df_pharma_sales_raw['WEEKLY_DATE']=df_pharma_sales_raw.apply(lambda x: monday_of_calenderweek(x['YEAR'], x['WEEK NUMBER']), axis=1)


print(df_pharma_sales_raw.head(5))

print(df_pharma_sales_raw.shape)

"""**7. Sample the sales on a weekly level (Monday of the week)**"""

selected_columns=[x for x in df_pharma_sales_raw.columns if x not in ['DATE','DAY OF THE WEEK','TRANSACTION COUNT','UNITS','HOLIDAY']]

df_pharma_sales_raw=df_pharma_sales_raw.groupby(selected_columns)['TRANSACTION COUNT','UNITS','HOLIDAY'].mean().reset_index()

print(df_pharma_sales_raw.head(5))

print(df_pharma_sales_raw.shape)

"""**8. LabelEncode non-numerical features**

**As a first approach, we are sampling Sales at Postcodes level**
"""

# Perhaps TRANSACTION COUNT is not a independent feature- so we DROP it


df_pharma_sales_raw=df_pharma_sales_raw[[x for x in df_pharma_sales_raw.columns if x not in ['TRANSACTION COUNT']]]

df_pharma_sales_raw=df_pharma_sales_raw[[x for x in df_pharma_sales_raw.columns if x not in ['OUTPUT_AREA']]]


df_pharma_sales_raw_tim_sers=df_pharma_sales_raw

df_pharma_sales_raw_tim_sers=df_pharma_sales_raw_tim_sers[df_pharma_sales_raw_tim_sers['REGION'].notna()].reset_index(drop=True)


df_pharma_sales_raw_tim_sers['REGION'].fillna('United Kingdom', inplace=True)
object_type_cols=[x for x in df_pharma_sales_raw.select_dtypes(include=[object]).columns if x not in ['WEEKLY_DATE','CATEGORY']]

df_pharma_sales_raw_tim_sers=MultiColumnLabelEncoder(columns = object_type_cols).fit_transform(df_pharma_sales_raw_tim_sers)


df_pharma_sales_raw_tim_sers.sample(5)

"""**9. Data transformation: converting the dataframe to a pivot table**"""

groupng_ftrs=[x for x in df_pharma_sales_raw_tim_sers.columns if x not in ['CATEGORY','UNITS']]


df_pharma_sales_raw_tim_sers=df_pharma_sales_raw_tim_sers.groupby(['CATEGORY']+groupng_ftrs)['UNITS'].mean().reset_index()
df_pharma_sales_raw_tim_sers=df_pharma_sales_raw_tim_sers.pivot_table('UNITS', groupng_ftrs, 'CATEGORY').reset_index(drop=False)

df_pharma_sales_raw_tim_sers.sample(5)

"""**We will treat sales of different durg items as independent of each other.
Building separate model(s) to predict sales of different items- this assumes sales of different items are unrelated- which might not be true- If there are correlations in Sales pattern of different drugs, one might have to uncorrelate those columns using PCA or other techniques**

**In the following we will focus on individual drug categories for their sale predictions**
"""

# Different drug categories of interest have to be looped over to build their individual Sales Forecasting Models.

df_pharma_sales_raw_tim_sers_one_catg=[df_pharma_sales_raw_tim_sers[[x for x in df_pharma_sales_raw_tim_sers.columns if \
                                                                        (x not in drug_catgrs)\
                                                                    |(x==drug_catgrs[which_drg_catg])]].reset_index(drop=True)\
                                        for which_drg_catg in range(len(drug_catgrs))]


# This stores sales of different drug items
print(df_pharma_sales_raw_tim_sers_one_catg[0])

prfmncs_df=pd.DataFrame()
model_type=[]
error_mae=[]
error_mse=[]
error_r2=[]

# Store different training-test datasets for various drug items
train_test_dataset_drug_catg=[]
for which_drg_catg in range(len(drug_catgrs)):
  train_test_dataset= pd.DataFrame()
  train_test_dataset['ds'] =df_pharma_sales_raw_tim_sers_one_catg[which_drg_catg]["WEEKLY_DATE"]
  train_test_dataset['y']=df_pharma_sales_raw_tim_sers_one_catg[which_drg_catg][drug_catgrs[which_drg_catg]]
  feature_names=[x for x in df_pharma_sales_raw_tim_sers_one_catg[which_drg_catg].columns if x not in ['WEEKLY_DATE',drug_catgrs[which_drg_catg]]]
  for x in feature_names:
    train_test_dataset[x]=df_pharma_sales_raw_tim_sers_one_catg[which_drg_catg][x]
  del train_test_dataset['YEAR']

  del train_test_dataset['MONTH']
  
  train_test_dataset=train_test_dataset.groupby([x for x in train_test_dataset.columns if x not in ['y']])['y'].mean()\
  .reset_index().sort_values(by='ds').reset_index(drop=True)
  
  train_test_dataset_drug_catg.append(train_test_dataset)


print(train_test_dataset_drug_catg)



# Split into train/test datasets based on drug categories
train_X_drug_catg=[]
test_X_full_drug_catg=[]
store_list_drug_catg=[]
for which_drg_catg in range(len(drug_catgrs)):
  # Split your dataset 
  # Define a size for your train set 
  train_size = int(0.7 * len(train_test_dataset_drug_catg[which_drg_catg]))
  train_X= train_test_dataset_drug_catg[which_drg_catg][:train_size]
  train_X_drug_catg.append(train_X)
  test_X_full= train_test_dataset_drug_catg[which_drg_catg][train_size:]
  test_X_full_drug_catg.append(test_X_full)
  store_list_drug_catg.append(np.unique(test_X_full_drug_catg[which_drg_catg]['STORE POSTCODE']))

"""**Part (b): Forecasting models for sales predictions**

---
We will use different approaches for Sales forecasting purpose:

(1) Facebook Prophet

**Facebook Prophet Linear growth model**
"""

for which_drg_catg in range(len(drug_catgrs)):
  for z in store_list_drug_catg[which_drg_catg]:
    test_X=test_X_full_drug_catg[which_drg_catg][test_X_full_drug_catg[which_drg_catg]['STORE POSTCODE']==z]
    
    pro_regressor = Prophet(growth='linear',
                  yearly_seasonality=False,
                  weekly_seasonality=True,
                  daily_seasonality=False,
                  holidays=None,
                  seasonality_mode='multiplicative',
                  seasonality_prior_scale=10,
                  holidays_prior_scale=10,
                  changepoint_prior_scale=.05,
                  mcmc_samples=0
                 ).add_seasonality(name='yearly',
                                    period=365.25,
                                    fourier_order=3,
                                    prior_scale=10,
                                    mode='additive')
    #pro_regressor.add_country_holidays(country_name='UK')
    chsen_variables=[ x for x in list(train_test_dataset_drug_catg[which_drg_catg].columns) if x not in ['ds','y']]
    for x in chsen_variables:
      pro_regressor.add_regressor(x)
      #Fitting the data
    pro_regressor.fit(train_X_drug_catg[which_drg_catg])
    #forecast the data for Test  data
    forecast_data = pro_regressor.predict(test_X)
    
    f, ax = plt.subplots(1)
    f.set_figheight(5)
    f.set_figwidth(15)
    plt.plot(test_X['ds'], test_X['y'], color='r',label='Actual sales of {} for store number {}'.format(drug_catgrs[which_drg_catg],z))
    fig = pro_regressor.plot(forecast_data, ax=ax)
    a = add_changepoints_to_plot(fig.gca(), pro_regressor, forecast_data)
    plt.legend()
    plt.show()
    
    # figure size in inches
    fig = plt.figure(1, figsize=(8, 14), frameon=False, dpi=100)
 

    test_X['ds']= pd.to_datetime(test_X['ds'].astype(str))
    forecast_data_grnd_truth=pd.merge(forecast_data, test_X[['ds','y']].reset_index(drop=True), on="ds")
    
    g=sns.jointplot('y','yhat', data=forecast_data_grnd_truth,kind="reg")
    g.fig.set_figwidth(10)
    g.fig.set_figheight(10)
    ax = g.fig.axes[1]
    
    forecast_data_grnd_truth=forecast_data_grnd_truth.dropna().reset_index(drop=True)
    ax.set_title('sales of drug {} for store number {} with Pearson correlation = {:+4.2f}\n and MAE = {:4.1f}'.\
                 format(drug_catgrs[which_drg_catg],z,forecast_data_grnd_truth.loc[:,['y','yhat']].corr().iloc[0,1],\
                    MAE(forecast_data_grnd_truth.loc[:,'y'].values,\
                        forecast_data_grnd_truth.loc[:,'yhat'].values)), fontsize=16)
    
    model_type.append('Prophet_Linear for drug {} and store postcode {}'.format(drug_catgrs[which_drg_catg],z))
    error_mae.append(MAE(forecast_data_grnd_truth.loc[:,'y'].values,forecast_data_grnd_truth.loc[:,'yhat'].values))
    error_r2.append(r2_score(forecast_data_grnd_truth.loc[:,'y'].values,forecast_data_grnd_truth.loc[:,'yhat'].values))
    error_mse.append(mean_squared_error(forecast_data_grnd_truth.loc[:,'y'].values,forecast_data_grnd_truth.loc[:,'yhat'].values))

    ax.set_ylabel("model's estimates", fontsize=15)
    
    ax.set_xlabel("actual sales observations", fontsize=15)

    ax.xaxis.set_label_coords(0.5, -0.025)

    ax.yaxis.set_label_coords(-0.15, -3.25)

    pro_regressor.plot_components(forecast_data)



"""**Facebook Prophet Logistic growth model**"""

for which_drg_catg in range(len(drug_catgrs)):
  for z in store_list_drug_catg[which_drg_catg]:

    cap = train_X_drug_catg[which_drg_catg]['y'].max()+10#20
    floor = 0
    train_X_drug_catg[which_drg_catg]['cap'] = cap
    train_X_drug_catg[which_drg_catg]['floor'] = floor

    test_X_full_drug_catg[which_drg_catg]['cap'] = cap
    test_X_full_drug_catg[which_drg_catg]['floor'] = floor
    test_X=test_X_full_drug_catg[which_drg_catg][test_X_full_drug_catg[which_drg_catg]['STORE POSTCODE']==z]
    
    pro_regressor = Prophet(growth='logistic',
                  changepoint_range=0.95,
                  yearly_seasonality=False,
                  weekly_seasonality=False,
                  daily_seasonality=False,
                  seasonality_prior_scale=10,
                  changepoint_prior_scale=.01)
    #pro_regressor.add_country_holidays(country_name='UK')
    chsen_variables=[ x for x in list(train_test_dataset_drug_catg[which_drg_catg].columns) if x not in ['ds','y']]
    for x in chsen_variables:
      pro_regressor.add_regressor(x)
      #Fitting the data
    pro_regressor.fit(train_X_drug_catg[which_drg_catg])
    #forecast the data for Test  data
    forecast_data = pro_regressor.predict(test_X)
    
    f, ax = plt.subplots(1)
    f.set_figheight(5)
    f.set_figwidth(15)
    plt.plot(test_X['ds'], test_X['y'], color='r',label='Actual sales of {} for store number {}'.format(drug_catgrs[which_drg_catg],z))
    fig = pro_regressor.plot(forecast_data, ax=ax)
    a = add_changepoints_to_plot(fig.gca(), pro_regressor, forecast_data)
    plt.legend()
    plt.show()
    
    # figure size in inches
    fig = plt.figure(1, figsize=(8, 14), frameon=False, dpi=100)
 

    test_X['ds']= pd.to_datetime(test_X['ds'].astype(str))
    forecast_data_grnd_truth=pd.merge(forecast_data, test_X[['ds','y']].reset_index(drop=True), on="ds")
    
    g=sns.jointplot('y','yhat', data=forecast_data_grnd_truth,kind="reg")
    g.fig.set_figwidth(10)
    g.fig.set_figheight(10)
    ax = g.fig.axes[1]
    
    forecast_data_grnd_truth=forecast_data_grnd_truth.dropna().reset_index(drop=True)
    ax.set_title('sales of drug {} for store number {} with Pearson correlation = {:+4.2f}\n and MAE = {:4.1f}'.\
                 format(drug_catgrs[which_drg_catg],z,forecast_data_grnd_truth.loc[:,['y','yhat']].corr().iloc[0,1],\
                    MAE(forecast_data_grnd_truth.loc[:,'y'].values,\
                        forecast_data_grnd_truth.loc[:,'yhat'].values)), fontsize=16)
    
    model_type.append('Prophet_Linear for drug {} and store postcode {}'.format(drug_catgrs[which_drg_catg],z))
    error_mae.append(MAE(forecast_data_grnd_truth.loc[:,'y'].values,forecast_data_grnd_truth.loc[:,'yhat'].values))
    error_r2.append(r2_score(forecast_data_grnd_truth.loc[:,'y'].values,forecast_data_grnd_truth.loc[:,'yhat'].values))
    error_mse.append(mean_squared_error(forecast_data_grnd_truth.loc[:,'y'].values,forecast_data_grnd_truth.loc[:,'yhat'].values))

    ax.set_ylabel("model's estimates", fontsize=15)
    
    ax.set_xlabel("actual sales observations", fontsize=15)

    ax.xaxis.set_label_coords(0.5, -0.025)

    ax.yaxis.set_label_coords(-0.15, -3.25)

    pro_regressor.plot_components(forecast_data)

"""**Different Regression based models**

---
One can try different regression based models:

LinearRegression

BayesianRidge

LassoLars

DecisionTreeRegressor

RandomForestRegressor

KNeighborsRegressor

XGBRegressor

SGDRegressor
"""

model_1= LinearRegression()

model_2 = BayesianRidge()

model_3 = LassoLars(alpha=0.3, fit_intercept=False, normalize=True)

model_4 = DecisionTreeRegressor(min_samples_leaf=20)

model_5 = RandomForestRegressor(n_estimators=30)


model_6 = KNeighborsRegressor(n_neighbors = 30)

model_7 = xgb.XGBRegressor(objective ='reg:squarederror', colsample_bytree = 0.3, learning_rate = 0.1, max_depth = 5, alpha = 10, n_estimators = 10)



model_8=SGDRegressor(max_iter=np.ceil(10**6 / max([len(x) for x in train_X_drug_catg])), tol=1e-3,loss="squared_loss", penalty=None)


model_list=[model_1,model_2,model_3,model_4,model_5,model_6,model_7,model_8]



model_name=['Linear','Bayesian','LassoLars','DecisionTree','RandomForest','KNeighbors','XGB','SGD']


model_dict=dict(zip(model_list,model_name))

for model_x in model_list:
  
  for which_drg_catg in range(len(drug_catgrs)):
    for z in store_list_drug_catg[which_drg_catg]:
      X_train=train_X_drug_catg[which_drg_catg].dropna().reset_index(drop=True)
      X_train['YEAR']=pd.to_datetime(train_X['ds'].astype(str)).dt.year
      features=[x for x in X_train.columns if x not in ['ds','y','floor','cap']]
    
      X_test= test_X_full_drug_catg[which_drg_catg][test_X_full_drug_catg[which_drg_catg]['STORE POSTCODE']==z].dropna().reset_index(drop=True)
      X_test['YEAR']=pd.to_datetime(X_test['ds'].astype(str)).dt.year
    
      model_x = model_x.fit(X_train[features],X_train['y'])
      yd_predicted = model_x.predict(X_train[features])
      yd_test_predicted = model_x.predict(X_test[features])
      model_type.append('{} for drug {} and store postcode {}'.format(model_dict.get(model_x),drug_catgrs[which_drg_catg],z))
      error_mae.append(MAE(X_test['y'], yd_test_predicted))
      error_r2.append(r2_score(X_test['y'], yd_test_predicted))
      error_mse.append(mean_squared_error(X_test['y'], yd_test_predicted))
      
    which_model=model_x # 
    if model_dict.get(which_model) in ['DecisionTree','RandomForest','XGB']:
      features = X_train[features].columns
      importances = which_model.feature_importances_
      indices = np.argsort(importances)
      plt.figure(figsize=(8,10))
      plt.title('Feature Importances', fontsize=20)
      plt.barh(range(len(indices)), importances[indices], color='pink', align='center')
      plt.yticks(range(len(indices)), features[indices])
      plt.xlabel('Relative Importance')
      plt.savefig('Feature importance {}'.format(model_dict.get(model_x))+'.png')

# This stores the performance of various models tested on various stores and different drug categories.

prfmncs_df['Model']=model_type
prfmncs_df['MAE']=error_mae
prfmncs_df['r2_score']=error_r2
prfmncs_df['MSE']=error_mse

prfmncs_df.to_csv('forecasting_prfmncs_df_models.csv')

prfmncs_df

