import dash, dash_table
import dash_bootstrap_components as dbc
from dash import html
from dash import dcc
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import json


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)


# css
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


# sidebar
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


# define app layout
app.layout = html.Div(
    children=[
        dcc.Location(id="url"),
        sidebar,
        html.Div(id="page-content", children=[], style=CONTENT_STYLE)
])


# render app layout
@app.callback(
    Output(component_id="page-content", component_property="children"),
    Input(component_id="url", component_property="pathname")
)
def render_page(pathname):
    if pathname == "/":
        page = [
            html.H1(id='overview-header', children="Overview", style={'textAlign':'center', "color":"#081A51"}),
            html.Div([
                dcc.Graph(id="bank-function-distribution-fig",
                        figure={},
                        style={'width': '46%', 'display': 'inline-block'}
                        ),
                dcc.Graph(id="sentiment-distribution-fig",
                        figure={},
                        style={'width': '46%', 'display': 'inline-block'}
                        ),
            ])
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
            html.Div([
                html.Link(rel="stylesheet", href="/assets/custom.css"),
                html.Div(
                    id="datatable",
                    style={
                        "paddingLeft": "5%",
                        "paddingRight": "5%"
                    },
                )
            ])
        ]
    return page


# render business function pages
@app.callback(
    [Output(component_id='business-function-header', component_property="children"), Output(component_id='business-function-graph', component_property='figure'), Output(component_id='datatable', component_property='children')],
    [Input("url", "pathname"), Input(component_id='metric-dropdown', component_property='value')]
)
def render_business_function_pages(pathname, metric_choice):
    if pathname == "/":
        raise PreventUpdate
    
    else:

        # generate user metrics chart
        def get_fig(df, metric_choice):
            df['date'] = pd.to_datetime(df['date'], format="%d/%m/%y")
            sorted_df = df.sort_values(by="date")
            
            if metric_choice == "Users":
                users_df = sorted_df.groupby(["date"])['account_number'].nunique().reset_index(name="user count")
                fig = px.line(users_df, x="date", y="user count", title="Number of Users Over Time")
            
            elif metric_choice == "Sessions":
                sessions_df = sorted_df.groupby(["date"]).size().reset_index(name="session count")
                fig = px.line(sessions_df, x="date", y="session count", title="Number of Sessions Over Time")
            
            fig.update_xaxes(rangeslider_visible=True)
            return fig
        
        # generate datatable
        def datatable(df):
            return dash_table.DataTable(
                data=df.to_dict('records'), 
                columns= [{"name": i, "id": i} for i in df.columns],
                sort_action="native",
                sort_mode="multi",
                export_columns="all",
                export_format="csv",
                export_headers="names",
                page_action="native",
                page_size=20,
                # filter_action='native',
                style_cell={'textOverflow': 'ellipsis', 'maxWidth': '150px'},
            )
        
        if pathname == "/check-balance":
            name = "Check Balance"
            df = pd.read_csv('../csv/check_balance.csv')
            
        
        if pathname == "/paynow-transfer":
            name = "Paynow Transfer"
            df = pd.read_csv('../csv/paynow_transfer.csv')
        
        if pathname == "/scan-to-pay":
            name = "Scan to Pay"
            df = pd.read_csv('../csv/scan_to_pay.csv')
        
        fig = get_fig(df, metric_choice)
        table = datatable(df)
        
        return name, fig, table


# render overview page
@app.callback(
    [Output(component_id='bank-function-distribution-fig', component_property='figure'), Output(component_id='sentiment-distribution-fig', component_property='figure')],
    Input("url", "pathname")
    
)
def render_overview_page(pathname):

    check_balance_df = pd.read_csv('../csv/check_balance.csv')
    paynow_transfer_df = pd.read_csv('../csv/paynow_transfer.csv')
    scan_to_pay_df = pd.read_csv('../csv/scan_to_pay.csv')

    if pathname == "/":

        # generate bank function distribution chart
        combined_df = pd.concat([check_balance_df, paynow_transfer_df, scan_to_pay_df], ignore_index=True)
        bank_function_count = combined_df.groupby(["bank_function"]).size().reset_index(name="bank_function_count")

        bank_function_distribution_fig = px.pie(
            bank_function_count,
            values="bank_function_count",
            names="bank_function",
            title="Bank Function Distribution",
            hole=0.6,
            color_discrete_sequence=["#FCCA8C", "#FBB35B", "#FA971F"]
        )

        bank_function_distribution_fig.update_layout(title_x=0.5)

        # generate sentiment distribution chart
        sentiment_df = pd.read_csv("../csv/sentiments.csv")
        sentiment_df["sentiment_label_score"] = sentiment_df["sentiment_label_score"].apply(lambda x: x.replace("'", "\""))
        sentiment_df["sentiment_label"] = sentiment_df["sentiment_label_score"].apply(lambda x: json.loads(x)["label"])
        sentiment_distribution = sentiment_df.groupby(["sentiment_label"]).size().reset_index(name="sentiment_distribution")

        sentiment_distribution_fig = px.pie(
            sentiment_distribution,
            values="sentiment_distribution",
            names="sentiment_label",
            title="Sentiment Distribution",
            hole=0.6,
            color_discrete_sequence=["#B8D5E5", "#92BFD8"]
        )

        sentiment_distribution_fig.update_layout(title_x=0.5)

        # generate user metrics chart


        return bank_function_distribution_fig, sentiment_distribution_fig

    else:
        PreventUpdate


if __name__=='__main__':
    app.run_server(debug=True, port=3200)
