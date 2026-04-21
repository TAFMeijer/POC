import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import json
import urllib.parse

from data_processing import df_b, df_i, df_w, COMP_COLORS, SHADES, TYPE_TO_WEIGHT, indicator_order, available_regions, country_to_shortname
dash_app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], suppress_callback_exceptions=True)

# Expose the standard Flask server for Gunicorn / WSGI deployments (e.g., Hugging Face)
app = dash_app.server


dash_app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
], fluid=True, className="dashboard-container")

def get_header():
    return dbc.Row([
        dbc.Col(html.Img(src=dash_app.get_asset_url('GF Logo.PNG'), className="dashboard-logo"), width="auto"),
        dbc.Col([
            html.Div("Budget - PF POC Dashboard", className="dashboard-title"),
            html.Div([
                "A proof of concept dashboard for FR-GM review of the mapping between Budget and Performance Framework, using ",
                html.B("publicly available"),
                " GC7 data for now.",
                html.Br(),
                "To be used for Regional, Country-level or Grant-level review."
            ], className="dashboard-subtitle")
        ], width=9, className="title-wrapper"),
        dbc.Col([
            dcc.Link("Regional Overview", href="/", className="btn btn-outline-primary mb-2 w-100", style={'marginTop': '10px'}),
            dcc.Link("Detailed Dashboard", href="/detailed", className="btn btn-outline-primary w-100")
        ], width=2)
    ], className="header-container")

def layout_overview():
    return html.Div([
        get_header(),
        dbc.Row([
            dbc.Col([
                dbc.Label("Select Region", style={'fontSize': '14px'}),
                dcc.Dropdown(
                    id='overview-region-dropdown',
                    options=[{'label': 'All Regions', 'value': 'ALL'}] + [{'label': r, 'value': r} for r in available_regions],
                    value='WCA'
                )
            ], width=2),
            dbc.Col([
                dbc.Checklist(
                    options=[{"label": "Include Custom & WPTM", "value": "include"}],
                    value=[],
                    id="toggle-custom-wptm",
                    switch=True,
                    className="large-toggle",
                    style={'marginTop': '25px', 'fontSize': '14px', 'display': 'inline-block', 'marginRight': '30px'}
                ),
                dbc.Checklist(
                    options=[{"label": "Percentage View", "value": "percent"}],
                    value=[],
                    id="toggle-percent",
                    switch=True,
                    className="large-toggle",
                    style={'fontSize': '14px', 'display': 'inline-block', 'marginTop': '25px'}
                )
            ], width=8, className="d-flex align-items-center")
        ], className="filter-row"),
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='overview-chart', clear_on_unhover=True)
            ], width=12, className="chart-wrapper")
        ])
    ])

def layout_detailed(country='Benin'):
    from data_processing import country_to_region
    region_val = country_to_region.get(country, 'WCA') if country != 'ALL' else 'ALL'
    
    if region_val == 'ALL':
        c_opts = df_b['Country'].dropna().unique()
    else:
        c_opts = [c for c in df_b['Country'].dropna().unique() if country_to_region.get(c) == region_val]
        
    if country == 'ALL':
        ips = df_b['Implementation Period Name'].dropna().unique()
    else:
        ips = df_b[df_b['Country'] == country]['Implementation Period Name'].dropna().unique()
        
    ip_val = 'ALL'

    return html.Div([
        get_header(),
        dbc.Row([
            dbc.Col([
                dbc.Label("Select Region", style={'fontSize': '14px'}),
                dcc.Dropdown(
                    id='region-dropdown',
                    options=[{'label': 'All Regions', 'value': 'ALL'}] + [{'label': r, 'value': r} for r in available_regions],
                    value=region_val
                )
            ], width=2),
            dbc.Col([
                dbc.Label("Select Country", style={'fontSize': '14px'}),
                dcc.Dropdown(
                    id='country-dropdown',
                    options=[{'label': 'All Countries', 'value': 'ALL'}] + [{'label': country_to_shortname.get(c, c), 'value': c} for c in c_opts],
                    value=country
                )
            ], width=2),
            dbc.Col([
                dbc.Label("Select Implementation Period", style={'fontSize': '14px'}),
                dcc.Dropdown(
                    id='ip-dropdown',
                    options=[{'label': 'All Implementation Periods', 'value': 'ALL'}] + [{'label': ip, 'value': ip} for ip in ips],
                    value=ip_val
                )
            ], width=3),
            dbc.Col([
                dbc.Label("Select Component", style={'fontSize': '14px'}),
                dcc.Dropdown(
                    id='component-dropdown',
                    options=[{'label': 'All Components', 'value': 'ALL'}] + [{'label': c, 'value': c} for c in ['HIV/AIDS', 'Tuberculosis', 'Malaria', 'RSSH', 'Program Management']],
                    value='ALL'
                )
            ], width=3),
            dbc.Col([
                dbc.Button("Download Excel", id="btn-download", color="secondary", className="w-100 btn-export"),
                dcc.Download(id="download-excel")
            ], width=2)
        ], className="filter-row"),
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='main-chart', clear_on_unhover=True),
                dcc.Tooltip(id='graph-tooltip')
            ], width=12, className="chart-wrapper")
        ])
    ])

