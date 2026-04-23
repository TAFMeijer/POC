import json
import urllib.parse
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_processing import (
    df_b, df_i, df_w, COMP_COLORS, SHADES, TYPE_TO_WEIGHT,
    country_to_region, country_to_shortname, filter_data, reassign_tb_hiv,
)

# ──────────────────────────────────────────────────────────────────────────────
# Shared helpers used by both merged and unmerged overview charts
# ──────────────────────────────────────────────────────────────────────────────

def _prepare_overview_data(region, inc_custom, exclude_pm, sort_budget):
    """Filter data, compute country totals, and return everything both chart
    variants need.  Returns (target_countries, b_filt, i_filt, w_filt,
    country_totals_b, country_totals_i, country_totals_w)."""

    all_countries = sorted(df_b['Country'].dropna().unique())
    if not region or region == 'ALL':
        target_countries = all_countries
    else:
        target_countries = [c for c in all_countries if country_to_region.get(c) == region]

    if not target_countries:
        return None, None, None, None, None, None, None

    b_filt, i_filt, _ = filter_data(region=region)
    # Re-filter to match target_countries exactly (filter_data is region-level)
    b_filt = b_filt[b_filt['Country'].isin(target_countries)].copy()
    i_filt = i_filt[i_filt['Country'].isin(target_countries)].copy()
    w_filt = df_w[df_w['Country'].isin(target_countries)].copy()

    i_filt = reassign_tb_hiv(b_filt, i_filt, target_countries)

    if not inc_custom:
        i_filt = i_filt[~i_filt['IsCustom']]
        w_filt = w_filt.iloc[0:0]

    if exclude_pm:
        excl = ['Program Management', 'Payment for Results']
        b_filt = b_filt[~b_filt['Module Parent Component'].isin(excl)]
        i_filt = i_filt[~i_filt['Module Parent Component'].isin(excl)]
        w_filt = w_filt[~w_filt['Module Parent Component'].isin(excl)]

    totals_b = b_filt.groupby('Country')['Total Amount'].sum().to_dict()
    totals_i = i_filt.groupby('Country').size().to_dict()
    totals_w = w_filt.groupby('Country').size().to_dict()
    # Ensure every target country has an entry (even if 0)
    for c in target_countries:
        totals_b.setdefault(c, 0)
        totals_i.setdefault(c, 0)
        totals_w.setdefault(c, 0)

    if sort_budget:
        target_countries = sorted(target_countries, key=lambda c: totals_b[c], reverse=True)

    return target_countries, b_filt, i_filt, w_filt, totals_b, totals_i, totals_w


def _build_y_labels(target_countries):
    """Build URL-encoded y-axis labels and a parallel raw-country list."""
    y_labels, raw = [], []
    for c in target_countries:
        raw.append(c)
        short = country_to_shortname.get(c, c)
        encoded = urllib.parse.quote(c)
        y_labels.append(f"<a href='/budget-pf-poc/detailed?country={encoded}'>{short}</a>")
    return y_labels, raw


def _add_total_label_trace(fig, y_vals, base_vals, is_percent, col, row=1, is_currency=False):
    """Add a transparent bar that renders the total label outside the stack."""
    text = []
    for v in base_vals:
        if v > 0:
            if is_percent:
                text.append(f" {v:.0f}%")
            elif is_currency:
                text.append(f" {v:,.1f}")
            else:
                text.append(f" {int(v)}")
        else:
            text.append("")
    fig.add_trace(go.Bar(
        y=y_vals, x=[0] * len(y_vals), base=base_vals, orientation='h',
        marker_color='rgba(0,0,0,0)', text=text,
        textfont=dict(size=14, color='black'),
        textposition='outside', constraintext='none',
        showlegend=False, hoverinfo='none', cliponaxis=False
    ), row=1, col=col)


def _make_subplot_fig(inc_custom, budget_title):
    """Create the subplot figure (2 or 3 columns)."""
    if inc_custom:
        return make_subplots(
            rows=1, cols=3, shared_yaxes=True, horizontal_spacing=0.02,
            subplot_titles=(budget_title, "Indicators Selected", "WPTM Count"),
            column_widths=[0.4, 0.3, 0.3])
    return make_subplots(
        rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.02,
        subplot_titles=(budget_title, "Standard Indicators Selected"),
        column_widths=[0.5, 0.5])


