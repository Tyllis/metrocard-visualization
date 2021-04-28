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
    """   
    Parameters
    ----------
    begin_week : str
        Ending date of the week (in yymmdd format) to begin the download.
    num_weeks : int
        Number of weeks to download starting from begin_week.
    save_dir : str
        Directory to save the files.

    Returns
    -------
    None.
    """
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
        

def add_data(df, data_path):
    """
    Parameters
    ----------
    df : str or pandas.DataFrame
        Path to the existing main data file, or existing pandas.DataFrame.
    data_dir : str
        Path to the new data file.

    Returns
    -------
    df : pandas.DataFrame
        Updated data.
    df : boolean
        Signal whether the new data is successfully added.    
    """
    if isinstance(df, str) :
        df = pd.read_csv(df)
    if df is None:
        df = pd.DataFrame()    
    if 'web.mta.info' in data_path:
        new_data = pd.read_csv(data_path, skiprows=2, index_col=False)
        file_date = datetime.strptime(data_path[-10:-4], '%y%m%d')
        data_date = file_date - timedelta(days=7)
        new_data['WEEK'] = '{:%Y-%m-%d}'.format(data_date)
    else:
        new_data = pd.read_csv(data_path)
        new_data['WEEK'] = '{:%Y-%m-%d}'.format(datetime.strptime(data_path[-10:-4], '%y%m%d'))
    new_data = new_data.drop(columns=[column for column in new_data.columns.tolist() if column.isspace()])
    new_data.columns = [column.strip() for column in new_data.columns.tolist()]
    new_data['STATION'] = new_data['STATION'].apply(lambda x: x.strip())
    if new_data['WEEK'].unique()[0] not in df['WEEK'].unique().tolist():
        df = df.append(new_data)
        df.index = range(len(df))
        added = True
        print('New data added.')
    else:
        added = False
        print('Data already in existing data frame. No new data added.')
    return df, added

	
def combine_all(load_dir):
    """
    Parameters
    ----------
    load_dir : str
        Directory storing all data files.

    Returns
    -------
    df : pandas.DataFrame
        Combined data frame.
    """
    file_names = os.listdir(load_dir)
    for idx, file in tqdm(enumerate(file_names)):
        data_dir = os.path.join(load_dir, file)
        if idx == 0:
            df = add_data(None, data_dir)
        else:
            df = add_data(df, data_dir)
    return df
	
	
def read_data(df_file='main.csv', files_dir='data', save_df='main.csv'):
    """
    Parameters
    ----------
    df_file : str, optional
        Path to the main data frame file. The default is 'main.csv'.
    files_dir : str, optional
        Directory to the files. The default is 'data'.
    save_df : str, optional
        Path to where the data to save. The default is 'main.csv'.

    Returns
    -------
    df : pandas.DataFrame
        DESCRIPTION.
    """
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
	save_dir = input('Directory to save the file: ')
	download_files(begin_week, num_weeks, save_dir)	
	

if __name__ == '__main__':
	main()