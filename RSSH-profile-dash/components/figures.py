import plotly.graph_objects as go
from data.dummy_data import *

C_NIG = '#1a8f4c'
C_NIG_L = '#a2d6b3'
C_MED = '#df8a46'
C_MED_L = '#fce4c8'
C_BG = '#fcfcfc'
font_fmt = dict(size=9, color='#666')

def layout_defaults():
    return dict(
        margin=dict(l=20, r=20, t=10, b=20),
        plot_bgcolor=C_BG,
        paper_bgcolor='white',
        showlegend=False,
        font=font_fmt
    )

def fig_dtp3(iso3="NGA", country_name="Nigeria"):
    df = get_dtp3_data(iso3)
    fig = go.Figure()
    
    upper = df['Upper'] if 'Upper' in df.columns else df['Median'] + 5
    lower = df['Lower'] if 'Lower' in df.columns else df['Median'] - 5
    upper = upper.clip(upper=100)
    lower = lower.clip(lower=0)
    
    fig.add_trace(go.Scatter(x=df['Year'], y=upper, fill=None, mode='lines', line=dict(color='rgba(255,255,255,0)'), showlegend=False, connectgaps=True))
    fig.add_trace(go.Scatter(x=df['Year'], y=lower, fill='tonexty', mode='lines', fillcolor=C_MED_L, line=dict(color='rgba(255,255,255,0)'), showlegend=False, connectgaps=True))
    
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Median'], customdata=df['Count'], mode='lines', line=dict(color=C_MED, width=1), showlegend=False, connectgaps=True))
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Country'], mode='lines+markers', marker=dict(color=C_NIG, size=4), line=dict(color=C_NIG, width=2), showlegend=False))
    
    fig.update_layout(**layout_defaults(), yaxis=dict(range=[0, 100], tickvals=[0, 20, 40, 60, 80, 100], ticktext=['0%', '20%', '40%', '60%', '80%', '100%'], gridcolor='#fff'))
    fig.update_xaxes(gridcolor='#fff')
    return fig

def fig_anc4(iso3="NGA", country_name="Nigeria"):
    df = get_anc4_data(iso3)
    fig = go.Figure()
    
    upper = df['Upper'] if 'Upper' in df.columns else df['Median'] + 8
    lower = df['Lower'] if 'Lower' in df.columns else df['Median'] - 8
    upper = upper.clip(upper=100)
    lower = lower.clip(lower=0)
    
    fig.add_trace(go.Scatter(x=df['Year'], y=upper, fill=None, mode='lines', line=dict(color='rgba(255,255,255,0)'), showlegend=False, connectgaps=True))
    fig.add_trace(go.Scatter(x=df['Year'], y=lower, fill='tonexty', mode='lines', fillcolor=C_MED_L, line=dict(color='rgba(255,255,255,0)'), showlegend=False, connectgaps=True))
    
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Median'], customdata=df['Count'], mode='lines', line=dict(color=C_MED, width=1), showlegend=False, connectgaps=True))
    fig.add_trace(go.Scatter(x=df['Year'], y=df['Country'], mode='lines+markers', marker=dict(color=C_NIG, size=4), line=dict(color=C_NIG, width=2), showlegend=False, connectgaps=True))
    
    fig.update_layout(**layout_defaults(), yaxis=dict(range=[0, 100], tickvals=[0, 20, 40, 60, 80, 100], ticktext=['0%', '20%', '40%', '60%', '80%', '100%'], gridcolor='#fff'))
    fig.update_xaxes(gridcolor='#fff')
    return fig

def _generic_line_chart(df, y_max=100, y_tick_step=20, is_percent=True):
    fig = go.Figure()
    if not df.empty and 'Year' in df.columns and 'Median' in df.columns and 'Country' in df.columns:
        upper = df['Upper'] if 'Upper' in df.columns else df['Median'] + 5
        lower = df['Lower'] if 'Lower' in df.columns else df['Median'] - 5
        if is_percent:
            upper = upper.clip(upper=100)
            lower = lower.clip(lower=0)
            
        fig.add_trace(go.Scatter(x=df['Year'], y=upper, fill=None, mode='lines', line=dict(color='rgba(255,255,255,0)'), showlegend=False, connectgaps=True))
        fig.add_trace(go.Scatter(x=df['Year'], y=lower, fill='tonexty', mode='lines', fillcolor=C_MED_L, line=dict(color='rgba(255,255,255,0)'), showlegend=False, connectgaps=True))
        
        fig.add_trace(go.Scatter(x=df['Year'], y=df['Median'], customdata=df['Count'], mode='lines', line=dict(color=C_MED, width=1), showlegend=False, connectgaps=True))
        fig.add_trace(go.Scatter(x=df['Year'], y=df['Country'], mode='lines+markers', marker=dict(color=C_NIG, size=4), line=dict(color=C_NIG, width=2), showlegend=False, connectgaps=True))
        
    ticks = list(range(0, y_max + 1, y_tick_step))
    ticktext = [f"{t}%" if is_percent else str(t) for t in ticks]
    
    fig.update_layout(**layout_defaults(), yaxis=dict(range=[0, y_max], tickvals=ticks, ticktext=ticktext, gridcolor='#fff'))
    fig.update_xaxes(gridcolor='#fff')
    return fig

