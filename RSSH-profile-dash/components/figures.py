import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from data.dummy_data import *

C_NIG = '#1a8f4c'
C_NIG_L = '#a2d6b3'
C_MED = '#999'  # Update text/counts for peer lines
C_MED_L = '#e5e5e5'
C_BG = '#fcfcfc'
font_fmt = dict(size=9, color='#666')

def layout_defaults():
    return dict(
        margin=dict(l=20, r=20, t=10, b=20),
        plot_bgcolor=C_BG,
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        font=font_fmt
    )

def fig_dtp3(iso3="NGA", country_name="Nigeria"):
    df = get_dtp3_data(iso3)
    eq_data = get_dtp3_equity_data(iso3)
    peer_lines = get_dtp3_peer_lines(iso3)
    
    # Filter for 2010+
    if not df.empty and 'Year' in df.columns:
        df = df[df['Year'] >= 2010]
        
    if not peer_lines.empty and 'Year' in peer_lines.columns:
        peer_lines = peer_lines[peer_lines['Year'] >= 2010]
        
    fig = make_subplots(rows=1, cols=2, column_widths=[0.85, 0.15], horizontal_spacing=0.08)
    
    if df.empty:
        return fig
        
    ht = 'year: %{x}<br>value: %{y:.1f}%<extra></extra>'
    
    if not peer_lines.empty:
        for code in peer_lines['ISO3'].unique():
            if code != iso3:
                p_df = peer_lines[peer_lines['ISO3'] == code]
                fig.add_trace(go.Scatter(x=p_df['Year'], y=p_df['COVERAGE'], mode='lines', line=dict(color='rgba(200,200,200,0.5)', width=1), showlegend=False, connectgaps=True, hoverinfo='skip'), row=1, col=1)
                
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Country'], customdata=df.get('Count', pd.Series(dtype=float)), mode='lines+markers', marker=dict(color=C_NIG, size=4), line=dict(color=C_NIG, width=2), showlegend=False, connectgaps=True, hovertemplate=ht), row=1, col=1)
    
    if eq_data:
        q1, q5 = eq_data['Q1'], eq_data['Q5']
        
        fig.add_trace(go.Scatter(x=['Spread', 'Spread'], y=[q1, q5], mode='lines', line=dict(color='#ccc', width=2), showlegend=False, hoverinfo='skip'), row=1, col=2)
        fig.add_trace(go.Scatter(x=['Spread'], y=[q1], mode='markers', marker=dict(color='#d9534f', size=6), showlegend=False, hovertemplate=f'Q1: {q1:.1f}%<extra></extra>'), row=1, col=2)
        fig.add_trace(go.Scatter(x=['Spread'], y=[q5], mode='markers', marker=dict(color='#5cb85c', size=6), showlegend=False, hovertemplate=f'Q5: {q5:.1f}%<extra></extra>'), row=1, col=2)
        
        # Shift annotations to sit nicely next to the vertical line without clamping to axis extremes
        fig.add_annotation(x=0.5, y=-0.03, text=f"{eq_data['year']} ({eq_data['source']})", showarrow=False, xref='x2', yref='paper', yanchor='top', font=dict(size=8, color='#000'), xanchor='center')
        fig.add_annotation(x=1.3, y=q1, text=f"{q1:.0f}%", showarrow=False, xref='x2', yref='y2', font=dict(size=8, color='#d9534f'), xanchor='left')
        fig.add_annotation(x=1.3, y=q5, text=f"{q5:.0f}%", showarrow=False, xref='x2', yref='y2', font=dict(size=8, color='#5cb85c'), xanchor='left')
        fig.add_annotation(x=0.5, y=-0.17, text="Lowest income<br>vs. highest<br>income quartile", showarrow=False, xref='x2', yref='paper', yanchor='top', font=dict(size=8, color='#666'), xanchor='center')

    year_max = df['Year'].max() if not df.empty else 2024
    xaxis_ticks = list(range(2010, int(year_max) + 1))
    
    lyt = layout_defaults()
    lyt['margin'] = dict(l=30, r=10, t=10, b=45)
    fig.update_layout(
        **lyt, 
        xaxis=dict(range=[2010, year_max], gridcolor='#fff', tickvals=xaxis_ticks, tickangle=-45), 
        yaxis=dict(range=[0, 100], tickvals=[20, 40, 60, 80, 100], ticktext=['20%', '40%', '60%', '80%', '100%'], gridcolor='#fff'),
        xaxis2=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis2=dict(range=[0, 100], showticklabels=False, showgrid=False, zeroline=False)
    )
    return fig

