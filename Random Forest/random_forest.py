# -*- coding: utf-8 -*-
"""RandomForest_bueno_(2)_(1)_(1).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ZeKKwBxZqyG093zNplFKkINyXGyXKvvQ
"""

pip install skforecast

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import pandas as pd

# Plots
# ==============================================================================
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')
plt.rcParams['lines.linewidth'] = 1.5
# %matplotlib inline

# Modeling and Forecasting
# ==============================================================================
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

from skforecast.ForecasterAutoreg import ForecasterAutoreg
from skforecast.ForecasterAutoregCustom import ForecasterAutoregCustom
from skforecast.ForecasterAutoregMultiOutput import ForecasterAutoregMultiOutput
from skforecast.model_selection import grid_search_forecaster
from skforecast.model_selection import backtesting_forecaster

from joblib import dump, load
from statsmodels.tsa.stattools import adfuller
import math
from math import exp

# Warnings configuration
# ==============================================================================
import warnings
# warnings.filterwarnings('ignore')

"""##Random Forest Univariado"""

dfu = pd.read_excel("data_col.xlsx")

"""**Preprocesamiento de los datos**"""

dfu.rename(columns = {"GDP, real, LCU":"PIB"}, inplace = True)
dfu = dfu.dropna()
dfu

dfu['date']=pd.to_datetime(dfu['year'].astype(str) + 'Q' + dfu['quarter'].astype(str))
dfu

# Index time
# ==============================================================================
SerieTiempou = dfu.set_index('date')
SerieTiempou = SerieTiempou.sort_index()
SerieTiempou.head()

"""**Normalización**"""

SerieTiempou["LPIB"] = np.log(SerieTiempou["PIB"])
SerieTiempou["DLPIB"] = SerieTiempou["LPIB"].diff()
SerieTiempou = SerieTiempou.drop(SerieTiempou.index[0])
SerieTiempou.head()

print(f'Number of rows with missing values: {SerieTiempou.isnull().any(axis=1).mean()}')

SerieTiempou = SerieTiempou.asfreq('QS')

fig, ax = plt.subplots()
ax.plot("PIB", data =SerieTiempou)
plt.show()

fig, ax = plt.subplots()
ax.plot("DLPIB", data =SerieTiempou)
plt.show()

adf= adfuller(SerieTiempou["DLPIB"], maxlag=1)
print("el t-test es:",adf[0])
print("el p-value es:", adf[1])
print("valores criticos:", adf[4])
#p-value es mayor a 0.5 por lo tanto no es estacionario

# Verify that a temporary index is complete
# ==============================================================================
(SerieTiempou.index == pd.date_range(start=SerieTiempou.index.min(),
                             end=SerieTiempou.index.max(),
                             freq=SerieTiempou.index.freq)).all()

print(SerieTiempou.index.max())

"""**Ajuste del conjunto de entrenamiento y validación**"""

# Split data into train-test
# ==============================================================================
steps = 12
data_trainu = SerieTiempou[:-steps]
data_testu  = SerieTiempou[-steps:]

print(f"Train dates : {data_trainu.index.min()} --- {data_trainu.index.max()}  (n={len(data_trainu)})")
print(f"Test dates  : {data_testu.index.min()} --- {data_testu.index.max()}  (n={len(data_testu)})")

fig, ax=plt.subplots(figsize=(9, 4))
data_trainu['DLPIB'].plot(ax=ax, label='train')
data_testu['DLPIB'].plot(ax=ax, label='test')
ax.legend();

"""**Entrenamiento**

"""

# Create and train forecaster
# ==============================================================================
forecasteru = ForecasterAutoreg(
                regressor = RandomForestRegressor(random_state=42),
                lags = 4
                )

forecasteru.fit(y=data_trainu['DLPIB'])
forecasteru

# Predictions
# ==============================================================================
steps = 12
predictionsu = forecasteru.predict(steps=steps)
predictionsu.head(15)

# Plot
# ==============================================================================
fig, ax = plt.subplots(figsize=(9, 4))
data_trainu['DLPIB'].plot(ax=ax, label='train')
data_testu['DLPIB'].plot(ax=ax, label='test')
predictionsu.plot(ax=ax, label='predictions')
ax.legend();