def _finalize_layout(fig, y_vals, calculated_height, inc_custom, legend_title,
                     margin_r=20, leg_y=0.98, leg_x=0.98,
                     leg_yanchor='top', leg_xanchor='right'):
    """Apply shared layout settings."""
    fig.update_layout(
        height=calculated_height,
        font_family="Arial",
        barmode='stack',
        bargap=0.3,
        margin=dict(l=150, r=margin_r, t=70, b=20),
        yaxis=dict(range=[len(y_vals) - 0.5, -0.75], tickfont=dict(size=12)),
        legend=dict(
            title=dict(text=legend_title),
            yanchor=leg_yanchor, y=leg_y,
            xanchor=leg_xanchor, x=leg_x,
            bgcolor="rgba(255, 255, 255, 0.8)",
            traceorder="normal"
        )
    )


def _apply_axis_padding(fig, is_percent, totals_b, totals_i, inc_custom,
                        max_budget_val=None):
    """Apply consistent axis range padding across all subplot columns."""
    if is_percent:
        fig.update_xaxes(range=[0, 105], row=1, col=1)
        fig.update_xaxes(range=[0, 105], row=1, col=2)
        if inc_custom:
            fig.update_xaxes(range=[0, 105], row=1, col=3)
    else:
        max_b = (max_budget_val or (max(totals_b.values()) / 1e6 if totals_b else 0))
        if max_b > 0:
            fig.update_xaxes(range=[0, max_b * 1.15], row=1, col=1)
        max_i = max(totals_i.values()) if totals_i else 0
        if max_i > 0:
            fig.update_xaxes(range=[0, max_i * 1.15], row=1, col=2)
            if inc_custom:
                fig.update_xaxes(range=[0, max_i * 1.15], row=1, col=3)

    if inc_custom:
        fig.update_xaxes(matches='x2', row=1, col=3)


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────────

def build_overview_chart(app, region, inc_custom=False, is_percent=False,
                         is_merged=False, exclude_pm=False, sort_budget=False):
    if is_merged:
        return build_merged_chart(app, region, inc_custom, is_percent, exclude_pm, sort_budget)
    return build_unmerged_chart(app, region, inc_custom, is_percent, exclude_pm, sort_budget)


# ──────────────────────────────────────────────────────────────────────────────
# Merged chart (one row per country)
# ──────────────────────────────────────────────────────────────────────────────

