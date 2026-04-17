import pandas as pd

df = pd.read_excel('data/Budget data.xlsx', usecols=['Country'])
mc = df[df['Country'].astype(str).str.contains('Multi', case=False) | df['Country'].astype(str).str.contains('MC', case=False)]['Country'].unique()
with open('mc_output.txt', 'w') as f:
    for m in mc:
        f.write(m + '\n')
