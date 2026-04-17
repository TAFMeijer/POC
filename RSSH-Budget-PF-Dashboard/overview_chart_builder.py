import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_processing import df_b, df_i, df_w, COMP_COLORS, SHADES, TYPE_TO_WEIGHT, country_to_region, country_to_shortname

def build_overview_chart(app, region, inc_custom=False, is_percent=False):
    all_countries = sorted(df_b['Country'].dropna().unique())
    if not region or region == 'ALL':
        target_countries = all_countries
    else:
        target_countries = [c for c in all_countries if country_to_region.get(c) == region]
        
    if not target_countries:
        return go.Figure(), {'height': '850px'}
        
    components = ['HIV/AIDS', 'Tuberculosis', 'Malaria', 'RSSH', 'Program Management']
    
    b_filt = df_b[df_b['Country'].isin(target_countries)].copy()
    i_filt = df_i[df_i['Country'].isin(target_countries)].copy()
    w_filt = df_w[df_w['Country'].isin(target_countries)].copy()
    
    tb_hiv_mask = i_filt['IndicatorCode'] == 'TB/HIV I-1'
    if tb_hiv_mask.any():
        for c in target_countries:
            c_mask = tb_hiv_mask & (i_filt['Country'] == c)
            if c_mask.any():
                hiv_b = b_filt[(b_filt['Country'] == c) & (b_filt['Module Parent Component'] == 'HIV/AIDS')]['Total Amount'].sum()
                tb_b = b_filt[(b_filt['Country'] == c) & (b_filt['Module Parent Component'] == 'Tuberculosis')]['Total Amount'].sum()
                winning_parent = 'HIV/AIDS' if hiv_b > tb_b else 'Tuberculosis'
                i_filt.loc[c_mask, 'Module Parent Component'] = winning_parent

    # PRE-CALCULATE TARGET COUNTRY LIMITS
    # Exclude Custom if toggle=False
    if not inc_custom:
        i_filt = i_filt[i_filt['IsCustom'] == False]
        w_filt = w_filt.iloc[0:0] # clear it out structurally natively

    country_totals_b = {}
    country_totals_i = {}
    country_totals_w = {}
    for c in target_countries:
        country_totals_b[c] = b_filt[b_filt['Country'] == c]['Total Amount'].sum()
        country_totals_i[c] = len(i_filt[i_filt['Country'] == c])
        country_totals_w[c] = len(w_filt[w_filt['Country'] == c])

    y_countries = []
    y_comps = []
    colors_list = []
    budget_sums = []
    wptm_counts = []
    
    import urllib.parse
    for c in target_countries:
        c_short = country_to_shortname.get(c, c)
        c_encoded = urllib.parse.quote(c)
        c_link = f"<a href='/budget-pf-poc/detailed?country={c_encoded}'>{c_short}</a>"
        for pc in components:
            y_countries.append(c_link)
            y_comps.append(pc)
            colors_list.append(COMP_COLORS.get(pc, '#7f7f7f'))
            
            b_val = b_filt[(b_filt['Country'] == c) & (b_filt['Module Parent Component'] == pc)]['Total Amount'].sum()
            budget_sums.append(b_val)
            
            w_val = len(w_filt[(w_filt['Country'] == c) & (w_filt['Module Parent Component'] == pc)])
            wptm_counts.append(w_val)
            
    # Subplot columns definition
    if inc_custom:
        fig = make_subplots(
            rows=1, cols=3, 
            shared_yaxes=True, 
            horizontal_spacing=0.02,
            subplot_titles=("Total Budget", "Indicators Selected", "WPTM Count"),
            column_widths=[0.4, 0.3, 0.3]
        )
    else:
        fig = make_subplots(
            rows=1, cols=2, 
            shared_yaxes=True, 
            horizontal_spacing=0.02,
            subplot_titles=("Total Budget", "Core Indicators Selected"),
            column_widths=[0.5, 0.5]
        )
        
    multi_y = [y_countries, y_comps]
    
    # --- CHART 1: BUDGET ---
    hover_b = []
    x_budget = []
    text_b = []
    for i, b in enumerate(budget_sums):
        raw_c = target_countries[i // 5]
        pc = y_comps[i]
        c_short = y_countries[i]
        tot = country_totals_b[raw_c]
        if is_percent:
            pct = (b / tot * 100) if tot > 0 else 0
            x_budget.append(pct)
            hover_b.append(f"<b>{c_short}</b><br>{pc}<br>Budget: {pct:.1f}% (${b/1e6:,.1f}M)")
            if pct > 4:
                text_b.append(f"{pct:.1f}%")
            else:
                text_b.append("")
        else:
            x_budget.append(b / 1e6)
            hover_b.append(f"<b>{c_short}</b><br>{pc}<br>Budget: ${b/1e6:,.1f}M")
            if b > 0:
                text_b.append(f"${b/1e6:,.1f}M")
            else:
                text_b.append("")
            
    fig.add_trace(go.Bar(
        y=multi_y,
        x=x_budget,
        orientation='h',
        marker_color=colors_list,
        text=text_b,
        textfont=dict(size=14),
        textposition='outside', # safely fit raw numeric/pct dynamically
        constraintext='none',
        cliponaxis=False,
        hoverinfo='text',
        hovertext=hover_b,
        name='Budget',
        showlegend=False,
    ), row=1, col=1)
    
    # --- CHART 2: INDICATORS ---
    tot_x_ind = [0] * len(y_comps)
    for ind_type in ['Coverage indicator', 'Outcome indicator', 'Impact indicator']:
        custom_loop = [False, True] if inc_custom else [False]
        for is_custom in custom_loop:
            counts = []
            bar_colors = []
            
            sub_i_filt = i_filt[(i_filt['IndicatorType'] == ind_type) & (i_filt['IsCustom'] == is_custom)]
            
            for i, pc in enumerate(y_comps):
                raw_c = target_countries[i // 5]
                c_val = len(sub_i_filt[(sub_i_filt['Country'] == raw_c) & (sub_i_filt['Module Parent Component'] == pc)])
                counts.append(c_val)
                
                weight = TYPE_TO_WEIGHT.get(ind_type, 'medium')
                col = SHADES.get(pc, SHADES['Other'])[weight]
                bar_colors.append(col)
                
            if sum(counts) > 0:
                x_ind = []
                text_ind = []
                hover_ind = []
                for i, count in enumerate(counts):
                    raw_c = target_countries[i // 5]
                    tot = country_totals_i[raw_c]
                    if is_percent:
                        pct = (count / tot * 100) if tot > 0 else 0
                        x_ind.append(pct)
                        tot_x_ind[i] += pct
                        text_ind.append(f"{pct:.0f}%" if count > 0 else "")
                        hover_ind.append(f"{pct:.1f}% ({count})" if count > 0 else "")
                    else:
                        x_ind.append(count)
                        tot_x_ind[i] += count
                        text_ind.append(str(count) if count > 0 else "")
                        hover_ind.append(str(count) if count > 0 else "")
                        
                trace_name = f"{ind_type} ({'Custom' if is_custom else 'Standard'})"
                trace_args = dict(
                    y=multi_y,
                    x=x_ind,
                    orientation='h',
                    name=trace_name,
                    marker_color=bar_colors,
                    text=text_ind,
                    textposition='inside',
                    insidetextanchor='middle',
                    textangle=0,
                    constraintext='none',
                    hovertext=hover_ind,
                    hoverinfo='name+text',
                    showlegend=False
                )
                
                if is_custom:
                    trace_args['marker_color'] = "#ececec"
                    trace_args['marker_pattern_shape'] = "/"
                    trace_args['marker_pattern_size'] = 3
                    trace_args['marker_pattern_fgcolor'] = bar_colors
                    
                fig.add_trace(go.Bar(**trace_args), row=1, col=2)
                
    fig.add_trace(go.Bar(
        x=[0]*len(multi_y),
        y=multi_y,
        base=tot_x_ind,
        orientation='h',
        marker_color='rgba(0,0,0,0)',
        text=[f" {val:.0f}%" if (is_percent and val > 0) else (f" {int(val)}" if val > 0 else "") for val in tot_x_ind],
        textfont=dict(size=14, color='black'),
        textposition='outside',
        constraintext='none',
        showlegend=False,
        hoverinfo='none',
        cliponaxis=False
    ), row=1, col=2)
                
    custom_loop = [False, True] if inc_custom else [False]
    for ind_type in ['Coverage indicator', 'Outcome indicator', 'Impact indicator']:
        for is_custom in custom_loop:
            weight = TYPE_TO_WEIGHT.get(ind_type, 'medium')
            col = SHADES.get('HIV/AIDS', SHADES['Other'])[weight]
            trace_args = dict(
                y=[None], x=[None],
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
            
    # --- CHART 3: WPTM ---
    if inc_custom:
        wptm_colors = []
        hover_w = []
        x_wptm = []
        text_w = []
        for i, w in enumerate(wptm_counts):
            raw_c = target_countries[i // 5]
            pc = y_comps[i]
            c_short = y_countries[i]
            col = SHADES.get(pc, SHADES['Other'])['medium']
            wptm_colors.append(col)
            
            tot = country_totals_w[raw_c]
            if is_percent:
                pct = (w / tot * 100) if tot > 0 else 0
                x_wptm.append(pct)
                hover_w.append(f"<b>{c_short}</b><br>{pc}<br>WPTM Count: {pct:.1f}% ({w})")
                text_w.append(f"{pct:.1f}%" if pct > 4 else "")
            else:
                x_wptm.append(w)
                hover_w.append(f"<b>{c_short}</b><br>{pc}<br>WPTM Count: {w}")
                text_w.append(str(w) if w > 0 else "")
                
        fig.add_trace(go.Bar(
            y=multi_y,
            x=x_wptm,
            orientation='h',
            marker_color=wptm_colors,
            text=text_w,
            textposition='outside', # explicitly put text on outside
            hoverinfo='text',
            hovertext=hover_w,
            name='WPTM',
            showlegend=False,
        ), row=1, col=3)
    
    # Axes Padding & Legend Logic
    max_w = max(wptm_counts) if wptm_counts else 0
    max_i = 0
    if not i_filt.empty:
        mod_counts = i_filt.groupby(['Country', 'Module Parent Component']).size()
        if not mod_counts.empty:
            max_i = mod_counts.max()
            
    overall_max = max(max_w, max_i)
    max_x_axis = overall_max * 1.15
    
    if is_percent:
        max_x_axis = 105.0 # Max axis dynamically scales slightly past 100% to fit labels
        
    leg_y = 0.98
    leg_x = 0.98
    leg_yanchor = "top"
    leg_xanchor = "right"
    margin_r = 20
    
    if overall_max > 0:
        threshold = max_x_axis * 0.30
        
        # Ensure we don't index out of bounds if there's no wptm count to check
        if inc_custom and wptm_counts:
            top_overlap = any((wptm_counts[i]/country_totals_w[target_countries[i//5]]*100 if is_percent and country_totals_w[target_countries[i//5]]>0 else wptm_counts[i]) > threshold for i in range(min(8, len(wptm_counts))))
        else:
            top_overlap = False
            
        if inc_custom and top_overlap:
            leg_y = 1.0
            leg_x = 1.02
            leg_yanchor = "top"
            leg_xanchor = "left"
            margin_r = 180

    calculated_height = max(800, len(y_countries) * 28 + 100)
    
    raw_countries_mapped = [target_countries[i // 5] for i in range(len(y_countries))]
    for trace in fig.data:
        if 'customdata' not in trace or trace['customdata'] is None:
            trace.customdata = raw_countries_mapped

    fig.update_layout(
        height=calculated_height,
        font_family="Arial",
        barmode='stack',
        bargap=0.3, # maintain native visual vertical gaps
        margin=dict(l=150, r=margin_r, t=70, b=20),
        yaxis=dict(range=[len(y_countries) - 0.5, -0.75], tickfont=dict(size=12)),
        legend=dict(
            title=dict(text="Indicator legend"),
            yanchor=leg_yanchor,
            y=leg_y,
            xanchor=leg_xanchor,
            x=leg_x,
            bgcolor="rgba(255, 255, 255, 0.8)"
        )
    )
    
    if inc_custom:
        fig.update_xaxes(matches='x2', row=1, col=3)
    
    if is_percent:
        fig.update_xaxes(range=[0, 105], row=1, col=1)
        fig.update_xaxes(range=[0, 105], row=1, col=2)
        if inc_custom:
            fig.update_xaxes(range=[0, 105], row=1, col=3)
    else:
        if budget_sums and max(budget_sums) > 0:
            max_b = max(budget_sums) / 1_000_000
            fig.update_xaxes(range=[0, max_b * 1.15], row=1, col=1)
            
        if overall_max > 0:
            fig.update_xaxes(range=[0, max_x_axis], row=1, col=2)
            if inc_custom:
                fig.update_xaxes(range=[0, max_x_axis], row=1, col=3)
        
    return fig, {'height': f"{calculated_height}px", 'transition': 'height 0.4s ease-out'}
