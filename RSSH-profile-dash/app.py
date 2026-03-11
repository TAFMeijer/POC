import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
from components import figures
from data.dummy_data import get_geography_data, get_country_income_group

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "RSSH Profile Dashboard"

# Load Geography Options
geo_df = get_geography_data()
dropdown_options = []
if not geo_df.empty:
    for _, row in geo_df.iterrows():
        dropdown_options.append({
            'label': row.get('Full Country Name', row.get('ISO3')),
            'value': row.get('ISO3')
        })
    default_iso = dropdown_options[0]['value'] if dropdown_options else "NGA"
    default_name = dropdown_options[0]['label'] if dropdown_options else "Nigeria"
else:
    # Fallback if no file exists
    default_iso = "NGA"
    default_name = "Nigeria"
    dropdown_options = [{'label': 'Nigeria', 'value': 'NGA'}]

# Load Chart URLs
try:
    url_df = pd.read_excel('data/URLs.xlsx')
    url_map = url_df.set_index('Indicator').to_dict('index')
except Exception as e:
    print(f"Error loading URLs: {e}")
    url_map = {}

def get_source_link(indicator_name):
    if indicator_name in url_map:
        source_name = url_map[indicator_name].get('Source', 'WHO')
        url_link = url_map[indicator_name].get('URL', '#')
        return html.Div(
            html.A(f"Source: {source_name}", href=url_link, target="_blank", style={"color": "#666", "textDecoration": "underline"}),
            className="plot-desc"
        )
    return html.Div("Source: Unknown", className="plot-desc")

def get_graph_shell(id_name, height=None):
    return html.Div(
        dcc.Graph(
            id=id_name,
            config={'displayModeBar': False},
            style={"height": "100%", "width": "100%"}
        ),
        style={"flexGrow": "1", "minHeight": "0"}
    )

