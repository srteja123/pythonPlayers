from flask import Flask, abort, jsonify, request
from flask import send_file
import seaborn as sns
import matplotlib.pyplot as plt
import PySimpleGUI as sg
from playerData import get_db_conn
import pandas as pd
import numpy as np
app = Flask(__name__)
dbname = 'CRICKET_PERF'
@app.route('/')
def index():
    return "<h1>Cricket Parser :)</h1>"
   
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404
    
@app.route('/api/v2/countries/all', methods=['GET'])
def get_all_countries():
  
    with get_db_conn(dbname) as sqlite_conn:
        cur = sqlite_conn.cursor()
    cur.execute('''select * from Countries; ''')
    
    s = "<table style='border:1px solid red'>"  
    col_name = [field[0] for field in cur.description]
    s = s + "<tr>" 
    for y in col_name:
        
        s = s + " <td>" + str(y) + "</td>" 
    s = s + "<tr>"    
    for row in cur:  
        s = s + "<tr>"  
        for x in row:  
            s = s + "<td>" + str(x) + "</td>"  
        s = s + "</tr>"  
    
    return "<html><body>" + s + "</body></html>"  


@app.route('/api/v2/playerStats/bowlingT20Plot/all', methods=['GET'])
def get_all_bowlerstats_plot():
    with get_db_conn(dbname) as sqlite_conn:
        query = "select * from Bowling_Stats_T20;"
        # Execute the query and fetch results into a pandas DataFrame
        df = pd.read_sql_query(query, sqlite_conn)
    
        # Replace '-' with 0 in 'matches_played' and 'wickets_taken' columns
        df['matches_played'] = pd.to_numeric(df['matches_played'].replace('-', '0'))
        df['wickets_taken'] = pd.to_numeric(df['wickets_taken'].replace('-', '0'))
    
        # Assuming 'matches_played' vs 'wickets_taken'
        sns.scatterplot(data=df, x='matches_played', y='wickets_taken')
        
        # Sort x and y values in ascending order
        x_values = sorted(df['matches_played'].unique())
        y_values = sorted(df['wickets_taken'].unique())

        # Define the ticks with ranges for x and y axes
        plt.xticks(range(0, max(x_values) + 1, 50))  # Adjust the range based on your data
        plt.yticks(range(0, max(y_values) + 1, 50))  # Adjust the range based on your data

        # Save the plot as an image file
        plt.savefig('Bowlerplot.png')  # Save the plot as 'plot.png' (you can choose any filename)

    # Return the image file in the API response
    return send_file('Bowlerplot.png', mimetype='image/png')
@app.route('/api/v2/playerStats/battingT20Plot/all', methods=['GET'])
def get_all_battingstats_plot():
    with get_db_conn(dbname) as sqlite_conn:
        query = "select * from Batting_Stats_T20;"
        # Execute the query and fetch results into a pandas DataFrame
        df = pd.read_sql_query(query, sqlite_conn)
    
        # Replace '-' with 0 in 'batting_average' and 'batting_strike_rate' columns
        df['batting_average'] = pd.to_numeric(df['batting_average'].replace('-', '0'))
        df['batting_strike_rate'] = pd.to_numeric(df['batting_strike_rate'].replace('-', '0'))
    
        # Assuming 'batting_average' vs 'batting_strike_rate'
        sns.scatterplot(data=df, x='batting_average', y='batting_strike_rate')
        
        # Sort x and y values in ascending order
        x_values = sorted(df['batting_average'].replace('-', '0').astype(float).unique())
        y_values = sorted(df['batting_strike_rate'].replace('-', '0').astype(float).unique())

        # Define the ticks with ranges for x and y axes
        plt.xticks(np.arange(0, max(x_values) + 1, 10))
        plt.yticks(np.arange(0, max(y_values) + 1, 50))

        # Save the plot as an image file
        plt.savefig('BattingPlot.png')  # Save the plot as 'BattingPlot.png' (you can choose any filename)

    # Return the image file in the API response
    return send_file('BattingPlot.png', mimetype='image/png')




@app.route('/api/v2/playerStats/battingT20/all', methods=['GET'])
def get_all_battingstats():
    with get_db_conn(dbname) as sqlite_conn:
        cur = sqlite_conn.cursor()
    cur.execute('''select * from Batting_Stats_T20; ''')
    
    s = "<table style='border:1px solid red'>"
    col_name = [field[0] for field in cur.description]
    s = s + "<tr>"
    for y in col_name:
        
        s = s + " <td>" + str(y) + "</td>"
    s = s + "<tr>"
    for row in cur:
        s = s + "<tr>"
        for x in row:
            s = s + "<td>" + str(x) + "</td>"
        s = s + "</tr>"
    
    return "<html><body>" + s + "</body></html>"


@app.route('/api/v2/playerStats/bowlingT20/all', methods=['GET'])
def get_all_bowlerstats():
    with get_db_conn(dbname) as sqlite_conn:
        cur = sqlite_conn.cursor()
    cur.execute('''select * from Bowling_Stats_T20; ''')
    
    s = "<table style='border:1px solid red'>"
    col_name = [field[0] for field in cur.description]
    s = s + "<tr>"
    for y in col_name:
        
        s = s + " <td>" + str(y) + "</td>"
    s = s + "<tr>"
    for row in cur:
        s = s + "<tr>"
        for x in row:
            s = s + "<td>" + str(x) + "</td>"
        s = s + "</tr>"
    
    return "<html><body>" + s + "</body></html>"
    


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)