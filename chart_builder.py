import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_processing import (
    df_b, df_i, COMP_COLORS, SHADES, TYPE_TO_WEIGHT,
    indicator_order, short_module_to_parent,
    filter_data, reassign_tb_hiv, country_to_region,
)

# Component sort order — Program Management firmly at the bottom
COMP_ORDER = {
    'HIV/AIDS': 1, 'Tuberculosis': 2, 'Malaria': 3, 'RSSH': 4,
    'Multi-Component': 5, 'Other': 6, 'Program Management': 99,
}

# Baseline Impact/Outcome pseudo-modules that must always appear
BASELINE_IO = [
    ('HIV/AIDS', 'HIV/AIDS (Impact/Outcome)'),
    ('Tuberculosis', 'Tuberculosis (Impact/Outcome)'),
    ('Malaria', 'Malaria (Impact/Outcome)'),
    ('RSSH', 'RSSH (Outcome)'),
]


def _inject_missing_modules(b_agg, i_filt, component):
    """Ensure every module that should appear on the Y-axis is present in b_agg,
    even if it has zero budget.  Collects all missing rows first then does a
    single concat (avoids ~40 individual pd.concat calls)."""
    existing = set(b_agg['Module'].values)
    missing_rows = []

    # Impact / Outcome modules from the indicator data
    io_mask = i_filt['IndicatorType'].isin(['Impact indicator', 'Outcome indicator'])
    for _, row in i_filt.loc[io_mask, ['Module', 'Module Parent Component']].drop_duplicates().iterrows():
        if row['Module'] not in existing:
            missing_rows.append({'Module Parent Component': row['Module Parent Component'],
                                 'Module': row['Module'], 'Total Amount': 0})
            existing.add(row['Module'])

    # Baseline Impact/Outcome rows
    for parent, io_mod in BASELINE_IO:
        if component != 'ALL' and parent != component:
            continue
        if io_mod not in existing:
            missing_rows.append({'Module Parent Component': parent, 'Module': io_mod, 'Total Amount': 0})
            existing.add(io_mod)

    # All 31 baseline module short-names
    for mod_short, parent in short_module_to_parent.items():
        if mod_short == 'Program management':
            parent = 'Program Management'
        if component != 'ALL' and parent != component:
            continue
        if mod_short not in existing:
            missing_rows.append({'Module Parent Component': parent, 'Module': mod_short, 'Total Amount': 0})
            existing.add(mod_short)

    if missing_rows:
        b_agg = pd.concat([b_agg, pd.DataFrame(missing_rows)], ignore_index=True)
    return b_agg