def build_merged_chart(app, region, inc_custom=False, is_percent=False,
                       exclude_pm=False, sort_budget=False):
    result = _prepare_overview_data(region, inc_custom, exclude_pm, sort_budget)
    target_countries, b_filt, i_filt, w_filt, totals_b, totals_i, totals_w = result
    if target_countries is None:
        return go.Figure(), {'height': '850px'}

    y_countries, raw_countries = _build_y_labels(target_countries)
    budget_title = "Total Budget (%)" if is_percent else "Total Budget ($M)"
    fig = _make_subplot_fig(inc_custom, budget_title)

    x_comps = ['HIV/AIDS', 'Tuberculosis', 'Malaria', 'RSSH']
    if not exclude_pm:
        x_comps += ['Program Management', 'Payment for Results']

    # --- CHART 1: Budget ---
    tot_b_x = [0.0] * len(target_countries)
    for pc in x_comps:
        x_b, text_b, hover_b = [], [], []
        for i, c in enumerate(target_countries):
            b_val = b_filt[(b_filt['Country'] == c) & (b_filt['Module Parent Component'] == pc)]['Total Amount'].sum()
            tot = totals_b[c]
            c_short = country_to_shortname.get(c, c)

            if is_percent:
                pct = (b_val / tot * 100) if tot > 0 else 0
                x_b.append(pct)
                tot_b_x[i] += pct
                if b_val > 0:
                    hover_b.append(f"<b>{c_short}</b><br>{pc}<br>Budget: {pct:.0f}% (${b_val/1e6:,.1f}M)")
                    text_b.append(f"{pct:.0f}%" if pct >= 6 else "")
                else:
                    hover_b.append("")
                    text_b.append("")
            else:
                x_b.append(b_val / 1e6)
                if b_val > 0:
                    hover_b.append(f"<b>{c_short}</b><br>{pc}<br>Budget: ${b_val/1e6:,.1f}M")
                    text_b.append(f"{b_val/1e6:,.1f}" if b_val >= 1e6 else "")
                else:
                    hover_b.append("")
                    text_b.append("")

        marker_color = COMP_COLORS.get(pc, '#000000')
        if pc == 'Payment for Results':
            marker_color = '#8c564b'

        fig.add_trace(go.Bar(
            y=y_countries, x=x_b, orientation='h',
            marker_color=marker_color,
            text=text_b,
            textposition='inside', insidetextanchor='middle',
            constraintext='none', cliponaxis=False,
            name=pc, showlegend=True, hoverinfo='text', hovertext=hover_b
        ), row=1, col=1)

    # Total label (absolute mode only)
    if not is_percent:
        base = [totals_b[c] / 1e6 for c in target_countries]
        _add_total_label_trace(fig, y_countries, base, False, col=1, is_currency=True)

    # --- CHART 2: Indicators ---
    tot_x_ind = [0.0] * len(target_countries)
    custom_loop = [False, True] if inc_custom else [False]
    for pc in x_comps:
        base_col = SHADES.get(pc, SHADES['Other'])
        col = base_col['medium']
        for is_custom in custom_loop:
            x_ind, text_ind, hover_ind = [], [], []
            for i, c in enumerate(target_countries):
                count = len(i_filt[(i_filt['Country'] == c) & (i_filt['Module Parent Component'] == pc) & (i_filt['IsCustom'] == is_custom)])
                tot = totals_i[c]
                if is_percent:
                    pct = (count / tot * 100) if tot > 0 else 0
                    x_ind.append(pct)
                    tot_x_ind[i] += pct
                    text_ind.append(f"{pct:.0f}%" if count > 0 and pct >= 6 else "")
                    hover_ind.append(f"{pct:.0f}% ({count})" if count > 0 else "")
                else:
                    x_ind.append(count)
                    tot_x_ind[i] += count
                    text_ind.append(str(count) if count > 0 else "")
                    hover_ind.append(str(count) if count > 0 else "")

            if sum(x_ind) > 0:
                fig.add_trace(go.Bar(
                    y=y_countries, x=x_ind, orientation='h',
                    marker_color=col,
                    marker_pattern_shape="/" if is_custom else "",
                    text=text_ind, textposition='inside', insidetextanchor='middle',
                    constraintext='none', cliponaxis=False,
                    name=pc, showlegend=False,
                    hoverinfo='text', hovertext=hover_ind
                ), row=1, col=2)

    if not is_percent:
        _add_total_label_trace(fig, y_countries, tot_x_ind, False, col=2)

    # --- CHART 3: WPTM (only when inc_custom) ---
    if inc_custom:
        tot_x_wptm = [0.0] * len(target_countries)
        for pc in x_comps:
            base_col = SHADES.get(pc, SHADES['Other'])
            col = base_col['medium']
            x_wptm, text_w, hover_w = [], [], []
            for i, c in enumerate(target_countries):
                w = len(w_filt[(w_filt['Country'] == c) & (w_filt['Module Parent Component'] == pc)])
                tot = totals_w[c]
                c_short = country_to_shortname.get(c, c)
                if is_percent:
                    pct = (w / tot * 100) if tot > 0 else 0
                    x_wptm.append(pct)
                    tot_x_wptm[i] += pct
                    hover_w.append(f"<b>{c_short}</b><br>{pc}<br>WPTM Count: {pct:.0f}% ({w})")
                    text_w.append(f"{pct:.0f}%" if pct >= 6 else "")
                else:
                    x_wptm.append(w)
                    tot_x_wptm[i] += w
                    hover_w.append(f"<b>{c_short}</b><br>{pc}<br>WPTM Count: {w}")
                    text_w.append(str(w) if w > 0 else "")

            if sum(x_wptm) > 0:
                fig.add_trace(go.Bar(
                    y=y_countries, x=x_wptm, orientation='h',
                    marker_color=col, text=text_w,
                    textposition='inside', insidetextanchor='middle',
                    constraintext='none', cliponaxis=False,
                    showlegend=False, hoverinfo='text', hovertext=hover_w
                ), row=1, col=3)

        if not is_percent:
            _add_total_label_trace(fig, y_countries, tot_x_wptm, False, col=3)

    # --- Layout ---
    margin_r = 180 if inc_custom else 20
    calculated_height = max(800, len(target_countries) * 55 + 100)

    for trace in fig.data:
        if trace.customdata is None:
            trace.customdata = raw_countries

    _finalize_layout(fig, y_countries, calculated_height, inc_custom,
                     "Budget Components", margin_r=margin_r,
                     leg_y=1.0, leg_x=1.02, leg_yanchor='top', leg_xanchor='left')
    _apply_axis_padding(fig, is_percent, totals_b, totals_i, inc_custom)

    return fig, {'height': f"{calculated_height}px", 'transition': 'height 0.4s ease-out'}