"""**Medidas de bondad de ajuste**"""

# Test error
# ==============================================================================
error_mseu = mean_squared_error(
                y_true = data_testu['DLPIB'],
                y_pred = predictionsu
            )

print(f"Test error (mse): {error_mseu}")

from sklearn.metrics import mean_squared_error
from math import sqrt

rmsu = sqrt(mean_squared_error(y_true=data_testu['DLPIB'], y_pred= predictionsu))
print(f"root mean squared error (rms): {rmsu}")

from sklearn.metrics import mean_absolute_error

maeu = mean_absolute_error(y_true=data_testu['DLPIB'], y_pred= predictionsu)
print(f"mean absolute error (MAE): {maeu}")

"""**Ajuste de hiperparámetros**"""

# Hyperparameter Grid search
# ==============================================================================
steps = 12
forecasteruh = ForecasterAutoreg(
                regressor = RandomForestRegressor(random_state=42),
                lags      = 6 # This value will be replaced in the grid search
             )

# Lags used as predictors
lags_griduh = [5, 10]

# Regressor's hyperparameters
param_grid = {'n_estimators': [100, 500, 1000],
              'max_depth': [1,3,7,11,17,19]}

results_griduh = grid_search_forecaster(
                        forecaster         = forecasteruh,
                        y                  = data_trainu['DLPIB'],
                        param_grid         = param_grid,
                        lags_grid          = lags_griduh,
                        steps              = steps,
                        refit              = True,
                        metric             = 'mean_squared_error',
                        initial_train_size = int(len(data_trainu)*0.5),
                        fixed_train_size   = False,
                        return_best        = True,
                        verbose            = False
               )

results_griduh

"""**Predicción con hiperparámetros**"""

# Create and train forecaster with the best hyperparameters
# ==============================================================================
regressoruh = RandomForestRegressor(max_depth=7, n_estimators=100, random_state=44)
forecasteruh = ForecasterAutoreg(
                regressor = regressoruh,
                lags      = 10
             )

forecasteruh.fit(y=data_trainu['DLPIB'])

# Predictions
# ==============================================================================
predictionsuh = forecasteruh.predict(steps=steps)

# Plot
# ==============================================================================
fig, ax = plt.subplots(figsize=(9, 4))
data_trainu['DLPIB'].plot(ax=ax, label='train')
data_testu['DLPIB'].plot(ax=ax, label='test')
predictionsuh.plot(ax=ax, label='predictions')
ax.legend();

# Test error
# ==============================================================================
error_mseuh = mean_squared_error(
                y_true = data_testu['DLPIB'],
                y_pred = predictionsuh
                )

print(f"Test error (mse): {error_mseuh}")

from sklearn.metrics import mean_squared_error
from math import sqrt

rmsuh = sqrt(mean_squared_error(y_true=data_testu['DLPIB'], y_pred= predictionsuh))
print(f"root mean squared error (rms): {rmsuh}")

from sklearn.metrics import mean_absolute_error

maeuh = mean_absolute_error(y_true=data_testu['DLPIB'], y_pred= predictionsuh)
print(f"mean absolute error (rms): {maeuh}")

"""**Volviendo a la serie original**"""

ori_predu = np.r_[data_trainu['LPIB'][-1], predictionsuh].cumsum()
exp_ori_predu = np.exp(ori_predu)
data_testu['predfecha']=exp_ori_predu[:-1] 
print(data_testu['predfecha'])

fig, ax = plt.subplots(figsize=(9, 4))
data_trainu['PIB'].plot(ax=ax, label='train')
data_testu['PIB'].plot(ax=ax, label='test')
data_testu['predfecha'].plot(ax=ax, label='exp_ori_pred')
ax.legend();

"""##Random Forest Multivariado

**Preprocesamiento de los datos**
"""

#SerieTiempo.head()
dfm = pd.read_excel("data_col.xlsx")
dfm.rename(columns = {"GDP, real, LCU":"PIB"}, inplace = True)
dfm = dfm.dropna()
dfm