def fig_anc4(iso3="NGA", country_name="Nigeria"):
    df = get_anc4_data(iso3)
    eq_data = get_anc4_equity_data(iso3)
    peer_lines = get_anc4_peer_lines(iso3)
    
    # Filter for 2010+
    if not df.empty and 'Year' in df.columns:
        df = df[df['Year'] >= 2010]
        
    if not peer_lines.empty and 'Year' in peer_lines.columns:
        peer_lines = peer_lines[peer_lines['Year'] >= 2010]
        
    fig = make_subplots(rows=1, cols=2, column_widths=[0.85, 0.15], horizontal_spacing=0.08)
    
    if df.empty:
        return fig
        
    ht = 'year: %{x}<br>value: %{y:.1f}%<extra></extra>'
    
    if not peer_lines.empty:
        for code in peer_lines['ISO3'].unique():
            if code != iso3:
                p_df = peer_lines[peer_lines['ISO3'] == code]
                fig.add_trace(go.Scatter(x=p_df['Year'], y=p_df['COVERAGE'], mode='lines', line=dict(color='rgba(200,200,200,0.5)', width=1), showlegend=False, connectgaps=True, hoverinfo='skip'), row=1, col=1)
                
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Country'], customdata=df.get('Count', pd.Series(dtype=float)), mode='lines+markers', marker=dict(color=C_NIG, size=4), line=dict(color=C_NIG, width=2), showlegend=False, connectgaps=True, hovertemplate=ht), row=1, col=1)
    
    if eq_data:
        q1, q5 = eq_data['Q1'], eq_data['Q5']
        
        fig.add_trace(go.Scatter(x=['Spread', 'Spread'], y=[q1, q5], mode='lines', line=dict(color='#ccc', width=2), showlegend=False, hoverinfo='skip'), row=1, col=2)
        fig.add_trace(go.Scatter(x=['Spread'], y=[q1], mode='markers', marker=dict(color='#d9534f', size=6), showlegend=False, hovertemplate=f'Q1: {q1:.1f}%<extra></extra>'), row=1, col=2)
        fig.add_trace(go.Scatter(x=['Spread'], y=[q5], mode='markers', marker=dict(color='#5cb85c', size=6), showlegend=False, hovertemplate=f'Q5: {q5:.1f}%<extra></extra>'), row=1, col=2)
        
        fig.add_annotation(x=0.5, y=-0.03, text=f"{eq_data['year']} ({eq_data['source']})", showarrow=False, xref='x2', yref='paper', yanchor='top', font=dict(size=8, color='#000'), xanchor='center')
        fig.add_annotation(x=1.3, y=q1, text=f"{q1:.0f}%", showarrow=False, xref='x2', yref='y2', font=dict(size=8, color='#d9534f'), xanchor='left')
        fig.add_annotation(x=1.3, y=q5, text=f"{q5:.0f}%", showarrow=False, xref='x2', yref='y2', font=dict(size=8, color='#5cb85c'), xanchor='left')
        fig.add_annotation(x=0.5, y=-0.17, text="Lowest income<br>vs. highest<br>income quartile", showarrow=False, xref='x2', yref='paper', yanchor='top', font=dict(size=8, color='#666'), xanchor='center')

    year_max = df['Year'].max() if not df.empty else 2024
    xaxis_ticks = list(range(2010, int(year_max) + 1))
    
    lyt = layout_defaults()
    lyt['margin'] = dict(l=30, r=10, t=10, b=45)
    fig.update_layout(
        **lyt, 
        xaxis=dict(range=[2010, year_max], gridcolor='#fff', tickvals=xaxis_ticks, tickangle=-45), 
        yaxis=dict(range=[0, 100], tickvals=[20, 40, 60, 80, 100], ticktext=['20%', '40%', '60%', '80%', '100%'], gridcolor='#fff'),
        xaxis2=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis2=dict(range=[0, 100], showticklabels=False, showgrid=False, zeroline=False)
    )
    return fig