app.layout = html.Div([
    html.Div(className="main-header", children=[
        html.Div([
            html.Span("RSSH PROFILE APP", style={"fontWeight": "bold", "marginRight": "15px"}),
            dcc.Dropdown(
                id='country-dropdown',
                options=dropdown_options,
                value=default_iso,
                clearable=False,
                style={"width": "300px", "display": "inline-block", "verticalAlign": "middle", "fontSize": "14px"}
            )
        ], style={"display": "flex", "alignItems": "center"}),
    ], style={"marginBottom": "15px", "borderBottom": "1px solid #ccc", "paddingBottom": "10px"}),

    html.Div(className="main-header", children=[
        html.Div([
            html.Span(id="header-country-name", className="country-name"),
            html.Span(id="header-income-group", className="country-income")
        ], className="header-left"),
        html.Div("RSSH PROFILE", className="header-right")
    ]),
    
    html.Div(className="dashboard-grid", children=[
        # Column 1: Universal Health Coverage indices
        html.Div(className="column", children=[
            html.Div("Universal Health Coverage indices", className="section-header"),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("UHC (Overall)", id="title-uhc-overall"),
                    html.Span("val", id="val-uhc-overall", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_source_link("UHC (overall)"),
                dbc.Tooltip("Universal Health Coverage overall index.", target="title-uhc-overall", placement="bottom"),
                get_graph_shell("graph-uhc-overall", "150px")
            ]),

            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("UHC (Infectious Disease)", id="title-uhc-id"),
                    html.Span("val", id="val-uhc-id", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_source_link("UHC (Infectious Disease)"),
                dbc.Tooltip("Universal Health Coverage infectious disease index.", target="title-uhc-id", placement="bottom"),
                get_graph_shell("graph-uhc-id", "150px")
            ]),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("UHC (RMNCH)", id="title-uhc-rmnch"),
                    html.Span("val", id="val-uhc-rmnch", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_source_link("UHC (RMNCH)"),
                dbc.Tooltip("Universal Health Coverage reproductive, maternal, newborn and child health index.", target="title-uhc-rmnch", placement="bottom"),
                get_graph_shell("graph-uhc-rmnch", "150px")
            ])
        ]),

        # Column 2: Maternal, Newborn & Child Health
        html.Div(className="column", children=[
            html.Div("Maternal, Newborn & Child Health", className="section-header"),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Coverage of antenatal care (ANC4)", id="title-anc4"),
                    html.Span("val", id="val-anc4", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_source_link("Coverage of antenatal care (ANC4)"),
                dbc.Tooltip("The percentage of women aged 15-49 with a live birth in a given time period, attended at least four times during pregnancy by any provider (skilled or unskilled) for reasons related to the pregnancy.", target="title-anc4", placement="bottom"),
                get_graph_shell("graph-anc4", "150px")
            ]),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Maternal Mortality Rate (MMR)", id="title-mmr"),
                    html.Span("val", id="val-mmr", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_source_link("Maternal Mortality Rate (MMR)"),
                dbc.Tooltip("Maternal mortality ratio (per 100,000 live births). Note: Y-axis is inverted where lower is better.", target="title-mmr", placement="bottom"),
                get_graph_shell("graph-mmr", "150px")
            ]),

            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Coverage of immunisation of children (DTP3)", id="title-dtp3"),
                    html.Span("val", id="val-dtp3", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_source_link("Coverage of immunisation of children (DTP3)"),
                dbc.Tooltip("The percentage of one-year-olds who have received three doses of the combined DTP vaccine in a given year.", target="title-dtp3", placement="bottom"),
                get_graph_shell("graph-dtp3", "150px")
            ])
        ]),
        
        # Column 3: Health Workforce
        html.Div(className="column", children=[
            html.Div("Health Workforce", className="section-header"),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Medical Doctors (per 10k pop)", id="title-hr1"),
                    html.Span("val", id="val-hr1", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_source_link("Medical Doctors (per 10k pop)"),
                dbc.Tooltip("Number of medical doctors per 10,000 population.", target="title-hr1", placement="bottom"),
                get_graph_shell("graph-hr1", "150px")
            ]),

            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Nursing and midwifery personnel (per 10k pop)", id="title-hr2"),
                    html.Span("val", id="val-hr2", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_source_link("Nursing and midwifery personnel (per 10k pop)"),
                dbc.Tooltip("Number of nursing and midwifery personnel per 10,000 population.", target="title-hr2", placement="bottom"),
                get_graph_shell("graph-hr2", "150px")
            ]),

            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Community Health Workers (per 10k pop)", id="title-hr3"),
                    html.Span("val", id="val-hr3", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_source_link("Community Health Workers (per 10k pop)"),
                dbc.Tooltip("Number of community health workers per 10,000 population. Note: data is provided as absolute number, and converted to per 10k pop for comparability to MD and nursing and midwifery personnel", target="title-hr3", placement="bottom"),
                get_graph_shell("graph-hr3", "150px")
            ])
        ]),
        
        # Column 4: Health system expenditure
        html.Div(className="column", children=[
            html.Div("Health system expenditure", className="section-header"),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Current Health Expenditure (CHE) as % of GDP", id="title-che"),
                    html.Span("val", id="val-che", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_source_link("Current Health Expenditure (CHE) as % of GDP"),
                dbc.Tooltip("Current Health Expenditure (CHE) expressed as a percentage of Gross Domestic Product (GDP).", target="title-che", placement="bottom"),
                get_graph_shell("graph-che", "150px")
            ]),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Domestic Govt. Health Exp. (GGHE-D) as % of GDP", id="title-gghe-d"),
                    html.Span("val", id="val-gghe-d", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_source_link("Domestic Govt. Health Exp. (GGHE-D) as % of GDP"),
                dbc.Tooltip("Domestic General Government Health Expenditure (GGHE-D) expressed as a percentage of Gross Domestic Product (GDP).", target="title-gghe-d", placement="bottom"),
                get_graph_shell("graph-gghe-d", "150px")
            ]),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Out of pocket expenditure (OOP) as % of GDP", id="title-oop"),
                    html.Span("val", id="val-oop", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_source_link("Out of pocket expenditure (OOP) as % of GDP"),
                dbc.Tooltip("Out-of-pocket expenditure (OOP) expressed as a percentage of Gross Domestic Product (GDP). Note: OOP data is provided as US$ per capita", target="title-oop", placement="bottom"),
                get_graph_shell("graph-oop", "150px")
            ])
        ])
    ])
], className="container", style={"fontFamily": "Arial, sans-serif"})


