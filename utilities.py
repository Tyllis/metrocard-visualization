import pandas as pd
import os
from datetime import timedelta, datetime
from tqdm import tqdm

"""
Note from http://web.mta.info/developers/fare.html:
These files show the number of MetroCard swipes made each week by customers entering each station 
of the New York City Subway, PATH, AirTrain JFK and the Roosevelt Island Tram, broken out to show 
the relative popularity of the various types of MetroCards. MTA New York City Transit posts the 
latest data every Saturday by 1 a.m., and the dates listed in the links reference the date the 
data is posted. The data in the files covers seven-day periods beginning on the Saturday two 
weeks prior to the posting date and ending on the following Friday. Thus, as an example, the file 
labeled Saturday, January 15, 2011, has data covering the period from Saturday, January 1, 2011, 
through Friday, January 7. The file labeled January 22 has data covering the period from Saturday, 
January 8, through Friday, January 14. And so on and so forth.
"""

def download_files(begin_week, num_weeks, save_dir):
	begin_week = datetime.strptime(begin_week, '%y%m%d')
	for i in range(num_weeks):
		print('Downloading Week ' + str(i+1) + '/' + str(num_weeks) + '...')
		report_week = begin_week + timedelta(days= i * 7)
		data_week =  report_week - timedelta(days=7)
		file_name = '{:%y%m%d}'.format(report_week) + '.csv'
		data_name = '{:%y%m%d}'.format(data_week) + '.csv'
		link = 'http://web.mta.info/developers/data/nyct/fares/fares_' + file_name
		df = pd.read_csv(link, skiprows=2, index_col=False)
		df = df.drop(columns=[column for column in df.columns.tolist() if column.isspace()])
		df.to_csv(os.path.join(save_dir, data_name), index=False)
        

def add_data(df, data_dir):
    if isinstance(df, str) :
        df = pd.read_csv(df)
    if df is None:
        df = pd.DataFrame()
    tmp = pd.read_csv(data_dir)
    tmp.columns =  [column.strip() for column in tmp.columns.tolist()]
    tmp['STATION'] = tmp['STATION'].apply(lambda x: x.strip())
    tmp['WEEK'] = '{:%Y-%m-%d}'.format(datetime.strptime(data_dir[-10:-4], '%y%m%d'))
    tmp = tmp[['WEEK'] + [ col for col in tmp.columns if col != 'WEEK' ]]
    df = df.append(tmp)
    df.index = range(len(df))
    return df

	
def combine_all(load_dir):
    file_names = os.listdir(load_dir)
    for idx, file in tqdm(enumerate(file_names)):
        data_dir = os.path.join(load_dir, file)
        if idx == 0:
            df = add_data(None, data_dir)
        else:
            df = add_data(df, data_dir)
    return df
	
	
def read_data(df_file='main.csv', files_dir='data', save_df='main.csv'):
	if os.path.exists(df_file):
		df = pd.read_csv(df_file)
	else:
		df = combine_all(files_dir)
	if save_df is not None:
		df.to_csv(save_df, index=False)
		print('Saving main data frame as', save_df+'.')
	return df

	
def main():
	begin_week = input('Begin week (YYMMDD): ')
	num_weeks = int(input('Number of weeks: '))
	save_dir = input('File directory to save: ')
	download_files(begin_week, num_weeks, save_dir)	
	

if __name__ == '__main__':
	main()