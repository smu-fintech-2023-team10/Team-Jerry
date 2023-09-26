import dash
import dash_table
import dash_bootstrap_components as dbc
from dash import html
from dash import dcc
import dash_mantine_components as dmc
import plotly.express as px
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.cluster import DBSCAN
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.util import ngrams
import wordnet
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import json


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

# Import Datasets
check_balance_df = pd.read_csv('../csv/check_balance.csv')
paynow_transfer_df = pd.read_csv('../csv/paynow_transfer.csv')
scan_to_pay_df = pd.read_csv('../csv/scan_to_pay.csv')

# Function to generate Data Tables
def datatable(df):
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'id': c, 'name': c} for c in df.columns],
        sort_action="native",
        sort_mode="multi",
        export_columns="all",
        export_format="csv",
        export_headers="names",
        page_action="native",
        page_size=20,
        style_data={
            'color': 'black',
            'backgroundColor': 'white'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(230, 230, 230)',
            },
            {
                "if": {"state": "selected"},
                "backgroundColor": "inherit !important",
                "border": "inherit !important",
            }
        ],
        style_header={
            'backgroundColor': 'rgb(200, 200, 200)',
            'color': 'black',
            'fontWeight': 'bold'
        },
        style_cell={'textOverflow': 'ellipsis', 'maxWidth': '150px'}
    )

# Function to generate User Metrics Chart

def get_metric_df(df, metric_choice, bf):
    df['date'] = pd.to_datetime(df['date'], format="%d/%m/%y")
    sorted_df = df.sort_values(by="date")

    if metric_choice == "Users":
        df = sorted_df.groupby(["date"])['account_number'].nunique(
        ).reset_index(name=bf + " user count")

    elif metric_choice == "Sessions":
        df = sorted_df.groupby(["date"]).size().reset_index(
            name=bf + " session count")
    return df


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
                        ], style={'display': 'flex', 'padding':'1rem'}),
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
                                    html.Div(id='popular_topic_list')
                                    ], style={'margin-top': '1rem'})
                            ], style={'padding':'1rem', 'height':'528px'})
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
                        ], style={'display': 'flex', 'padding':'1rem'}),
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
                        children=[html.H3("<User Ratings to be Placed Here>")]
                    ), style={'marginLeft': '1rem', 'width': '34%', 'display': 'inline'}
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
    [Output(component_id='bank-function-distribution-fig', component_property='figure'), Output(component_id='sentiment-distribution-fig', component_property='figure'), Output(component_id='overview-metrics-fig', component_property='figure'), Output(component_id='overview-datatable', component_property='children'), Output(component_id='popular_topic_list', component_property='children')],
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

        # Generate List of Popular Topics
        overview_df = pd.read_csv('../csv/overview.csv')
        # Data Clean-up
        overview_df['unrecognised_msgs'] = overview_df['unrecognised_msgs'].str.replace(
            '[', '').str.replace(']', '')
        msg_list_v1 = []
        for msg in overview_df['unrecognised_msgs']:
            msg_list_v1.append(msg.split(','))
        msg_list_v2 = []
        for msg in msg_list_v1:
            for x in msg:
                msg_list_v2.append(x.replace('"', '').strip())
        msg_df = pd.DataFrame(msg_list_v2, columns=['unrecognised_msgs'])
        msg_df = msg_df.dropna()

        # Pre-processing Unrecognised Messages, Stopword removal and Lemmatization
        stop_words = set(stopwords.words('english'))
        stop_words.add('like')
        stop_words.add('do')
        lemmatizer = WordNetLemmatizer()

        def preprocess_text(text):
            text = text.lower()
            words = text.split()
            words = [word for word in words if word not in stop_words]
            words = [lemmatizer.lemmatize(word) for word in words]
            return ' '.join(words)

        msg_df['Preprocessed Messages'] = msg_df['unrecognised_msgs'].apply(
            preprocess_text)

        popular_topic_list = []

        # Extract Trigrams from Pre-processed messages
        count_vectorizer_trigram = CountVectorizer(ngram_range=(3, 3))
        X1_trigram = count_vectorizer_trigram.fit_transform(
            msg_df['Preprocessed Messages'])
        features_trigram = (count_vectorizer_trigram.get_feature_names_out())

        # Applying TFIDF for Trigrams
        tf_vectorizer_trigram = TfidfVectorizer(ngram_range=(3, 3))
        X2_trigram = tf_vectorizer_trigram.fit_transform(
            msg_df['Preprocessed Messages'])
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
        popular_topic_list_items = [html.Li(html.H1(dbc.Badge(item, color="white", text_color="dark", className="border border-dark border-2 me-1"))) for item in popular_topic_list]

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
        sentiment_datatable = datatable(
            sentiment_df.drop("sentiment_label_score", axis=1))

        # generate user metrics table
        bf_csv = {"check balance": check_balance_df,
                  "paynow transfer": paynow_transfer_df, "scan to pay": scan_to_pay_df}
        bf_colour = {'check balance': '#92C0D8',
                     'paynow transfer': '#FDCA8C', 'scan to pay': '#9DD4A3'}

        final_df = pd.DataFrame({"date": []})
        for bf in bf_csv:
            df = bf_csv[bf]
            dff = get_metric_df(df, metric_choice, bf)
            final_df = pd.merge(final_df, dff, on='date', how='outer')

        overview_user_metrics_fig = px.line(final_df, x='date', y=final_df.columns,
                                            color_discrete_map=bf_colour, title="Number of {} over time".format(metric_choice))
        overview_user_metrics_fig.update_layout(
            yaxis_title='{} count'.format(metric_choice))
        overview_user_metrics_fig.update_traces(line={'width': 2})
        overview_user_metrics_fig.update_xaxes(rangeslider_visible=True)

        return bank_function_distribution_fig, sentiment_distribution_fig, overview_user_metrics_fig, sentiment_datatable, html.Ul(popular_topic_list_items)

    else:
        PreventUpdate

# Rendering Components for all BF Pages


@app.callback(
    [Output(component_id='business-function-graph', component_property='figure'),
     Output(component_id='datatable', component_property='children')],
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

        if pathname == "/paynow-transfer":
            bf = "Paynow Transfer"
            df = paynow_transfer_df

        if pathname == "/scan-to-pay":
            bf = "Scan To Pay"
            df = scan_to_pay_df

        # generate user metric table
        dff = get_metric_df(df, metric_choice, bf)
        y_axis = "{} {} count".format(bf, metric_choice.lower()[:-1])
        fig = px.line(dff, x="date", y=y_axis,
                      title="Number of {} Over Time".format(metric_choice))
        fig.update_xaxes(rangeslider_visible=True)

        # generate datable
        user_table = datatable(df)

        return fig, user_table


if __name__ == '__main__':
    app.run_server(debug=True, port=3000)
