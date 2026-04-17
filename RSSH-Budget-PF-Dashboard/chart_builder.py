import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from data_processing import df_b, df_i, df_w, COMP_COLORS, SHADES, TYPE_TO_WEIGHT, indicator_order, short_module_to_parent

def build_main_chart(app, region, country, ip, component):
    if not country or not ip:
        return go.Figure(), {'height': '850px'}
    
    b_filt = df_b.copy()
    i_filt = df_i.copy()
    w_filt = df_w.copy()
    
    if country != 'ALL':
        b_filt = b_filt[(b_filt['Country'] == country)]
        i_filt = i_filt[(i_filt['Country'] == country)]
        w_filt = w_filt[(w_filt['Country'] == country)]
    elif region and region != 'ALL':
        from data_processing import country_to_region
        b_filt = b_filt[b_filt['Country'].map(country_to_region) == region]
        i_filt = i_filt[i_filt['Country'].map(country_to_region) == region]
        w_filt = w_filt[w_filt['Country'].map(country_to_region) == region]
        
    if ip != 'ALL':
        b_filt = b_filt[(b_filt['Implementation Period Name'] == ip)]
        i_filt = i_filt[(i_filt['Implementation Period Name'] == ip)]
        w_filt = w_filt[(w_filt['Implementation Period Name'] == ip)]
        
    # Dynamically map TB/HIV I-1 indicator to the disease with the larger budget contextually
    tb_hiv_mask = i_filt['IndicatorCode'] == 'TB/HIV I-1'
    if tb_hiv_mask.any():
        hiv_b = b_filt[b_filt['Module Parent Component'] == 'HIV/AIDS']['Total Amount'].sum()
        tb_b = b_filt[b_filt['Module Parent Component'] == 'Tuberculosis']['Total Amount'].sum()
        winning_parent = 'HIV/AIDS' if hiv_b > tb_b else 'Tuberculosis'
        i_filt.loc[tb_hiv_mask, 'Module Parent Component'] = winning_parent
        i_filt.loc[tb_hiv_mask, 'Module'] = winning_parent + ' (Impact/Outcome)'

    if component != 'ALL':
        b_filt = b_filt[b_filt['Module Parent Component'] == component]
        i_filt = i_filt[i_filt['Module Parent Component'] == component]
        w_filt = w_filt[w_filt['Module Parent Component'] == component]
    
    # Aggregate Budget grouping so it contains total sum per module for height and ranking mapping
    b_agg = b_filt.groupby(['Module Parent Component', 'Module'])['Total Amount'].sum().reset_index()
    
    # Identify modules that exist for this country/IP
    # Add Impact/Outcome modules correctly to the Budget Dataframe with 0 budget (so they show up grouped correctly)
    io_modules_df = i_filt[i_filt['IndicatorType'].isin(['Impact indicator', 'Outcome indicator'])]
    for _, row in io_modules_df[['Module', 'Module Parent Component']].drop_duplicates().iterrows():
        io_mod = row['Module']
        parent = row['Module Parent Component']
        if io_mod not in b_agg['Module'].values:
            b_agg = pd.concat([b_agg, pd.DataFrame([{'Module Parent Component': parent, 'Module': io_mod, 'Total Amount': 0}])], ignore_index=True)

    # Force injection of ALL modules that exist globally across the selected scope, so filtering by IP doesn't break the Y-Axis structure
    if country == 'ALL':
        if region and region != 'ALL':
            from data_processing import country_to_region
            country_b_filt = df_b[df_b['Country'].map(country_to_region) == region]
            country_i_filt = df_i[df_i['Country'].map(country_to_region) == region]
        else:
            country_b_filt = df_b.copy()
            country_i_filt = df_i.copy()
    else:
        country_b_filt = df_b[df_b['Country'] == country]
        country_i_filt = df_i[df_i['Country'] == country]
    if component != 'ALL':
        country_b_filt = country_b_filt[country_b_filt['Module Parent Component'] == component]
        country_i_filt = country_i_filt[country_i_filt['Module Parent Component'] == component]
        
    for _, row in country_b_filt[['Module Parent Component', 'Module']].drop_duplicates().iterrows():
        c_mod = row['Module']
        c_parent = row['Module Parent Component']
        if c_mod not in b_agg['Module'].values:
            b_agg = pd.concat([b_agg, pd.DataFrame([{'Module Parent Component': c_parent, 'Module': c_mod, 'Total Amount': 0}])], ignore_index=True)
            
    c_io_modules_df = country_i_filt[country_i_filt['IndicatorType'].isin(['Impact indicator', 'Outcome indicator'])]
    for _, row in c_io_modules_df[['Module', 'Module Parent Component']].drop_duplicates().iterrows():
        io_mod = row['Module']
        parent = row['Module Parent Component']
        if io_mod not in b_agg['Module'].values:
            b_agg = pd.concat([b_agg, pd.DataFrame([{'Module Parent Component': parent, 'Module': io_mod, 'Total Amount': 0}])], ignore_index=True)

    # Force injection of standard baseline Impact/Outcome rows 
    baseline_io = [
        ('HIV/AIDS', 'HIV/AIDS (Impact/Outcome)'),
        ('Tuberculosis', 'Tuberculosis (Impact/Outcome)'),
        ('Malaria', 'Malaria (Impact/Outcome)'),
        ('RSSH', 'RSSH (Outcome)')
    ]
    for parent_comp, io_mod in baseline_io:
        if component != 'ALL' and parent_comp != component:
            continue
        if io_mod not in b_agg['Module'].values:
            b_agg = pd.concat([b_agg, pd.DataFrame([{'Module Parent Component': parent_comp, 'Module': io_mod, 'Total Amount': 0}])], ignore_index=True)

    # Force injection of all 31 baseline modules mapping to explicitly appear on the Y-Axis even when empty
    for mod_short, parent_comp in short_module_to_parent.items():
        if mod_short == 'Program management':
            parent_comp = 'Program Management'
            
        if component != 'ALL' and parent_comp != component:
            continue
            
        if mod_short not in b_agg['Module'].values:
            b_agg = pd.concat([b_agg, pd.DataFrame([{'Module Parent Component': parent_comp, 'Module': mod_short, 'Total Amount': 0}])], ignore_index=True)

    # Custom Sort Order for Components ensuring Program Management is firmly at the bottom
    comp_order_dict = {
        'HIV/AIDS': 1,
        'Tuberculosis': 2,
        'Malaria': 3,
        'RSSH': 4,
        'Multi-Component': 5,
        'Other': 6,
        'Program Management': 99
    }
    b_agg['comp_sort'] = b_agg['Module Parent Component'].map(comp_order_dict).fillna(7)
    
    # Sort Budget descending inside component grouping, forcing Impact/Outcome to the bottom of the zero-budget list
    b_agg['is_io'] = b_agg['Module'].astype(str).str.contains('(Impact/Outcome)', regex=False) | b_agg['Module'].astype(str).str.contains('(Outcome)', regex=False)
    b_agg = b_agg.sort_values(by=['comp_sort', 'Total Amount', 'is_io'], ascending=[True, False, True])
    
    # Inject blank spacing rows between distinct components
    new_b_agg_rows = []
    current_comp = None
    space_counter = 1
    
    for _, row in b_agg.iterrows():
        comp = row['Module Parent Component']
        if current_comp is not None and comp != current_comp:
            blank_name = " " * space_counter
            space_counter += 1
            new_b_agg_rows.append({
                'Module Parent Component': 'Spacer',
                'Module': blank_name,
                'Total Amount': 0,
                'comp_sort': row['comp_sort'] - 0.5
            })
        current_comp = comp
        new_b_agg_rows.append(row.to_dict())
        
    b_agg = pd.DataFrame(new_b_agg_rows)
    
    # We have 3 subplots side by side
    fig = make_subplots(
        rows=1, cols=3, 
        shared_yaxes=True, 
        horizontal_spacing=0.02,
        subplot_titles=("Budget ($M)", "Indicators Selected", "WPTM Count"),
        column_widths=[0.4, 0.3, 0.3]
    )
    
    # Y axis - Category string
    y_vals = b_agg['Module'].tolist()
    module_to_pc = dict(zip(b_agg['Module'], b_agg['Module Parent Component']))
    
    # Define shades for indicators mapped to parent component colors
    
    # Chart 1: Total Budget with strict JSON Tooltips 
    colors = [COMP_COLORS.get(pc, '#7f7f7f') for pc in b_agg['Module Parent Component']]
    custom_data_b = []
    
    for y_m in y_vals:
        mod_b = b_filt[b_filt['Module'] == y_m]
        # Sum by intervention
        int_agg = mod_b.groupby('Intervention')['Total Amount'].sum().reset_index()
        int_agg = int_agg.sort_values(by='Total Amount', ascending=False)
        
        if int_agg.empty or int_agg['Total Amount'].sum() == 0:
            custom_data_b.append([json.dumps({'type': 'BUDGET', 'data': []})])
        else:
            data = []
            for _, row in int_agg.iterrows():
                if row['Total Amount'] > 0:
                    data.append({'Intervention': str(row.get('Intervention', '')), 'Amount': f"{row['Total Amount']/1_000_000:,.1f}"})
            custom_data_b.append([json.dumps({'type': 'BUDGET', 'data': data})])
    
    fig.add_trace(go.Bar(
        y=y_vals,
        x=b_agg['Total Amount'] / 1_000_000,
        orientation='h',
        marker_color=colors,
        text=b_agg['Total Amount'].apply(lambda x: f"{x/1_000_000:,.1f}" if x>0 else ""),
        textfont=dict(size=14),
        textposition='outside',
        constraintext='none',
        cliponaxis=False,
        textangle=0,
        name='Budget',
        showlegend=False,
        customdata=custom_data_b,
        hoverinfo='none'
    ), row=1, col=1)
    
    # Chart 2: Indicators Count with JSON tooltips
    tot_x_ind = [0] * len(y_vals)
    for ind_type in ['Coverage indicator', 'Outcome indicator', 'Impact indicator']:
        for is_custom in [False, True]:
            sub_i_filt = i_filt[(i_filt['IndicatorType'] == ind_type) & (i_filt['IsCustom'] == is_custom)]
            
            counts = []
            bar_colors = []
            custom_data_i = []
            
            for i, y_m in enumerate(y_vals):
                mod_sub = sub_i_filt[sub_i_filt['Module'] == y_m]
                c = len(mod_sub)
                counts.append(c)
                tot_x_ind[i] += c
                
                pc = module_to_pc.get(y_m, 'Other')
                weight = TYPE_TO_WEIGHT.get(ind_type, 'medium')
                
                col = SHADES.get(pc, SHADES['Other'])[weight]
                bar_colors.append(col)
                
                if c > 0:
                    data = []
                    mod_sub = mod_sub.copy()
                    mod_sub['__sort_code'] = mod_sub['IndicatorCode'].fillna(mod_sub['IndicatorCustomName'])
                    mod_sub['__sort_order'] = mod_sub['__sort_code'].map(indicator_order).fillna(99999)
                    mod_sub.sort_values(by=['__sort_order', '__sort_code', 'Implementation Period Name'], inplace=True)
                    
                    if is_custom:
                        grouped = mod_sub.groupby(['IndicatorCustomName', '__sort_order', '__sort_code'], dropna=False).size().reset_index(name='count')
                        grouped.sort_values(by=['count', '__sort_order', '__sort_code'], ascending=[False, True, True], inplace=True)
                        for _, row in grouped.iterrows():
                            name = str(row['IndicatorCustomName'])
                            if name == 'nan': name = 'Unknown'
                            data.append({'name': name, 'count': int(row['count'])})
                        custom_data_i.append([json.dumps({'type': 'INDICATOR_CUSTOM', 'title': f"{ind_type} (Custom)", 'data': data})])
                    else:
                        grouped = mod_sub.groupby(['IndicatorCode', 'IndicatorDescription', '__sort_order', '__sort_code'], dropna=False).size().reset_index(name='count')
                        grouped.sort_values(by=['count', '__sort_order', '__sort_code'], ascending=[False, True, True], inplace=True)
                        for _, row in grouped.iterrows():
                            code = str(row['IndicatorCode'])
                            desc = str(row['IndicatorDescription'])
                            if code == 'nan': code = ''
                            if desc == 'nan': desc = ''
                            data.append({'code': code, 'desc': desc, 'count': int(row['count'])})
                        custom_data_i.append([json.dumps({'type': 'INDICATOR_STANDARD', 'title': f"{ind_type} (Standard)", 'data': data})])
                else:
                    custom_data_i.append([json.dumps({'type': 'EMPTY'})])
                
            if sum(counts) > 0:
                trace_args = dict(
                    y=y_vals,
                    x=counts,
                    orientation='h',
                    name=f"{ind_type} ({'Custom' if is_custom else 'Standard'})",
                    marker_color=bar_colors,
                    text=[str(c) if c > 0 else "" for c in counts],
                    textposition='inside',
                    insidetextanchor='middle',
                    textangle=0,
                    constraintext='none',
                    showlegend=False,
                    customdata=custom_data_i,
                    hoverinfo='none'
                )
                
                if is_custom:
                    trace_args['marker_color'] = "#ececec"
                    trace_args['marker_pattern_shape'] = "/"
                    trace_args['marker_pattern_size'] = 3
                    trace_args['marker_pattern_fgcolor'] = bar_colors
                    
                fig.add_trace(go.Bar(**trace_args), row=1, col=2)
                
    fig.add_trace(go.Bar(
        x=[0]*len(y_vals),
        y=y_vals,
        base=tot_x_ind,
        orientation='h',
        marker_color='rgba(0,0,0,0)',
        text=[f" {c}" if c > 0 else "" for c in tot_x_ind],
        textfont=dict(size=14, color='black'),
        textposition='outside',
        constraintext='none',
        showlegend=False,
        hoverinfo='none',
        cliponaxis=False
    ), row=1, col=2)
    
    # Add dummy traces for the dynamic legend
    legend_component = component if component != 'ALL' else 'Other'
    dummy_y = [y_vals[0]] if y_vals else [None]
    
    for ind_type in ['Coverage indicator', 'Outcome indicator', 'Impact indicator']:
        for is_custom in [False, True]:
            weight = TYPE_TO_WEIGHT.get(ind_type, 'medium')
            col = SHADES.get(legend_component, SHADES['Other'])[weight]
            
            trace_args = dict(
                y=dummy_y, x=[None],
                name=f"{ind_type} ({'Custom' if is_custom else 'Standard'})",
                marker_color=col,
                showlegend=True,
                hoverinfo='none'
            )
            
            if is_custom:
                trace_args['marker_color'] = "#ececec"
                trace_args['marker_pattern_shape'] = "/"
                trace_args['marker_pattern_size'] = 3
                trace_args['marker_pattern_fgcolor'] = col
                
            fig.add_trace(go.Bar(**trace_args), row=1, col=2)
    
    # Chart 3: WPTM Count with JSON Tooltips
    wptm_counts = []
    wptm_colors = []
    custom_data_w = []
    for y_m in y_vals:
        mod_w = w_filt[w_filt['Module'] == y_m]
        c = len(mod_w)
        wptm_counts.append(c)
        pc = module_to_pc.get(y_m, 'Other')
        col = SHADES.get(pc, SHADES['Other'])['medium']
        wptm_colors.append(col)
        
        if c > 0:
            data = []
            for _, row in mod_w.iterrows():
                ip_name = str(row.get('Implementation Period Name', ''))
                act = str(row.get('KeyActivity', ''))
                if ip_name == 'nan': ip_name = 'Unknown'
                if act == 'nan': act = ''
                data.append({'ip': ip_name, 'act': act})
            custom_data_w.append([json.dumps({'type': 'WPTM', 'data': data})])
        else:
            custom_data_w.append([json.dumps({'type': 'EMPTY'})])
        
    fig.add_trace(go.Bar(
        y=y_vals,
        x=wptm_counts,
        orientation='h',
        marker_color=wptm_colors,
        text=[str(c) if c > 0 else "" for c in wptm_counts],
        textfont=dict(size=14),
        textposition='outside',
        constraintext='none',
        cliponaxis=False,
        textangle=0,
        name='WPTM',
        showlegend=False,
        customdata=custom_data_w,
        hoverinfo='none'
    ), row=1, col=3)
    
    # Dynamic Legend Placement to avoid WPTM overlaps
    max_w = max(wptm_counts) if wptm_counts else 0
    max_i = 0
    if not i_filt.empty:
        mod_counts = i_filt.groupby('Module').size()
        if not mod_counts.empty:
            max_i = mod_counts.max()
            
    overall_max = max(max_w, max_i)
    max_x_axis = overall_max * 1.15
    
    leg_y = 0.98
    leg_x = 0.98
    leg_yanchor = "top"
    leg_xanchor = "right"
    margin_r = 20
    
    if overall_max > 0:
        # Check first 8 rows for wide WPTM bars pushing into the legend space
        threshold = max_x_axis * 0.30
        top_overlap = any(w > threshold for w in wptm_counts[:8])
        
        if top_overlap:
            leg_y = 1.0
            leg_x = 1.02
            leg_yanchor = "top"
            leg_xanchor = "left"
            margin_r = 180

    # Dynamic Height constrained natively scaling to explicitly track Row count
    num_rows = max(1, len(y_vals))
    calculated_height = min(850, max(250, num_rows * 30 + 130))

    # Formatting
    fig.update_layout(
        height=calculated_height,
        font_family="Arial",
        barmode='stack',
        bargap=0.3,
        margin=dict(l=450, r=margin_r, t=40, b=20),
        yaxis=dict(autorange="reversed", ticklabelstandoff=4, dtick=1, tickfont=dict(size=13)), # Show sorted top to bottom, offset text visually, force ALL tickets to render even if squished
        legend=dict(
            title=dict(text="Indicator legend"),
            yanchor=leg_yanchor,
            y=leg_y,
            xanchor=leg_xanchor,
            x=leg_x,
            bgcolor="rgba(255, 255, 255, 0.8)"
        )
    )
    
    # Inject Custom Image Icons cleanly centered dynamically across the Y-axis native bounds
    icon_map = {
        'HIV/AIDS': 'HIV.png',
        'Tuberculosis': 'TB.png',
        'Malaria': 'malaria.png',
        'RSSH': 'RSSH.png'
    }
    
    comp_indices = {}
    for m in y_vals:
        comp = module_to_pc.get(m)
        if m.strip() != "":
            comp_indices.setdefault(comp, []).append(m)
            
    for comp, fn in icon_map.items():
        mods = comp_indices.get(comp, [])
        if mods:
            mid_idx = len(mods) // 2
            y_mid_str = mods[mid_idx]
            
            fig.add_layout_image(
                dict(
                    source=app.get_asset_url(fn),
                    xref="paper", yref="y",
                    x=-0.35, y=y_mid_str,
                    sizex=0.05, sizey=3,
                    xanchor="right", yanchor="middle",
                    sizing="contain"
                )
            )
    
    fig.update_xaxes(matches='x2', row=1, col=3)
    
    # Pad budget axis to guarantee text doesn't overflow
    if not b_agg.empty and b_agg['Total Amount'].max() > 0:
        max_b = b_agg['Total Amount'].max() / 1_000_000
        fig.update_xaxes(range=[0, max_b * 1.15], row=1, col=1)

    # Pad shared axes for Indicators and WPTM to guarantee text doesn't overflow
    if overall_max > 0:
        fig.update_xaxes(range=[0, max_x_axis], row=1, col=2)
        
    return fig, {'height': f"{calculated_height}px", 'transition': 'height 0.4s ease-out'}
