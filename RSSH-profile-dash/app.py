import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
from components import figures
from data.dummy_data import get_geography_data

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

def get_graph_shell(id_name, height):
    return dcc.Graph(
        id=id_name,
        config={'displayModeBar': False},
        style={"height": height}
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
        # Left Column
        html.Div(className="column", children=[
            html.Div("Overall Health System indicators", className="section-header"),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("UHC (Overall)"),
                    html.Span("val", id="val-uhc-overall", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                html.Div("Universal Health Coverage overall index.", className="plot-desc"),
                get_graph_shell("graph-uhc-overall", "150px")
            ]),

            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("UHC (Infectious Disease)"),
                    html.Span("val", id="val-uhc-id", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                html.Div("Universal Health Coverage infectious disease index.", className="plot-desc"),
                get_graph_shell("graph-uhc-id", "150px")
            ]),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("UHC (RMNCH)"),
                    html.Span("val", id="val-uhc-rmnch", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                html.Div("Universal Health Coverage reproductive, maternal, newborn and child health index.", className="plot-desc"),
                get_graph_shell("graph-uhc-rmnch", "150px")
            ]),

            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Coverage of antenatal care (ANC4)"),
                    html.Span("val", id="val-anc4", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                html.Div("The percentage of women aged 15-49 with a live birth in a given time period, attended at least four times during pregnancy by any provider (skilled or unskilled) for reasons related to the pregnancy.", className="plot-desc"),
                get_graph_shell("graph-anc4", "150px")
            ]),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Maternal Mortality Rate (MMR)"),
                    html.Span("val", id="val-mmr", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                html.Div("Maternal mortality ratio (per 100,000 live births). Note: Y-axis is inverted where lower is better.", className="plot-desc"),
                get_graph_shell("graph-mmr", "150px")
            ]),

            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Coverage of immunisation of children (DTP3)"),
                    html.Span("val", id="val-dtp3", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                html.Div("The percentage of one-year-olds who have received three doses of the combined diphtheria, tetanus toxoid, and pertussis vaccine in a given year.", className="plot-desc"),
                get_graph_shell("graph-dtp3", "150px")
            ])
        ]),
        
        # Middle Column
        html.Div(className="column", children=[
            html.Div("Country health expenditure & Global Fund investments on RSSH", className="section-header"),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Current Health Expenditure (CHE) as % of GDP"),
                    html.Span("val", id="val-che", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_graph_shell("graph-che", "150px")
            ]),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Domestic General Gov. Health Exp. (GGHE-D) as % of GDP"),
                    html.Span("val", id="val-gghe-d", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_graph_shell("graph-gghe-d", "150px")
            ]),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Composition of Current Health Expenditure (CHE) in 2019"),
                    html.Span("val", id="val-composition", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title"),
                get_graph_shell("graph-composition", "150px")
            ]),

            html.Div(className="plot-container", children=[
                html.Div("RSSH investment in 2017-2022 allocation periods (approved budget)", className="plot-title-grey"),
                html.Div("The values to the right of the bars are the percentage of the total amount (contributory and direct combined) for each component...", className="plot-desc"),
                get_graph_shell("graph-rssh", "280px")
            ])
        ]),
        
        # Right Column
        html.Div(className="column", children=[
            html.Div("Health systems tracers", className="section-header"),
            
            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Human resources for health availability"),
                    html.Span("val", id="val-hr", style={"color": figures.C_MED, "float": "right", "fontSize": "10px"})
                ], className="plot-title-grey"),
                get_graph_shell("graph-hr", "100px")
            ]),

            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Service delivery availability: Sum of health posts, centres/clinics and hospitals in NA"),
                    html.Span("NA", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title-grey"),
                html.Div("[1] \"Data unavailable\"", className="data-unavailable")
            ]),

            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Medicines availability: Availability of selected generic medicines (24 tracers) in 2016"),
                    html.Span("val", id="val-med-avail", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title-grey"),
                get_graph_shell("graph-med-avail", "40px")
            ]),

            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Service diagnostics availability: Availability of selected generic medicines (24 tracers) in 2016"),
                    html.Span("val", id="val-diag-avail", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title-grey"),
                get_graph_shell("graph-diag-avail", "40px")
            ]),

            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("External supervision: Facilities which received at least one external supervisory visit from the district, regional or national office during the six months before the survey in NA"),
                    html.Span("3", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title-grey"),
                html.Div("[1] \"Data unavailable\"", className="data-unavailable")
            ]),

            html.Div(className="plot-container", children=[
                html.Div([
                    html.Span("Absence rate: Health workers that are not off duty who are absent from the facility on an announced visit (sampled randomly from ten workers in 2013)"),
                    html.Span("val", id="val-absence", style={"color": figures.C_MED, "float": "right"})
                ], className="plot-title-grey"),
                get_graph_shell("graph-absence", "40px")
            ]),

            html.Div(className="plot-container", children=[
                html.Div("How to read the plots", className="section-header-green-small"),
                html.Div([
                    html.Span("Green represents ", style={"fontSize": "10px"}),
                    html.B(id="footer-country-name", style={"color": "#1a8f4c", "fontSize": "10px"}),
                    html.Span(". Orange represents ", style={"fontSize": "10px"}),
                    html.B("the average (median) values from the income group of", style={"color": "#df8a46", "fontSize": "10px"}),
                    html.Span(id="footer-country-income", style={"fontSize": "10px"}),
                    html.Span(" The number of countries used to calculate the average is given in orange in the top right corner...", style={"fontSize": "10px"})
                ], style={"marginBottom": "10px"}),
                html.Div("Detailed notes are available on the separate Explanatory Notes page", style={"fontSize": "10px", "color": "#666"}),
                html.Div("Sources:", style={"fontSize": "9px", "color": "#888", "marginTop": "10px"}),
                html.Div("Left column: Household Surveys... Middle column: GHED, WHO...", style={"fontSize": "8px", "color": "#888"})
            ])
        ])
    ])
], className="container", style={"fontFamily": "Arial, sans-serif"})


