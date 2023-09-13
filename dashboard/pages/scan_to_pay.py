import dash
import dash_bootstrap_components as dbc
from dash import html
from dash import dcc
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


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
                dbc.NavLink("Overview", href="/overview", active="exact", className='text-light font-weight-bold'),
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


content = html.Div(id="page-content", children=[
        html.H1(id='business-function-name', children="", style={'textAlign':'center', "color":"#081A51"}),
        dcc.Dropdown(id='metric-choice',
                    options=[{"label":x, "value":x} for x in ["Users", "Sessions"]],
                    value="Users"
                    ),
        dcc.Graph(id="my-graph",
                figure={}
                ),
], style=CONTENT_STYLE)


app.layout = html.Div(
    children=[
    dcc.Location(id="url"),
    sidebar,
    content
])


@app.callback(
    [Output(component_id='business-function-name', component_property="children"), Output(component_id='my-graph', component_property='figure')],
    [Input("url", "pathname"), Input(component_id='metric-choice', component_property='value')]
    
)
def render_page_content(pathname="/scan-to-pay", metric_choice="Users"):

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

    if pathname == "/overview":
        return [

                ]
    
    elif pathname == "/check-balance":
        return [

                ]
    
    elif pathname == "/paynow-transfer":

        return [

                ]
    
    elif pathname == "/scan-to-pay":

        scan_to_pay_df = pd.read_csv('../csv/scan_to_pay.csv')
        fig = get_fig(scan_to_pay_df, metric_choice)

        return "Scan to Pay", fig

    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )


if __name__=='__main__':
    app.run_server(debug=True, port=3200)
