# -*- coding: utf-8 -*-
"""
@author: junyan
"""

import pandas as pd
import psycopg2 


df = pd.read_csv('main.csv')
cols = df.columns

#connect to the database
conn = psycopg2.connect(host='ec2-52-87-107-83.compute-1.amazonaws.com',
                        dbname='d9gub7fgrbcs3b',
                        user='rbyhgbyamtyidr',
                        password='24013be04e604386b94c1e81754cd49a649db34f424725fc0c9943233bbe10ae',
                        port='5432')  
#create a cursor object 
#cursor object is used to interact with the database
cur = conn.cursor()

#create table with same headers as csv file

sql_str = '''create table fare('''
for col in cols:
    sql_str += '"' + col + '"' + ' char(50), '
sql_str = sql_str[:-2] + ''');'''

cur.execute(sql_str)

#open the csv file using python standard file I/O
#copy file into the table just created 
f = open('main.csv','r')
cur.copy_from(f, 'fare', sep=',')
f.close()

conn.commit()
conn.close()

def postgresql_to_dataframe(conn, select_query, column_names):
    """
    Tranform a SELECT query into a pandas dataframe
    """
    cursor = conn.cursor()
    try:
        cursor.execute(select_query)
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        cursor.close()
        return 1
    
    # Naturally we get a list of tupples
    tupples = cursor.fetchall()
    cursor.close()
    
    # We just need to turn it into a pandas dataframe
    df = pd.DataFrame(tupples, columns=column_names)
    return df


df = postgresql_to_dataframe(conn, "select * from fare", cols)
df.head()
