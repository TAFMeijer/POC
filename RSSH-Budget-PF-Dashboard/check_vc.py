import pandas as pd
from data_processing import df_i, oi_map

vc = df_i[df_i['IndicatorCode'].astype(str).str.contains('VC', na=False, case=False)]
print(vc[['Country', 'IndicatorType', 'IndicatorCode', 'IndicatorCustomName', 'Intervention', 'Module Parent Component', 'Module']].head(10).to_string())

vc2 = df_i[df_i['IndicatorCustomName'].astype(str).str.contains('VC', na=False, case=False)]
print(vc2[['Country', 'IndicatorType', 'IndicatorCode', 'IndicatorCustomName', 'Intervention', 'Module Parent Component', 'Module']].head(10).to_string())
