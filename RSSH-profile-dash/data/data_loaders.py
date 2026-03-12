import pandas as pd
import numpy as np

# Cache for frequently accessed files
_CACHE = {}

def get_geography_data():
    try:
        if 'geography' not in _CACHE:
            _CACHE['geography'] = pd.read_excel('data/Geography.xlsx')
        return _CACHE['geography']
    except Exception as e:
        print(f"Error loading Geography.xlsx: {e}")
        return pd.DataFrame()

def get_equity_data(iso3, filepath):
    try:
        if filepath not in _CACHE:
            _CACHE[filepath] = pd.read_excel(filepath, sheet_name='WIQ')
        df = _CACHE[filepath]
        country_data = df[df['iso'] == iso3]
        if not country_data.empty:
            res = country_data.iloc[0].to_dict()
            return {
                'Q1': res.get('Q1', 0),
                'Q5': res.get('Q5', 0),
                'year': res.get('year', ''),
                'source': res.get('source', '')
            }
        return None
    except Exception as e:
        print(f"Error loading equity data from {filepath}: {e}")
        return None

def get_dtp3_equity_data(iso3="NGA"):
    return get_equity_data(iso3, 'data/DPT3_coverage_equity(2030).xlsx')

def get_anc4_equity_data(iso3="NGA"):
    return get_equity_data(iso3, 'data/ANC4_coverage_equity(2030).xlsx')

def get_precalculated_stats(iso3, indicator_name):
    try:
        if 'wbig' not in _CACHE:
            _CACHE['wbig'] = pd.read_excel('data/world-bank-income-groups.xlsx')
        if 'peer_stats' not in _CACHE:
            _CACHE['peer_stats'] = pd.read_csv('data/peer_stats_summary.csv')
            
        df_wbig = _CACHE['wbig']
        df_stats = _CACHE['peer_stats']
    except Exception as e:
        print(f"Error loading precalculated data: {e}")
        return pd.DataFrame()

    if df_wbig.empty or df_stats.empty:
        return pd.DataFrame()

    # Find the income groups for this specific country across all available years
    country_wbig = df_wbig[df_wbig["Code"] == iso3][['Year', "World Bank's income classification"]]
    country_wbig.rename(columns={"World Bank's income classification": 'Income Group'}, inplace=True)
    
    if country_wbig.empty:
        return pd.DataFrame()

    # Filter stats for exactly this indicator
    stats_indicator = df_stats[df_stats['Indicator Name'] == indicator_name]
    
    # Merge the country's annual income bracket against the matching bracket distributions
    peer_stats = pd.merge(country_wbig, stats_indicator, on=['Year', 'Income Group'], how='inner')
    
    # Restrict and map output to the structure expected by the charting generic helper
    if not peer_stats.empty:
        return peer_stats[['Year', 'Median', 'Lower Bound', 'Upper Bound', 'Count']].rename(
            columns={'Lower Bound': 'Lower', 'Upper Bound': 'Upper'}
        )
    return pd.DataFrame()

def get_dtp3_data(iso3="NGA"):
    try:
        if 'dpt1_cov' not in _CACHE:
            _CACHE['dpt1_cov'] = pd.read_excel('data/DPT1_WUENIC.xlsx')
        df_dpt = _CACHE['dpt1_cov']
        
        # We will keep requesting the old precalculated stats unless a new DPT1 peer_stats was provided
        peer_stats = get_precalculated_stats(iso3, 'DTP3 Coverage')
        
        df_country = df_dpt[df_dpt['CODE'] == iso3][['YEAR', 'DPT1']]
        df_country.rename(columns={'DPT1': 'Country'}, inplace=True)
        
        min_year = 2000
        max_year = int(df_dpt['YEAR'].max()) if not df_dpt['YEAR'].isna().all() else 2021
        years_df = pd.DataFrame({'YEAR': range(min_year, max_year + 1)})
        
        if not peer_stats.empty:
            peer_stats.rename(columns={'Year': 'YEAR'}, inplace=True)
            result = pd.merge(years_df, peer_stats, on='YEAR', how='left')
        else:
            result = years_df.copy()
            result['Median'] = np.nan
            result['Lower'] = np.nan
            result['Upper'] = np.nan
            result['Count'] = np.nan
            
        result = pd.merge(result, df_country, on='YEAR', how='left')
        result.rename(columns={'YEAR': 'Year'}, inplace=True)
        result.replace({np.nan: None}, inplace=True)
        return result
        
    except Exception as e:
        print(f"Error processing real DPT3 data: {e}.")
        return pd.DataFrame()
        
