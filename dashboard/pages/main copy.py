import dash
import dash_bootstrap_components as dbc
from dash import html
from dash import dcc
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)


SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "backgroundColor": "#081A51",
}

CONTENT_STYLE = {
    "marginLeft": "18rem",
    "marginRight": "2rem",
    "padding": "2rem 1rem",
}


sidebar = html.Div(
    [   
        html.Img(src=app.get_asset_url('team_jerry_logo.png'), style={'height':'61px', 'width':'163px', "marginLeft": "20px"}),

        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Overview", href="/", active="exact", className='text-light font-weight-bold'),
                dbc.NavLink("Check Balance", href="/check-balance", active="exact", className='text-light font-weight-bold'),
                dbc.NavLink("PayNow Transfer", href="/paynow-transfer", active="exact", className='text-light font-weight-bold'),
                dbc.NavLink("Scan To Pay", href="/scan-to-pay", active="exact", className='text-light font-weight-bold')
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)


content = html.Div(id="page-content", children=[], style=CONTENT_STYLE)


app.layout = html.Div(
    children=[
    dcc.Location(id="url"),
    sidebar,
    content
])

# render page structure
@app.callback(
    Output(component_id="page-content", component_property="children"),
    Input(component_id="url", component_property="pathname")
)
def render_page(pathname):
    if pathname == "/":
        page = [
            html.H1(id='overview-header', children="Overview", style={'textAlign':'center', "color":"#081A51"}),
            dcc.Graph(id="overview-graph",
                    figure={}
                    ),
        ]
        
    else:
        page = [
            html.H1(id='business-function-header', children="", style={'textAlign':'center', "color":"#081A51"}),
            dcc.Dropdown(id='metric-dropdown',
                        options=[{"label":x, "value":x} for x in ["Users", "Sessions"]],
                        value="Users"
                        ),
            dcc.Graph(id="business-function-graph",
                    figure={}
                    ),
        ]
    return page

# render business function pages
@app.callback(
    [Output(component_id='business-function-header', component_property="children"), Output(component_id='business-function-graph', component_property='figure')],
    [Input("url", "pathname"), Input(component_id='metric-dropdown', component_property='value')]
)
def render_business_function_pages(pathname, metric_choice):
    if pathname == "/":
        raise PreventUpdate
    
    check_balance_df = pd.read_csv('../csv/check_balance.csv')
    paynow_transfer_df = pd.read_csv('../csv/paynow_transfer.csv')
    scan_to_pay_df = pd.read_csv('../csv/scan_to_pay.csv')

    def get_fig(df, metric_choice):
        df['date'] = pd.to_datetime(df['date'], format="%d/%m/%y")
        sorted_df = df.sort_values(by="date")
        
        if metric_choice == "Users":
            users_df = sorted_df.groupby(["date"])['account_number'].nunique().reset_index(name="user count")
            fig = px.line(users_df, x="date", y="user count", title="Number of Users Over Time")
        
        elif metric_choice == "Sessions":
            sessions_df = sorted_df.groupby(["date"]).size().reset_index(name="session count")
            fig = px.line(sessions_df, x="date", y="session count", title="Number of Sessions Over Time")
        
        return fig
    
    if pathname == "/check-balance":
        fig = get_fig(check_balance_df, metric_choice)
        return "Check Balance", fig
    
    if pathname == "/paynow-transfer":
        fig = get_fig(paynow_transfer_df, metric_choice)
        return "Paynow Transfer", fig
    
    if pathname == "/scan-to-pay":
        fig = get_fig(scan_to_pay_df, metric_choice)
        return "Scan to Pay", fig
    
    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )

# render overview page
@app.callback(
    Output(component_id='overview-graph', component_property='figure'),
    Input("url", "pathname")
    
)
def render_overview_page(pathname):

    check_balance_df = pd.read_csv('../csv/check_balance.csv')
    paynow_transfer_df = pd.read_csv('../csv/paynow_transfer.csv')
    scan_to_pay_df = pd.read_csv('../csv/scan_to_pay.csv')

    if pathname == "/":
        combined_df = pd.concat([check_balance_df, paynow_transfer_df, scan_to_pay_df], ignore_index=True)
        bank_function_count = combined_df.groupby(["bank_function"]).size().reset_index(name="bank_function_count")
        fig = px.pie(
            bank_function_count,
            values="bank_function_count",
            names="bank_function",
            title="Bank Function Distribution",
            hole=0.6,
            color_discrete_sequence=["#B8D5E5", "#92BFD8", "#63A3C7"]
        )
        return fig

    else:
        PreventUpdate


if __name__=='__main__':
    app.run_server(debug=True, port=3200)
