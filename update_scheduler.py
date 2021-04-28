# -*- coding: utf-8 -*-
"""
@author: junyan

Scheduler to update the data/main.csv every week.
"""

import os
import sys
import pandas as pd
import utilities as util
from github import Github, InputGitTreeElement
from datetime import timedelta, datetime

if 'DATA_URL' in os.environ: 	
    data_url = os.environ['DATA_URL']
    token = os.environ['GITHUB_TOKEN']
else:
    data_url = 'data/'  

df = pd.read_csv(data_url + 'main.csv')
last_date = datetime.strptime(df['WEEK'].max(), '%Y-%m-%d')
new_date = last_date + timedelta(days=7)
file_date = new_date + timedelta(days=7)
file_name = 'fares_{:%y%m%d}.csv'.format(file_date)
new_data_url = 'http://web.mta.info/developers/data/nyct/fares/' + file_name

try:
    df, new_data_added = util.add_data(df, new_data_url)
except:
    print('Unexpected error:', sys.exc_info()[0])
    print('The data link generated is: ', new_data_url)
    new_data_added = False

if new_data_added:
    df = df.to_csv(sep=',', index=False)
    commit_message = "Data Updated - " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    g = Github(token)
    repo = g.get_user().get_repo('metrocard-visualization')
    master_ref = repo.get_git_ref("heads/master")
    master_sha = master_ref.object.sha
    base_tree = repo.get_git_tree(master_sha)
    element = InputGitTreeElement('data/main.csv', '100644', 'blob', df)
    tree = repo.create_git_tree([element], base_tree)
    parent = repo.get_git_commit(master_sha)
    commit = repo.create_git_commit(commit_message, tree, [parent])
    master_ref.edit(commit.sha)