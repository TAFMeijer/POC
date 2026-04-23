import pandas as pd

# Load Data
budget_path = 'data/Budget data.xlsx'
indicator_path = 'data/PF indicator data.xlsx'
wptm_path = 'data/PF WPTM data.xlsx'

df_b = pd.read_excel(budget_path, usecols=['Source', 'Country', 'ImplementationPeriodName', 'Module Parent Component', 'Module', 'Intervention', 'Total Amount'])
df_i = pd.read_excel(indicator_path, usecols=['Source', 'Country', 'Implementation Period Name', 'Intervention', 'IndicatorType', 'IndicatorCode', 'IndicatorDescription', 'IndicatorCustomName'])
df_w = pd.read_excel(wptm_path, usecols=['Source', 'Country', 'Implementation Period Name', 'Module', 'Intervention', 'KeyActivity'])
df_ms = pd.read_excel('data/Module Short.xlsx')
df_order = pd.read_excel('data/Indicator order.xlsx')
df_g = pd.read_excel('data/Geography.xlsx')
df_c19 = pd.read_excel('data/C19RM mapping.xlsx')

# Filter out Multicountry projects
df_b = df_b[~df_b['Country'].astype(str).str.startswith('Multicountry')]
df_i = df_i[~df_i['Country'].astype(str).str.startswith('Multicountry')]
df_w = df_w[~df_w['Country'].astype(str).str.startswith('Multicountry')]

country_to_region = df_g.set_index('Geography Name')['NewRegioShort'].to_dict()
country_to_shortname = df_g.set_index('Geography Name')['Country short name'].to_dict()
available_regions = sorted([r for r in df_g['NewRegioShort'].dropna().unique() if r])

indicator_order = dict(zip(df_order['Indicator'], df_order['Order']))

# Normalize column names for merging/filtering later
df_b.rename(columns={'ImplementationPeriodName': 'Implementation Period Name'}, inplace=True)
df_w.dropna(subset=['Module'], inplace=True)
df_i['IndicatorType'] = df_i['IndicatorType'].replace('Coverage / Output indicator', 'Coverage indicator')

# Intervention in df_i acts as 'Module' for Coverage / Output
df_i['Module'] = df_i['Intervention']

# Merge GC7 COVID-19 instances into General C19RM everywhere and force parent to RSSH
for df in [df_b, df_i, df_w]:
    df['Module'] = df['Module'].replace('COVID-19', 'General C19RM')
    df.loc[df['Module'] == 'General C19RM', 'Module Parent Component'] = 'RSSH'

# Create mapping dictionary of Module -> Module Parent Component from Budget Data
module_to_parent = df_b.dropna(subset=['Module']).set_index('Module')['Module Parent Component'].to_dict()

module_to_short = dict(zip(df_ms['Module'], df_ms['ModuleShort']))
short_module_to_parent = {module_to_short.get(m, m): p for m, p in module_to_parent.items()}

# Create C19RM Mapping Dictionary
c19_map = dict(zip(
    df_c19['COVID-19 Intervention'].astype(str).str.lower().str.strip(),
    df_c19['GC7 Module'].replace('COVID-19', 'General C19RM')
))

# Function to apply C19RM logic
def apply_c19rm_mapping(df):
    if 'Source' not in df.columns or 'Intervention' not in df.columns:
        return
    c19_mask = df['Source'].astype(str).str.contains('C19RM', case=False, na=False)
    if not c19_mask.any():
        return
    # Temporarily normalize intervention string
    norm_int = df.loc[c19_mask, 'Intervention'].astype(str).str.lower().str.strip()
    mapped_modules = norm_int.map(c19_map).fillna('General C19RM')
    df.loc[c19_mask, 'Module'] = mapped_modules

# Apply mapped C19RM modules before we convert to short aliases
apply_c19rm_mapping(df_b)
apply_c19rm_mapping(df_i)
apply_c19rm_mapping(df_w)

# Rename modules to short versions
df_b['Module'] = df_b['Module'].map(module_to_short).fillna(df_b['Module'])
df_i['Module'] = df_i['Module'].map(module_to_short).fillna(df_i['Module'])
df_w['Module'] = df_w['Module'].map(module_to_short).fillna(df_w['Module'])

# Force df_b (Budget Data) missing/typo component mappings to strictly conform to the global dictionary
df_b['Module Parent Component'] = df_b['Module'].map(short_module_to_parent).fillna(df_b['Module Parent Component'])
# Pre-map WPTM array to its parent component for the new filter
df_w['Module Parent Component'] = df_w['Module'].map(short_module_to_parent)

# Re-enforce C19RM parent components: Program Management -> Program Management, else RSSH
c19_mask_b = df_b['Source'].astype(str).str.contains('C19RM', case=False, na=False)
df_b.loc[c19_mask_b & (~df_b['Module'].astype(str).str.lower().str.strip().isin(['program management'])), 'Module Parent Component'] = 'RSSH'

c19_mask_i = df_i['Source'].astype(str).str.contains('C19RM', case=False, na=False)
df_i.loc[c19_mask_i & (~df_i['Module'].astype(str).str.lower().str.strip().isin(['program management'])), 'Module Parent Component'] = 'RSSH'

c19_mask_w = df_w['Source'].astype(str).str.contains('C19RM', case=False, na=False)
df_w.loc[c19_mask_w & (~df_w['Module'].astype(str).str.lower().str.strip().isin(['program management'])), 'Module Parent Component'] = 'RSSH'

