import unittest
from unittest.mock import patch, MagicMock,mock_open
from flask import json
from bs4 import BeautifulSoup
from playerData import get_db_conn,main, get_country_details, get_player_details, get_player_statistics
from app import app, dbname, get_db_conn
import pandas as pd
from flask import send_file
from io import BytesIO
import requests
import sqlite3


dbname = 'CRICKET_PERF'


class CricketParserTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.mock_conn = MagicMock()
        self.mock_cursor = self.mock_conn.cursor.return_value
        self.url_values = ["/cricketers/player-one-789", "/cricketers/player-two-012"]
        self.match_types = [2, 3]
        self.sqlite_conn = sqlite3.connect(':memory:')
        self.sqlite_conn.execute('CREATE TABLE Players (country_id text, player_id text, player text, play_link text, odi_cap text, t20_cap text)')
        self.cur = self.sqlite_conn.cursor()

    def test_index(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn("<h1>Python Players</h1>", response.data.decode('utf-8'))

    def test_page_not_found(self):
        response = self.app.get('/nonexistent')
        self.assertEqual(response.status_code, 404)
        self.assertIn("<h1>404</h1><p>The resource could not be found.</p>", response.data.decode('utf-8'))

    def test_get_db_conn_success(self):
        with patch('sqlite3.connect', return_value=self.mock_conn):
            conn = get_db_conn('test_db')
            self.assertEqual(conn, self.mock_conn)

    def test_get_db_conn_failure(self):
        with patch('sqlite3.connect', side_effect=Exception('test')):
            with self.assertRaises(SystemExit):
                get_db_conn('test_db')

    @patch('app.get_db_conn')
    def test_get_all_countries(self, mock_get_db_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [('Country_ID',), ('Country_Name',)]
        mock_cursor.fetchall.return_value = [(1, 'Country A'), (2, 'Country B')]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        
        response = self.app.get('/api/v2/countries/all')
        self.assertEqual(response.status_code, 200)
        self.assertIn("<td>Country_ID</td>", response.data.decode('utf-8'))

    def test_get_country_details(self):
        country_links = ['England', 'India']
        selected_countries = ['England', 'Australia']
        country_map = {'England': '1', 'Australia': '2'}
        get_country_details(country_links, selected_countries, self.mock_conn, country_map)
        self.mock_cursor.execute.assert_called_once_with(
            'INSERT OR IGNORE INTO Countries (country_id,country) VALUES (?,?)',
            ('1', 'England')
        )
        self.mock_conn.commit.assert_called_once()

    def test_get_player_details(self):
        url_values = ['/team/india-6']
        match_types = [2, 3]
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = 'Test HTML'
            with patch('bs4.BeautifulSoup', return_value=MagicMock()):
                get_player_details(url_values, self.mock_conn, match_types)
                self.assertFalse(self.mock_cursor.execute.called)
                #self.mock_conn.commit.assert_called()

    def test_get_player_statistics_battingODI(self):
        action = 'batting'
        play_list = [(40, 'Afghanistan', 1059030, 'PlayerName', '/players/player-1')]
        match_type = 2
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = 'Test HTML'
            with patch('bs4.BeautifulSoup', return_value=MagicMock()):
                get_player_statistics(action, play_list, match_type, self.mock_conn)
                self.assertFalse(self.mock_cursor.execute.called)
                #self.mock_conn.commit.assert_called()

    def test_get_player_statistics_bowlingODI(self):
        action = 'bowling'
        play_list = [(40, 'Afghanistan', 1059030, 'PlayerName', '/players/player-1')]
        match_type = 2
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = 'Test HTML'
            with patch('bs4.BeautifulSoup', return_value=MagicMock()):
                get_player_statistics(action, play_list, match_type, self.mock_conn)
                self.assertFalse(self.mock_cursor.execute.called)

    def test_get_player_statistics_bowlingT20(self):
        action = 'bowling'
        play_list = [(40, 'Afghanistan', 1059030, 'Abdul Malik', '/cricketers/abdul-malik-1059030')]
        match_type = 3
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = 'Test HTML'
            with patch('bs4.BeautifulSoup', return_value=MagicMock()):
                get_player_statistics(action, play_list, match_type, self.mock_conn)
                self.assertFalse(self.mock_cursor.execute.called)
                #self.mock_conn.commit.assert_called()


    @patch('playerData.get_db_conn')
    def test_get_player_statistics_battingT20(self,mock_get_db_conn):
        action = 'batting'
        play_list = [(40, 'Afghanistan', 352048, 'Gulbadin Naib', '/cricketers/gulbadin-naib-352048')]
        match_type = 3
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = 'Test HTML'
            with patch('bs4.BeautifulSoup', return_value=MagicMock()):
                get_player_statistics(action, play_list, match_type, mock_get_db_conn)
                self.assertFalse(mock_cursor.execute.called)
    
    @patch('playerData.requests.get')
    def test_main_url_status_code_200(self, mock_get):
        # Setup mock to simulate a successful page response
        mock_response = MagicMock({})
        mock_response.status_code = 200
        mock_response.text="<html></html>"
        mock_get.return_value = mock_response
        
        # Call the main function
        main()

        # Check if get method was called with the correct URL
        mock_get.assert_called_with('https://www.espncricinfo.com/team')
    
    @patch('playerData.requests.get')
    def test_main_url_status_code_404(self, mock_get):
        # Setup mock to simulate a 404 page response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Call the main function while suppressing stdout and stderr
        with self.assertLogs(level='ERROR') as cm, self.assertRaises(SystemExit) as cm_exit:
            main()

        # Check if SystemExit was called with the correct code
        self.assertEqual(cm_exit.exception.code, -1)
        # Check if the logger recorded an error message
        self.assertIn('Url provided doesn\'t exist,exiting with error code 404', cm.output[0])

    @patch('app.get_db_conn')
    def test_get_all_battingstats(self, mock_get_db_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [('Player',), ('Runs',)]
        mock_cursor.fetchall.return_value = [('Player A', '1000'), ('Player B', '900')]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn

        response = self.app.get('/api/v2/playerStats/battingT20/all')
        self.assertEqual(response.status_code, 200)
        self.assertIn("<td>Player</td>", response.data.decode('utf-8'))
        #self.assertIn("<td>1000</td>", response.data.decode('utf-8'))

    @patch('app.get_db_conn')
    def test_get_all_battingstatsODI(self, mock_get_db_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [('Player',), ('Runs',)]
        mock_cursor.fetchall.return_value = [('Player A', '1000'), ('Player B', '900')]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn

        response = self.app.get('/api/v2/playerStats/battingODI/all')
        self.assertEqual(response.status_code, 200)
        self.assertIn("<td>Player</td>", response.data.decode('utf-8'))

    @patch('app.get_db_conn')
    def test_get_all_bowlerstats(self, mock_get_db_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [('Bowler',), ('Wickets',)]
        mock_cursor.fetchall.return_value = [('Bowler A', '50'), ('Bowler B', '40')]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn

        response = self.app.get('/api/v2/playerStats/bowlingT20/all')
        self.assertEqual(response.status_code, 200)
        self.assertIn("<td>Bowler</td>", response.data.decode('utf-8'))
        #self.assertIn("<td>50</td>", response.data.decode('utf-8'))

    @patch('app.get_db_conn')
    def test_get_all_bowlerstatsODI(self, mock_get_db_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.description = [('Bowler',), ('Wickets',)]
        mock_cursor.fetchall.return_value = [('Bowler A', '50'), ('Bowler B', '40')]
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn

        response = self.app.get('/api/v2/playerStats/bowlingODI/all')
        self.assertEqual(response.status_code, 200)
        self.assertIn("<td>Bowler</td>", response.data.decode('utf-8'))

    @patch('playerData.get_db_conn')
    @patch('playerData.BeautifulSoup')
    @patch('playerData.requests.get')
    def test_main_creates_necessary_tables(self, mock_get, mock_bs, mock_db_conn):
        # Mock successful page response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_db_conn.return_value = mock_conn
        
        # Mock BeautifulSoup
        mock_bs.return_value = BeautifulSoup("<html></html>", "html.parser")
        
        # Redirect standard output during test to avoid printing to console
        with patch('sys.stdout', new=mock_open()):
            main()
        
        # Check database calls
        self.assertTrue(mock_db_conn.called)

    @patch('app.get_db_conn')
    @patch('app.send_file')
    @patch('pandas.read_sql_query')
    @patch('seaborn.scatterplot')
    @patch('matplotlib.pyplot.savefig')
    def test_get_all_bowlerstats_plotCheck(
        self, mock_savefig, mock_scatterplot, mock_read_sql, mock_send_file, mock_get_db_conn
    ):
        # Arrange
        mock_conn = MagicMock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        dataframe = pd.DataFrame({
            'matches_played': ['-', '2', '5'],
            'wickets_taken': ['-', '4', '7']
        })
        mock_read_sql.return_value = dataframe
        # Mock the send_file to return a BytesIO object simulating an image file
        mock_send_file.return_value = BytesIO(b"image data")

        # Act
        response = app.test_client().get('/api/v2/playerStats/bowlingT20Plot/all')

        # Assert
        # Ensure that a database connection is established
        mock_get_db_conn.assert_called_with(dbname)
        # Ensure the SQL query is executed
        mock_read_sql.assert_called_with("select * from Bowling_Stats_T20;", mock_conn)
        # Ensure that '-' is replaced with 0 in dataframe columns
        pd.testing.assert_series_equal(dataframe['matches_played'], pd.Series([0, 2, 5]), check_names=False)
        pd.testing.assert_series_equal(dataframe['wickets_taken'], pd.Series([0, 4, 7]), check_names=False)
        # Ensure that the scatterplot is created
        mock_scatterplot.assert_called_once()
        # Ensure that xticks and yticks are set
        #self.assertEqual(plt.xticks(), ((0, 50), ()))
        #self.assertEqual(plt.yticks(), ((0, 50), ()))
        # Ensure that the plot is saved
        mock_savefig.assert_called_with('Bowlerplot.png')
        # Ensure that the plot is sent in the response
        mock_send_file.assert_called_with('Bowlerplot.png', mimetype='image/png')
        self.assertEqual(response.data, b"image data")
        #self.assertEqual(response.mimetype, 'image/png')

    @patch('app.get_db_conn')
    @patch('app.send_file')
    @patch('pandas.read_sql_query')
    @patch('seaborn.scatterplot')
    @patch('matplotlib.pyplot.savefig')
    def test_get_all_bowlerstats_plotCheckODI(
        self, mock_savefig, mock_scatterplot, mock_read_sql, mock_send_file, mock_get_db_conn
    ):
        # Arrange
        mock_conn = MagicMock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn
        dataframe = pd.DataFrame({
            'matches_played': ['-', '2', '5'],
            'wickets_taken': ['-', '4', '7']
        })
        mock_read_sql.return_value = dataframe
        # Mock the send_file to return a BytesIO object simulating an image file
        mock_send_file.return_value = BytesIO(b"image data")

        # Act
        response = app.test_client().get('/api/v2/playerStats/bowlingODIPlot/all')

        # Assert
        # Ensure that a database connection is established
        mock_get_db_conn.assert_called_with(dbname)
        # Ensure the SQL query is executed
        mock_read_sql.assert_called_with("select * from Bowling_Stats_Odi;", mock_conn)
        # Ensure that '-' is replaced with 0 in dataframe columns
        pd.testing.assert_series_equal(dataframe['matches_played'], pd.Series([0, 2, 5]), check_names=False)
        pd.testing.assert_series_equal(dataframe['wickets_taken'], pd.Series([0, 4, 7]), check_names=False)
        # Ensure that the scatterplot is created
        mock_scatterplot.assert_called_once()
        # Ensure that xticks and yticks are set
        #self.assertEqual(plt.xticks(), ((0, 50), ()))
        #self.assertEqual(plt.yticks(), ((0, 50), ()))
        # Ensure that the plot is saved
        mock_savefig.assert_called_with('BowlerplotODI.png')
        # Ensure that the plot is sent in the response
        mock_send_file.assert_called_with('BowlerplotODI.png', mimetype='image/png')
        self.assertEqual(response.data, b"image data")
        #self.assertEqual(response.mimetype, 'image/png')

    @patch('app.get_db_conn')
    @patch('app.send_file')
    @patch('pandas.read_sql_query')
    @patch('seaborn.scatterplot')
    @patch('matplotlib.pyplot.savefig')
    def test_get_all_battingstats_plot(self, mock_savefig, mock_scatterplot, mock_read_sql, mock_send_file, mock_get_db_conn):
        # Set up mock database connection context manager
        mock_conn = MagicMock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn

        # Create a dummy DataFrame
        dataframe = pd.DataFrame({
            'batting_average': ['-', '50', '60'],
            'batting_strike_rate': ['-', '80', '90']
        })
        mock_read_sql.return_value = dataframe
        # Mock the send_file to return a BytesIO object simulating an image file
        mock_send_file.return_value = BytesIO(b"image data")

        response = app.test_client().get('/api/v2/playerStats/battingT20Plot/all')


        # Assert that the SQL query was executed
        mock_get_db_conn.assert_called_once_with(dbname)
        mock_read_sql.assert_called_with("select * from Batting_Stats_T20;", mock_conn)


        # Assert that the DataFrame was modified as expected
        pd.testing.assert_series_equal(dataframe['batting_average'], pd.Series([0, 50, 60]), check_names=False)
        pd.testing.assert_series_equal(dataframe['batting_strike_rate'], pd.Series([0, 80, 90]), check_names=False)

        # Ensure that the scatterplot is created
        mock_scatterplot.assert_called_once()

        # Assert that xticks and yticks were set
        #mock_plt.xticks.assert_called_once_with(np.arange(0, max(expected_df['batting_average']) + 1, 10))
        #mock_plt.yticks.assert_called_once_with(np.arange(0, max(expected_df['batting_strike_rate']) + 1, 50))

        # Ensure that the plot is saved
        mock_savefig.assert_called_once_with('BattingPlot.png')
        # Ensure that the plot is sent in the response
        mock_send_file.assert_called_with('BattingPlot.png', mimetype='image/png')
        self.assertEqual(response.data, b"image data")

    @patch('app.get_db_conn')
    @patch('app.send_file')
    @patch('pandas.read_sql_query')
    @patch('seaborn.scatterplot')
    @patch('matplotlib.pyplot.savefig')
    def test_get_all_battingstats_plotODI(self, mock_savefig, mock_scatterplot, mock_read_sql, mock_send_file, mock_get_db_conn):
        # Set up mock database connection context manager
        mock_conn = MagicMock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn

        # Create a dummy DataFrame
        dataframe = pd.DataFrame({
            'batting_average': ['-', '50', '60'],
            'batting_strike_rate': ['-', '80', '90']
        })
        mock_read_sql.return_value = dataframe
        # Mock the send_file to return a BytesIO object simulating an image file
        mock_send_file.return_value = BytesIO(b"image data")

        response = app.test_client().get('/api/v2/playerStats/battingODIPlot/all')


        # Assert that the SQL query was executed
        mock_get_db_conn.assert_called_once_with(dbname)
        mock_read_sql.assert_called_with("select * from Batting_Stats_Odi;", mock_conn)


        # Assert that the DataFrame was modified as expected
        pd.testing.assert_series_equal(dataframe['batting_average'], pd.Series([0, 50, 60]), check_names=False)
        pd.testing.assert_series_equal(dataframe['batting_strike_rate'], pd.Series([0, 80, 90]), check_names=False)

        # Ensure that the scatterplot is created
        mock_scatterplot.assert_called_once()

        # Assert that xticks and yticks were set
        #mock_plt.xticks.assert_called_once_with(np.arange(0, max(expected_df['batting_average']) + 1, 10))
        #mock_plt.yticks.assert_called_once_with(np.arange(0, max(expected_df['batting_strike_rate']) + 1, 50))

        # Ensure that the plot is saved
        mock_savefig.assert_called_once_with('BattingPlotODI.png')
        # Ensure that the plot is sent in the response
        mock_send_file.assert_called_with('BattingPlotODI.png', mimetype='image/png')
        self.assertEqual(response.data, b"image data")
        
    def test_function_with_valid_data(self):
        with patch('requests.get') as mock_get, patch('playerData.BeautifulSoup') as mock_bs:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = 'squad_page_content'
            mock_bs.return_value.find_all.return_value = [
                 MagicMock(title='Player One', get=MagicMock(return_value='/cricketers/player-one-789')),
                 MagicMock(title='Player Two', get=MagicMock(return_value='/cricketers/player-two-012')),
            ]
            get_player_details(self.url_values, self.sqlite_conn, self.match_types)

            self.cur.execute('SELECT * FROM Players')
            players = self.cur.fetchall()
            self.assertEqual(len(players), 8)
            self.assertIn(('012', '012', '/cricketers/player-two-012', '/cricketers/player-two-012', None, 'Y'), players)

    @patch('app.get_db_conn')
    @patch('app.send_file')
    def test_get_all_battingstats_plot_empty_dataframe(self, mock_get_db_conn,mock_send_file):
        # Set up mock database connection context manager
        mock_conn = MagicMock()
        mock_get_db_conn.return_value.__enter__.return_value = mock_conn

        # Create an empty DataFrame
        empty_df = pd.DataFrame()
        mock_conn.execute.return_value.fetchall.return_value = empty_df

        mock_send_file.return_value = BytesIO(b"image data")
        # Call the function
        response = app.test_client().get('/api/v2/playerStats/battingT20Plot/all')

        self.assertEqual(response.status_code, 500)
    @patch('playerData.requests.get')
    def test_main_url_status_code_200(self, mock_get):
        # Setup mock to simulate a successful page response
        mock_response = MagicMock({})
        mock_response.status_code = 200
        mock_response.text="<html></html>"
        mock_get.return_value = mock_response
        
        # Call the main function
        main()

        # Check if get method was called with the correct URL
        mock_get.assert_called_with('https://www.espncricinfo.com/team')
    
    @patch('playerData.requests.get')
    def test_main_url_status_code_404(self, mock_get):
        # Setup mock to simulate a 404 page response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Call the main function while suppressing stdout and stderr
        with self.assertLogs(level='ERROR') as cm, self.assertRaises(SystemExit) as cm_exit:
            main()

        # Check if SystemExit was called with the correct code
        self.assertEqual(cm_exit.exception.code, -1)
        # Check if the logger recorded an error message
        self.assertIn('Url provided doesn\'t exist,exiting with error code 404', cm.output[0])
    
    @patch('playerData.get_db_conn')
    @patch('playerData.BeautifulSoup')
    @patch('playerData.requests.get')
    def test_main_creates_necessary_tables(self, mock_get, mock_bs, mock_db_conn):
        # Mock successful page response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_db_conn.return_value = mock_conn
        
        # Mock BeautifulSoup
        mock_bs.return_value = BeautifulSoup("<html></html>", "html.parser")
        
        # Redirect standard output during test to avoid printing to console
        with patch('sys.stdout', new=mock_open()):
            main()
        
        # Check database calls
        self.assertTrue(mock_db_conn.called)
    def test_function_with_no_player_links(self):
        with patch('requests.get') as mock_get, patch('playerData.BeautifulSoup') as mock_bs:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = 'squad_page_content_no_players'
            mock_bs.return_value.find_all.return_value = []
            get_player_details(self.url_values, self.sqlite_conn, self.match_types)

            self.cur.execute('SELECT * FROM Players')
            self.assertEqual(self.cur.fetchall(), [])

    def test_function_with_request_error(self):
        with patch('requests.get') as mock_get, patch('playerData.BeautifulSoup') as mock_bs:
            mock_get.side_effect = requests.exceptions.RequestException
            self.assertRaises(requests.exceptions.RequestException, get_player_details, self.url_values, self.sqlite_conn, self.match_types)
    
    def tearDown(self):
        self.sqlite_conn.close()

        
if __name__ == '__main__':
    unittest.main()