dfm['date']=pd.to_datetime(dfm['year'].astype(str) + 'Q' + dfm['quarter'].astype(str))
dfm

SerieTiempom = dfm.set_index('date')
SerieTiempom = SerieTiempom.sort_index()
SerieTiempom.head()

x = dfm[['Consumer price index','Consumption, government, real, LCU',	'Consumption, private, real, LCU',	'Current account of balance of payments, LCU',	'Employment, total (miles)',	'Exchange rate, period average, per Euro',	'Exchange rate, period average',	'Exports, goods & services, real, LCU',	'Foreign direct investment, US$',	'Government balance, share of GDP',	'Gross government debt (as a % of GDP)',	'Imports, goods & services, real, LCU',	'Interest rate, 10-year government bond yields',	'Investment, total fixed investment, real, LCU',	'Reserves, foreign exchange, US$', 'Unemployment rate']]
x

y=dfm[["PIB"]]
y

fig, ax = plt.subplots(figsize=(9, 4))
dfm["PIB"].plot(ax=ax, label="GDP, real, LCU")
x.plot(ax=ax, label='exogenous variable')
ax.legend();

"""##Normalización Multivariado"""

adf1= adfuller(SerieTiempom["PIB"], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es mayor a 0.5 por lo tanto no es estacionario

SerieTiempom ["LPIB"] = np.log(SerieTiempom ["PIB"])
SerieTiempom ["DLPIB"] = SerieTiempom ["LPIB"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Consumer price index'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es mayor a 0.5 por lo tanto no es estacionario

SerieTiempom['LIPC'] = np.log(SerieTiempom['Consumer price index'])
SerieTiempom["DLIPC"] = SerieTiempom["LIPC"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Consumption, government, real, LCU'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es menor a 0.5 por lo tanto es estacionario, solo se aplica log

SerieTiempom['LCG'] = np.log(SerieTiempom['Consumption, government, real, LCU'])
SerieTiempom["DLCG"] = SerieTiempom["LCG"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Consumption, private, real, LCU'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es mayor a 0.5 por lo tanto no es estacionario

SerieTiempom['LCP'] = np.log(SerieTiempom['Consumption, private, real, LCU'])
SerieTiempom["DLCP"] = SerieTiempom["LCP"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Current account of balance of payments, LCU'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es menor a 0.5 por lo tanto es estacionario sacamos log

SerieTiempom['LCCTE'] = np.log((SerieTiempom['Current account of balance of payments, LCU']*(-1)))
SerieTiempom["DLCCTE"] = SerieTiempom["LCCTE"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Employment, total (miles)'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es mayor a 0.5 por lo tanto no es estacionario

SerieTiempom['LEMP'] = np.log(SerieTiempom['Employment, total (miles)'])
SerieTiempom["DLEMP"] = SerieTiempom["LEMP"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Exchange rate, period average, per Euro'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es mayor a 0.5 por lo tanto no es estacionario

SerieTiempom['LTRMEUR'] = np.log(SerieTiempom['Exchange rate, period average, per Euro'])
SerieTiempom["DLTRMEUR"] = SerieTiempom["LTRMEUR"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Exchange rate, period average'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es mayor a 0.5 por lo tanto no es estacionario

SerieTiempom['LTRM'] = np.log(SerieTiempom['Exchange rate, period average'])
SerieTiempom["DLTRM"] = SerieTiempom["LTRM"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Exports, goods & services, real, LCU'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es menor a 0.5 por lo tanto  es estacionario, sacamos log

SerieTiempom['LX'] = np.log(SerieTiempom['Exports, goods & services, real, LCU'])
SerieTiempom["DLX"] = SerieTiempom["LX"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Foreign direct investment, US$'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es menor a 0.5 por lo tanto no es estacionario, sacamos log

SerieTiempom['LIED'] = np.log(SerieTiempom['Foreign direct investment, US$'])
SerieTiempom["DLIED"] = SerieTiempom["LIED"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Government balance, share of GDP'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es menor a 0.5 por lo tanto es estacionario

SerieTiempom['LDGO'] = np.log(SerieTiempom['Government balance, share of GDP'])
SerieTiempom["DLDGO"] = SerieTiempom["LDGO"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Gross government debt (as a % of GDP)'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es mayor a 0.5 por lo tanto no es estacionario

SerieTiempom['LDFGOB'] = np.log(SerieTiempom['Gross government debt (as a % of GDP)'])
SerieTiempom["DLDFGOB"] = SerieTiempom["LDFGOB"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Imports, goods & services, real, LCU'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es menor a 0.5 por lo tanto  es estacionario sacamos log

SerieTiempom['LM'] = np.log(SerieTiempom['Imports, goods & services, real, LCU'])
SerieTiempom["DLM"] = SerieTiempom["LM"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Interest rate, 10-year government bond yields'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es menor a 0.5 por lo tanto  es estacionario

SerieTiempom['LINT'] = np.log(SerieTiempom['Interest rate, 10-year government bond yields'])
SerieTiempom["DLINT"] = SerieTiempom["LINT"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Investment, total fixed investment, real, LCU'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es menor a 0.5 por lo tanto  es estacionario sacamos log

SerieTiempom['LI'] = np.log(SerieTiempom['Investment, total fixed investment, real, LCU'])
SerieTiempom["DLI"] = SerieTiempom["LI"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Reserves, foreign exchange, US$'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es mayor a 0.5 por lo tanto no es estacionario

SerieTiempom['LRE'] = np.log(SerieTiempom['Reserves, foreign exchange, US$'])
SerieTiempom["DLRE"] = SerieTiempom["LRE"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

adf1= adfuller(SerieTiempom['Unemployment rate'], maxlag=1)
print("el t-test es:",adf1[0])
print("el p-value es:", adf1[1])
print("valores criticos:", adf1[4])
#p-value es menor a 0.5 por lo tanto  es estacionario

SerieTiempom['LUN'] = np.log(SerieTiempom['Unemployment rate'])
SerieTiempom["DLUN"] = SerieTiempom["LUN"].diff()
SerieTiempom = SerieTiempom.drop(SerieTiempom.index[0])
SerieTiempom.head()

"""##Ajuste del conjunto de entrenamiento y validación"""

x1 = SerieTiempom[['DLIPC','DLCG',	'DLCP',	'DLCCTE',	'DLEMP',	'DLTRMEUR',	'DLTRM',	'DLX',	'DLIED',	'DLDFGOB', 'DLM',	'DLINT',	'DLI',	'DLRE', 'DLUN']]
len(x1)
x1

y1=SerieTiempom[["DLPIB"]]
len(y1)

print(f'Number of rows with missing values: {x1.isnull().any(axis=1).mean()}')

print(f'Number of rows with missing values: {y1.isnull().any(axis=1).mean()}')

# Split data into train-test
# ==============================================================================
steps = 12
data_trainm= SerieTiempom[:-steps]
data_testm = SerieTiempom[-steps:]

print(f"Train dates : {data_trainm.index.min()} --- {data_trainm.index.max()}  (n={len(data_trainm)})")
print(f"Test dates  : {data_testm.index.min()} --- {data_testm.index.max()}  (n={len(data_testm)})")

"""**Entrenamiento**"""

# Create and train forecaster
# ==============================================================================
forecasterm = ForecasterAutoreg(
                regressor = RandomForestRegressor(random_state=42),
                lags      = 5
             )

forecasterm.fit(
    y   = data_trainm['DLPIB'].asfreq('QS'), 
    exog = data_trainm [['DLIPC','DLCG',	'DLCP',	'DLCCTE',	'DLEMP',	'DLTRMEUR',	'DLTRM',	'DLX',	'DLIED',	'DLDFGOB', 'DLM',	'DLINT',	'DLI',	'DLRE', 'DLUN']].asfreq('QS')
    )
forecasterm

# Predictions
# ==============================================================================
predictionsm = forecasterm.predict(steps=steps, 
                                 exog=data_testm[['DLIPC','DLCG',	'DLCP',	'DLCCTE',	'DLEMP',	'DLTRMEUR',	'DLTRM',	'DLX',	'DLIED',	'DLDFGOB', 'DLM',	'DLINT',	'DLI',	'DLRE', 'DLUN']].asfreq('QS'))

# Plot
# ==============================================================================
fig, ax=plt.subplots(figsize=(9, 4))
data_trainm['DLPIB'].plot(ax=ax, label='train')
data_testm['DLPIB'].plot(ax=ax, label='test')
predictionsm.plot(ax=ax, label='predictions')
ax.legend();

"""**Medidas de bondad de ajuste**"""

# Test error
# ==============================================================================
error_msem = mean_squared_error(
                y_true = data_testm['DLPIB'],
                y_pred = predictionsm
            )

print(f"Test error (mse): {error_msem}")

from sklearn.metrics import mean_squared_error
from math import sqrt

rmsm = sqrt(mean_squared_error(y_true=data_testm['DLPIB'], y_pred= predictionsm))
print(f"root mean squared error (rms): {rmsm}")

from sklearn.metrics import mean_absolute_error

maem = mean_absolute_error(y_true=data_testm['DLPIB'], y_pred= predictionsm)
print(f"mean absolute error (mae): {maem}")

"""**Regresar a las variables originales**"""

ori_predm = np.r_[data_trainm['LPIB'][-1], predictionsm].cumsum()
exp_ori_predm = np.exp(ori_predm)
data_testm['predfecha']=exp_ori_predm[:-1] 
print(data_testm['predfecha'])

fig, ax = plt.subplots(figsize=(9, 4))
data_trainm['PIB'].plot(ax=ax, label='train')
data_testm['PIB'].plot(ax=ax, label='test')
data_testm['predfecha'].plot(ax=ax, label='exp_ori_pred')
ax.legend();

"""**Ajuste de hiperparámetros**"""

# Hyperparameter Grid search
# ==============================================================================
steps = 12
forecastermh = ForecasterAutoreg(
                regressor = RandomForestRegressor(random_state=42),
                lags      = 6 # This value will be replaced in the grid search
             )

# Lags used as predictors
lags_gridmh = [5, 10]

# Regressor's hyperparameters
param_grid = {'n_estimators': [100, 500, 1000],
              'max_depth': [1,3,7,11,17,19]}

results_gridmh = grid_search_forecaster(
                        forecaster         = forecastermh,
                        y                  = data_trainu['DLPIB'],
                        param_grid         = param_grid,
                        lags_grid          = lags_gridmh,
                        steps              = steps,
                        refit              = True,
                        metric             = 'mean_squared_error',
                        initial_train_size = int(len(data_trainu)*0.5),
                        fixed_train_size   = False,
                        return_best        = True,
                        verbose            = False
               )

results_gridmh

"""**Predicción con hiperparámetros**"""

# Create and train forecaster with the best hyperparameters
# ==============================================================================
regressormh = RandomForestRegressor(max_depth=7, n_estimators=100, random_state=44)
forecastermh = ForecasterAutoreg(
                regressor = regressormh,
                lags      = 10
             )

forecastermh.fit(y=data_trainm['DLPIB'].asfreq('QS'))

# Predictions
# ==============================================================================
predictionsmh = forecastermh.predict(steps=steps)

# Plot
# ==============================================================================
fig, ax = plt.subplots(figsize=(9, 4))
data_trainm['DLPIB'].plot(ax=ax, label='train')
data_testm['DLPIB'].plot(ax=ax, label='test')
predictionsm.plot(ax=ax, label='predictions')
ax.legend();

# Test error
# ==============================================================================
error_msemh = mean_squared_error(
                y_true = data_testm['DLPIB'],
                y_pred = predictionsmh
                )

print(f"Test error (mse): {error_msemh}")

from sklearn.metrics import mean_squared_error
from math import sqrt

rmsmh = sqrt(mean_squared_error(y_true=data_testm['DLPIB'], y_pred= predictionsmh))
print(f"root mean squared error (rms): {rmsmh}")

from sklearn.metrics import mean_absolute_error

maemh = mean_absolute_error(y_true=data_testm['DLPIB'], y_pred= predictionsmh)
print(f"mean absolute error (maemh): {maemh}")