def get_country_income_group(iso3):
    try:
        if 'wbig' not in _CACHE:
            _CACHE['wbig'] = pd.read_excel('data/world-bank-income-groups.xlsx')
        df_wbig = _CACHE['wbig']
        
        iso3_data = df_wbig[df_wbig['Code'] == iso3]
        if iso3_data.empty: return "Unknown"
        
        latest_year = iso3_data['Year'].max()
        income_group = iso3_data[iso3_data['Year'] == latest_year]["World Bank's income classification"].iloc[0]
        return income_group
    except Exception as e:
        print(f"Error fetching income group: {e}")
        return "Unknown"

def get_peer_count_range(iso3):
    income_group = get_country_income_group(iso3)
    if income_group == "Unknown":
        return (0, 0)
        
    try:
        if 'peer_stats' not in _CACHE:
            _CACHE['peer_stats'] = pd.read_csv('data/peer_stats_summary.csv')
        df_stats = _CACHE['peer_stats']
        
        # Filter stats to only this income group
        group_stats = df_stats[df_stats['Income Group'] == income_group]
        if group_stats.empty:
            return (0, 0)
            
        # Get min and max counts across all indicators
        min_peers = int(group_stats['Count'].min())
        max_peers = int(group_stats['Count'].max())
        return (min_peers, max_peers)
    except Exception as e:
        print(f"Error calculating peer count: {e}")
        return (0, 0)

def get_generic_peer_lines(iso3, filepath, identifier_col='ISO3', year_col='Year'):
    try:
        if 'wbig' not in _CACHE:
            _CACHE['wbig'] = pd.read_excel('data/world-bank-income-groups.xlsx')
        df_wbig = _CACHE['wbig']
        
        iso3_data = df_wbig[df_wbig['Code'] == iso3]
        if iso3_data.empty: return pd.DataFrame()
        
        latest_year = iso3_data['Year'].max()
        income_group = iso3_data[iso3_data['Year'] == latest_year]["World Bank's income classification"].iloc[0]
        
        peer_codes = df_wbig[(df_wbig['Year'] == latest_year) & (df_wbig["World Bank's income classification"] == income_group)]['Code'].unique()
        
        df_target = pd.read_excel(filepath)
        # Use copy to avoid SettingWithCopyWarning
        peer_df = df_target[df_target[identifier_col].isin(peer_codes)].copy()
        if year_col != 'Year':
            peer_df.rename(columns={year_col: 'Year'}, inplace=True)
        if identifier_col != 'ISO3':
            peer_df.rename(columns={identifier_col: 'ISO3'}, inplace=True)
            
        return peer_df
    except Exception as e:
        print(f"Error fetching peer lines from {filepath}: {e}")
        return pd.DataFrame()

def get_dtp3_peer_lines(iso3="NGA"):
    return get_generic_peer_lines(iso3, 'data/DPT3_coverage.xlsx', 'CODE', 'YEAR')

def get_anc4_peer_lines(iso3="NGA"):
    return get_generic_peer_lines(iso3, 'data/ANC4_coverage.xlsx', 'CODE', 'YEAR')

def get_anc4_data(iso3="NGA"):
    try:
        if 'anc4_cov' not in _CACHE:
            _CACHE['anc4_cov'] = pd.read_excel('data/ANC4_coverage.xlsx')
        df_anc = _CACHE['anc4_cov']
        
        peer_stats = get_precalculated_stats(iso3, 'ANC4 Coverage')
        
        df_country = df_anc[df_anc['CODE'] == iso3][['YEAR', 'COVERAGE']]
        df_country.rename(columns={'COVERAGE': 'Country'}, inplace=True)
        
        min_year = 2000
        max_year = int(df_anc['YEAR'].max()) if not df_anc['YEAR'].isna().all() else 2021
        years_df = pd.DataFrame({'YEAR': range(min_year, max_year + 1)})
        
        if not peer_stats.empty:
            peer_stats.rename(columns={'Year': 'YEAR'}, inplace=True)
            result = pd.merge(years_df, peer_stats, on='YEAR', how='left')
        else:
            result = years_df.copy()
            result['Median'] = np.nan
            result['Lower'] = np.nan
            result['Upper'] = np.nan
            result['Count'] = np.nan
            
        result = pd.merge(result, df_country, on='YEAR', how='left')
        result.rename(columns={'YEAR': 'Year'}, inplace=True)
        result.replace({np.nan: None}, inplace=True)
        return result
        
    except Exception as e:
        print(f"Error processing ANC4: {e}")
        return pd.DataFrame()

