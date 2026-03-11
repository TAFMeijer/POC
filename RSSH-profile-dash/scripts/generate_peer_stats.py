import pandas as pd
import numpy as np
import os

def generate_peer_stats():
    try:
        df_wbig = pd.read_excel('data/world-bank-income-groups.xlsx')
        df_wbig.rename(columns={"World Bank's income classification": 'IncomeGroup'}, inplace=True)
    except Exception as e:
        print(f"Error loading wbig: {e}")
        return

    # Helper function to process individual datasets
    def process_dataset(filepath, code_col, year_col, val_col, indicator_name, multiplier_df=None, multiplier_col=None):
        try:
            df_target = pd.read_excel(filepath)
            
            if multiplier_df is not None and multiplier_col is not None:
                # Merge target with multiplier df to scale the main metric
                df_target = pd.merge(df_target, multiplier_df, on=[code_col, year_col], how='inner')
                df_target[val_col] = (df_target[val_col] * df_target[multiplier_col]) / 100.0
            
            # Special cleanup parsing for existing bugs
            if indicator_name == "Nursing and midwifery personnel (per 10k)":
                if val_col in df_target.columns:
                    df_target[val_col] = pd.to_numeric(df_target[val_col].astype(str).str.replace(' ', ''), errors='coerce')
            if indicator_name == 'Maternal Mortality Rate (MMR)':
                return pd.DataFrame()
            if indicator_name == 'Out of pocket (OOPS)':
                if val_col in df_target.columns:
                    df_target[val_col] = df_target[val_col] * 100.0

            df_wbig_renamed = df_wbig.rename(columns={'Code': code_col, 'Year': year_col})
            df_merged = pd.merge(df_target, df_wbig_renamed, on=[code_col, year_col], how='inner')
            
            stats = df_merged.groupby([year_col, 'IncomeGroup'])[val_col].agg(['median', 'std']).reset_index()
            
            # The dashboard expects the 'Count' to reflect the pool of the LATEST classification year
            latest_year = df_wbig_renamed[year_col].max()
            latest_wbig = df_wbig_renamed[df_wbig_renamed[year_col] == latest_year]
            
            merged_latest = pd.merge(df_target, latest_wbig, on=code_col, how='inner')
            income_group_counts = merged_latest.groupby('IncomeGroup')[code_col].nunique().reset_index(name='Count')
            
            stats = pd.merge(stats, income_group_counts, on='IncomeGroup', how='left')
            
            stats['Indicator Name'] = indicator_name
            stats['Income Group'] = stats['IncomeGroup']
            stats['Median'] = stats['median']
            stats['Lower Bound'] = stats['median'] - stats['std'].fillna(5)
            stats['Upper Bound'] = stats['median'] + stats['std'].fillna(5)
            
            # Select and rename final columns requested
            final_df = stats[['Indicator Name', 'Income Group', year_col, 'Median', 'Lower Bound', 'Upper Bound', 'Count']]
            final_df.rename(columns={year_col: 'Year'}, inplace=True)
            return final_df
        except Exception as e:
            print(f"Error processing {indicator_name}: {e}")
            return pd.DataFrame()

    all_stats = []

    # 1. DTP3
    res_dtp3 = process_dataset('data/DPT3_coverage.xlsx', 'CODE', 'YEAR', 'COVERAGE', 'DTP3 Coverage')
    if not res_dtp3.empty: all_stats.append(res_dtp3)

    # 2. ANC4
    res_anc4 = process_dataset('data/ANC4_coverage.xlsx', 'CODE', 'YEAR', 'COVERAGE', 'ANC4 Coverage')
    if not res_anc4.empty: all_stats.append(res_anc4)
        
    # 3. UHC Indicies
    try:
        res_uhc_ov = process_dataset('data/UHC_overall.xlsx', 'ISO3', 'Year', 'UHC', 'UHC (Overall)')
        res_uhc_id = process_dataset('data/UHC_ID.xlsx', 'ISO3', 'Year', 'UHC_ID', 'UHC (Infectious Disease)')
        res_uhc_rm = process_dataset('data/UHC_RMNCH.xlsx', 'ISO3', 'Year', 'UHC_RMNCH', 'UHC (RMNCH)')
        if not res_uhc_ov.empty: all_stats.append(res_uhc_ov)
        if not res_uhc_id.empty: all_stats.append(res_uhc_id)
        if not res_uhc_rm.empty: all_stats.append(res_uhc_rm)
    except Exception as e:
        print(f"Error processing UHC: {e}")

    # 4. Expenditures
    try:
        res_che = process_dataset('data/CHE.xlsx', 'ISO3', 'Year', 'CHE', 'Current Health Expenditure (CHE)')
        df_che = pd.read_excel('data/CHE.xlsx') # Load CHE to use as a multiplier for GGHE-D & OOP
        res_gghe = process_dataset('data/GCHE-D.xlsx', 'ISO3', 'Year', 'GCHE-D', 'Domestic General Government Health Exp (GGHE-D)', multiplier_df=df_che, multiplier_col='CHE')
        res_oop = process_dataset('data/OOP.xlsx', 'ISO3', 'Year', 'OOP as % of GDP', 'Out of pocket (OOPS)')
        
        if not res_che.empty: all_stats.append(res_che)
        if not res_gghe.empty: all_stats.append(res_gghe)
        if not res_oop.empty: all_stats.append(res_oop)
    except Exception as e:
        print(f"Error processing Expenditures: {e}")

    # 5. Workforce
    res_md = process_dataset('data/MD_per10k.xlsx', 'ISO3', 'Year', 'MD per 10k pop', 'Medical Doctors (per 10k)')
    res_nurse = process_dataset('data/Nurse_per10k.xlsx', 'ISO3', 'Year', 'Nurse and midwives per 10k pop', 'Nursing and midwifery personnel (per 10k)')
    res_chw = process_dataset('data/CHW_per10k.xlsx', 'ISO3', 'Year', 'CHW per 10k pop', 'Community Health Workers (per 10k)')
    
    if not res_md.empty: all_stats.append(res_md)
    if not res_nurse.empty: all_stats.append(res_nurse)
    if not res_chw.empty: all_stats.append(res_chw)

    if all_stats:
        final_csv = pd.concat(all_stats, ignore_index=True)
        final_csv.to_csv('data/peer_stats_summary.csv', index=False)
        print("Successfully generated data/peer_stats_summary.csv")
        print(final_csv.head())
    else:
        print("No stats were generated.")

if __name__ == "__main__":
    generate_peer_stats()