def fig_uhc_overall(iso3="NGA", country_name="Nigeria"):
    return _generic_line_chart(get_uhc_overall_data(iso3))

def fig_uhc_id(iso3="NGA", country_name="Nigeria"):
    return _generic_line_chart(get_uhc_id_data(iso3))

def fig_uhc_rmnch(iso3="NGA", country_name="Nigeria"):
    return _generic_line_chart(get_uhc_rmnch_data(iso3))

def fig_mmr(iso3="NGA", country_name="Nigeria"):
    df = get_mmr_data(iso3)
    y_max = 1000
    if not df.empty and 'Country' in df.columns:
        y_max = int(df[['Country', 'Median']].max().max() * 1.2)
        y_max = max(100, (y_max // 100) * 100) # round up to nearest 100
        
    return _generic_line_chart(df, y_max=y_max, y_tick_step=y_max//5, is_percent=False)

def fig_che(iso3="NGA", country_name="Nigeria"):
    df = get_che_data(iso3)
    fig = go.Figure()
    
    if df.empty:
        return fig
        
    y_max_che = df[['CHE_GDP', 'CHE_Upper', 'CHE_Median']].max().max() if 'CHE_Upper' in df.columns else df['CHE_GDP'].max()
    y_max = max(1, y_max_che * 1.15) if pd.notna(y_max_che) else 10
    
    # Plot CHE bounds and median
    if 'CHE_Upper' in df.columns:
        fig.add_trace(go.Scatter(x=df['Year'], y=df['CHE_Upper'].clip(upper=y_max), fill=None, mode='lines', line=dict(color='rgba(255,255,255,0)'), showlegend=False, connectgaps=True))
        fig.add_trace(go.Scatter(x=df['Year'], y=df['CHE_Lower'].clip(lower=0), fill='tonexty', mode='lines', fillcolor='rgba(252,228,200,0.6)', line=dict(color='rgba(255,255,255,0)'), showlegend=False, connectgaps=True))
        fig.add_trace(go.Scatter(x=df['Year'], y=df['CHE_Median'], customdata=df['CHE_Count'], mode='lines', line=dict(color=C_MED, width=2), showlegend=False, connectgaps=True))

    fig.add_trace(go.Scatter(x=df['Year'], y=df['CHE_GDP'], mode='lines+markers', marker=dict(color=C_NIG, size=4), line=dict(color=C_NIG, width=2), connectgaps=True))
    
    lyt = layout_defaults()
    lyt['margin'] = dict(l=30, r=10, t=10, b=20)
    fig.update_layout(**lyt, yaxis=dict(range=[0, y_max], title='CHE as % of GDP', gridcolor='#fff', title_font=dict(size=8)))
    fig.update_xaxes(gridcolor='#fff')
    return fig

def fig_gghe_d(iso3="NGA", country_name="Nigeria"):
    df = get_che_data(iso3)
    fig = go.Figure()
    
    if df.empty:
        return fig
        
    y_max_gghe = df[['GGHE_GDP', 'GGHE_Upper', 'GGHE_Median']].max().max() if 'GGHE_Upper' in df.columns else df['GGHE_GDP'].max()
    y_max = max(1, y_max_gghe * 1.15) if pd.notna(y_max_gghe) else 10
    
    # Plot GGHE-D bounds and median
    if 'GGHE_Upper' in df.columns:
        fig.add_trace(go.Scatter(x=df['Year'], y=df['GGHE_Upper'].clip(upper=y_max), fill=None, mode='lines', line=dict(color='rgba(255,255,255,0)'), showlegend=False, connectgaps=True))
        fig.add_trace(go.Scatter(x=df['Year'], y=df['GGHE_Lower'].clip(lower=0), fill='tonexty', mode='lines', fillcolor='rgba(252,228,200,0.6)', line=dict(color='rgba(255,255,255,0)'), showlegend=False, connectgaps=True))
        fig.add_trace(go.Scatter(x=df['Year'], y=df['GGHE_Median'], customdata=df['GGHE_Count'], mode='lines', line=dict(color=C_MED, width=2), showlegend=False, connectgaps=True))
        
    fig.add_trace(go.Scatter(x=df['Year'], y=df['GGHE_GDP'], mode='lines+markers', marker=dict(color=C_NIG, size=4), line=dict(color=C_NIG, width=2), connectgaps=True))
    
    lyt = layout_defaults()
    lyt['margin'] = dict(l=30, r=10, t=10, b=20)
    fig.update_layout(**lyt, yaxis=dict(range=[0, y_max], title='GGHE-D as % of GDP', gridcolor='#fff', title_font=dict(size=8)))
    fig.update_xaxes(gridcolor='#fff')
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
