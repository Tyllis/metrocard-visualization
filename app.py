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
server = app.server				

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

card_intro_text = dbc.Card([  
    dbc.CardBody([
        html.H5('Welcome to the MTA MetroCard Swipes Analytics Dashboard',
                style={'font-weight':'bold'}),
        
        html.P([
            'Last updated: ' + datetime.strftime(week_ending_cur, '%b %d, %Y'),
            html.Br(),
            'Data source: ',
            html.A('http://web.mta.info/developers/fare.html', 
                   href='http://web.mta.info/developers/fare.html')
            ]),
        html.P([
            'For the Pandemic Recovery map, the size of the circle reflects the relative ' +
            'volume of MetroCard swipes at each station for the current week ' +
            '(larger means more swipes); the color reflects the % recovery, ' +
            'calculated by dividing the current volume by the pre-pandemic ' +
            'volume. The pre-pandemic data is defined as the 2019 data at the week ' + 
            'corresponding to current week. ',
            'Explore the map by using the "Box Select" or "Lasso Select" to select the stations ' +
            'of interest. ' +
            'For the trend graph, double click on one of the MetroCard type to ' +
            'select the card type of interest; or single click to exclude the card from the graph. ',
            'The MetroCard type description can be found ',
            html.A('here', 
                   href='http://web.mta.info/developers/resources/nyct/fares/fare_type_description.txt'),
            '. Explore the ranking graph by dragging the slider to view station ranking ' +
            'in different time period, or use the play button for animation.'             
            ])
        ])
    ],
    className=card_class
    )

card_selected_stations = dbc.Card([
    dbc.FormGroup([
        dbc.CardHeader('Selected Stations:',
                   style={'font-weight':'bold'}
                  ),
        html.Div(
            id='station_text',
            style={"maxHeight": "80px", "overflow": "scroll", 'align':'center'}
            )         
        ])
    ],
    className=card_class
    )

card_mapbox = dbc.Card([
    dbc.CardHeader("NYC Subway Stations Pandemic Recovery Map",
                   style={'font-weight':'bold'}
                   ),
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
    dbc.CardHeader("Stations Ranked by Total MetroCard Swipes",
                   style={'font-weight':'bold'}
                   ),
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
    dbc.CardHeader("MetroCard Swipes Trend",
                   style={'font-weight':'bold'}
                   ),
    dbc.CardBody(
        dcc.Graph(
            id = 'area_plot',
            figure=fig
            )        
        )
    ],
    
    className=card_class
    )

app.layout = html.Div([
    dbc.Row([
        dbc.Col([
            dbc.Row(dbc.Col(card_intro_text)),
            html.Br(),
            dbc.Row(dbc.Col(card_selected_stations))
            ],
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
    Input('mapbox_scatter', 'selectedData')
    ) 
def mapbox_select(mapbox_selected):
    if mapbox_selected is None:
        mapbox_selected = {'points':[]}
    if len(mapbox_selected['points']) == 0:
        selected_station = stations
    else:
        selected_station = [mapbox_selected['points'][i]['customdata'][0] 
                            for i in range(len(mapbox_selected['points']))]
    return json.dumps(selected_station)
    
@app.callback(
    Output('station_text', 'children'),
    Input('selected_station', 'children')
    )
def selected_station_text(selected_station):
    selected_station = list(set(json.loads(selected_station)))
    selected_station.sort()
    if set(selected_station) == set(stations):
        text = ' All Stations'
    else:
        text = ' '
        for station in selected_station:
            text += station + ' | ' 
        text = text[:-2]
    return text

@app.callback(
    Output('bar_plot', 'figure'),
    Input('selected_station', 'children')
    )
def create_barplot(selected_station):
    selected_station = list(set(json.loads(selected_station)))
    num_bars = 10
    cols = ['WEEK', 'REMOTE', 'STATION'] + card_types
    tmp = df[df['STATION'].isin(selected_station)][cols].copy() 
    tmp = tmp[tmp['WEEK'] >= datetime.strptime(start_date, '%Y-%m-%d')]
    tmp = tmp.groupby(['WEEK', 'STATION'], as_index=False).sum()
    tmp = pd.melt(tmp, id_vars=['WEEK', 'STATION'], value_vars=card_types, var_name='card_type', value_name='swipes')
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
        labels={'STATION':'Station Name',
                'WEEK': 'Week Ending',
                'swipes':'Average Daily MetroCard Swipes'},
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
    fig.update_layout(
		margin={"r":0,"t":0,"l":0,"b":0}
		)
    return fig

@app.callback(
    Output('area_plot', 'figure'),
    Input('selected_station', 'children')
    )
def create_areaplot(selected_station):
    selected_station = list(set(json.loads(selected_station))) 
    cols = ['WEEK', 'REMOTE', 'STATION'] + card_types
    tmp = df[df['STATION'].isin(selected_station)][cols].copy() 
    tmp = tmp[tmp['WEEK'] >= datetime.strptime(start_date, '%Y-%m-%d')]
    tmp = tmp.groupby('WEEK', as_index=False).sum()
    tmp = pd.melt(tmp, id_vars=['WEEK'], value_vars=card_types, var_name='card_type', value_name='swipes')
    tmp.WEEK = tmp.WEEK.apply(lambda x: '{:%Y-%m-%d}'.format(x))
    sorted_cards = tmp.groupby('card_type', as_index=False).mean().\
        sort_values('swipes', ascending=False).card_type.tolist()
    tmp = tmp.set_index('card_type').loc[sorted_cards]
    tmp = tmp.reset_index()
    tmp['swipes'] = (tmp['swipes'] / 7).astype('int')
    fig = px.area(
        tmp, x='WEEK', y='swipes', color='card_type', template='seaborn',
        labels={'card_type':'MetroCard Type', 
                'WEEK':'Date',
                'swipes':'Average Daily MetroCard Swipes'},
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
        margin={"r":0,"t":0,"l":0,"b":0}
        )
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)