def _generic_line_chart(df, y_max=100, y_tick_step=20, is_percent=True, peer_lines=None, peer_val_col=None, iso3="NGA"):
    fig = go.Figure()
    
    # Filter for 2010+
    if not df.empty and 'Year' in df.columns:
        df = df[df['Year'] >= 2010]
        
    year_max = df['Year'].max() if not df.empty and 'Year' in df.columns else 2024
    
    ht = 'year: %{x}<br>value: %{y:.1f}%<extra></extra>' if is_percent else 'year: %{x}<br>value: %{y:.0f}<extra></extra>'
    
    if peer_lines is not None and not peer_lines.empty and 'Year' in peer_lines.columns:
        peer_lines = peer_lines[peer_lines['Year'] >= 2010]
        for code in peer_lines['ISO3'].unique():
            if code != iso3:
                p_df = peer_lines[peer_lines['ISO3'] == code]
                fig.add_trace(go.Scatter(x=p_df['Year'], y=p_df[peer_val_col], mode='lines', line=dict(color='rgba(200,200,200,0.5)', width=1), showlegend=False, connectgaps=True, hoverinfo='skip'))

    if not df.empty and 'Year' in df.columns and 'Country' in df.columns:
        if peer_lines is None:
            if 'Upper' in df.columns and 'Lower' in df.columns:
                upper = df['Upper']
                lower = df['Lower']
                if is_percent:
                    upper = upper.clip(upper=100)
                    lower = lower.clip(lower=0)
                    
                fig.add_trace(go.Scatter(x=df['Year'], y=upper, fill=None, mode='lines', line=dict(color='rgba(255,255,255,0)'), showlegend=False, connectgaps=True, hoverinfo='skip'))
                fig.add_trace(go.Scatter(x=df['Year'], y=lower, fill='tonexty', mode='lines', fillcolor=C_MED_L, line=dict(color='rgba(255,255,255,0)'), showlegend=False, connectgaps=True, hoverinfo='skip'))
                
            if 'Median' in df.columns:
                fig.add_trace(go.Scatter(x=df['Year'], y=df['Median'], customdata=df.get('Count', pd.Series(dtype=float)), mode='lines', line=dict(color=C_MED, width=1), showlegend=False, connectgaps=True, hovertemplate=ht))
                
        fig.add_trace(go.Scatter(x=df['Year'], y=df['Country'], customdata=df.get('Count', pd.Series(dtype=float)), mode='lines+markers', marker=dict(color=C_NIG, size=4), line=dict(color=C_NIG, width=2), showlegend=False, connectgaps=True, hovertemplate=ht))
        
    # start ticks from y_tick_step to skip 0
    ticks = list(range(y_tick_step, y_max + 1, y_tick_step))
    ticktext = [f"{t}%" if is_percent else f"{t:,}" for t in ticks]
    
    xaxis_ticks = list(range(2010, int(year_max) + 1))
    
    lyt = layout_defaults()
    lyt['margin'] = dict(l=30, r=10, t=10, b=20)
    fig.update_layout(
        **lyt, 
        xaxis=dict(range=[2010, year_max], gridcolor='#fff', tickvals=xaxis_ticks, tickangle=-45), 
        yaxis=dict(range=[0, y_max], tickvals=ticks, ticktext=ticktext, gridcolor='#fff')
    )
    return fig

def fig_uhc_overall(iso3="NGA", country_name="Nigeria"):
    return _generic_line_chart(get_uhc_overall_data(iso3), peer_lines=get_uhc_overall_peer_lines(iso3), peer_val_col='UHC', iso3=iso3)

