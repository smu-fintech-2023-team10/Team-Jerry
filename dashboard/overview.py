import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from dash import html
from dash import dcc
import plotly.express as px
from dash.dependencies import Input, Output
import pandas as pd
import base64
import os

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#081A51",
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [   
        html.Img(src=app.get_asset_url('team_jerry_logo.png'), style={'height':'61px', 'width':'163px', "margin-left": "20px"}),

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

top_bar = html.Div(
    [
        html.H1("Overview", style={"margin-left": "270px", "margin-top": "20px", "font-weight": "bold", "font-size": "40px"}),
        html.Hr(),
    ]
)

content = html.Div(id="page-content", children=[], style=CONTENT_STYLE)

app.layout = html.Div(
    children=[
    dcc.Location(id="url"),
    sidebar,
    top_bar,
    content
])

if __name__=='__main__':
    app.run_server(debug=True, port=3000)