# ──────────────────────────────────────────────────────────────────────────────
# Unmerged chart (one row per country × component)
# ──────────────────────────────────────────────────────────────────────────────

def build_unmerged_chart(app, region, inc_custom=False, is_percent=False,
                         exclude_pm=False, sort_budget=False):
    result = _prepare_overview_data(region, inc_custom, exclude_pm, sort_budget)
    target_countries, b_filt, i_filt, w_filt, totals_b, totals_i, totals_w = result
    if target_countries is None:
        return go.Figure(), {'height': '850px'}

    components = ['HIV/AIDS', 'Tuberculosis', 'Malaria', 'RSSH']
    if not exclude_pm:
        components.append('Other (PM/PfR)')
    num_comps = len(components)

    # Build multi-category y-axis
    y_countries, y_comps = [], []
    colors_main, budget_main = [], []
    colors_pfr, budget_pfr = [], []
    wptm_counts = []

    for c in target_countries:
        c_short = country_to_shortname.get(c, c)
        c_encoded = urllib.parse.quote(c)
        c_link = f"<a href='/budget-pf-poc/detailed?country={c_encoded}'>{c_short}</a>"
        for pc in components:
            y_countries.append(c_link)
            y_comps.append(pc)

            if pc == 'Other (PM/PfR)':
                b_pm = b_filt[(b_filt['Country'] == c) & (b_filt['Module Parent Component'] == 'Program Management')]['Total Amount'].sum()
                b_pfr_val = b_filt[(b_filt['Country'] == c) & (b_filt['Module Parent Component'] == 'Payment for Results')]['Total Amount'].sum()
                budget_main.append(b_pm)
                budget_pfr.append(b_pfr_val)
                colors_main.append(COMP_COLORS.get('Program Management', '#000000'))
                colors_pfr.append(COMP_COLORS.get('Payment for Results', '#8c564b'))
                w_pm = len(w_filt[(w_filt['Country'] == c) & (w_filt['Module Parent Component'] == 'Program Management')])
                w_pfr_val = len(w_filt[(w_filt['Country'] == c) & (w_filt['Module Parent Component'] == 'Payment for Results')])
                wptm_counts.append(w_pm + w_pfr_val)
            else:
                b_val = b_filt[(b_filt['Country'] == c) & (b_filt['Module Parent Component'] == pc)]['Total Amount'].sum()
                budget_main.append(b_val)
                budget_pfr.append(0)
                colors_main.append(COMP_COLORS.get(pc, '#7f7f7f'))
                colors_pfr.append('rgba(0,0,0,0)')
                w_val = len(w_filt[(w_filt['Country'] == c) & (w_filt['Module Parent Component'] == pc)])
                wptm_counts.append(w_val)

    multi_y = [y_countries, y_comps]
    budget_title = "Total Budget (%)" if is_percent else "Total Budget ($M)"
    fig = _make_subplot_fig(inc_custom, budget_title)

    # --- CHART 1: Budget ---
    def _budget_trace_data(b_sums, is_pfr=False):
        x_out, hover_out, text_out, text_pos, text_col = [], [], [], [], []
        for i, b in enumerate(b_sums):
            raw_c = target_countries[i // num_comps]
            pc_name = y_comps[i]
            if pc_name == 'Other (PM/PfR)':
                actual_pc = 'Payment for Results' if is_pfr else 'Program Management'
                t_pos, t_col_val = 'inside', 'white'
            else:
                actual_pc = pc_name
                t_pos, t_col_val = 'outside', 'black'

            c_short = y_countries[i]
            tot = totals_b[raw_c]

            if is_percent:
                pct = (b / tot * 100) if tot > 0 else 0
                x_out.append(pct)
                if b > 0:
                    hover_out.append(f"<b>{c_short}</b><br>{actual_pc}<br>Budget: {pct:.0f}% (${b/1e6:,.1f}M)")
                    text_out.append(f"{pct:.0f}%" if not (pc_name == 'Other (PM/PfR)' and pct < 2) else "")
                else:
                    hover_out.append("")
                    text_out.append("")
            else:
                x_out.append(b / 1e6)
                if b > 0:
                    hover_out.append(f"<b>{c_short}</b><br>{actual_pc}<br>Budget: ${b/1e6:,.1f}M")
                    text_out.append(f"{b/1e6:,.1f}" if not (pc_name == 'Other (PM/PfR)' and b < 1e6) else "")
                else:
                    hover_out.append("")
                    text_out.append("")
            text_pos.append(t_pos)
            text_col.append(t_col_val)
        return x_out, hover_out, text_out, text_pos, text_col

    x_bm, h_bm, t_bm, p_bm, c_bm = _budget_trace_data(budget_main, False)
    x_bp, h_bp, t_bp, p_bp, c_bp = _budget_trace_data(budget_pfr, True)

    fig.add_trace(go.Bar(
        y=multi_y, x=x_bm, orientation='h',
        marker_color=colors_main, text=t_bm,
        textfont=dict(size=14, color=c_bm), textposition=p_bm,
        insidetextanchor='middle', constraintext='none', cliponaxis=False,
        hoverinfo='text', hovertext=h_bm,
        name='Budget (Main/PM)', showlegend=False,
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        y=multi_y, x=x_bp, orientation='h',
        marker_color=colors_pfr, text=t_bp,
        textfont=dict(size=14, color=c_bp), textposition=p_bp,
        insidetextanchor='middle', constraintext='none', cliponaxis=False,
        hoverinfo='text', hovertext=h_bp,
        name='Budget (PfR)', showlegend=False,
    ), row=1, col=1)

    # Budget total labels for PM/PfR combined rows
    base_b_total = [0.0] * len(y_comps)
    text_b_total = [""] * len(y_comps)
    for i, pc in enumerate(y_comps):
        if pc == 'Other (PM/PfR)':
            tot_b_row = budget_main[i] + budget_pfr[i]
            if is_percent:
                raw_c = target_countries[i // num_comps]
                t_tot = totals_b[raw_c]
                pct = (tot_b_row / t_tot * 100) if t_tot > 0 else 0
                base_b_total[i] = pct
                text_b_total[i] = f" {pct:.0f}%" if pct > 0 else ""
            else:
                base_b_total[i] = tot_b_row / 1e6
                text_b_total[i] = f" {tot_b_row/1e6:,.1f}" if tot_b_row > 0 else ""

    fig.add_trace(go.Bar(
        x=[0] * len(multi_y[0]), y=multi_y, base=base_b_total, orientation='h',
        marker_color='rgba(0,0,0,0)', text=text_b_total,
        textfont=dict(size=14, color='black'), textposition='outside',
        constraintext='none', showlegend=False, hoverinfo='none', cliponaxis=False
    ), row=1, col=1)

    # --- CHART 2: Indicators ---
    tot_x_ind = [0.0] * len(y_comps)
    custom_loop = [False, True] if inc_custom else [False]
    for ind_type in ['Coverage indicator', 'Outcome indicator', 'Impact indicator']:
        for is_custom in custom_loop:
            weight = TYPE_TO_WEIGHT.get(ind_type, 'medium')
            counts, bar_colors = [], []
            sub = i_filt[(i_filt['IndicatorType'] == ind_type) & (i_filt['IsCustom'] == is_custom)]

            for i, pc in enumerate(y_comps):
                raw_c = target_countries[i // num_comps]
                if pc == 'Other (PM/PfR)':
                    c_val = len(sub[(sub['Country'] == raw_c) & (sub['Module Parent Component'].isin(['Program Management', 'Payment for Results']))])
                    col = SHADES.get('Program Management', SHADES['Other'])[weight]
                else:
                    c_val = len(sub[(sub['Country'] == raw_c) & (sub['Module Parent Component'] == pc)])
                    col = SHADES.get(pc, SHADES['Other'])[weight]
                counts.append(c_val)
                bar_colors.append(col)

            if sum(counts) > 0:
                x_ind, text_ind, hover_ind = [], [], []
                for i, count in enumerate(counts):
                    raw_c = target_countries[i // num_comps]
                    tot = totals_i[raw_c]
                    if is_percent:
                        pct = (count / tot * 100) if tot > 0 else 0
                        x_ind.append(pct)
                        tot_x_ind[i] += pct
                        text_ind.append(f"{pct:.0f}%" if count > 0 and (not inc_custom or pct >= 6) else "")
                        hover_ind.append(f"{pct:.0f}% ({count})" if count > 0 else "")
                    else:
                        x_ind.append(count)
                        tot_x_ind[i] += count
                        text_ind.append(str(count) if count > 0 else "")
                        hover_ind.append(str(count) if count > 0 else "")

                trace_args = dict(
                    y=multi_y, x=x_ind, orientation='h',
                    name=f"{ind_type} ({'Custom' if is_custom else 'Standard'})",
                    marker_color=bar_colors,
                    text=text_ind, textposition='inside', insidetextanchor='middle',
                    textangle=0, constraintext='none',
                    hovertext=hover_ind, hoverinfo='name+text', showlegend=False
                )
                if is_custom:
                    trace_args['marker_color'] = "#ececec"
                    trace_args['marker_pattern_shape'] = "/"
                    trace_args['marker_pattern_size'] = 3
                    trace_args['marker_pattern_fgcolor'] = bar_colors
                fig.add_trace(go.Bar(**trace_args), row=1, col=2)

    # Indicator total labels
    ind_total_text = [
        f" {val:.0f}%" if (is_percent and val > 0) else (f" {int(val)}" if val > 0 else "")
        for val in tot_x_ind
    ]
    fig.add_trace(go.Bar(
        x=[0] * len(y_comps), y=multi_y, base=tot_x_ind, orientation='h',
        marker_color='rgba(0,0,0,0)', text=ind_total_text,
        textfont=dict(size=14, color='black'), textposition='outside',
        constraintext='none', showlegend=False, hoverinfo='none', cliponaxis=False
    ), row=1, col=2)

    # Indicator legend (dummy traces)
    for ind_type in ['Coverage indicator', 'Outcome indicator', 'Impact indicator']:
        for is_custom in custom_loop:
            weight = TYPE_TO_WEIGHT.get(ind_type, 'medium')
            col = SHADES.get('HIV/AIDS', SHADES['Other'])[weight]
            trace_args = dict(
                y=[None], x=[None],
                name=f"{ind_type} ({'Custom' if is_custom else 'Standard'})",
                marker_color=col, showlegend=True, hoverinfo='none'
            )
            if is_custom:
                trace_args['marker_color'] = "#ececec"
                trace_args['marker_pattern_shape'] = "/"
                trace_args['marker_pattern_size'] = 3
                trace_args['marker_pattern_fgcolor'] = col
            fig.add_trace(go.Bar(**trace_args), row=1, col=2)

    # --- CHART 3: WPTM ---
    if inc_custom:
        wptm_colors, hover_w, x_wptm, text_w = [], [], [], []
        for i, w in enumerate(wptm_counts):
            raw_c = target_countries[i // num_comps]
            pc = y_comps[i]
            c_short = y_countries[i]
            shade_key = 'Program Management' if pc == 'Other (PM/PfR)' else pc
            col = SHADES.get(shade_key, SHADES['Other'])['medium']
            wptm_colors.append(col)

            tot = totals_w[raw_c]
            if is_percent:
                pct = (w / tot * 100) if tot > 0 else 0
                x_wptm.append(pct)
                hover_w.append(f"<b>{c_short}</b><br>{pc}<br>WPTM Count: {pct:.0f}% ({w})")
                text_w.append(f"{pct:.0f}%" if pct >= 6 else "")
            else:
                x_wptm.append(w)
                hover_w.append(f"<b>{c_short}</b><br>{pc}<br>WPTM Count: {w}")
                text_w.append(str(w) if w > 0 else "")

        fig.add_trace(go.Bar(
            y=multi_y, x=x_wptm, orientation='h',
            marker_color=wptm_colors, text=text_w,
            textposition='outside',
            hoverinfo='text', hovertext=hover_w,
            name='WPTM', showlegend=False,
        ), row=1, col=3)

    # --- Legend collision detection ---
    max_w = max(wptm_counts) if wptm_counts else 0
    max_i = 0
    if not i_filt.empty:
        mod_counts = i_filt.groupby(['Country', 'Module Parent Component']).size()
        if not mod_counts.empty:
            max_i = mod_counts.max()
    overall_max = max(max_w, max_i)
    max_x_axis = 105.0 if is_percent else overall_max * 1.15

    leg_y, leg_x = 0.98, 0.98
    leg_yanchor, leg_xanchor = "top", "right"
    margin_r = 20
    if overall_max > 0 and inc_custom and wptm_counts:
        threshold = max_x_axis * 0.30
        top_overlap = any(
            (wptm_counts[i] / totals_w[target_countries[i // num_comps]] * 100
             if is_percent and totals_w[target_countries[i // num_comps]] > 0
             else wptm_counts[i]) > threshold
            for i in range(min(8, len(wptm_counts)))
        )
        if top_overlap:
            leg_y, leg_x = 1.0, 1.02
            leg_yanchor, leg_xanchor = "top", "left"
            margin_r = 180

    calculated_height = max(800, len(y_countries) * 28 + 100)

    # Inject raw country names for click navigation
    raw_mapped = [target_countries[i // num_comps] for i in range(len(y_countries))]
    for trace in fig.data:
        if trace.customdata is None:
            trace.customdata = raw_mapped

    _finalize_layout(fig, y_countries, calculated_height, inc_custom,
                     "Indicator legend", margin_r=margin_r,
                     leg_y=leg_y, leg_x=leg_x,
                     leg_yanchor=leg_yanchor, leg_xanchor=leg_xanchor)

    # PM/PfR annotation
    if not exclude_pm:
        fig.add_annotation(
            row=1, col=1, x=0.98, y=0.02,
            xref='x domain', yref='y domain',
            text="<span style='color:black;'>■</span> Prog. Mngt. <span style='color:#8c564b;'>■</span> PfR",
            showarrow=False, xanchor='right', yanchor='bottom',
            font=dict(size=11, color='#333'),
            bgcolor='rgba(255,255,255,0.8)', borderpad=4,
            borderwidth=1, bordercolor='#ddd'
        )

    # Country separator lines
    for i in range(1, len(target_countries)):
        fig.add_hline(y=i * num_comps - 0.5, line_width=1, line_color='black', layer='below')

    # Axis padding
    max_budget_val = None
    if not is_percent and budget_main:
        max_budget_val = max(b + p for b, p in zip(budget_main, budget_pfr)) / 1e6
    _apply_axis_padding(fig, is_percent, totals_b, totals_i, inc_custom,
                        max_budget_val=max_budget_val)

    return fig, {'height': f"{calculated_height}px", 'transition': 'height 0.4s ease-out'}
