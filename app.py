import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import json
import urllib.parse

from data_processing import df_b, df_i, available_regions, country_to_shortname, country_to_region
from chart_builder import build_main_chart
from overview_chart_builder import build_overview_chart
from excel_exporter import build_excel_export

dash_app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], suppress_callback_exceptions=True)

# Expose the standard Flask server for Gunicorn / WSGI deployments (Azure App Service)
app = dash_app.server

# Shared toggle style to avoid repetition in layout
_TOGGLE_STYLE = {'fontSize': '14px', 'display': 'inline-block', 'marginTop': '25px', 'marginRight': '30px'}


def _is_checked(toggle_value, key):
    """Parse a DBC Checklist toggle value."""
    return bool(toggle_value and key in toggle_value)


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
                " GC7 and C19RM data for now.",
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
                dbc.Checklist(options=[{"label": "Include Custom & WPTM", "value": "include"}],
                              value=[], id="toggle-custom-wptm", switch=True,
                              className="large-toggle", style=_TOGGLE_STYLE),
                dbc.Checklist(options=[{"label": "Merge Components", "value": "merge"}],
                              value=[], id="toggle-merge", switch=True,
                              className="large-toggle", style=_TOGGLE_STYLE),
                dbc.Checklist(options=[{"label": "Percentage View", "value": "percent"}],
                              value=[], id="toggle-percent", switch=True,
                              className="large-toggle", style=_TOGGLE_STYLE),
                dbc.Checklist(options=[{"label": "Exclude PM/PfR", "value": "exclude"}],
                              value=[], id="toggle-exclude-pm", switch=True,
                              className="large-toggle", style=_TOGGLE_STYLE),
                dbc.Checklist(options=[{"label": "Exclude C19RM", "value": "exclude"}],
                              value=[], id="toggle-exclude-c19rm", switch=True,
                              className="large-toggle", style={**_TOGGLE_STYLE, 'marginRight': '0px'})
            ], width=8, className="d-flex align-items-center")
        ], className="filter-row"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Checklist(
                        options=[{"label": "Sort High-to-Low", "value": "sort"}],
                        value=[], id="toggle-sort-budget", switch=True, className="large-toggle",
                        style={'position': 'absolute', 'left': '580px', 'top': '48px',
                               'zIndex': '999', 'fontSize': '12px'}
                    ),
                    dcc.Graph(id='overview-chart', clear_on_unhover=True)
                ], style={'position': 'relative'})
            ], width=12, className="chart-wrapper")
        ])
    ])


def layout_detailed(country='Benin'):
    region_val = country_to_region.get(country, 'WCA') if country != 'ALL' else 'ALL'

    if region_val == 'ALL':
        c_opts = df_b['Country'].dropna().unique()
    else:
        c_opts = [c for c in df_b['Country'].dropna().unique() if country_to_region.get(c) == region_val]

    if country == 'ALL':
        ips = df_b['Implementation Period Name'].dropna().unique()
    else:
        ips = df_b[df_b['Country'] == country]['Implementation Period Name'].dropna().unique()

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
                dbc.Label("Select Grant", style={'fontSize': '14px'}),
                dcc.Dropdown(
                    id='ip-dropdown',
                    options=[{'label': 'All Grants', 'value': 'ALL'}] + [{'label': ip, 'value': ip} for ip in ips],
                    value='ALL'
                )
            ], width=2),
            dbc.Col([
                dbc.Label("Select Component", style={'fontSize': '14px'}),
                dcc.Dropdown(
                    id='component-dropdown',
                    options=[{'label': 'All Components', 'value': 'ALL'}] + [{'label': c, 'value': c} for c in ['HIV/AIDS', 'Tuberculosis', 'Malaria', 'RSSH', 'Program Management']],
                    value='ALL'
                )
            ], width=2),
            dbc.Col([
                dbc.Checklist(options=[{"label": "Exclude C19RM", "value": "exclude"}],
                              value=[], id="toggle-exclude-c19rm-detailed", switch=True,
                              className="large-toggle", style={**_TOGGLE_STYLE, 'marginTop': '32px', 'marginRight': '0px'})
            ], width=2),
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


# ──────────────────────────────────────────────────────────────────────────────
# Callbacks
# ──────────────────────────────────────────────────────────────────────────────

