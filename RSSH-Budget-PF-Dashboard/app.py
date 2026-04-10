import dash
from dash import dcc, html, Input, Output, State # Triggered hot-reload for refreshed mapping data
import io
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json

from data_processing import df_b, df_i, df_w, COMP_COLORS, SHADES, TYPE_TO_WEIGHT, indicator_order
app = dash.Dash(__name__, url_base_pathname='/budget-pf-poc/', external_stylesheets=[dbc.themes.FLATLY])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Img(src=app.get_asset_url('GF Logo.PNG'), className="dashboard-logo"), width="auto"),
        dbc.Col([
            html.Div("Budget - PF POC Dashboard", className="dashboard-title"),
            html.Div("A proof of concept dashboard for Funding Request and Grant Making review of the mapping between Budget and Performance Framework, using selected GC7 data for now. To be used at Country-level review or Implementation Period-level.", 
                   className="dashboard-subtitle")
        ], width=12, className="title-wrapper")
    ], className="header-container"),
    dbc.Row([
        dbc.Col([
            dbc.Label("Select Country"),
            dcc.Dropdown(
                id='country-dropdown',
                options=[{'label': c, 'value': c} for c in df_b['Country'].dropna().unique()],
                value=df_b['Country'].dropna().unique()[0] if len(df_b['Country'].dropna().unique()) > 0 else None
            )
        ], width=3),
        dbc.Col([
            dbc.Label("Select Implementation Period"),
            dcc.Dropdown(id='ip-dropdown')
        ], width=3),
        dbc.Col([
            dbc.Label("Select Component"),
            dcc.Dropdown(
                id='component-dropdown',
                options=[{'label': 'All Components', 'value': 'ALL'}] + [{'label': c, 'value': c} for c in ['HIV/AIDS', 'Tuberculosis', 'Malaria', 'RSSH', 'Multi-Component', 'Program Management']],
                value='ALL'
            )
        ], width=3),
        dbc.Col([
            dbc.Button("Download Excel Export", id="btn-download", color="secondary", className="w-100 btn-export"),
            dcc.Download(id="download-excel")
        ], width=3)
    ], className="filter-row"),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='main-chart', clear_on_unhover=True),
            dcc.Tooltip(id='graph-tooltip')
        ], width=12, className="chart-wrapper")
    ])
], fluid=True, className="dashboard-container")

@app.callback(
    Output('ip-dropdown', 'options'),
    Output('ip-dropdown', 'value'),
    Input('country-dropdown', 'value')
)
def update_ip_dropdown(country):
    if not country:
        return [], None
    ips = df_b[df_b['Country'] == country]['Implementation Period Name'].dropna().unique()
    opts = [{'label': 'All Implementation Periods', 'value': 'ALL'}] + [{'label': ip, 'value': ip} for ip in ips]
    val = 'ALL'
    return opts, val

@app.callback(
    [Output('main-chart', 'figure'),
     Output('main-chart', 'style')],
    [Input('country-dropdown', 'value'),
     Input('ip-dropdown', 'value'),
     Input('component-dropdown', 'value')]
)
def update_chart(country, ip, component):
    from chart_builder import build_main_chart
    return build_main_chart(app, country, ip, component)

@app.callback(
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
        return False, dash.no_update, dash.no_update
        
    cd = pt["customdata"]
    if isinstance(cd, list):
        cd = cd[0]
        
    try:
        obj = json.loads(cd)
    except Exception:
        return False, dash.no_update, dash.no_update
        
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
        
    style_table = {'borderCollapse': 'collapse', 'textAlign': 'left', 'width': '100%', 'fontSize': fsize, 'whiteSpace': 'normal', 'wordWrap': 'break-word', 'tableLayout': 'fixed'}
    style_th = {'padding': pad, 'borderBottom': '1px solid #ddd', 'backgroundColor': '#f8f9fa', 'color': '#333', 'whiteSpace': 'normal', 'wordWrap': 'break-word'}
    style_td = {'padding': pad, 'borderBottom': '1px solid #eee', 'color': '#333', 'whiteSpace': 'normal', 'wordWrap': 'break-word'}
        
    dir_ = 'right' if type_ == 'BUDGET' else 'left'
    if bbox["y0"] > 450:
        dir_ = 'top'

    if type_ == 'BUDGET':
        if not data:
            return True, bbox, html.Div([
                html.B("Budget Details"), html.Br(), "No Interventions"
            ])
        rows = [html.Tr([html.Th("Intervention", style=style_th), html.Th("Budget ($M)", style=style_th)])]
        for d in data:
            rows.append(html.Tr([html.Td(d['Intervention'], style=style_td), html.Td(d['Amount'], style=style_td)]))
        return True, bbox, html.Div([
            html.B("Interventions", style={'marginBottom': '10px', 'display': 'block'}),
            html.Table(rows, style=style_table)
        ], style={'width': '375px'}), dir_
        
    elif type_ == 'INDICATOR_CUSTOM':
        data = obj.get('data', [])
        title = obj.get('title', 'Indicators')
        # Setting Indicator Name roughly 3x wider (75% to 25%)
        rows = [html.Tr([html.Th("Implementation Period", style={**style_th, 'width': '25%'}), html.Th("Indicator Name", style={**style_th, 'width': '75%'})])]
        for d in data:
            rows.append(html.Tr([html.Td(d['ip'], style=style_td), html.Td(d['name'], style=style_td)]))
        return True, bbox, html.Div([
            html.B(title, style={'marginBottom': '10px', 'display': 'block'}),
            html.Table(rows, style=style_table)
        ], style={'width': '525px'}), dir_
        
    elif type_ == 'INDICATOR_STANDARD':
        data = obj.get('data', [])
        title = obj.get('title', 'Indicators')
        # Setting Indicator Name vastly wider (65%) vs IP (20%) and Code (15%)
        rows = [html.Tr([html.Th("Implementation Period", style={**style_th, 'width': '20%'}), html.Th("Indicator Code", style={**style_th, 'width': '15%'}), html.Th("Indicator Name", style={**style_th, 'width': '65%'})])]
        for d in data:
            rows.append(html.Tr([html.Td(d['ip'], style=style_td), html.Td(d['code'], style=style_td), html.Td(d['desc'], style=style_td)]))
        return True, bbox, html.Div([
            html.B(title, style={'marginBottom': '10px', 'display': 'block'}),
            html.Table(rows, style=style_table)
        ], style={'width': '600px'}), dir_
        
    elif type_ == 'WPTM':
        data = obj.get('data', [])
        rows = [html.Tr([html.Th("Implementation Period", style=style_th), html.Th("Key Activity", style=style_th)])]
        for d in data:
            rows.append(html.Tr([html.Td(d['ip'], style=style_td), html.Td(d['act'], style=style_td)]))
        return True, bbox, html.Div([
            html.B("WPTM Activities", style={'marginBottom': '10px', 'display': 'block'}),
            html.Table(rows, style=style_table)
        ], style={'width': '375px'}), dir_

    return False, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    Output("download-excel", "data"),
    Input("btn-download", "n_clicks"),
    State("country-dropdown", "value"),
    State("ip-dropdown", "value"),
    State("component-dropdown", "value"),
    prevent_initial_call=True
)
def download_excel(n_clicks, country, ip, component):
    from excel_exporter import build_excel_export
    return build_excel_export(n_clicks, country, ip, component)

if __name__ == '__main__':
    app.run(debug=True, port=8050)