@dash_app.callback(
    Output('country-dropdown', 'options'),
    Output('country-dropdown', 'value'),
    Input('region-dropdown', 'value'),
    prevent_initial_call=True
)
def update_country_dropdown(region):
    from data_processing import df_b, country_to_region, country_to_shortname
    all_countries = df_b['Country'].dropna().unique()
    if not region or region == 'ALL':
        countries = list(all_countries)
    else:
        countries = [c for c in all_countries if country_to_region.get(c) == region]
    
    opts = [{'label': 'All Countries', 'value': 'ALL'}] + [{'label': country_to_shortname.get(c, c), 'value': c} for c in countries]
    val = 'ALL'
    return opts, val

@dash_app.callback(
    Output('ip-dropdown', 'options'),
    Output('ip-dropdown', 'value'),
    Input('country-dropdown', 'value'),
    prevent_initial_call=True
)
def update_ip_dropdown(country):
    if not country or country == 'ALL':
        ips = df_b['Implementation Period Name'].dropna().unique()
    else:
        ips = df_b[df_b['Country'] == country]['Implementation Period Name'].dropna().unique()
    opts = [{'label': 'All Implementation Periods', 'value': 'ALL'}] + [{'label': ip, 'value': ip} for ip in ips]
    val = 'ALL'
    return opts, val

@dash_app.callback(
    [Output('main-chart', 'figure'),
     Output('main-chart', 'style'),
     Output('main-chart', 'className')],
    [Input('country-dropdown', 'value'),
     Input('ip-dropdown', 'value'),
     Input('component-dropdown', 'value'),
     Input('region-dropdown', 'value')]
)
def update_chart(country, ip, component, region):
    try:
        from chart_builder import build_main_chart
        fig, style = build_main_chart(dash_app, region, country, ip, component)
        if component == 'ALL':
            cname = "modebar-vertical-all"
        else:
            cname = "modebar-horizontal-single"
        return fig, style, cname
    except Exception as e:
        import traceback
        import plotly.graph_objects as go
        err_text = f"CRASH: {str(e)}<br>{traceback.format_exc()}"
        fig = go.Figure()
        fig.update_layout(title=dict(text=err_text[:450], font=dict(color='red', size=10)))
        return fig, {'height': '850px'}, ''

