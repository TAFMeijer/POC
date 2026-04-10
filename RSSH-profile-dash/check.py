import pandas as pd
from scripts.generate_peer_stats import process_dataset
df_wbig = pd.read_excel('data/world-bank-income-groups.xlsx')
df_wbig.rename(columns={"World Bank's income classification": 'IncomeGroup'}, inplace=True)
import scripts.generate_peer_stats as gps
gps.df_wbig = df_wbig

df_che = pd.read_excel('data/CHE.xlsx')
res = gps.process_dataset('data/GCHE-D.xlsx', 'ISO3', 'Year', 'GCHE-D', 'GGHE-D', multiplier_df=df_che, multiplier_col='CHE')
print(res.head())
