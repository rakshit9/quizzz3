import pyodbc
import pandas as pd
import numpy as np
import os

# Print the current working directory
print("Current working directory: ", os.getcwd())

# Print all files and directories in the current directory
print("Directory content: ", os.listdir())


# Connect to your Azure SQL database
server = 'ccdb24db.database.windows.net'
username = 'rakshit'
password = 'Canada@90'
database = 'firstdatabase'
driver = '{ODBC Driver 18 for SQL Server}'


connection = pyodbc.connect('DRIVER='+driver+';SERVER='+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password)

cursor = connection.cursor()

# Read your CSV file
data = pd.read_csv('data_exam.csv')

# Convert the dataframe to a list of tuples
data_tuples = list(data.itertuples(index=False, name=None))

# Write data to Azure SQL
# Prepare the SQL INSERT statement
# table_name - your target table name
# columns - a string with column names, comma separated 
table_name = 'EarthquakeDataExam'
columns = ', '.join(data.columns)

for row in data_tuples:
    # Convert 'nan' and other non-numeric values to None
    row = tuple((None if pd.isnull(value) else value) for value in row)

    values_placeholder = ', '.join('?' * len(row))
    sql_query = f"INSERT INTO {table_name} ({columns}) VALUES ({values_placeholder})"

    try:
        cursor.execute(sql_query, row)
        connection.commit()
    except Exception as e:
        print(f"Error occurred with row {row}: {e}")

connection.close()
