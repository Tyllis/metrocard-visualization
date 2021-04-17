import pandas as pd
import json
import dash
import plotly.express as px
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from datetime import timedelta, datetime


app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.FLATLY], 
                title='MTA MetroCard Swipes')

df = pd.read_csv('main.csv')
geo_df = pd.read_csv('station_gis.csv')
df.WEEK = df.WEEK.apply(lambda x: datetime.strptime(x, '%Y-%m-%d'))
card_types = df.drop(columns=['WEEK', 'REMOTE', 'STATION']).sum(axis=0).\
    sort_values(ascending=False).index.tolist()
stations = df['STATION'].sort_values().unique().tolist()
week_ending_cur = df.WEEK.max()
week_ending_old = week_ending_cur - timedelta(weeks= 2 * 52)
start_date = '2020-01-04'  

df_sel = df[df['STATION'].isin(stations)].copy()
df_sel['row_sum'] = df_sel[card_types].sum(axis=1)
df_cur = df_sel[df_sel['WEEK']==week_ending_cur][['STATION', 'row_sum']].groupby('STATION', as_index=False).sum() 
df_old = df_sel[df_sel['WEEK']==week_ending_old][['STATION', 'row_sum']].groupby('STATION', as_index=False).sum()
df_meg = df_cur.merge(df_old, how='left', on='STATION')
df_meg['ratio'] = round(df_meg.row_sum_x / df_meg.row_sum_y, 4)
df_meg['Current Daily'] = (df_meg['row_sum_x'] / 7).apply(lambda x: '{:,}'.format(int(x) if x == x else 0 ))
df_meg['Pre-pandemic Daily'] = (df_meg['row_sum_y'] / 7).apply(lambda x: '{:,}'.format(int(x) if x == x else 0))
df_meg = df_meg.merge(geo_df, how='left', on='STATION')
df_meg['size'] = df_meg['row_sum_x'].fillna(0) / 7
df_meg['ratio'] = df_meg['ratio'].fillna(0)
fig = px.scatter_mapbox(
    df_meg, lat="lat", lon="lon", size='size', color='ratio', zoom=10,
    labels={'ratio':'% Recovery'},
    custom_data=['STATION', 'Pre-pandemic Daily', 'Current Daily', 'ratio'],
    range_color=[0, df_meg['ratio'].quantile(0.75)],
    color_continuous_scale=px.colors.sequential.Blues
    )        
fig.update_layout(
    mapbox_style="carto-positron",
    margin={"r":0,"t":0,"l":0,"b":0},
    coloraxis={'colorbar':{'len':0.5, 'x':0, 'tickformat':'.0%', 'yanchor':'top'}}
    )
fig.update_traces(
    hovertemplate=
        '<b>Station: %{customdata[0]}</b> <br>' + 
        'Current Average Daily: %{customdata[2]} <br>' +
        'Pre-pandemic Daily: %{customdata[1]} <br>' +
        '% Recovery : %{customdata[3]:.2%}'
    )    

card_class = 'card border-info'
css_style = {'height':'50px', 
             'margin-top':'50px', 'margin-bottom':'50px',
             'margin-left':'50px', 'margin-right':'50px'} 

card_mapbox = dbc.Card([
    dbc.CardHeader("MAPBOX TITLE"),
    dbc.CardBody(
        dcc.Graph(
            id = 'mapbox_scatter',
            figure=fig
            )        
        )
    ],
    className=card_class
    )

card_barplot = dbc.Card([
    dbc.CardHeader("BARPLOT TITLE"),
    dbc.CardBody(
        dcc.Graph(
            id = 'bar_plot',
            figure=fig
            )        
        )
    ],
    className=card_class
    )

card_areaplot = dbc.Card([
    dbc.CardHeader("AREAPLOT TITLE"),
    dbc.CardBody(
        dcc.Graph(
            id = 'area_plot',
            figure=fig
            )        
        )
    ],
    
    className=card_class
    )

card_control = dbc.Card([
    dbc.FormGroup([
        dbc.Label('Select MetroCard Type'),
        dcc.Dropdown(
            id = 'card_selector',
            options = [{'label':card, 'value':card} for card in card_types],
            value = [], 
            multi=True
            )      
        ]),
    dbc.FormGroup([
        dbc.Label('Search Subway Station'),
        dcc.Dropdown(
            id = 'station_selector',
            options = [{'label':station, 'value':station} for station in stations],
            value = [],
            multi=True
            )        
        ]),
    dbc.FormGroup([
        dbc.Label('Selected Stations:'),
        html.Div(
            id='station_text',
            style={"maxHeight": "200px", "overflow": "scroll", 'align':'center'}
            )         
        ])
    ],
    className=card_class
    )

app.layout = html.Div([
    
    dbc.Row([
        dbc.Col(
            card_control, 
            md=4
            ),
        
        dbc.Col(
            card_mapbox,
            md=8
            )
        ]),
    html.Br(),
    dbc.Row([
        dbc.Col(
            card_barplot       
            ),
        
        dbc.Col(
            card_areaplot
            )        
        ]),
    
    html.Div(
        id='selected_station', style={'display':'none'}
        )
    ],
    style=css_style   
    )

@app.callback(
    Output('selected_station', 'children'),
    Input('station_selector', 'value'),
    Input('mapbox_scatter', 'selectedData')
    ) 