def _generic_excel_loader(iso3, filepath, val_col, year_col='Year', str_indicator=''):
    try:
        if filepath not in _CACHE:
            _CACHE[filepath] = pd.read_excel(filepath)
        df_target = _CACHE[filepath]
        
        peer_stats = get_precalculated_stats(iso3, str_indicator)
        
        df_country = df_target[df_target['ISO3'] == iso3][[year_col, val_col]]
        df_country.rename(columns={val_col: 'Country'}, inplace=True)
        
        min_year = 2000
        max_year = int(df_target[year_col].max()) if not df_target[year_col].isna().all() else 2021
        years_df = pd.DataFrame({year_col: range(min_year, max_year + 1)})
        
        if not peer_stats.empty:
            peer_stats.rename(columns={'Year': year_col}, inplace=True)
            result = pd.merge(years_df, peer_stats, on=year_col, how='left')
        else:
            result = years_df.copy()
            result['Median'] = np.nan
            result['Lower'] = np.nan
            result['Upper'] = np.nan
            result['Count'] = np.nan
            
        result = pd.merge(result, df_country, on=year_col, how='left')
        result.rename(columns={year_col: 'Year'}, inplace=True)
        return result
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return pd.DataFrame()

def get_uhc_overall_data(iso3="NGA"): return _generic_excel_loader(iso3, 'data/UHC_overall.xlsx', 'UHC', 'Year', 'UHC (Overall)')
def get_uhc_id_data(iso3="NGA"): return _generic_excel_loader(iso3, 'data/UHC_ID.xlsx', 'UHC_ID', 'Year', 'UHC (Infectious Disease)')
def get_uhc_rmnch_data(iso3="NGA"): return _generic_excel_loader(iso3, 'data/UHC_RMNCH.xlsx', 'UHC_RMNCH', 'Year', 'UHC (RMNCH)')

def get_uhc_overall_peer_lines(iso3="NGA"): return get_generic_peer_lines(iso3, 'data/UHC_overall.xlsx')
def get_uhc_id_peer_lines(iso3="NGA"): return get_generic_peer_lines(iso3, 'data/UHC_ID.xlsx')
def get_uhc_rmnch_peer_lines(iso3="NGA"): return get_generic_peer_lines(iso3, 'data/UHC_RMNCH.xlsx')

def get_mmr_peer_lines(iso3="NGA"):
    return get_generic_peer_lines(iso3, 'data/MMR.xlsx', 'ISO3', 'Year of estimate')

def get_mmr_data(iso3="NGA"): return _generic_excel_loader(iso3, 'data/MMR.xlsx', 'MMR', 'Year of estimate')

def get_che_peer_lines(iso3="NGA"):
    try:
        if 'wbig' not in _CACHE:
            _CACHE['wbig'] = pd.read_excel('data/world-bank-income-groups.xlsx')
        df_wbig = _CACHE['wbig']
        
        iso3_data = df_wbig[df_wbig['Code'] == iso3]
        if iso3_data.empty: return pd.DataFrame()
        latest_year = iso3_data['Year'].max()
        income_group = iso3_data[iso3_data['Year'] == latest_year]["World Bank's income classification"].iloc[0]
        peer_codes = df_wbig[(df_wbig['Year'] == latest_year) & (df_wbig["World Bank's income classification"] == income_group)]['Code'].unique()
        
        if 'che' not in _CACHE: _CACHE['che'] = pd.read_excel('data/CHE.xlsx')
        if 'gche-d' not in _CACHE: _CACHE['gche-d'] = pd.read_excel('data/GCHE-D.xlsx')
        che = _CACHE['che']
        gche = _CACHE['gche-d']
        merged = pd.merge(che, gche, on=['ISO3', 'Year'], how='inner')
        merged['GGHE_GDP'] = (merged['CHE'] * merged['GCHE-D']) / 100.0
        
        return merged[merged['ISO3'].isin(peer_codes)]
    except Exception as e:
        print(f"Error fetching CHE peer lines: {e}")
        return pd.DataFrame()