@dash_app.callback(
    Output("graph-tooltip", "show"),
    Output("graph-tooltip", "bbox"),
    Output("graph-tooltip", "children"),
    Output("graph-tooltip", "direction"),
    Input("main-chart", "hoverData"),
)
def display_hover(hoverData):
    if hoverData is None:
        return False, dash.no_update, dash.no_update, dash.no_update
        
    pt = hoverData["points"][0]
    bbox = pt["bbox"]
    
    if "customdata" not in pt:
        return False, dash.no_update, dash.no_update, dash.no_update
        
    cd = pt["customdata"]
    if isinstance(cd, list):
        cd = cd[0]
        
    try:
        obj = json.loads(cd)
    except Exception:
        return False, dash.no_update, dash.no_update, dash.no_update
        
    type_ = obj.get('type')
    if type_ == 'EMPTY' or not type_:
        return False, dash.no_update, dash.no_update, dash.no_update
        
    data = obj.get('data', [])
    num_rows = len(data)
    
    # Scale CSS styles strictly based on the number of records so large tables fit cleanly on screen
    if num_rows > 20:
        pad = '2px'
        fsize = '7.5px'
    elif num_rows > 10:
        pad = '4px'
        fsize = '9px'
    else:
        pad = '0.075in'
        fsize = '10.5px'
        
    style_table = {'borderCollapse': 'collapse', 'textAlign': 'left', 'width': '100%', 'fontSize': fsize, 'whiteSpace': 'normal', 'wordWrap': 'break-word', 'tableLayout': 'auto'}
    style_th = {'padding': pad, 'borderBottom': '1px solid #ddd', 'backgroundColor': '#f8f9fa', 'color': '#333', 'whiteSpace': 'normal', 'wordWrap': 'break-word'}
    style_td = {'padding': pad, 'borderBottom': '1px solid #eee', 'color': '#333', 'whiteSpace': 'normal', 'wordWrap': 'break-word'}
        
    dir_ = 'right' if type_ == 'BUDGET' else 'left'
    
    if bbox["y0"] < 250:
        dir_ = 'bottom' # HARD BOUNDARY tracking upper graph margin to inherently protect Dropsdowns
    elif bbox["y0"] > 450:
        dir_ = 'top'

    style_no_wrap = {**style_td, 'whiteSpace': 'nowrap', 'width': '1%'}
    style_th_no_wrap = {**style_th, 'whiteSpace': 'nowrap', 'width': '1%'}

    if type_ == 'BUDGET':
        style_budget_th = {**style_th_no_wrap, 'textAlign': 'right'}
        style_budget_td = {**style_no_wrap, 'textAlign': 'right'}
        if not data:
            return True, bbox, html.Div([
                html.B("Budget Details"), html.Br(), "No Interventions"
            ]), dir_
        rows = [html.Tr([html.Th("Intervention", style=style_th), html.Th("Budget ($M)", style=style_budget_th)])]
        for d in data:
            rows.append(html.Tr([html.Td(d['Intervention'], style=style_td), html.Td(d['Amount'], style=style_budget_td)]))
        return True, bbox, html.Div([
            html.B("Interventions", style={'marginBottom': '10px', 'display': 'block'}),
            html.Table(rows, style=style_table)
        ], style={'width': '375px'}), dir_
        
    elif type_ == 'INDICATOR_CUSTOM':
        data = obj.get('data', [])
        title = obj.get('title', 'Indicators')
        rows = [html.Tr([html.Th("Indicator Name", style=style_th), html.Th("Count", style=style_th_no_wrap)])]
        for d in data:
            rows.append(html.Tr([html.Td(d['name'], style=style_td), html.Td(d.get('count', ''), style=style_no_wrap)]))
        return True, bbox, html.Div([
            html.B(title, style={'marginBottom': '10px', 'display': 'block'}),
            html.Table(rows, style=style_table)
        ], style={'width': '525px'}), dir_
        
    elif type_ == 'INDICATOR_STANDARD':
        data = obj.get('data', [])
        title = obj.get('title', 'Indicators')
        rows = [html.Tr([html.Th("Indicator Code", style=style_th_no_wrap), html.Th("Indicator Name", style=style_th), html.Th("Count", style=style_th_no_wrap)])]
        for d in data:
            rows.append(html.Tr([html.Td(d['code'], style=style_no_wrap), html.Td(d['desc'], style=style_td), html.Td(d.get('count', ''), style=style_no_wrap)]))
        return True, bbox, html.Div([
            html.B(title, style={'marginBottom': '10px', 'display': 'block'}),
            html.Table(rows, style=style_table)
        ], style={'width': '650px'}), dir_
        
    elif type_ == 'WPTM':
        data = obj.get('data', [])
        rows = [html.Tr([html.Th("Implementation Period", style=style_th_no_wrap), html.Th("Key Activity", style=style_th)])]
        for d in data:
            rows.append(html.Tr([html.Td(d['ip'], style=style_no_wrap), html.Td(d['act'], style=style_td)]))
        return True, bbox, html.Div([
            html.B("WPTM Activities", style={'marginBottom': '10px', 'display': 'block'}),
            html.Table(rows, style=style_table)
        ], style={'width': '450px'}), dir_

    return False, dash.no_update, dash.no_update, dash.no_update

@dash_app.callback(
    Output("download-excel", "data"),
    Input("btn-download", "n_clicks"),
    State("country-dropdown", "value"),
    State("ip-dropdown", "value"),
    State("component-dropdown", "value"),
    State("region-dropdown", "value"),
    prevent_initial_call=True
)
def download_excel(n_clicks, country, ip, component, region):
    from excel_exporter import build_excel_export
    return build_excel_export(n_clicks, region, country, ip, component)

@dash_app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('url', 'search')
)
def display_page(pathname, search):
    if pathname and ('/detailed' in pathname):
        if search:
            parsed = urllib.parse.parse_qs(search.lstrip('?'))
            if 'country' in parsed:
                return layout_detailed(country=parsed['country'][0])
        return layout_detailed()
    return layout_overview()

@dash_app.callback(
    Output('overview-chart', 'figure'),
    [Input('overview-region-dropdown', 'value'),
     Input('toggle-custom-wptm', 'value'),
     Input('toggle-percent', 'value')]
)
def update_overview_chart(region, custom_wptm, percent):
    from overview_chart_builder import build_overview_chart
    inc_custom = bool(custom_wptm and "include" in custom_wptm)
    is_percent = bool(percent and "percent" in percent)
    fig, style = build_overview_chart(dash_app, region, inc_custom, is_percent)
    return fig

@dash_app.callback(
    Output('url', 'search'),
    Output('url', 'pathname'),
    Input('overview-chart', 'clickData'),
    prevent_initial_call=True
)
def navigate_to_detailed(clickData):
    if not clickData:
        return dash.no_update, dash.no_update
        
    pt = clickData['points'][0]
    if 'customdata' in pt:
        raw_c = pt['customdata']
        if isinstance(raw_c, list):
            raw_c = raw_c[0]
            
        return f"?country={urllib.parse.quote(str(raw_c))}", "/detailed"
        
    return dash.no_update, dash.no_update

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8000))
    dash_app.run(debug=True, host='0.0.0.0', port=port)