def dropdown_select(dropdown_selected, mapbox_selected):
    if mapbox_selected is None:
        mapbox_selected = {'points':[]}
    if len(dropdown_selected) == 0 and len(mapbox_selected['points']) == 0:
        selected_station = stations
    else:
        selected_station = dropdown_selected + \
            [mapbox_selected['points'][i]['customdata'][0] 
             for i in range(len(mapbox_selected['points']))]
    return json.dumps(selected_station)
    

@app.callback(
    Output('station_text', 'children'),
    Input('selected_station', 'children')
    )
def selected_station_text(selected_station):
    selected_station = list(set(json.loads(selected_station)))
    if set(selected_station) == set(stations):
        text = 'All Stations'
    else:
        text = ''
        for station in selected_station:
            text += station + ', ' 
        text = text[:-2]
    return text

@app.callback(
    
    Output('bar_plot', 'figure'),
    Input('selected_station', 'children'),
    Input('card_selector', 'value'),
    )
def create_barplot(selected_station, selected_cards):
    selected_station = list(set(json.loads(selected_station)))
    if len(selected_cards) == 0:
        selected_cards = card_types   
    num_bars = 10
    cols = ['WEEK', 'REMOTE', 'STATION'] + selected_cards
    tmp = df[df['STATION'].isin(selected_station)][cols].copy() 
    tmp = tmp[tmp['WEEK'] >= datetime.strptime(start_date, '%Y-%m-%d')]
    tmp = tmp.groupby(['WEEK', 'STATION'], as_index=False).sum()
    tmp = pd.melt(tmp, id_vars=['WEEK', 'STATION'], value_vars=selected_cards, var_name='card_type', value_name='swipes')
    tmp = tmp.groupby(['WEEK', 'STATION'], as_index=False).sum()
    tmp_ = tmp.groupby('WEEK')['swipes'].nlargest(num_bars)
    try:
        time, indx = zip(*tmp_.index.tolist())
    except:
        indx = tmp_.index.tolist()
    tmp = tmp.iloc[list(indx)]
    tmp.WEEK = tmp.WEEK.apply(lambda x: '{:%Y-%m-%d}'.format(x))
    tmp = tmp.reset_index(drop=True)
    tmp['swipes'] = (tmp['swipes'] / 7).astype('int')
    max_range = tmp.groupby(['WEEK', 'STATION'], as_index=False)['swipes'].sum()['swipes'].max()
    
    fig = px.bar(
        tmp, y = 'STATION', x = 'swipes', animation_frame = 'WEEK', 
        range_x=[0,max_range], orientation='h', template='seaborn',
        labels={'STATION':'Ranked Stations',
                'WEEK': 'Week Ending',
                'swipes':'Daily MetroCard Swipes'},
        custom_data=['STATION', 'WEEK', 'swipes']
        )

    fig.update_layout(
        yaxis=dict(autorange="reversed"))
    
    fig.update_traces(
        hovertemplate=
            'Station: %{customdata[0]} <br>' +
            'Week Ending: %{customdata[1]} <br>' +
            'Swipes: %{customdata[2]:,}<extra></extra>'
        )
    return fig


@app.callback(
    Output('area_plot', 'figure'),
    Input('selected_station', 'children'),
    Input('card_selector', 'value'),
    )
def create_areaplot(selected_station, selected_cards):
    selected_station = list(set(json.loads(selected_station)))
    if len(selected_cards) == 0:
        selected_cards = card_types   
    cols = ['WEEK', 'REMOTE', 'STATION'] + selected_cards
    tmp = df[df['STATION'].isin(selected_station)][cols].copy() 
    tmp = tmp[tmp['WEEK'] >= datetime.strptime(start_date, '%Y-%m-%d')]
    tmp = tmp.groupby('WEEK', as_index=False).sum()
    tmp = pd.melt(tmp, id_vars=['WEEK'], value_vars=selected_cards, var_name='card_type', value_name='swipes')
    #tmp = tmp[tmp['card_type'].isin(selected_cards)]
    tmp.WEEK = tmp.WEEK.apply(lambda x: '{:%Y-%m-%d}'.format(x))
    sorted_cards = tmp.groupby('card_type', as_index=False).mean().\
        sort_values('swipes', ascending=False).card_type.tolist()
    tmp = tmp.set_index('card_type').loc[sorted_cards]
    tmp = tmp.reset_index()
    tmp['swipes'] = (tmp['swipes'] / 7).astype('int')
    fig = px.area(
        tmp, x='WEEK', y='swipes', color='card_type', template='seaborn',
        labels={'card_type':'MetroCard Type', 
                'WEEK':'',
                'swipes':'Daily MetroCard Swipes'},
        custom_data=['card_type', 'swipes', 'WEEK']
        )
    fig.update_xaxes(spikemode='across', spikethickness=1)
    fig.update_traces(
        hovertemplate=
            '<b>MetroCard Type: %{customdata[0]}</b> <br>' +
            'MetroCard Swipes: %{customdata[1]:,} <br>' +
            'Week Ending: %{customdata[2]}<extra></extra>'
        )
    fig.update_layout(
        margin={"r":0,"t":20,"l":0,"b":0}
        )
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)