def get_oop_peer_lines(iso3="NGA"):
    try:
        if 'wbig' not in _CACHE:
            _CACHE['wbig'] = pd.read_excel('data/world-bank-income-groups.xlsx')
        df_wbig = _CACHE['wbig']
        
        iso3_data = df_wbig[df_wbig['Code'] == iso3]
        if iso3_data.empty: return pd.DataFrame()
        latest_year = iso3_data['Year'].max()
        income_group = iso3_data[iso3_data['Year'] == latest_year]["World Bank's income classification"].iloc[0]
        peer_codes = df_wbig[(df_wbig['Year'] == latest_year) & (df_wbig["World Bank's income classification"] == income_group)]['Code'].unique()
        
        if 'oop' not in _CACHE:
            _CACHE['oop'] = pd.read_excel('data/OOP.xlsx')
        oop = _CACHE['oop'].copy()
        oop.rename(columns={'OOP as % of GDP': 'OOP_GDP'}, inplace=True)
        oop['OOP_GDP'] = oop['OOP_GDP'] * 100.0
        
        return oop[oop['ISO3'].isin(peer_codes)]
    except Exception as e:
        print(f"Error fetching OOP peer lines: {e}")
        return pd.DataFrame()

def get_che_data(iso3="NGA"):
    try:
        if 'che' not in _CACHE: _CACHE['che'] = pd.read_excel('data/CHE.xlsx')
        if 'gche-d' not in _CACHE: _CACHE['gche-d'] = pd.read_excel('data/GCHE-D.xlsx')
        che = _CACHE['che']
        gche = _CACHE['gche-d']
        
        # Merge them
        merged = pd.merge(che, gche, on=['ISO3', 'Year'], how='inner')
        # GGHE-D in the raw dataset is % of CHE, we need it as % of GDP for the line chart
        merged['GGHE_GDP'] = (merged['CHE'] * merged['GCHE-D']) / 100.0
        
        # Peer stats for CHE
        peer_che = get_precalculated_stats(iso3, 'Current Health Expenditure (CHE)')
        if not peer_che.empty:
            peer_che.rename(columns={'Median': 'CHE_Median', 'Lower': 'CHE_Lower', 'Upper': 'CHE_Upper', 'Count': 'CHE_Count'}, inplace=True)
        
        # Peer stats for GGHE_GDP (we need to pass a slice to standard calculate function)
        peer_gghe = get_precalculated_stats(iso3, 'Domestic General Government Health Exp (GGHE-D)')
        if not peer_gghe.empty:
            peer_gghe.rename(columns={'Median': 'GGHE_Median', 'Lower': 'GGHE_Lower', 'Upper': 'GGHE_Upper', 'Count': 'GGHE_Count'}, inplace=True)
        
        # Country data
        df_country = merged[merged['ISO3'] == iso3][['Year', 'CHE', 'GGHE_GDP']]
        df_country.rename(columns={'CHE': 'CHE_GDP'}, inplace=True)
        
        min_year = 2000
        max_year = int(merged['Year'].max()) if not merged['Year'].isna().all() else 2023
        result = pd.DataFrame({'Year': range(min_year, max_year + 1)})
        
        if not peer_che.empty: result = pd.merge(result, peer_che, on='Year', how='left')
        else:
            result['CHE_Median'] = np.nan
            result['CHE_Lower'] = np.nan
            result['CHE_Upper'] = np.nan
            result['CHE_Count'] = np.nan
            
        if not peer_gghe.empty: result = pd.merge(result, peer_gghe, on='Year', how='left')
        else:
            result['GGHE_Median'] = np.nan
            result['GGHE_Lower'] = np.nan
            result['GGHE_Upper'] = np.nan
            result['GGHE_Count'] = np.nan
            
        result = pd.merge(result, df_country, on='Year', how='left')
        
        return result
    except Exception as e:
        print(f"Error processing CHE data: {e}")
        return pd.DataFrame()

def get_oop_data(iso3="NGA"):
    try:
        if 'oop' not in _CACHE:
            _CACHE['oop'] = pd.read_excel('data/OOP.xlsx')
        oop = _CACHE['oop'].copy()
        oop.rename(columns={'OOP as % of GDP': 'OOP_GDP'}, inplace=True)
        oop['OOP_GDP'] = oop['OOP_GDP'] * 100.0
        
        peer_oop = get_precalculated_stats(iso3, 'Out of pocket (OOPS)')
        if not peer_oop.empty:
            peer_oop.rename(columns={'Median': 'OOP_Median', 'Lower': 'OOP_Lower', 'Upper': 'OOP_Upper', 'Count': 'OOP_Count'}, inplace=True)
            
        df_country = oop[oop['ISO3'] == iso3][['Year', 'OOP_GDP']]
        
        min_year = 2000
        max_year = int(oop['Year'].max()) if not oop['Year'].isna().all() else 2023
        result = pd.DataFrame({'Year': range(min_year, max_year + 1)})
        
        if not peer_oop.empty:
            result = pd.merge(result, peer_oop, on='Year', how='left')
        else:
            result['OOP_Median'] = np.nan
            result['OOP_Lower'] = np.nan
            result['OOP_Upper'] = np.nan
            result['OOP_Count'] = np.nan
            
        result = pd.merge(result, df_country, on='Year', how='left')
        return result
    except Exception as e:
        print(f"Error processing OOP data: {e}")
        return pd.DataFrame()

