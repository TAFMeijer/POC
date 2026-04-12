import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from data_processing import df_b, df_i, df_w, COMP_COLORS, SHADES, TYPE_TO_WEIGHT, indicator_order

def build_main_chart(app, country, ip, component):
    if not country or not ip:
        return go.Figure(), {'height': '765px'}
    
    # Filter datasets
    if ip == 'ALL':
        b_filt = df_b[(df_b['Country'] == country)]
        i_filt = df_i[(df_i['Country'] == country)]
        w_filt = df_w[(df_w['Country'] == country)].copy()
    else:
        b_filt = df_b[(df_b['Country'] == country) & (df_b['Implementation Period Name'] == ip)]
        i_filt = df_i[(df_i['Country'] == country) & (df_i['Implementation Period Name'] == ip)]
        w_filt = df_w[(df_w['Country'] == country) & (df_w['Implementation Period Name'] == ip)].copy()
        
    if component != 'ALL':
        b_filt = b_filt[b_filt['Module Parent Component'] == component]
        i_filt = i_filt[i_filt['Module Parent Component'] == component]
        w_filt = w_filt[w_filt['Module Parent Component'] == component]
    
    # Aggregate Budget grouping so it contains total sum per module for height and ranking mapping
    b_agg = b_filt.groupby(['Module Parent Component', 'Module'])['Total Amount'].sum().reset_index()
    
    # Identify modules that exist for this country/IP
    # Add Impact/Outcome modules correctly to the Budget Dataframe with 0 budget (so they show up grouped correctly)
    io_modules = i_filt[i_filt['IndicatorType'].isin(['Impact indicator', 'Outcome indicator'])]['Module'].unique()
    for io_mod in io_modules:
        if io_mod not in b_agg['Module'].values:
            parent = str(io_mod).replace(" (Impact/Outcome)", "")
            b_agg = pd.concat([b_agg, pd.DataFrame([{'Module Parent Component': parent, 'Module': io_mod, 'Total Amount': 0}])], ignore_index=True)

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
    
    # Sort Budget descending inside component grouping
    b_agg = b_agg.sort_values(by=['comp_sort', 'Total Amount'], ascending=[True, False])
    
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
        textposition='outside',
        textangle=0,
        name='Budget',
        showlegend=False,
        customdata=custom_data_b,
        hoverinfo='none'
    ), row=1, col=1)
    
    # Chart 2: Indicators Count with JSON tooltips
    for ind_type in ['Coverage indicator', 'Outcome indicator', 'Impact indicator']:
        for is_custom in [False, True]:
            sub_i_filt = i_filt[(i_filt['IndicatorType'] == ind_type) & (i_filt['IsCustom'] == is_custom)]
            
            counts = []
            bar_colors = []
            custom_data_i = []
            
            for y_m in y_vals:
                mod_sub = sub_i_filt[sub_i_filt['Module'] == y_m]
                c = len(mod_sub)
                counts.append(c)
                
                pc = module_to_pc.get(y_m, 'Other')
                weight = TYPE_TO_WEIGHT.get(ind_type, 'medium')
                
                if is_custom:
                    col = SHADES['Custom'][weight]
                else:
                    col = SHADES.get(pc, SHADES['Other'])[weight]
                bar_colors.append(col)
                
                if c > 0:
                    data = []
                    mod_sub = mod_sub.copy()
                    mod_sub['__sort_code'] = mod_sub['IndicatorCode'].fillna(mod_sub['IndicatorCustomName'])
                    mod_sub['__sort_order'] = mod_sub['__sort_code'].map(indicator_order).fillna(99999)
                    mod_sub.sort_values(by=['__sort_order', '__sort_code', 'Implementation Period Name'], inplace=True)
                    
                    if is_custom:
                        for _, row in mod_sub.iterrows():
                            name = str(row.get('IndicatorCustomName', ''))
                            ip_name = str(row.get('Implementation Period Name', ''))
                            if name == 'nan': name = ''
                            if ip_name == 'nan': ip_name = 'Unknown'
                            data.append({'ip': ip_name, 'name': name})
                        custom_data_i.append([json.dumps({'type': 'INDICATOR_CUSTOM', 'title': f"{ind_type} (Custom)", 'data': data})])
                    else:
                        for _, row in mod_sub.iterrows():
                            ip_name = str(row.get('Implementation Period Name', ''))
                            code = str(row.get('IndicatorCode', ''))
                            desc = str(row.get('IndicatorDescription', ''))
                            if code == 'nan': code = ''
                            if desc == 'nan': desc = ''
                            if ip_name == 'nan': ip_name = 'Unknown'
                            data.append({'ip': ip_name, 'code': code, 'desc': desc})
                        custom_data_i.append([json.dumps({'type': 'INDICATOR_STANDARD', 'title': f"{ind_type} (Standard)", 'data': data})])
                else:
                    custom_data_i.append([json.dumps({'type': 'EMPTY'})])
                
            if sum(counts) > 0:
                fig.add_trace(go.Bar(
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
                ), row=1, col=2)
    
    # Add dummy traces for the dynamic legend
    legend_component = component if component != 'ALL' else 'Other'
    
    for ind_type in ['Coverage indicator', 'Outcome indicator', 'Impact indicator']:
        for is_custom in [False, True]:
            weight = TYPE_TO_WEIGHT.get(ind_type, 'medium')
            if is_custom:
                col = SHADES['Custom'][weight]
            else:
                col = SHADES.get(legend_component, SHADES['Other'])[weight]
                
            fig.add_trace(go.Bar(
                y=[None], x=[None],
                name=f"{ind_type} ({'Custom' if is_custom else 'Standard'})",
                marker_color=col,
                showlegend=True,
                hoverinfo='none'
            ), row=1, col=2)
    
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
        textposition='outside',
        textangle=0,
        name='WPTM',
        showlegend=False,
        customdata=custom_data_w,
        hoverinfo='none'
    ), row=1, col=3)
    
    # Dynamic Legend Placement to avoid WPTM overlaps
    max_w = max(wptm_counts) if wptm_counts else 0
    leg_y = 0.98
    leg_x = 0.98
    leg_yanchor = "top"
    leg_xanchor = "right"
    margin_r = 20
    
    if max_w > 0:
        # Check first 8 rows for wide WPTM bars pushing into the legend space
        top_overlap = any(w > max_w * 0.25 for w in wptm_counts[:8])
        
        if top_overlap:
            leg_y = 1.0
            leg_x = 1.02
            leg_yanchor = "top"
            leg_xanchor = "left"
            margin_r = 180

    # Dynamic Height constrained natively scaling to explicitly track Row count
    num_rows = max(1, len(y_vals))
    calculated_height = min(765, max(250, num_rows * 26 + 130))

    # Formatting
    fig.update_layout(
        height=calculated_height,
        font_family="Arial",
        barmode='stack',
        bargap=0.3,
        margin=dict(l=450, r=margin_r, t=60, b=20),
        yaxis=dict(autorange="reversed", ticklabelstandoff=4), # Show sorted top to bottom, offset text visually
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
    max_i = 0
    if not i_filt.empty:
        mod_counts = i_filt.groupby('Module').size()
        if not mod_counts.empty:
            max_i = mod_counts.max()
            
    overall_max = max(max_w, max_i)
    if overall_max > 0:
        fig.update_xaxes(range=[0, overall_max * 1.15], row=1, col=2)
        
    return fig, {'height': f"{calculated_height}px", 'transition': 'height 0.4s ease-out'}
