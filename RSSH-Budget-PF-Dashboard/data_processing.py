import pandas as pd
import numpy as np

print("Loading data...")

# Load Data
budget_path = 'data/Budget data.xlsx'
indicator_path = 'data/PF indicator data.xlsx'
wptm_path = 'data/PF WPTM data.xlsx'

df_b = pd.read_excel(budget_path, usecols=['Country', 'ImplementationPeriodName', 'Module Parent Component', 'Module', 'Intervention', 'Total Amount'])
df_i = pd.read_excel(indicator_path, usecols=['Country', 'Implementation Period Name', 'Intervention', 'IndicatorType', 'IndicatorCode', 'IndicatorDescription', 'IndicatorCustomName'])
df_w = pd.read_excel(wptm_path, usecols=['Country', 'Implementation Period Name', 'Module', 'KeyActivity'])
df_ms = pd.read_excel('data/Module Short.xlsx')
df_order = pd.read_excel('data/Indicator order.xlsx')

indicator_order = dict(zip(df_order['Indicator'], df_order['Order']))

# Normalize column names for merging/filtering later
df_b.rename(columns={'ImplementationPeriodName': 'Implementation Period Name'}, inplace=True)
df_w.dropna(subset=['Module'], inplace=True)
df_i['IndicatorType'] = df_i['IndicatorType'].replace('Coverage / Output indicator', 'Coverage indicator')

# Intervention in df_i acts as 'Module' for Coverage / Output
df_i['Module'] = df_i['Intervention']

# Create mapping dictionary of Module -> Module Parent Component from Budget Data
module_to_parent = df_b.dropna(subset=['Module']).set_index('Module')['Module Parent Component'].to_dict()

module_to_short = dict(zip(df_ms['Module'], df_ms['ModuleShort']))
short_module_to_parent = {module_to_short.get(m, m): p for m, p in module_to_parent.items()}

# Rename modules to short versions
df_b['Module'] = df_b['Module'].map(module_to_short).fillna(df_b['Module'])
df_i['Module'] = df_i['Module'].map(module_to_short).fillna(df_i['Module'])
df_w['Module'] = df_w['Module'].map(module_to_short).fillna(df_w['Module'])

# Pre-map WPTM array to its parent component for the new filter
df_w['Module Parent Component'] = df_w['Module'].map(short_module_to_parent)

# Component Color Map
COMP_COLORS = {
    'RSSH': '#44cc36',
    'HIV/AIDS': '#ee0c3d',
    'Tuberculosis': '#2e4df9',
    'Malaria': '#fad90d',
    'Multi-Component': '#8c564b', # brown as default
    'Program Management': '#000000', # black
    'Spacer': 'rgba(0,0,0,0)',
    'Other': '#7f7f7f'
}

def map_parent_component(row):
    # For Impact / Outcome indicators, map based on IndicatorCode / CustomName
    if row['IndicatorType'] in ['Impact indicator', 'Outcome indicator']:
        val = row['IndicatorCode'] if pd.notna(row['IndicatorCode']) else row['IndicatorCustomName']
        if pd.notna(val):
            val_upper = str(val).upper()
            if 'HIV' in val_upper and 'TB' in val_upper: return 'Multi-Component'
            if 'HIV' in val_upper: return 'HIV/AIDS'
            if 'TB' in val_upper or 'TUBERCULOSIS' in val_upper: return 'Tuberculosis'
            if 'MAL' in val_upper: return 'Malaria'
            if 'RSSH' in val_upper or 'HSS' in val_upper: return 'RSSH'
        return 'Other'
    else:
        # Coverage / Output indicators use the module mapping
        mod = row['Module']
        return short_module_to_parent.get(mod, 'Other')

df_i['Module Parent Component'] = df_i.apply(map_parent_component, axis=1)

# Load the Outcome and Impact mapping overrides
try:
    df_oi_map = pd.read_excel('data/PF outcome and impact mapping.xlsx', sheet_name='mapping')
    df_oi_map = df_oi_map[df_oi_map['Module'].notna()]
    df_oi_map = df_oi_map[~df_oi_map['Module'].astype(str).str.upper().isin(['N/A', 'NAN', ''])]
    oi_map = df_oi_map.set_index('IndicatorCode')['Module'].to_dict()
except Exception:
    oi_map = {}

# Apply the default pseudo-module to all Impact/Outcome indicators
impact_outcome_mask = df_i['IndicatorType'].isin(['Impact indicator', 'Outcome indicator'])
df_i.loc[impact_outcome_mask, 'Module'] = df_i.loc[impact_outcome_mask, 'Module Parent Component'] + " (Impact/Outcome)"

# Override with valid mappings from the custom file
if oi_map:
    mapped_modules = df_i.loc[impact_outcome_mask, 'IndicatorCode'].map(oi_map)
    df_i.loc[impact_outcome_mask & mapped_modules.notna(), 'Module'] = mapped_modules

# Identify custom indicators
df_i['IsCustom'] = df_i['IndicatorCustomName'].notna()

# Force "Program management" module to map intrinsically to its own unique Component Category
df_b.loc[df_b['Module'] == 'Program management', 'Module Parent Component'] = 'Program Management'
df_i.loc[df_i['Module'] == 'Program management', 'Module Parent Component'] = 'Program Management'
df_w.loc[df_w['Module'] == 'Program management', 'Module Parent Component'] = 'Program Management'

SHADES = {
    'RSSH': {'light': '#8ee085', 'medium': '#44cc36', 'dark': '#2c8a22'},
    'HIV/AIDS': {'light': '#f56d8a', 'medium': '#ee0c3d', 'dark': '#a6082a'},
    'Tuberculosis': {'light': '#8296fb', 'medium': '#2e4df9', 'dark': '#172ab5'},
    'Malaria': {'light': '#fce86e', 'medium': '#fad90d', 'dark': '#b59e09'},
    'Multi-Component': {'light': '#c49c94', 'medium': '#8c564b', 'dark': '#593c31'},
    'Other': {'light': '#c7c7c7', 'medium': '#7f7f7f', 'dark': '#4d4d4d'},
    'Custom': {'light': '#d9d9d9', 'medium': '#969696', 'dark': '#525252'},
    'Program Management': {'light': '#737373', 'medium': '#252525', 'dark': '#000000'},
    'Spacer': {'light': 'rgba(0,0,0,0)', 'medium': 'rgba(0,0,0,0)', 'dark': 'rgba(0,0,0,0)'}
}

TYPE_TO_WEIGHT = {
    'Impact indicator': 'light',
    'Outcome indicator': 'medium',
    'Coverage indicator': 'dark'
}