# Component Color Map
COMP_COLORS = {
    'RSSH': '#8B31D8',
    'HIV/AIDS': '#ee0c3d',
    'Tuberculosis': '#2e4df9',
    'Malaria': '#fad90d',
    'Multi-Component': '#8c564b', # brown as default
    'Payment for Results': '#8c564b', # brown
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
            if 'TB/HIV' in val_upper: return 'Tuberculosis'
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

# Rename RSSH specifically since it lacks impact indicators
df_i.loc[impact_outcome_mask & (df_i['Module Parent Component'] == 'RSSH'), 'Module'] = 'RSSH (Outcome)'

# Override with valid mappings from the custom file
if oi_map:
    mapped_modules = df_i.loc[impact_outcome_mask, 'IndicatorCode'].map(oi_map)
    df_i.loc[impact_outcome_mask & mapped_modules.notna(), 'Module'] = mapped_modules

# Identify custom indicators
df_i['IsCustom'] = df_i['IndicatorCustomName'].notna()

# Force "Program management" module to map intrinsically to its own unique Component Category
for df in [df_b, df_i, df_w]:
    pm_mask = df['Module'].astype(str).str.lower().str.strip() == 'program management'
    df.loc[pm_mask, 'Module'] = 'Program management'
    df.loc[pm_mask, 'Module Parent Component'] = 'Program Management'

df_b.loc[df_b['Module'] == 'Payment for results', 'Module Parent Component'] = 'Payment for Results'
df_i.loc[df_i['Module'] == 'Payment for results', 'Module Parent Component'] = 'Payment for Results'
df_w.loc[df_w['Module'] == 'Payment for results', 'Module Parent Component'] = 'Payment for Results'

SHADES = {
    'RSSH': {'light': '#C79CEC', 'medium': '#8B31D8', 'dark': '#481573'},
    'HIV/AIDS': {'light': '#f56d8a', 'medium': '#ee0c3d', 'dark': '#a6082a'},
    'Tuberculosis': {'light': '#8296fb', 'medium': '#2e4df9', 'dark': '#172ab5'},
    'Malaria': {'light': '#fce86e', 'medium': '#fad90d', 'dark': '#b59e09'},
    'Multi-Component': {'light': '#c49c94', 'medium': '#8c564b', 'dark': '#593c31'},
    'Other': {'light': '#c7c7c7', 'medium': '#7f7f7f', 'dark': '#4d4d4d'},
    'Custom': {'light': '#d9d9d9', 'medium': '#969696', 'dark': '#525252'},
    'Program Management': {'light': '#737373', 'medium': '#252525', 'dark': '#000000'},
    'Payment for Results': {'light': '#c49c94', 'medium': '#8c564b', 'dark': '#593c31'},
    'Spacer': {'light': 'rgba(0,0,0,0)', 'medium': 'rgba(0,0,0,0)', 'dark': 'rgba(0,0,0,0)'}
}

TYPE_TO_WEIGHT = {
    'Impact indicator': 'light',
    'Outcome indicator': 'medium',
    'Coverage indicator': 'dark'
}


def filter_data(region=None, country=None, ip=None, component=None, exclude_c19rm=False):
    """Central filter applied identically by chart_builder, excel_exporter, and overview_chart_builder."""
    b = df_b.copy()
    i = df_i.copy()
    w = df_w.copy()

    if exclude_c19rm:
        b = b[~b['Source'].astype(str).str.contains('C19RM', case=False, na=False)]
        i = i[~i['Source'].astype(str).str.contains('C19RM', case=False, na=False)]
        w = w[~w['Source'].astype(str).str.contains('C19RM', case=False, na=False)]

    if country and country != 'ALL':
        b = b[b['Country'] == country]
        i = i[i['Country'] == country]
        w = w[w['Country'] == country]
    elif region and region != 'ALL':
        b = b[b['Country'].map(country_to_region) == region]
        i = i[i['Country'].map(country_to_region) == region]
        w = w[w['Country'].map(country_to_region) == region]

    if ip and ip != 'ALL':
        b = b[b['Implementation Period Name'] == ip]
        i = i[i['Implementation Period Name'] == ip]
        w = w[w['Implementation Period Name'] == ip]

    if component and component != 'ALL':
        b = b[b['Module Parent Component'] == component]
        i = i[i['Module Parent Component'] == component]
        w = w[w['Module Parent Component'] == component]

    return b, i, w


def reassign_tb_hiv(b_filt, i_filt, countries=None):
    """Reassign TB/HIV I-1 indicator to the disease component with the larger budget."""
    mask = i_filt['IndicatorCode'] == 'TB/HIV I-1'
    if not mask.any():
        return i_filt
    i_filt = i_filt.copy()
    target = countries if countries is not None else i_filt.loc[mask, 'Country'].unique()
    for c in target:
        c_mask = mask & (i_filt['Country'] == c)
        if not c_mask.any():
            continue
        hiv = b_filt[(b_filt['Country'] == c) & (b_filt['Module Parent Component'] == 'HIV/AIDS')]['Total Amount'].sum()
        tb = b_filt[(b_filt['Country'] == c) & (b_filt['Module Parent Component'] == 'Tuberculosis')]['Total Amount'].sum()
        winner = 'HIV/AIDS' if hiv > tb else 'Tuberculosis'
        i_filt.loc[c_mask, 'Module Parent Component'] = winner
    return i_filt

