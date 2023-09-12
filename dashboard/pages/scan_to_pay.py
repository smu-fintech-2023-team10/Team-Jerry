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


content = html.Div(id="page-content", children=[], style=CONTENT_STYLE)

app.layout = html.Div(
    children=[
    dcc.Location(id="url"),
    sidebar,
    content
])

@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")],
)
def render_page_content(pathname):
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

        # convert scan to pay csv into a pandas dataframe
        scan_to_pay_df = pd.read_csv('../csv/scan_to_pay.csv')

        # change date to a datetime column
        scan_to_pay_df['date'] = pd.to_datetime(scan_to_pay_df['date'], format="%d/%m/%y")

        # sort by date so can plot in chronological order
        sorted_scan_to_pay = scan_to_pay_df.sort_values(by="date")

        # to get no. of users over time groupby date
        users_df = sorted_scan_to_pay.groupby(["date"]).size().reset_index(name="count")

        user_fig = px.line(users_df, x="date", y="count", title="Number of Users Over Time")

        return [
                html.H1('Scan to Pay', style={'textAlign':'center', "color":"#081A51"}),
                dcc.Graph(id='bargraph', figure=user_fig)
                ]

    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )

if __name__=='__main__':
    app.run_server(debug=True, port=3200)