def fig_uhc_id(iso3="NGA", country_name="Nigeria"):
    return _generic_line_chart(get_uhc_id_data(iso3), peer_lines=get_uhc_id_peer_lines(iso3), peer_val_col='UHC_ID', iso3=iso3)

def fig_uhc_rmnch(iso3="NGA", country_name="Nigeria"):
    return _generic_line_chart(get_uhc_rmnch_data(iso3), peer_lines=get_uhc_rmnch_peer_lines(iso3), peer_val_col='UHC_RMNCH', iso3=iso3)

def fig_mmr(iso3="NGA", country_name="Nigeria"):
    df = get_mmr_data(iso3)
    peer_lines = get_mmr_peer_lines(iso3)
    
    if not df.empty and not peer_lines.empty:
        df['Count'] = peer_lines['ISO3'].nunique()
        
    # Filter for 2010+
    if not df.empty and 'Year' in df.columns:
        df = df[df['Year'] >= 2010]
        
    if not peer_lines.empty and 'Year' in peer_lines.columns:
        peer_lines = peer_lines[peer_lines['Year'] >= 2010]
        
    fig = go.Figure()
    
    y_max = 1000
    if not df.empty and 'Country' in df.columns:
        max_val = df[['Country', 'Upper']].max(numeric_only=True).max() if 'Upper' in df.columns else df[['Country', 'Median']].max().max()
        y_max = int(max_val * 1.2)
        y_max = max(100, (y_max // 100) * 100) # round up to nearest 100
        
    t_step = max(10, y_max // 5)
    
    ht = 'year: %{x}<br>value: %{y:,.0f}<extra></extra>'
    
    if not peer_lines.empty:
        for code in peer_lines['ISO3'].unique():
            if code != iso3:
                p_df = peer_lines[peer_lines['ISO3'] == code]
                fig.add_trace(go.Scatter(x=p_df['Year'], y=p_df['MMR'], mode='lines', line=dict(color='rgba(200,200,200,0.5)', width=1), showlegend=False, connectgaps=True, hoverinfo='skip'))
                
    if not df.empty and 'Year' in df.columns and 'Country' in df.columns:
        fig.add_trace(go.Scatter(x=df['Year'], y=df['Country'], customdata=df.get('Count', pd.Series(dtype=float)), mode='lines+markers', marker=dict(color=C_NIG, size=4), line=dict(color=C_NIG, width=2), showlegend=False, connectgaps=True, hovertemplate=ht))
        
    year_max = df['Year'].max() if not df.empty and 'Year' in df.columns else 2024
    
    ticks = list(range(t_step, y_max + 1, t_step))
    ticktext = [f"{t:,}" for t in ticks]
    
    xaxis_ticks = list(range(2010, int(year_max) + 1))
    
    lyt = layout_defaults()
    lyt['margin'] = dict(l=30, r=10, t=10, b=20)
    fig.update_layout(
        **lyt, 
        xaxis=dict(range=[2010, year_max], gridcolor='#fff', tickvals=[2010, 2015, 2020, 2023], tickangle=0), 
        yaxis=dict(range=[0, y_max], tickvals=ticks, ticktext=ticktext, gridcolor='#fff')
    )
    fig.update_xaxes(range=[2010, 2023.5])
    return fig

def fig_che(iso3="NGA", country_name="Nigeria"):
    df = get_che_data(iso3)
    peer_lines = get_che_peer_lines(iso3)
    
    # Filter for 2010+
    if not df.empty and 'Year' in df.columns:
        df = df[df['Year'] >= 2010]
        
    if not peer_lines.empty and 'Year' in peer_lines.columns:
        peer_lines = peer_lines[peer_lines['Year'] >= 2010]
        
    fig = go.Figure()
    
    if df.empty:
        return fig
        
    y_max_che = df[['CHE_GDP', 'CHE_Upper']].max(numeric_only=True).max() if 'CHE_Upper' in df.columns else df['CHE_GDP'].max()
    y_max = max(1, y_max_che * 1.2) if pd.notna(y_max_che) else 10
    
    ht = 'year: %{x}<br>value: %{y:.1f}%<extra></extra>'
    
    if not peer_lines.empty:
        for code in peer_lines['ISO3'].unique():
            if code != iso3:
                p_df = peer_lines[peer_lines['ISO3'] == code]
                fig.add_trace(go.Scatter(x=p_df['Year'], y=p_df['CHE'], mode='lines', line=dict(color='rgba(200,200,200,0.5)', width=1), showlegend=False, connectgaps=True, hoverinfo='skip'))

    fig.add_trace(go.Scatter(x=df['Year'], y=df['CHE_GDP'], customdata=df.get('CHE_Count', pd.Series(dtype=float)), mode='lines+markers', marker=dict(color=C_NIG, size=4), line=dict(color=C_NIG, width=2), connectgaps=True, hovertemplate=ht))
    
    year_max = df['Year'].max() if not df.empty else 2024
    
    # Calculate ticks skipping 0
    t_step = max(1, y_max // 5)
    ticks = list(np.arange(t_step, y_max + 1, t_step)) if y_max > 0 else []
    
    xaxis_ticks = list(range(2010, int(year_max) + 1))
    
    lyt = layout_defaults()
    lyt['margin'] = dict(l=30, r=10, t=10, b=20)
    fig.update_layout(
        **lyt, 
        xaxis=dict(range=[2010, year_max], gridcolor='#fff', tickvals=xaxis_ticks, tickangle=-45), 
        yaxis=dict(range=[0, y_max], tickvals=ticks, title='CHE as % of GDP', gridcolor='#fff', title_font=dict(size=8))
    )
    return fig

def fig_gghe_d(iso3="NGA", country_name="Nigeria"):
    df = get_che_data(iso3)
    peer_lines = get_che_peer_lines(iso3)

    # Filter for 2010+
    if not df.empty and 'Year' in df.columns:
        df = df[df['Year'] >= 2010]
        
    if not peer_lines.empty and 'Year' in peer_lines.columns:
        peer_lines = peer_lines[peer_lines['Year'] >= 2010]
        
    fig = go.Figure()
    
    if df.empty:
        return fig
        
    y_max_gghe = df[['GGHE_GDP', 'GGHE_Upper']].max(numeric_only=True).max() if 'GGHE_Upper' in df.columns else df['GGHE_GDP'].max()
    y_max = max(1, y_max_gghe * 1.2) if pd.notna(y_max_gghe) else 10
    
    ht = 'year: %{x}<br>value: %{y:.1f}%<extra></extra>'
    
    if not peer_lines.empty:
        for code in peer_lines['ISO3'].unique():
            if code != iso3:
                p_df = peer_lines[peer_lines['ISO3'] == code]
                fig.add_trace(go.Scatter(x=p_df['Year'], y=p_df['GGHE_GDP'], mode='lines', line=dict(color='rgba(200,200,200,0.5)', width=1), showlegend=False, connectgaps=True, hoverinfo='skip'))
        
    fig.add_trace(go.Scatter(x=df['Year'], y=df['GGHE_GDP'], customdata=df.get('GGHE_Count', pd.Series(dtype=float)), mode='lines+markers', marker=dict(color=C_NIG, size=4), line=dict(color=C_NIG, width=2), connectgaps=True, hovertemplate=ht))
    
    year_max = df['Year'].max() if not df.empty else 2024
    
    # Calculate ticks skipping 0
    t_step = max(1, y_max // 5)
    ticks = list(np.arange(t_step, y_max + 1, t_step)) if y_max > 0 else []
    
    xaxis_ticks = list(range(2010, int(year_max) + 1))
    
    lyt = layout_defaults()
    lyt['margin'] = dict(l=30, r=10, t=10, b=20)
    fig.update_layout(
        **lyt, 
        xaxis=dict(range=[2010, year_max], gridcolor='#fff', tickvals=xaxis_ticks, tickangle=-45), 
        yaxis=dict(range=[0, y_max], tickvals=ticks, title='GGHE-D as % of GDP', gridcolor='#fff', title_font=dict(size=8))
    )
    return fig

def fig_oop(iso3="NGA", country_name="Nigeria"):
    df = get_oop_data(iso3)
    peer_lines = get_oop_peer_lines(iso3)

    # Filter for 2010+
    if not df.empty and 'Year' in df.columns:
        df = df[df['Year'] >= 2010]
        
    if not peer_lines.empty and 'Year' in peer_lines.columns:
        peer_lines = peer_lines[peer_lines['Year'] >= 2010]
        
    fig = go.Figure()
    
    if df.empty:
        return fig
        
    y_max_oop = df[['OOP_GDP', 'OOP_Upper']].max(numeric_only=True).max() if 'OOP_Upper' in df.columns else df['OOP_GDP'].max()
    y_max = max(1, y_max_oop * 1.2) if pd.notna(y_max_oop) else 10
    
    ht = 'year: %{x}<br>value: %{y:.1f}%<extra></extra>'
    
    if not peer_lines.empty:
        for code in peer_lines['ISO3'].unique():
            if code != iso3:
                p_df = peer_lines[peer_lines['ISO3'] == code]
                fig.add_trace(go.Scatter(x=p_df['Year'], y=p_df['OOP_GDP'], mode='lines', line=dict(color='rgba(200,200,200,0.5)', width=1), showlegend=False, connectgaps=True, hoverinfo='skip'))
        
    fig.add_trace(go.Scatter(x=df['Year'], y=df['OOP_GDP'], customdata=df.get('OOP_Count', pd.Series(dtype=float)), mode='lines+markers', marker=dict(color=C_NIG, size=4), line=dict(color=C_NIG, width=2), connectgaps=True, hovertemplate=ht))
    
    year_max = df['Year'].max() if not df.empty else 2024
    
    # Calculate ticks skipping 0
    t_step = max(1, y_max // 5)
    ticks = list(np.arange(t_step, y_max + 1, t_step)) if y_max > 0 else []
    
    xaxis_ticks = list(range(2010, int(year_max) + 1))
    
    lyt = layout_defaults()
    lyt['margin'] = dict(l=30, r=10, t=10, b=20)
    fig.update_layout(
        **lyt, 
        xaxis=dict(range=[2010, year_max], gridcolor='#fff', tickvals=xaxis_ticks, tickangle=-45), 
        yaxis=dict(range=[0, y_max], tickvals=ticks, title='OOPS as % of GDP', gridcolor='#fff', title_font=dict(size=8))
    )
    return fig

def fig_che_ppp(iso3="NGA", country_name="Nigeria"):
    df = get_che_ppp_data(iso3)
    fig = go.Figure()
    
    for i, row in df.iterrows():
        fig.add_trace(go.Scatter(x=[row['Metric'], row['Metric']], y=[0, max(row['Value'], row['Median']) + 10], mode='lines', line=dict(color='#ccc', width=1)))
        fig.add_trace(go.Scatter(x=[row['Metric']], y=[row['Value']], mode='markers', marker=dict(color=C_NIG, size=8)))
        fig.add_trace(go.Scatter(x=[row['Metric']], y=[row['Median']], mode='markers', marker=dict(color=C_MED, size=8)))

    lyt = layout_defaults()
    lyt['margin'] = dict(l=30, r=5, t=10, b=20)
    fig.update_layout(**lyt, yaxis=dict(range=[0, max(df['Value'].max(), df['Median'].max()) + 50], title='ppp int$ in 2019', gridcolor='#fff', title_font=dict(size=8)))
    return fig

def fig_composition(iso3="NGA", country_name="Nigeria"):
    df = get_composition_che_data(iso3)
    fig = go.Figure()
    for i, row in df.iterrows():
        fig.add_trace(go.Scatter(x=[0, 100], y=[row['Component'], row['Component']], mode='lines', line=dict(color='#ccc', width=1)))
        fig.add_trace(go.Scatter(x=[row['Median']], y=[row['Component']], mode='markers', marker=dict(color=C_MED, size=8)))
        fig.add_trace(go.Scatter(x=[row['Country']], y=[row['Component']], mode='markers', marker=dict(color=C_NIG, size=8)))
        
    lyt = layout_defaults()
    lyt['margin'] = dict(l=200, r=10, t=10, b=20)
    fig.update_layout(**lyt, xaxis=dict(range=[0, 100], tickvals=[0, 20, 40, 60, 80, 100], ticktext=['0%', '20%', '40%', '60%', '80%', '100%'], gridcolor='#fff'))
    return fig

def fig_rssh(iso3="NGA", country_name="Nigeria"):
    df = get_rssh_investment_data(iso3)
    fig = go.Figure()
    
    fig.add_trace(go.Bar(y=df['Category'], x=df['NFM2_Contributory'], orientation='h', name='Contributory', marker=dict(color=C_NIG_L), legendgroup='NFM2', offsetgroup=1))
    fig.add_trace(go.Bar(y=df['Category'], x=df['NFM2_Direct'], orientation='h', name='Direct', marker=dict(color=C_NIG), legendgroup='NFM2', offsetgroup=1, base=df['NFM2_Contributory']))
    
    fig.add_trace(go.Bar(y=df['Category'], x=df['NFM3_Contributory'], orientation='h', showlegend=False, marker=dict(color=C_NIG_L), legendgroup='NFM3', offsetgroup=2))
    fig.add_trace(go.Bar(y=df['Category'], x=df['NFM3_Direct'], orientation='h', showlegend=False, marker=dict(color=C_NIG), legendgroup='NFM3', offsetgroup=2, base=df['NFM3_Contributory']))
    
    lyt = layout_defaults()
    lyt['margin'] = dict(l=180, r=10, t=40, b=20)
    lyt['showlegend'] = True
    fig.update_layout(
        **lyt, 
        barmode='group',
        yaxis=dict(autorange='reversed'),
        xaxis=dict(gridcolor='#fff'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=9))
    )
    return fig

def fig_hr(iso3="NGA", country_name="Nigeria"):
    df = get_human_resources_data(iso3)
    fig = go.Figure()
    for i, row in df.iterrows():
        fig.add_trace(go.Scatter(x=[row['Median'], row['Country']], y=[row['Type'], row['Type']], mode='lines', line=dict(color='#ccc', width=1)))
        fig.add_trace(go.Scatter(x=[row['Median']], y=[row['Type']], mode='markers', marker=dict(color=C_MED, size=8)))
        fig.add_trace(go.Scatter(x=[row['Country']], y=[row['Type']], mode='markers', marker=dict(color=C_NIG, size=8)))
        
    lyt = layout_defaults()
    lyt['margin'] = dict(l=10, r=10, t=10, b=20)
    
    max_val = max(df['Median'].max(), df['Country'].max()) + 5
    fig.update_layout(**lyt, yaxis=dict(showticklabels=False), xaxis=dict(range=[0, max_val], title='density per 10,000 population', gridcolor='#fff', title_font=dict(size=8)))
    
    for i, row in df.iterrows():
        fig.add_annotation(x=max_val/2, y=row['Type'], text=row['Type'], showarrow=False, yshift=15, font=dict(size=9, color='#666'))
    return fig

def _single_point_fig(x_med=None, x_nig=None, range_max=100):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, range_max], y=['Metric', 'Metric'], mode='lines', line=dict(color='#ccc', width=1)))
    if x_med is not None:
        fig.add_trace(go.Scatter(x=[x_med], y=['Metric'], mode='markers', marker=dict(color=C_MED, size=8)))
    if x_nig is not None:
        fig.add_trace(go.Scatter(x=[x_nig], y=['Metric'], mode='markers', marker=dict(color=C_NIG, size=8)))
        
    lyt = layout_defaults()
    lyt['margin'] = dict(l=10, r=10, t=0, b=15)
    fig.update_layout(**lyt, yaxis=dict(showticklabels=False), xaxis=dict(range=[0, range_max], tickvals=[0, 20, 40, 60, 80, 100], ticktext=['0%', '20%', '40%', '60%', '80%', '100%'] if range_max==100 else None, gridcolor='#fff'))
    return fig

def fig_med_avail(iso3="NGA", country_name="Nigeria"):
    from data.dummy_data import generate_pseudo_random_variance
    return _single_point_fig(x_med=None, x_nig=min(100, max(0, 35 + generate_pseudo_random_variance(iso3, 0, 10))))

def fig_diag_avail(iso3="NGA", country_name="Nigeria"):
    from data.dummy_data import generate_pseudo_random_variance
    return _single_point_fig(x_med=60, x_nig=min(100, max(0, 65 + generate_pseudo_random_variance(iso3, 0, 10))))

def fig_absence(iso3="NGA", country_name="Nigeria"):
    from data.dummy_data import generate_pseudo_random_variance
    return _single_point_fig(x_med=None, x_nig=min(100, max(0, 45 + generate_pseudo_random_variance(iso3, 0, 10))))

def fig_md(iso3="NGA", country_name="Nigeria"):
    df = get_md_data(iso3)
    
    # Filter for 2010+
    if not df.empty and 'Year' in df.columns:
        df = df[df['Year'] >= 2010]
        
    y_max = 50
    if not df.empty:
        max_val = df[['Country', 'Upper']].max(numeric_only=True).max() if 'Upper' in df.columns else df['Country'].max()
        if pd.notna(max_val) and max_val > 0:
            y_max = int(np.ceil((max_val * 1.2) / 10.0)) * 10
            
    y_tick_step = max(10, y_max // 5)
            
    fig = _generic_line_chart(df, y_max=y_max, y_tick_step=y_tick_step, is_percent=False, peer_lines=get_md_peer_lines(iso3), peer_val_col='MD per 10k pop', iso3=iso3)
    fig.update_traces(hovertemplate='year: %{x}<br>value: %{y:.2f}<extra></extra>')
    return fig

def fig_nurse(iso3="NGA", country_name="Nigeria"):
    df = get_nurse_data(iso3)
    
    # Filter for 2010+
    if not df.empty and 'Year' in df.columns:
        df = df[df['Year'] >= 2010]
        
    y_max = 100
    if not df.empty:
        max_val = df[['Country', 'Upper']].max(numeric_only=True).max() if 'Upper' in df.columns else df['Country'].max()
        if pd.notna(max_val) and max_val > 0:
            y_max = int(np.ceil((max_val * 1.2) / 10.0)) * 10
            
    y_tick_step = max(10, y_max // 5)
            
    fig = _generic_line_chart(df, y_max=y_max, y_tick_step=y_tick_step, is_percent=False, peer_lines=get_nurse_peer_lines(iso3), peer_val_col='Nurse and midwives per 10k pop', iso3=iso3)
    fig.update_traces(hovertemplate='year: %{x}<br>value: %{y:.2f}<extra></extra>')
    return fig

def fig_chw(iso3="NGA", country_name="Nigeria"):
    df = get_chw_data(iso3)
    
    # Filter for 2010+
    if not df.empty and 'Year' in df.columns:
        df = df[df['Year'] >= 2010]
        
    y_max = 50
    if not df.empty:
        max_val = df[['Country', 'Upper']].max(numeric_only=True).max() if 'Upper' in df.columns else df['Country'].max()
        if pd.notna(max_val) and max_val > 0:
            y_max = int(np.ceil((max_val * 1.2) / 10.0)) * 10
            
    y_tick_step = max(10, y_max // 5)
            
    fig = _generic_line_chart(df, y_max=y_max, y_tick_step=y_tick_step, is_percent=False, peer_lines=get_chw_peer_lines(iso3), peer_val_col='CHW per 10k pop', iso3=iso3)
    fig.update_traces(hovertemplate='year: %{x}<br>value: %{y:.2f}<extra></extra>')
    return fig