@dash_app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('url', 'search')
)
def display_page(pathname, search):
    if pathname and '/detailed' in pathname:
        if search:
            parsed = urllib.parse.parse_qs(search.lstrip('?'))
            if 'country' in parsed:
                return layout_detailed(country=parsed['country'][0])
        return layout_detailed()
    return layout_overview()


@dash_app.callback(
    Output('country-dropdown', 'options'),
    Output('country-dropdown', 'value'),
    Input('region-dropdown', 'value'),
    prevent_initial_call=True
)
def update_country_dropdown(region):
    all_countries = df_b['Country'].dropna().unique()
    if not region or region == 'ALL':
        countries = list(all_countries)
    else:
        countries = [c for c in all_countries if country_to_region.get(c) == region]
    opts = [{'label': 'All Countries', 'value': 'ALL'}] + [
        {'label': country_to_shortname.get(c, c), 'value': c} for c in countries]
    return opts, 'ALL'


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
    opts = [{'label': 'All Grants', 'value': 'ALL'}] + [{'label': ip, 'value': ip} for ip in ips]
    return opts, 'ALL'


@dash_app.callback(
    [Output('main-chart', 'figure'),
     Output('main-chart', 'style'),
     Output('main-chart', 'className')],
    [Input('country-dropdown', 'value'),
     Input('ip-dropdown', 'value'),
     Input('component-dropdown', 'value'),
     Input('region-dropdown', 'value'),
     Input('toggle-exclude-c19rm-detailed', 'value')]
)
def update_chart(country, ip, component, region, excl_c19rm):
    try:
        is_excl_c19rm = _is_checked(excl_c19rm, "exclude")
        fig, style = build_main_chart(dash_app, region, country, ip, component, exclude_c19rm=is_excl_c19rm)
        cname = "modebar-vertical-all" if component == 'ALL' else "modebar-horizontal-single"
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

    # Scale CSS styles based on record count so large tables fit on screen
    if num_rows > 20:
        pad, fsize = '2px', '7.5px'
    elif num_rows > 10:
        pad, fsize = '4px', '9px'
    else:
        pad, fsize = '0.075in', '10.5px'

    style_table = {'borderCollapse': 'collapse', 'textAlign': 'left', 'width': '100%',
                   'fontSize': fsize, 'whiteSpace': 'normal', 'wordWrap': 'break-word', 'tableLayout': 'auto'}
    style_th = {'padding': pad, 'borderBottom': '1px solid #ddd', 'backgroundColor': '#f8f9fa',
                'color': '#333', 'whiteSpace': 'normal', 'wordWrap': 'break-word'}
    style_td = {'padding': pad, 'borderBottom': '1px solid #eee', 'color': '#333',
                'whiteSpace': 'normal', 'wordWrap': 'break-word'}
    style_no_wrap = {**style_td, 'whiteSpace': 'nowrap', 'width': '1%'}
    style_th_no_wrap = {**style_th, 'whiteSpace': 'nowrap', 'width': '1%'}

    # Tooltip direction based on position
    dir_ = 'right' if type_ == 'BUDGET' else 'left'
    if bbox["y0"] < 250:
        dir_ = 'bottom'  # Protect dropdowns at top
    elif bbox["y0"] > 450:
        dir_ = 'top'

    if type_ == 'BUDGET':
        budget_th = {**style_th_no_wrap, 'textAlign': 'right'}
        budget_td = {**style_no_wrap, 'textAlign': 'right'}
        if not data:
            return True, bbox, html.Div([html.B("Budget Details"), html.Br(), "No Interventions"]), dir_
        show_source = any('source' in d for d in data)
        headers = [html.Th("Intervention", style=style_th)]
        if show_source: headers.append(html.Th("Source", style=style_th_no_wrap))
        headers.append(html.Th("Budget ($M)", style=budget_th))
        rows = [html.Tr(headers)]
        
        for d in data:
            cells = [html.Td(d['Intervention'], style=style_td)]
            if show_source: cells.append(html.Td(d.get('source', ''), style=style_no_wrap))
            cells.append(html.Td(d['Amount'], style=budget_td))
            rows.append(html.Tr(cells))

        return True, bbox, html.Div([
            html.B("Interventions", style={'marginBottom': '10px', 'display': 'block'}),
            html.Table(rows, style=style_table)
        ], style={'width': '425px' if show_source else '375px'}), dir_

    elif type_ == 'INDICATOR_CUSTOM':
        title = obj.get('title', 'Indicators')
        show_source = any('source' in d for d in data)
        headers = [html.Th("Indicator Name", style=style_th)]
        if show_source: headers.append(html.Th("Source", style=style_th_no_wrap))
        headers.append(html.Th("Count", style=style_th_no_wrap))
        rows = [html.Tr(headers)]
        
        for d in data:
            cells = [html.Td(d['name'], style=style_td)]
            if show_source: cells.append(html.Td(d.get('source', ''), style=style_no_wrap))
            cells.append(html.Td(d.get('count', ''), style=style_no_wrap))
            rows.append(html.Tr(cells))

        return True, bbox, html.Div([
            html.B(title, style={'marginBottom': '10px', 'display': 'block'}),
            html.Table(rows, style=style_table)
        ], style={'width': '575px' if show_source else '525px'}), dir_

    elif type_ == 'INDICATOR_STANDARD':
        title = obj.get('title', 'Indicators')
        show_source = any('source' in d for d in data)
        headers = [html.Th("Indicator Code", style=style_th_no_wrap), html.Th("Indicator Name", style=style_th)]
        if show_source: headers.append(html.Th("Source", style=style_th_no_wrap))
        headers.append(html.Th("Count", style=style_th_no_wrap))
        rows = [html.Tr(headers)]
        
        for d in data:
            cells = [html.Td(d['code'], style=style_no_wrap), html.Td(d['desc'], style=style_td)]
            if show_source: cells.append(html.Td(d.get('source', ''), style=style_no_wrap))
            cells.append(html.Td(d.get('count', ''), style=style_no_wrap))
            rows.append(html.Tr(cells))

        return True, bbox, html.Div([
            html.B(title, style={'marginBottom': '10px', 'display': 'block'}),
            html.Table(rows, style=style_table)
        ], style={'width': '700px' if show_source else '650px'}), dir_

    elif type_ == 'WPTM':
        show_source = any('source' in d for d in data)
        headers = [html.Th("Grant", style=style_th_no_wrap), html.Th("Key Activity", style=style_th)]
        if show_source: headers.append(html.Th("Source", style=style_th_no_wrap))
        rows = [html.Tr(headers)]
        
        for d in data:
            cells = [html.Td(d['ip'], style=style_no_wrap), html.Td(d['act'], style=style_td)]
            if show_source: cells.append(html.Td(d.get('source', ''), style=style_no_wrap))
            rows.append(html.Tr(cells))

        return True, bbox, html.Div([
            html.B("WPTM Activities", style={'marginBottom': '10px', 'display': 'block'}),
            html.Table(rows, style=style_table)
        ], style={'width': '500px' if show_source else '450px'}), dir_

    return False, dash.no_update, dash.no_update, dash.no_update