def build_main_chart(app, region, country, ip, component, exclude_c19rm=False):
    if not country or not ip:
        return go.Figure(), {'height': '850px'}

    b_filt, i_filt, w_filt = filter_data(region=region, country=country, ip=ip, component=component, exclude_c19rm=exclude_c19rm)

    # TB/HIV I-1 reassignment (single country or all)
    i_filt = reassign_tb_hiv(b_filt, i_filt)

    # Also apply component filter on indicators for TB/HIV I-1 that just got reassigned
    if component != 'ALL':
        i_filt = i_filt[i_filt['Module Parent Component'] == component]

    # Aggregate budget per module
    b_agg = b_filt.groupby(['Module Parent Component', 'Module'])['Total Amount'].sum().reset_index()

    # Inject global modules (from unfiltered country/region scope) so Y-axis is complete
    scope_b, scope_i, _ = filter_data(region=region, country=country, component=component, exclude_c19rm=exclude_c19rm)
    for _, row in scope_b[['Module Parent Component', 'Module']].drop_duplicates().iterrows():
        if row['Module'] not in b_agg['Module'].values:
            b_agg = pd.concat([b_agg, pd.DataFrame([{'Module Parent Component': row['Module Parent Component'],
                                                       'Module': row['Module'], 'Total Amount': 0}])],
                              ignore_index=True)
    b_agg = _inject_missing_modules(b_agg, scope_i, component)

    # Sort: component order → budget desc → Impact/Outcome at bottom
    b_agg['comp_sort'] = b_agg['Module Parent Component'].map(COMP_ORDER).fillna(7)
    b_agg['is_io'] = (b_agg['Module'].str.contains('(Impact/Outcome)', regex=False) |
                      b_agg['Module'].str.contains('(Outcome)', regex=False))
    b_agg = b_agg.sort_values(by=['comp_sort', 'Total Amount', 'is_io'],
                              ascending=[True, False, True])

    # Inject blank spacing rows between components
    new_rows = []
    current_comp = None
    space_counter = 1
    for _, row in b_agg.iterrows():
        comp = row['Module Parent Component']
        if current_comp is not None and comp != current_comp:
            new_rows.append({'Module Parent Component': 'Spacer',
                             'Module': " " * space_counter,
                             'Total Amount': 0,
                             'comp_sort': row['comp_sort'] - 0.5})
            space_counter += 1
        current_comp = comp
        new_rows.append(row.to_dict())
    b_agg = pd.DataFrame(new_rows)

    # Build subplots
    fig = make_subplots(
        rows=1, cols=3, shared_yaxes=True, horizontal_spacing=0.02,
        subplot_titles=("Budget ($M)", "Indicators Selected", "WPTM Count"),
        column_widths=[0.4, 0.3, 0.3]
    )

    y_vals = b_agg['Module'].tolist()
    module_to_pc = dict(zip(b_agg['Module'], b_agg['Module Parent Component']))

    # ── Chart 1: Budget ────────────────────────────────────────────────────
    colors = [COMP_COLORS.get(pc, '#7f7f7f') for pc in b_agg['Module Parent Component']]
    custom_data_b = []
    for y_m in y_vals:
        int_agg = b_filt[b_filt['Module'] == y_m].groupby(['Intervention', 'Source'], dropna=False)['Total Amount'].sum().reset_index()
        int_agg = int_agg.sort_values(by='Total Amount', ascending=False)
        if int_agg.empty or int_agg['Total Amount'].sum() == 0:
            custom_data_b.append([json.dumps({'type': 'BUDGET', 'data': []})])
        else:
            data = [{'Intervention': str(r['Intervention']),
                     'source': str(r['Source']) if str(r['Source']) != 'nan' else '',
                     'Amount': f"{r['Total Amount']/1e6:,.1f}"}
                    for _, r in int_agg.iterrows() if r['Total Amount'] > 0]
            custom_data_b.append([json.dumps({'type': 'BUDGET', 'data': data})])

    fig.add_trace(go.Bar(
        y=y_vals, x=b_agg['Total Amount'] / 1e6, orientation='h',
        marker_color=colors,
        text=b_agg['Total Amount'].apply(lambda x: f"{x/1e6:,.1f}" if x > 0 else ""),
        textfont=dict(size=14), textposition='outside',
        constraintext='none', cliponaxis=False, textangle=0,
        name='Budget', showlegend=False,
        customdata=custom_data_b, hoverinfo='none'
    ), row=1, col=1)

    # ── Chart 2: Indicators ───────────────────────────────────────────────
    tot_x_ind = [0] * len(y_vals)
    for ind_type in ['Coverage indicator', 'Outcome indicator', 'Impact indicator']:
        for is_custom in [False, True]:
            c19_loop = [False, True] if (not is_custom and ind_type == 'Coverage indicator') else [False]
            for is_c19 in c19_loop:
                if is_c19:
                    sub = i_filt[(i_filt['IndicatorType'] == ind_type) & (i_filt['IsCustom'] == is_custom) & (i_filt['Source'].astype(str).str.contains('C19RM', case=False, na=False))]
                else:
                    if len(c19_loop) == 2:
                        sub = i_filt[(i_filt['IndicatorType'] == ind_type) & (i_filt['IsCustom'] == is_custom) & (~i_filt['Source'].astype(str).str.contains('C19RM', case=False, na=False))]
                    else:
                        sub = i_filt[(i_filt['IndicatorType'] == ind_type) & (i_filt['IsCustom'] == is_custom)]
                
                counts, bar_colors, custom_data_i = [], [], []

                for i, y_m in enumerate(y_vals):
                    mod_sub = sub[sub['Module'] == y_m]
                    c = len(mod_sub)
                    counts.append(c)
                    tot_x_ind[i] += c

                    pc = module_to_pc.get(y_m, 'Other')
                    weight = TYPE_TO_WEIGHT.get(ind_type, 'medium')
                    if is_c19:
                        bar_colors.append(SHADES['RSSH'][weight])
                    else:
                        bar_colors.append(SHADES.get(pc, SHADES['Other'])[weight])

                    if c > 0:
                        mod_sub = mod_sub.copy()
                        mod_sub['__sort_code'] = mod_sub['IndicatorCode'].fillna(mod_sub['IndicatorCustomName'])
                        mod_sub['__sort_order'] = mod_sub['__sort_code'].map(indicator_order).fillna(99999)
                        mod_sub.sort_values(by=['__sort_order', '__sort_code', 'Implementation Period Name'], inplace=True)

                        if is_custom:
                            grouped = (mod_sub.groupby(['IndicatorCustomName', '__sort_order', '__sort_code', 'Source'], dropna=False)
                                       .size().reset_index(name='count'))
                            grouped.sort_values(by=['count', '__sort_order', '__sort_code'],
                                                ascending=[False, True, True], inplace=True)
                            data = [{'name': str(r['IndicatorCustomName']) if str(r['IndicatorCustomName']) != 'nan' else 'Unknown',
                                     'source': str(r['Source']) if str(r['Source']) != 'nan' else '',
                                     'count': int(r['count'])} for _, r in grouped.iterrows()]
                            custom_data_i.append([json.dumps({'type': 'INDICATOR_CUSTOM', 'title': f"{ind_type} (Custom)", 'data': data})])
                        else:
                            grouped = (mod_sub.groupby(['IndicatorCode', 'IndicatorDescription', '__sort_order', '__sort_code', 'Source'], dropna=False)
                                       .size().reset_index(name='count'))
                            grouped.sort_values(by=['count', '__sort_order', '__sort_code'],
                                                ascending=[False, True, True], inplace=True)
                            data = [{'code': '' if str(r['IndicatorCode']) == 'nan' else str(r['IndicatorCode']),
                                     'desc': '' if str(r['IndicatorDescription']) == 'nan' else str(r['IndicatorDescription']),
                                     'source': str(r['Source']) if str(r['Source']) != 'nan' else '',
                                     'count': int(r['count'])} for _, r in grouped.iterrows()]
                            custom_data_i.append([json.dumps({'type': 'INDICATOR_STANDARD', 'title': f"{ind_type} (Standard{' - C19RM' if is_c19 else ''})", 'data': data})])
                    else:
                        custom_data_i.append([json.dumps({'type': 'EMPTY'})])

                if sum(counts) > 0:
                    trace_args = dict(
                        y=y_vals, x=counts, orientation='h',
                        name=f"{ind_type} ({'Custom' if is_custom else 'Standard'}{' - C19RM' if is_c19 else ''})",
                        marker_color=bar_colors,
                        text=[str(c) if c > 0 else "" for c in counts],
                        textposition='inside', insidetextanchor='middle',
                        textangle=0, constraintext='none',
                        showlegend=False, customdata=custom_data_i, hoverinfo='none'
                    )
                    if is_custom:
                        trace_args['marker_color'] = "#ececec"
                        trace_args['marker_pattern_shape'] = "/"
                        trace_args['marker_pattern_size'] = 3
                        trace_args['marker_pattern_fgcolor'] = bar_colors
                    elif is_c19:
                        trace_args['marker_pattern_shape'] = "."
                        trace_args['marker_pattern_size'] = 3
                        trace_args['marker_pattern_fgcolor'] = "white"
                    fig.add_trace(go.Bar(**trace_args), row=1, col=2)

    # Indicator total labels
    fig.add_trace(go.Bar(
        x=[0] * len(y_vals), y=y_vals, base=tot_x_ind, orientation='h',
        marker_color='rgba(0,0,0,0)',
        text=[f" {c}" if c > 0 else "" for c in tot_x_ind],
        textfont=dict(size=14, color='black'), textposition='outside',
        constraintext='none', showlegend=False, hoverinfo='none', cliponaxis=False
    ), row=1, col=2)

    # Indicator legend (dummy traces)
    legend_component = component if component != 'ALL' else 'Other'
    dummy_y = [y_vals[0]] if y_vals else [None]
    for ind_type in ['Coverage indicator', 'Outcome indicator', 'Impact indicator']:
        for is_custom in [False, True]:
            weight = TYPE_TO_WEIGHT.get(ind_type, 'medium')
            col = SHADES.get(legend_component, SHADES['Other'])[weight]
            trace_args = dict(
                y=dummy_y, x=[None],
                name=f"{ind_type} ({'Custom' if is_custom else 'Standard'})",
                marker_color=col, showlegend=True, hoverinfo='none'
            )
            if is_custom:
                trace_args['marker_color'] = "#ececec"
                trace_args['marker_pattern_shape'] = "/"
                trace_args['marker_pattern_size'] = 3
                trace_args['marker_pattern_fgcolor'] = col
            fig.add_trace(go.Bar(**trace_args), row=1, col=2)

            if not is_custom and ind_type == 'Coverage indicator' and not exclude_c19rm:
                c19_col = SHADES['RSSH'][weight]
                fig.add_trace(go.Bar(
                    y=dummy_y, x=[None],
                    name='Coverage indicator (Standard - C19RM)',
                    marker_color=c19_col, marker_pattern_shape=".",
                    marker_pattern_size=3, marker_pattern_fgcolor="white",
                    showlegend=True, hoverinfo='none'
                ), row=1, col=2)

    # ── Chart 3: WPTM ─────────────────────────────────────────────────────
    wptm_counts, wptm_colors, custom_data_w = [], [], []
    for y_m in y_vals:
        mod_w = w_filt[w_filt['Module'] == y_m]
        c = len(mod_w)
        wptm_counts.append(c)
        pc = module_to_pc.get(y_m, 'Other')
        wptm_colors.append(SHADES.get(pc, SHADES['Other'])['medium'])

        if c > 0:
            data = []
            for _, row in mod_w.iterrows():
                ip_name = str(row.get('Implementation Period Name', ''))
                act = str(row.get('KeyActivity', ''))
                src = str(row.get('Source', ''))
                data.append({'ip': 'Unknown' if ip_name == 'nan' else ip_name,
                             'source': '' if src == 'nan' else src,
                             'act': '' if act == 'nan' else act})
            custom_data_w.append([json.dumps({'type': 'WPTM', 'data': data})])
        else:
            custom_data_w.append([json.dumps({'type': 'EMPTY'})])

    fig.add_trace(go.Bar(
        y=y_vals, x=wptm_counts, orientation='h',
        marker_color=wptm_colors,
        text=[str(c) if c > 0 else "" for c in wptm_counts],
        textfont=dict(size=14), textposition='outside',
        constraintext='none', cliponaxis=False, textangle=0,
        name='WPTM', showlegend=False,
        customdata=custom_data_w, hoverinfo='none'
    ), row=1, col=3)

    # ── Dynamic Legend Placement ───────────────────────────────────────────
    max_w = max(wptm_counts) if wptm_counts else 0
    max_i = i_filt.groupby('Module').size().max() if not i_filt.empty else 0
    overall_max = max(max_w, max_i if max_i else 0)
    max_x_axis = overall_max * 1.15

    leg_y, leg_x = 0.98, 0.98
    leg_yanchor, leg_xanchor = "top", "right"
    margin_r = 20
    if overall_max > 0:
        threshold = max_x_axis * 0.30
        if any(w > threshold for w in wptm_counts[:8]):
            leg_y, leg_x = 1.0, 1.02
            leg_yanchor, leg_xanchor = "top", "left"
            margin_r = 180

    # Dynamic height capped at 850px
    num_rows = max(1, len(y_vals))
    calculated_height = min(850, max(250, num_rows * 30 + 130))

    fig.update_layout(
        height=calculated_height,
        font_family="Arial",
        barmode='stack',
        bargap=0.3,
        margin=dict(l=450, r=margin_r, t=40, b=20),
        yaxis=dict(autorange="reversed", dtick=1, tickfont=dict(size=13)),
        legend=dict(
            title=dict(text="Indicator legend"),
            yanchor=leg_yanchor, y=leg_y,
            xanchor=leg_xanchor, x=leg_x,
            bgcolor="rgba(255, 255, 255, 0.8)"
        )
    )

    # Component icons
    icon_map = {'HIV/AIDS': 'HIV.png', 'Tuberculosis': 'TB.png',
                'Malaria': 'malaria.png', 'RSSH': 'RSSH.png'}
    comp_indices = {}
    for m in y_vals:
        comp = module_to_pc.get(m)
        if m.strip():
            comp_indices.setdefault(comp, []).append(m)

    for comp, fn in icon_map.items():
        mods = comp_indices.get(comp, [])
        if mods:
            fig.add_layout_image(dict(
                source=app.get_asset_url(fn),
                xref="paper", yref="y",
                x=-0.35, y=mods[len(mods) // 2],
                sizex=0.05, sizey=3,
                xanchor="right", yanchor="middle",
                sizing="contain"
            ))

    fig.update_xaxes(matches='x2', row=1, col=3)

    # Axis padding
    if not b_agg.empty and b_agg['Total Amount'].max() > 0:
        fig.update_xaxes(range=[0, b_agg['Total Amount'].max() / 1e6 * 1.15], row=1, col=1)
    if overall_max > 0:
        fig.update_xaxes(range=[0, max_x_axis], row=1, col=2)

    return fig, {'height': f"{calculated_height}px", 'transition': 'height 0.4s ease-out'}
