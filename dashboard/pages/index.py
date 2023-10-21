from time import strftime, strptime
import dash
import dash_table
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import matplotlib.pyplot as plt
from dash_holoniq_wordcloud import DashWordcloud
from dash import html
from dash import dcc
import dash_daq as daq
import dash_mantine_components as dmc
import plotly.express as px
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.cluster import DBSCAN
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.util import ngrams
from wordcloud import WordCloud
import wordnet
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from collections import defaultdict
import json
import numpy as np


# big query connector
import pandas_gbq
from google.oauth2 import service_account
import pandas as pd


app = dash.Dash(__name__, external_stylesheets=[
                dbc.themes.LUMEN], suppress_callback_exceptions=True)


# Set CSS
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
    "background-color": "#F8F9FF",
}


# Set Sidebar Component
sidebar = html.Div(
    [
        html.Img(src=app.get_asset_url('team_jerry_logo.png'), style={
                 'height': '61px', 'width': '163px', "marginLeft": "20px"}),

        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Overview", href="/", active="exact",
                            className='text-light font-weight-bold'),
                dbc.NavLink("Check Balance", href="/check-balance",
                            active="exact", className='text-light font-weight-bold'),
                dbc.NavLink("PayNow Transfer", href="/paynow-transfer",
                            active="exact", className='text-light font-weight-bold'),
                dbc.NavLink("Scan To Pay", href="/scan-to-pay",
                            active="exact", className='text-light font-weight-bold')
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

# Set Top Bar Component
top_bar = html.Div(
    [
        html.H1(id='page-header', children="",
                style={"margin-top": "10px", "margin-left": "280px", "font-weight": "bold", "font-size": "40px", }),
        html.Hr(style={"padding": "0px", "margin-top": "0px",
                "margin-bottom": "0px"}),
    ],
    style={"background-color": "#ffffff", },
)

## big query connector
credentials = service_account.Credentials.from_service_account_file('smu-fyp-396613-6aefbba11d63.json')
project_id = 'smu-fyp-396613'

check_balances_df_sql = f"""
SELECT *
FROM smufyp.check_balance_sessions
"""

paynow_transfer_df_sql = f"""
SELECT *
FROM smufyp.paynow_transfer_sessions
"""

scan_to_pay_df_sql = f"""
SELECT *
FROM smufyp.scan_to_pay_sessions
"""

overview_df_sql = f"""
SELECT *
FROM smufyp.unrecognized_messages
"""

check_balance_df = pd.read_gbq(check_balances_df_sql, project_id=project_id, dialect='standard', credentials=credentials)
paynow_transfer_df = pd.read_gbq(paynow_transfer_df_sql, project_id=project_id, dialect='standard', credentials=credentials)
scan_to_pay_df = pd.read_gbq(scan_to_pay_df_sql, project_id=project_id, dialect='standard', credentials=credentials)
overview_df = pd.read_gbq(overview_df_sql, project_id=project_id, dialect='standard', credentials=credentials)

# Function to generate Data Tables
def datatable(df, function=''):
    if function in ['Paynow Transfer', 'Scan To Pay', 'Check Balance']:
        df['datee'] = df['date'].astype(str)
        df['datee'] = df['datee'].apply(lambda x: x[:11])
        df = df.drop('date', axis=1)
        df.insert(0, 'datee', df.pop('datee'))

        if function in ['Paynow Transfer', 'Scan To Pay']:
            df = df.rename(columns={'session_id': 'Session ID', 'bank_function': 'Bank Function', 'datee': 'Date', 'account_number': 'Sender Mobile Number', 'recipient_number': 'Recipient Mobile Number/ NRIC', 'amount': 'Amount', 'session_rating': 'Session Rating'})
        else:
            df['see_past_transactions'] = df['see_past_transactions'].apply(lambda x: x[3:] if x is not None else x)
            df = df.rename(columns={'session_id': 'Session ID', 'bank_function': 'Bank Function', 'datee': 'Date', 'account_number': 'Balance', 'see_past_transactions': 'See Past Transactions', 'session_rating': 'Session Rating'})

    df = df.fillna("na")

    col_defs = []
    for i in df.columns:
        col_defs.append({"field": i})

    return html.Div(
        [
            html.Button("Download CSV", id="csv-button", n_clicks=0),
            dag.AgGrid(
                id="export-data-grid",
                rowData=df.to_dict("records"),
                defaultColDef={"sortable": True, "resizable": True},
                columnDefs=col_defs,
                dashGridOptions={"pagination": True, "paginationPageSize":10},
                columnSize="sizeToFit",
                csvExportParams={
                    "fileName": "jerry_whatsapp_banking.csv",
                },
                className="ag-theme-alpine",
            )
        ]
    )

@app.callback(
    Output("export-data-grid", "exportDataAsCsv"),
    Input("csv-button", "n_clicks"),
)
def export_data_as_csv(n_clicks):
    if n_clicks:
        return True
    return False

# Function to generate User Metrics Chart

def get_metric_df(df, metric_choice, bf):
    df['date'] = pd.to_datetime(df['date'], format="%d/%M/%y")
    sorted_df = df.sort_values(by="date")

    if metric_choice == "Users":
        df = sorted_df.groupby(["date"])['account_number'].nunique(
        ).reset_index(name=bf)

    elif metric_choice == "Sessions":
        df = sorted_df.groupby(["date"]).size().reset_index(
            name=bf)
    return df

# Function to generate User Ratings
def get_average_rating(df):
    return round(df['session_rating'].mean(),3)


# Set Overall Page Layout
app.layout = html.Div([
    dcc.Location(id="url"),
    html.Div(sidebar),
    html.Div([
        top_bar,
        html.Div(id="page-content", children=[], style=CONTENT_STYLE
                 )
    ])
], style={"background-color": "#F8F9FF"})


# Initialize Page Layout based on URL Pathname
@app.callback(
    [Output(component_id="page-header", component_property="children"),
     Output(component_id="page-content", component_property="children")],
    Input(component_id="url", component_property="pathname")
)
def render_page(pathname):
    # If "/", initialize Overview Page
    if pathname == "/":
        header = "Overview"
        page = html.Div([
            html.Div([
                html.Div(
                    dmc.Paper(
                        radius="md",
                        withBorder=True,
                        shadow='xs',
                        p='sm',
                        children=[
                            html.Div([
                            html.Div(html.H2("Activity"), style={
                                'width': '20%', 'display': 'inline'}),
                            html.Div(dcc.Dropdown(id='overview-metric-dropdown',
                                                  options=[{"label": x, "value": x}
                                                           for x in ["Users", "Sessions"]],
                                                  value="Users"
                                                  ), style={'width': '80%', 'display': 'inline'}
                                     ),
                        ], style={'display': 'flex', 'padding':'1rem', 'padding-bottom':'0px'}),
                            dcc.Graph(id="overview-metrics-fig",
                                      figure={}
                                      )
                        ]), style={'width': '66%', 'display': 'inline'}
                ), # Metrics
                html.Div(
                    dmc.Paper(
                        radius="md",
                        withBorder=True,
                        shadow='xs',
                        p='sm',
                        children=[
                            html.Div([
                            html.H2("Popular Topics"),
                            html.Div([
                                    html.Div(id='popular_topic_list'),
                                    ])
                            ])
                            ,
                            html.Div([
                                html.Div(id='wordcloud-fig', style={'margin-left': '2rem'})
                            ])
            ]), style={'marginLeft': '1rem', 'width': '34%', 'display': 'flex-wrap'}
                ), # Popular Topics
            ], style={'display': 'flex'}), # for Metrics and Popular Topics
            html.Div([
                html.Div([
                    dmc.Paper(
                        radius="md",
                        withBorder=True,
                        shadow='xs',
                        p='sm',
                        children=[
                            dcc.Graph(id="bank-function-distribution-fig",
                            figure={}
                            )
                        ]),
                ],style={'width': '50%', 'display': 'inline', 'marginRight':'1rem'}), # Bank Function Distribution
                html.Div([
                    dmc.Paper(
                        radius="md",
                        withBorder=True,
                        shadow='xs',
                        p='sm',
                        children=[
                            dcc.Graph(id="sentiment-distribution-fig",
                            figure={},
                            )
                        ])
                ],style={'width': '49%', 'display': 'inline'}), # Sentiment Distribution
            ], style={'margin-top':'1rem','display': 'flex'}), # for Bank Function Distribution and Sentiment Distribution
            html.Div(
                dmc.Paper(
                    radius="md",
                    withBorder=True,
                    shadow='xs',
                    p='sm',
                    children=[
                        html.Div([html.Div(html.H2("Unrecognized Messages")),
                        html.Div(id="overview-datatable", style={'margin-top': '1rem'})], style={'padding':'1rem'})
                        ]), style={'margin-top': '1rem', 'width': '100%', 'display': 'inline-block'}
            ), # for Datatable of Unrecognised Messages
        ])

    # Else, initialize BF Pages
    else:
        if pathname == "/check-balance":
            header = "Check Balance"
        if pathname == "/paynow-transfer":
            header = "PayNow Transfer"
        if pathname == "/scan-to-pay":
            header = "Scan To Pay"

        page = html.Div([
            html.Div([
                html.Div(
                    dmc.Paper(
                        radius="md",
                        withBorder=True,
                        shadow='xs',
                        p='sm',
                        children=[html.Div([
                            html.Div(html.H2("Activity"), style={
                                'width': '20%', 'display': 'inline'}),
                            html.Div(dcc.Dropdown(id='metric-dropdown',
                                                  options=[{"label": x, "value": x}
                                                           for x in ["Users", "Sessions"]],
                                                  value="Users"
                                                  ), style={'width': '80%', 'display': 'inline'}
                                     ),
                        ], style={'display': 'flex', 'padding':'1rem', 'padding-bottom':'0px'}),
                            dcc.Graph(id="business-function-graph",
                                      figure={}
                                      )]
                    ), style={'width': '66%', 'display': 'inline'}
                ),
                 html.Div(
                     dmc.Paper(
                         radius="md",
                         withBorder=True,
                         shadow='xs',
                         p='sm',
                         children=[
                         html.Div([
                         html.H3("Avg. User Rating"),
                         daq.Gauge(
                         id='business-function-rating',
                         value=3,
                         showCurrentValue=True,
                         max=5,
                         min=0,
                         )
                         ], style={'height':'512px', 'textAlign': 'center'})
                         ]
                     ), style={'marginLeft': '1rem', 'width': '34%'}
                )
            ], style={'display': 'flex'}),
            html.Div(
                dmc.Paper(
                    radius="md",
                    withBorder=True,
                    shadow='xs',
                    p='sm',
                    children=[
                        html.Div([html.Div(html.H2("Table of Data")),
                        html.Div(id="datatable", style={'margin-top': '1rem'})],style={'padding':'1rem'})
                        ]
                ), style={'margin-top': '1rem', 'width': '100%', 'display': 'inline-block'})
        ])

    return header, page


# Rendering Overview Page Components

@app.callback(
    [Output(component_id='bank-function-distribution-fig', component_property='figure'), Output(component_id='sentiment-distribution-fig', component_property='figure'), Output(component_id='overview-metrics-fig', component_property='figure'), Output(component_id='overview-datatable', component_property='children'), Output(component_id='popular_topic_list', component_property='children'), Output(component_id='wordcloud-fig', component_property='children')],
    [Input("url", "pathname"), Input(component_id='overview-metric-dropdown', component_property='value')]
)
def render_overview_page(pathname, metric_choice):

    if pathname == "/":

        # generate bank function distribution chart
        combined_df = pd.concat(
            [check_balance_df, paynow_transfer_df, scan_to_pay_df], ignore_index=True)
        bank_function_count = combined_df.groupby(
            ["bank_function"]).size().reset_index(name="bank_function_count")

        bank_function_distribution_fig = px.pie(
            bank_function_count,
            values="bank_function_count",
            names="bank_function",
            title="Bank Function Distribution",
            hole=0.4,
            color_discrete_sequence=["#FCCA8C", "#FBB35B", "#FA971F"]
        )

        bank_function_distribution_fig.update_layout(title_x=0.5)

        # generate sentiment distribution chart
        sentiment_df = pd.read_csv("../csv/sentiments.csv")

        sentiment_df["sentiment_label_score"] = sentiment_df["sentiment_label_score"].apply(
            lambda x: x.replace("'", "\""))
        sentiment_df["sentiment_label"] = sentiment_df["sentiment_label_score"].apply(
            lambda x: json.loads(x)["label"])
        sentiment_df["sentiment_score"] = sentiment_df["sentiment_label_score"].apply(
            lambda x: json.loads(x)["score"])
        sentiment_distribution = sentiment_df.groupby(
            ["sentiment_label"]).size().reset_index(name="sentiment_distribution")

        # Pre-processing Unrecognised Messages, Stopword removal and Lemmatization
        stop_words = set(stopwords.words('english'))
        stop_words.add('like')
        stop_words.add('do')
        lemmatizer = WordNetLemmatizer()

        def preprocess_text(text):
            text = text.lower()
            words = text.split()
            # words = [word for word in words if word not in stop_words]
            words = [lemmatizer.lemmatize(word) for word in words]
            return ' '.join(words)

        overview_df['Preprocessed Messages'] = overview_df['message'].apply(
            preprocess_text)

        popular_topic_list = []

        # Extract Trigrams from Pre-processed messages
        count_vectorizer_trigram = CountVectorizer(ngram_range=(1, 1))
        X1_trigram = count_vectorizer_trigram.fit_transform(
            overview_df['Preprocessed Messages'])
        features_trigram = (count_vectorizer_trigram.get_feature_names_out())

        # Applying TFIDF for Trigrams
        tf_vectorizer_trigram = TfidfVectorizer(ngram_range=(1, 1))
        X2_trigram = tf_vectorizer_trigram.fit_transform(
            overview_df['Preprocessed Messages'])
        scores = (X2_trigram.toarray())

        # Getting top 5 Trigrams
        sums_trigram = X2_trigram.sum(axis=0)
        data1_trigram = []
        for col, term in enumerate(features_trigram):
            data1_trigram.append((term, sums_trigram[0, col]))
        trigram_ranking = pd.DataFrame(data1_trigram, columns=['term', 'rank'])
        trigram_words = (trigram_ranking.sort_values('rank', ascending=False))
        for x in trigram_words['term'].head(5):
            if 'do' not in x:
                popular_topic_list.append("'" + x + "'")
        popular_topic_list_items = [html.Li(html.H3(dbc.Badge(item, color="white", text_color="info", className="border border-info border-2 me-1")), className="no-bullet-list") for item in popular_topic_list]

        sentiment_distribution_fig = px.pie(
            sentiment_distribution,
            values="sentiment_distribution",
            names="sentiment_label",
            title="Sentiment Distribution",
            hole=0.4,
            color_discrete_sequence=["#B8D5E5", "#92BFD8"]
        )

        sentiment_distribution_fig.update_layout(title_x=0.5)

        # generate datatable
        inappropriate_words = ["fk you", "fk", "fuck", "bitch"]
        filtered_sentiment_df = sentiment_df[~sentiment_df['unrecognised_msgs'].str.contains('|'.join(inappropriate_words), case=False)]
        sentiment_datatable = filtered_sentiment_df.drop("sentiment_label_score", axis=1).rename(columns={'unrecognised_msgs': 'Unrecognized Messages', 'sentiment_label': 'Sentiment Label', 'sentiment_score': 'Sentiment Score'})
        sentiment_datatable = datatable(sentiment_datatable)

        # generate user metrics table
        bf_csv = {"Check Balance": check_balance_df,
                  "Paynow Transfer": paynow_transfer_df, "Scan To Pay": scan_to_pay_df}
        bf_colour = {'Check Balance': '#D252A7',
                     'Paynow transfer': '#017EFA', 'Scan To Pay': '#9DD4A3'}

        final_df = pd.DataFrame({"date": []})
        for bf in bf_csv:
            df = bf_csv[bf]
            dff = get_metric_df(df, metric_choice, bf)
            final_df = pd.merge(final_df, dff, on='date', how='outer')

        overview_user_metrics_fig = px.line(final_df, x='date', y=final_df.columns,
                                            color_discrete_map=bf_colour)
        overview_user_metrics_fig.update_layout(
            yaxis_title='Daily {}'.format(metric_choice))
        overview_user_metrics_fig.update_traces(line={'width': 3})
        overview_user_metrics_fig.update_xaxes(rangeslider_visible=True)
        
        word_counts = defaultdict(int)

        for message in overview_df['message']:
            message = message.lower()  # Convert the message to lowercase for case-insensitive counting
            if message not in ["fk you", "fk", "fuck", "bitch", "brandon", "brandondc"]:
                word_counts[message] += 9
        word_count_list = [[word, count] for word, count in word_counts.items()]
        word_count_list.sort(key=lambda x: x[1], reverse=True)
        
        wordcloud_fig = DashWordcloud(
                        list=word_count_list,
                        width=300, height=220,
                        gridSize=16,
                        # color= '#FFFDD0',
                        color='white',
                        backgroundColor="#92BFD8",
                        shuffle=False,
                        rotateRatio=0.3,
                        shrinkToFit=True,
                        shape='circle',
                        )
        return bank_function_distribution_fig, sentiment_distribution_fig, overview_user_metrics_fig, sentiment_datatable, html.Ul(popular_topic_list_items), wordcloud_fig

    else:
        PreventUpdate

# Rendering Components for all BF Pages


@app.callback(
    [Output(component_id='business-function-graph', component_property='figure'),
     Output(component_id='datatable', component_property='children'), Output(component_id='business-function-rating', component_property='value')],
    [Input("url", "pathname"), Input(
        component_id='metric-dropdown', component_property='value')]
)
def render_business_function_pages(pathname, metric_choice):
    if pathname == "/":
        raise PreventUpdate

    else:
        if pathname == "/check-balance":
            bf = "Check Balance"
            df = check_balance_df
            avg_rating = get_average_rating(df)

        if pathname == "/paynow-transfer":
            bf = "Paynow Transfer"
            df = paynow_transfer_df
            avg_rating = get_average_rating(df)

        if pathname == "/scan-to-pay":
            bf = "Scan To Pay"
            df = scan_to_pay_df
            avg_rating = get_average_rating(df)

        # generate user metric table
        dff = get_metric_df(df, metric_choice, bf)
        y_axis = "{}".format(bf)
        fig = px.line(dff, x="date", y=y_axis)
        fig.update_xaxes(rangeslider_visible=True)

        # generate datable
        user_table = datatable(df, bf)

        return fig, user_table, avg_rating


if __name__ == '__main__':
    app.run_server(debug=True, port=3000)