@dash_app.callback(
    Output("download-excel", "data"),
    Input("btn-download", "n_clicks"),
    State("country-dropdown", "value"),
    State("ip-dropdown", "value"),
    State("component-dropdown", "value"),
    State("region-dropdown", "value"),
    State("toggle-exclude-c19rm-detailed", "value"),
    prevent_initial_call=True
)
def download_excel(n_clicks, country, ip, component, region, excl_c19rm):
    is_excl_c19rm = _is_checked(excl_c19rm, "exclude")
    return build_excel_export(n_clicks, region, country, ip, component, exclude_c19rm=is_excl_c19rm)


@dash_app.callback(
    Output('overview-chart', 'figure'),
    [Input('overview-region-dropdown', 'value'),
     Input('toggle-custom-wptm', 'value'),
     Input('toggle-merge', 'value'),
     Input('toggle-percent', 'value'),
     Input('toggle-exclude-pm', 'value'),
     Input('toggle-exclude-c19rm', 'value'),
     Input('toggle-sort-budget', 'value')]
)
def update_overview_chart(region, custom_wptm, merge, percent, excl_pm, excl_c19rm, sort_b):
    fig, style = build_overview_chart(
        dash_app, region,
        inc_custom=_is_checked(custom_wptm, "include"),
        is_percent=_is_checked(percent, "percent"),
        is_merged=_is_checked(merge, "merge"),
        exclude_pm=_is_checked(excl_pm, "exclude"),
        exclude_c19rm=_is_checked(excl_c19rm, "exclude"),
        sort_budget=_is_checked(sort_b, "sort"),
    )
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
