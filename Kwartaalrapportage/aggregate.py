import pandas as pd
import numpy as np
import os

cwd = '/Users/tommeijer/Git/Kwartaalrapportage'
intercompany_path = os.path.join(cwd, 'Intercompany.xlsx')
mapping_path = os.path.join(cwd, 'mapping.xlsx')

def clean_rekening(val):
    try:
        if pd.isna(val) or val == '':
            return np.nan
        return int(float(val))
    except:
        return np.nan

print("Loading Intecompany.xlsx...")
ic_df = pd.read_excel(intercompany_path, header=1)
ic_df.columns = [str(c).strip() for c in ic_df.columns]

ic_total_sum = ic_df['totaal'].sum(skipna=True)
ic_huidig_sum = ic_df['2026 huidig kwartaal'].sum(skipna=True)

tech_row = ic_df[ic_df['Entity'].str.contains('TECH', na=False, case=False)]
ic_tech_total = tech_row['totaal'].sum() if not tech_row.empty else 0
ic_tech_huidig = tech_row['2026 huidig kwartaal'].sum() if not tech_row.empty else 0

veh_row = ic_df[ic_df['Entity'].str.contains('Vehicles', na=False, case=False)]
ic_veh_total = veh_row['totaal'].sum() if not veh_row.empty else 0
ic_veh_huidig = veh_row['2026 huidig kwartaal'].sum() if not veh_row.empty else 0

def process_entity(file_path, entity_name, target_col):
    print(f"Processing {entity_name}...")
    df = pd.read_excel(file_path, header=5)
    df.columns = [str(c).strip() for c in df.columns]
    
    if target_col not in df.columns:
        print(f"Warning: {target_col} not found in {file_path}. Using 'Eindsaldo' fallback.")
        if 'Eindsaldo' in df.columns:
            target_col = 'Eindsaldo'

    df['Rekening_Clean'] = df['Rekening'].apply(clean_rekening)
    df = df.dropna(subset=['Rekening_Clean']).copy()
    df['Rekening_Clean'] = df['Rekening_Clean'].astype('Int64')
    
    df['Eindsaldo'] = pd.to_numeric(df[target_col], errors='coerce').fillna(0.0)
    
    # Zero out
    zero_out_texts = ['R/c OOY Group Holding', 'R/c OOY TECH', 'R/c OOY Mobility', 'R/c OOY Vehicies']
    mask = df['Omschrijving'].astype(str).apply(lambda x: any(t.lower() in x.lower() for t in zero_out_texts))
    df.loc[mask, 'Eindsaldo'] = 0.0
    
    # Reductions
    if entity_name == 'Mobility':
        df.loc[df['Rekening_Clean'] == 153000, 'Eindsaldo'] -= ic_total_sum
        df.loc[df['Rekening_Clean'] == 441300, 'Eindsaldo'] -= ic_huidig_sum
    elif entity_name == 'Tech':
        df.loc[df['Rekening_Clean'] == 800100, 'Eindsaldo'] -= ic_tech_huidig
        df.loc[df['Rekening_Clean'] == 132000, 'Eindsaldo'] -= ic_tech_total
    elif entity_name == 'Vehicles':
        df.loc[df['Rekening_Clean'] == 800100, 'Eindsaldo'] -= ic_veh_huidig
        df.loc[df['Rekening_Clean'] == 132000, 'Eindsaldo'] -= ic_veh_total

    df['Organisatie'] = entity_name
    return df[['Organisatie', 'Rekening', 'Rekening_Clean', 'Soort', 'Omschrijving', 'Eindsaldo']]

dfs = []
dfs.append(process_entity(os.path.join(cwd, 'VISMA', 'Q1 2026 Group.xlsx'), 'Group', 'Correctie Eindsaldo'))
dfs.append(process_entity(os.path.join(cwd, 'VISMA', 'Q1 2026 Mobility.xlsx'), 'Mobility', 'Correctie Eindsaldo'))
dfs.append(process_entity(os.path.join(cwd, 'VISMA', 'Q1 2026 Tech.xlsx'), 'Tech', 'Eindsaldo'))
dfs.append(process_entity(os.path.join(cwd, 'VISMA', 'Q1 2026 Vehicles.xlsx'), 'Vehicles', 'Eindsaldo'))

all_data = pd.concat(dfs, ignore_index=True)

print("Loading mapping.xlsx...")
map_df = pd.read_excel(mapping_path, header=1)
map_df.columns = [str(c).strip() for c in map_df.columns]
map_df['Rekening_Clean'] = map_df['Rekening'].apply(clean_rekening).astype('Int64')

def map_entity(org):
    org = str(org).lower()
    if 'group' in org: return 'Group'
    if 'mobility' in org: return 'Mobility'
    if 'tech' in org: return 'Tech'
    if 'vehicles' in org: return 'Vehicles'
    return 'Unknown'
    
map_df['Organisatie_Clean'] = map_df['Organisatie'].apply(map_entity)

# Keep only relevant columns to avoid conflicts if others overlap
map_df_clean = map_df[['Organisatie_Clean', 'Rekening_Clean', 'Mapping']].dropna(subset=['Rekening_Clean'])

print("Merging data...")
merged = pd.merge(all_data, map_df_clean, 
                  left_on=['Organisatie', 'Rekening_Clean'], 
                  right_on=['Organisatie_Clean', 'Rekening_Clean'], 
                  how='left')

merged = merged.drop(columns=['Organisatie_Clean'])

unmapped = merged[(merged['Mapping'].isna()) & (merged['Eindsaldo'] != 0.0)]
if not unmapped.empty:
    print(f"Warning: {len(unmapped)} lines have no mapping with non-zero balance!")

summary = pd.pivot_table(merged, values='Eindsaldo', index='Mapping', columns='Organisatie', aggfunc='sum', fill_value=0.0)
expected_cols = ['Mobility', 'Vehicles', 'Group', 'Tech']
for c in expected_cols:
    if c not in summary.columns:
        summary[c] = 0.0
summary = summary.reindex(columns=expected_cols)

out_file = os.path.join(cwd, 'Aggregation_Results.xlsx')
print(f"Exporting results to {out_file}...")
with pd.ExcelWriter(out_file) as writer:
    summary.to_excel(writer, sheet_name='Summary')
    merged.to_excel(writer, sheet_name='Detailed Data', index=False)
    if not unmapped.empty:
        unmapped.to_excel(writer, sheet_name='Unmapped', index=False)

print("Export complete.")