@app.callback(
    [
        Output('header-country-name', 'children'),
        Output('header-income-group', 'children'),
        Output('graph-dtp3', 'figure'),
        Output('graph-anc4', 'figure'),
        Output('graph-uhc-overall', 'figure'),
        Output('graph-uhc-id', 'figure'),
        Output('graph-uhc-rmnch', 'figure'),
        Output('graph-mmr', 'figure'),
        Output('graph-hr1', 'figure'),
        Output('graph-hr2', 'figure'),
        Output('graph-hr3', 'figure'),
        Output('graph-che', 'figure'),
        Output('graph-gghe-d', 'figure'),
        Output('graph-oop', 'figure'),
        
        # Values next to titles
        Output('val-dtp3', 'children'),
        Output('val-anc4', 'children'),
        Output('val-uhc-overall', 'children'),
        Output('val-uhc-id', 'children'),
        Output('val-uhc-rmnch', 'children'),
        Output('val-mmr', 'children'),
        Output('val-hr1', 'children'),
        Output('val-hr2', 'children'),
        Output('val-hr3', 'children'),
        Output('val-che', 'children'),
        Output('val-gghe-d', 'children'),
        Output('val-oop', 'children')
    ],
    [Input('country-dropdown', 'value')]
)
def update_dashboard(iso3):
    # Lookup country name and income
    cn_name = "Nigeria"
    income = "lower middle income"
    if not geo_df.empty:
        row = geo_df[geo_df['ISO3'] == iso3]
        if not row.empty:
            cn_name = row.iloc[0].get('Full Country Name', cn_name)
            
    wb_income = get_country_income_group(iso3)
    if wb_income != "Unknown":
        income = wb_income.lower().replace("-", " ").replace(" countries", "")
    
    # Generate Figures
    f_dtp3 = figures.fig_dtp3(iso3, cn_name)
    f_anc4 = figures.fig_anc4(iso3, cn_name)
    f_uhc_over = figures.fig_uhc_overall(iso3, cn_name)
    f_uhc_id = figures.fig_uhc_id(iso3, cn_name)
    f_uhc_rmnch = figures.fig_uhc_rmnch(iso3, cn_name)
    f_mmr = figures.fig_mmr(iso3, cn_name)
    f_hr1 = figures.fig_md(iso3, cn_name)
    f_hr2 = figures.fig_nurse(iso3, cn_name)
    f_hr3 = figures.fig_chw(iso3, cn_name)
    f_che = figures.fig_che(iso3, cn_name)
    f_gghe_d = figures.fig_gghe_d(iso3, cn_name)
    f_oop = figures.fig_oop(iso3, cn_name)
    
    def get_latest_val(fig):
        try:
            # Scan traces to find the one holding Count metadata
            for trace in fig.data:
                if trace.customdata is not None:
                    y_vals = trace.y
                    custom_vals = trace.customdata
                    valid_pairs = [(y, c) for y, c in zip(y_vals, custom_vals) if y is not None and y == y and c is not None and c == c]
                    if valid_pairs:
                        return str(int(valid_pairs[-1][1]))
        except:
            pass
        return "--"
        
    return [
        f"{cn_name} ",
        f"| {income}",
        
        f_dtp3, f_anc4, f_uhc_over, f_uhc_id, f_uhc_rmnch, f_mmr,
        f_hr1, f_hr2, f_hr3,
        f_che, f_gghe_d, f_oop,
        
        get_latest_val(f_dtp3), get_latest_val(f_anc4), get_latest_val(f_uhc_over), get_latest_val(f_uhc_id), get_latest_val(f_uhc_rmnch), get_latest_val(f_mmr),
        get_latest_val(f_hr1), get_latest_val(f_hr2), get_latest_val(f_hr3),
        get_latest_val(f_che), get_latest_val(f_gghe_d), get_latest_val(f_oop)
    ]

if __name__ == '__main__':
    app.run(debug=True, port=8050)
