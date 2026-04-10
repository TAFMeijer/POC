import pandas as pd
df_target = pd.read_excel('data/GCHE-D.xlsx')
df_che = pd.read_excel('data/CHE.xlsx')
df_target = pd.merge(df_target, df_che, on=['ISO3', 'Year'], how='inner')
print("Before multiplier:")
print(df_target[['GCHE-D', 'CHE']].head())
df_target['GCHE-D'] = (df_target['GCHE-D'] * df_target['CHE']) / 100.0
print("After multiplier:")
print(df_target[['GCHE-D']].head())
print("Max GCHE-D:", df_target['GCHE-D'].max())