@app.callback(
    [
        Output('header-country-name', 'children'),
        Output('header-income-group', 'children'),
        Output('footer-country-name', 'children'),
        Output('footer-country-income', 'children'),
        Output('graph-dtp3', 'figure'),
        Output('graph-anc4', 'figure'),
        Output('graph-uhc-overall', 'figure'),
        Output('graph-uhc-id', 'figure'),
        Output('graph-uhc-rmnch', 'figure'),
        Output('graph-mmr', 'figure'),
        Output('graph-che', 'figure'),
        Output('graph-gghe-d', 'figure'),
        Output('graph-composition', 'figure'),
        Output('graph-rssh', 'figure'),
        Output('graph-hr', 'figure'),
        Output('graph-med-avail', 'figure'),
        Output('graph-diag-avail', 'figure'),
        Output('graph-absence', 'figure'),
        
        # Values next to titles
        Output('val-dtp3', 'children'),
        Output('val-anc4', 'children'),
        Output('val-uhc-overall', 'children'),
        Output('val-uhc-id', 'children'),
        Output('val-uhc-rmnch', 'children'),
        Output('val-mmr', 'children'),
        Output('val-che', 'children'),
        Output('val-gghe-d', 'children'),
        Output('val-composition', 'children'),
        Output('val-hr', 'children'),
        Output('val-med-avail', 'children'),
        Output('val-diag-avail', 'children'),
        Output('val-absence', 'children')
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
            income_class = row.iloc[0].get('World Bank Income Classification', 'LLMI')
            if income_class == "LLMI":
                income = "lower middle income"
            elif income_class == "ULMI":
                income = "upper middle income"
            elif income_class == "LI":
                income = "low income"
            else:
                income = str(income_class)
    
    # Generate Figures
    f_dtp3 = figures.fig_dtp3(iso3, cn_name)
    f_anc4 = figures.fig_anc4(iso3, cn_name)
    f_uhc_over = figures.fig_uhc_overall(iso3, cn_name)
    f_uhc_id = figures.fig_uhc_id(iso3, cn_name)
    f_uhc_rmnch = figures.fig_uhc_rmnch(iso3, cn_name)
    f_mmr = figures.fig_mmr(iso3, cn_name)
    f_che = figures.fig_che(iso3, cn_name)
    f_gghe_d = figures.fig_gghe_d(iso3, cn_name)
    f_comp = figures.fig_composition(iso3, cn_name)
    f_rssh = figures.fig_rssh(iso3, cn_name)
    f_hr = figures.fig_hr(iso3, cn_name)
    f_ma = figures.fig_med_avail(iso3, cn_name)
    f_da = figures.fig_diag_avail(iso3, cn_name)
    f_ab = figures.fig_absence(iso3, cn_name)
    
    # Pseudo-randomize some indicator numbers to make them dynamic too
    from data.dummy_data import generate_pseudo_random_variance
    v_base = lambda b: str(max(0, b + generate_pseudo_random_variance(iso3, 0, 5)))
    
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
        cn_name,
        f" {cn_name} ({income}).",
        
        f_dtp3, f_anc4, f_uhc_over, f_uhc_id, f_uhc_rmnch, f_mmr,
        f_che, f_gghe_d, f_comp, f_rssh,
        f_hr, f_ma, f_da, f_ab,
        
        get_latest_val(f_dtp3), get_latest_val(f_anc4), get_latest_val(f_uhc_over), get_latest_val(f_uhc_id), get_latest_val(f_uhc_rmnch), get_latest_val(f_mmr),
        get_latest_val(f_che), get_latest_val(f_gghe_d), v_base(50), "phy: 2 | n&m: 10", v_base(5),
        v_base(4), v_base(1)
    ]

if __name__ == '__main__':
    app.run(debug=True, port=8050)