def get_md_peer_lines(iso3="NGA"): return get_generic_peer_lines(iso3, 'data/MD_per10k.xlsx')
def get_nurse_peer_lines(iso3="NGA"): return get_generic_peer_lines(iso3, 'data/Nurse_per10k.xlsx')
def get_chw_peer_lines(iso3="NGA"): return get_generic_peer_lines(iso3, 'data/CHW_per10k.xlsx')

def get_md_data(iso3="NGA"):
    try:
        if 'md' not in _CACHE:
            _CACHE['md'] = pd.read_excel('data/MD_per10k.xlsx')
        df_md = _CACHE['md']
        
        peer_stats = get_precalculated_stats(iso3, 'Medical Doctors (per 10k)')
        
        df_country = df_md[df_md['ISO3'] == iso3][['Year', 'MD per 10k pop']]
        df_country.rename(columns={'MD per 10k pop': 'Country'}, inplace=True)
        
        min_year = 2000
        max_year = int(df_md['Year'].max()) if not df_md['Year'].isna().all() else 2021
        years_df = pd.DataFrame({'Year': range(min_year, max_year + 1)})
        
        if not peer_stats.empty:
            result = pd.merge(years_df, peer_stats, on='Year', how='left')
        else:
            result = years_df.copy()
            result['Median'] = np.nan
            result['Lower'] = np.nan
            result['Upper'] = np.nan
            result['Count'] = np.nan
            
        result = pd.merge(result, df_country, on='Year', how='left')
        result.replace({np.nan: None}, inplace=True)
        return result
    except Exception as e:
        print(f"Error loading MD data: {e}")
        return pd.DataFrame()

def get_nurse_data(iso3="NGA"):
    try:
        if 'nurse' not in _CACHE:
            _CACHE['nurse'] = pd.read_excel('data/Nurse_per10k.xlsx')
        df_nurse = _CACHE['nurse']
        
        peer_stats = get_precalculated_stats(iso3, 'Nursing and midwifery personnel (per 10k)')
        
        df_country = df_nurse[df_nurse['ISO3'] == iso3][['Year', 'Nurse and midwives per 10k pop']]
        df_country.rename(columns={'Nurse and midwives per 10k pop': 'Country'}, inplace=True)
        
        min_year = 2000
        max_year = int(df_nurse['Year'].max()) if not df_nurse['Year'].isna().all() else 2021
        years_df = pd.DataFrame({'Year': range(min_year, max_year + 1)})
        
        if not peer_stats.empty:
            result = pd.merge(years_df, peer_stats, on='Year', how='left')
        else:
            result = years_df.copy()
            result['Median'] = np.nan
            result['Lower'] = np.nan
            result['Upper'] = np.nan
            result['Count'] = np.nan
            
        result = pd.merge(result, df_country, on='Year', how='left')
        result.replace({np.nan: None}, inplace=True)
        return result
    except Exception as e:
        print(f"Error loading Nurse data: {e}")
        return pd.DataFrame()

def get_chw_data(iso3="NGA"):
    try:
        if 'chw' not in _CACHE:
            _CACHE['chw'] = pd.read_excel('data/CHW_per10k.xlsx')
        df_chw = _CACHE['chw']
        
        peer_stats = get_precalculated_stats(iso3, 'Community Health Workers (per 10k)')
        
        df_country = df_chw[df_chw['ISO3'] == iso3][['Year', 'CHW per 10k pop']]
        df_country.rename(columns={'CHW per 10k pop': 'Country'}, inplace=True)
        
        min_year = 2000
        max_year = int(df_chw['Year'].max()) if not df_chw['Year'].isna().all() else 2021
        years_df = pd.DataFrame({'Year': range(min_year, max_year + 1)})
        
        if not peer_stats.empty:
            result = pd.merge(years_df, peer_stats, on='Year', how='left')
        else:
            result = years_df.copy()
            result['Median'] = np.nan
            result['Lower'] = np.nan
            result['Upper'] = np.nan
            result['Count'] = np.nan
            
        result = pd.merge(result, df_country, on='Year', how='left')
        result.replace({np.nan: None}, inplace=True)
        return result
    except Exception as e:
        print(f"Error loading CHW data: {e}")
        return pd.DataFrame()
