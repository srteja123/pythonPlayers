import sqlite3
import requests
from bs4 import BeautifulSoup
import re,sys,argparse
import logging
import datetime
import traceback
from logging.handlers import RotatingFileHandler
dbname = 'CRICKET_PERF'

def get_db_conn(dbname):
    '''Returns sqlite db connection'''
    try:
        conn=sqlite3.connect(dbname+'.sqlite')
    except Exception as e:
        print('Unable to establish connection with database with error',e)
        sys.exit(-1)
        
    return conn

def get_country_details(country_links,selected_countries,sqlite_conn,country_map):
    
    cur = sqlite_conn.cursor()
    for selCountry in selected_countries:
        for country_link in country_links:
            if selCountry ==  country_link:
                cur.execute('INSERT OR IGNORE INTO Countries (country_id,country) VALUES (?,?)',(country_map[country_link],country_link))
            else:
                continue
    sqlite_conn.commit()
    
def get_player_details(url_values,sqlite_conn,match_types):
    
    cur = sqlite_conn.cursor()
    for urlValue in url_values:
        cid = urlValue.split('-')[-1]
        for type_no in match_types:
            squad_url='https://www.espncricinfo.com/cricketers'+urlValue
            
            squad_page=requests.get(squad_url)
            soupPlayer=BeautifulSoup(squad_page.text,"html.parser")
            player_links=soupPlayer.find_all('a',href=re.compile('/cricketers/'))
            for i in player_links:
                if i.get('title'):
                    player_id=i.get('href').split('-')[-1]
                    player=i.get('title').strip()
                    player_url=i.get('href')
                    if type_no == 2:
                        
                        cur.execute('INSERT OR IGNORE INTO Players (country_id,player_id,player,play_link) VALUES (:X, :Y, :Z, :A)',{'X':cid,'Y':player_id,'Z':player, 'A':player_url})
                        cur.execute("UPDATE Players Set odi_cap ='Y' where country_id=:X AND player_id=:Y AND player=:Z",{'X':cid,'Y':player_id,'Z':player})
                        
                    elif type_no == 3:
                        cur.execute('INSERT OR IGNORE INTO Players (country_id,player_id,player,play_link) VALUES (:X, :Y, :Z, :A)',{'X':cid,'Y':player_id,'Z':player, 'A':player_url})
                        cur.execute("UPDATE Players Set t20_cap ='Y' where country_id=:X AND player_id=:Y AND player=:Z",{'X':cid,'Y':player_id,'Z':player})
            
            
                sqlite_conn.commit()

def get_player_statistics(action,play_list,match_type,sqlite_conn):
    
    cur = sqlite_conn.cursor()
    i=0
    for play in play_list:
        i+=1
        if i%100==0:
            print(i)
        dict_batting_val={}
        dict_bowling_val={}
        player_name=play[3]
        player_link=play[4]
        stats_url='https://www.espncricinfo.com'+player_link
        try:
            stats_page=requests.get(stats_url)
            soup2=BeautifulSoup(stats_page.text,"html.parser")
            #logger.info("start")
            # Step 1: Find the specific paragraphs containing 'Batting & Fielding' and 'Bowling' string values
            bowling_div = soup2.find('p', string='Bowling')
            batting_fielding_div = soup2.find('p', string='Batting & Fielding')
            batting_fielding_odi_values=[]
            bowling_odi_values=[]
            bowling_th_values=[]
            batting_fielding_th_values=[]
            batting_fielding_t20s_values=[]
            bowling_t20s_values=[]
            if match_type==2:
                table_name_bat = 'Batting_Stats_Odi'
                table_name_bowl = 'Bowling_Stats_Odi'
            
            if batting_fielding_div:
                batting_fielding_thead = batting_fielding_div.find_next('thead', class_='ds-bg-fill-content-alternate ds-text-left ds-text-right')
                batting_fielding_th_values = [th.string.strip() for th in batting_fielding_thead.find_all('th')]
                batting_fielding_tbody = batting_fielding_thead.find_next('tbody')
                if batting_fielding_tbody.find('td', string='ODIs'):
                    batting_fielding_odi_values = [td.string.strip() for td in batting_fielding_tbody.find('td', string='ODIs').parent.find_all('td')]

            if bowling_div:
                bowling_thead = bowling_div.find_next('thead', class_='ds-bg-fill-content-alternate ds-text-left ds-text-right')
                bowling_th_values = [th.string.strip() for th in bowling_thead.find_all('th')]
                bowling_tbody = bowling_thead.find_next('tbody')
                if bowling_tbody.find('td', string='ODIs'):
                    bowling_odi_values = [td.string.strip() for td in bowling_tbody.find('td', string='ODIs').parent.find_all('td')]

            #Batting values
            if len(batting_fielding_th_values) > 1:
                    batting_fielding_th_values = batting_fielding_th_values[1:]
                    if len(batting_fielding_odi_values) > 1:
                        batting_fielding_odi_values = batting_fielding_odi_values[1:]
                        dict_batting_val = dict(zip(batting_fielding_th_values,batting_fielding_odi_values))
            #Bowling values
            if len(bowling_th_values) > 1:
                    bowling_th_values = bowling_th_values[1:]
                    if len(bowling_odi_values) > 1:
                        bowling_odi_values = bowling_odi_values[1:]
                        dict_bowling_val = dict(zip(bowling_th_values,bowling_odi_values))
                # Outputting the values
                    print("Batting & Fielding TH values:", batting_fielding_th_values)
                    print("Batting & Fielding  ODIs values:", batting_fielding_odi_values)
                    print("Bowling TH values:", bowling_th_values)
                    print("Bowling ODIs values:", bowling_odi_values)
                    print(dict_batting_val)
                    print(dict_bowling_val)
            elif match_type==3:
                table_name_bat = 'Batting_Stats_T20'
                table_name_bowl = 'Bowling_Stats_T20'
            if batting_fielding_div:
                batting_fielding_thead = batting_fielding_div.find_next('thead', class_='ds-bg-fill-content-alternate ds-text-left ds-text-right')
                batting_fielding_th_values = [th.string.strip() for th in batting_fielding_thead.find_all('th')]
                batting_fielding_tbody = batting_fielding_thead.find_next('tbody')
                if batting_fielding_tbody.find('td', string='T20s'):
                    batting_fielding_t20s_values = [td.string.strip() for td in batting_fielding_tbody.find('td', string='T20s').parent.find_all('td')]

            if bowling_div:
                bowling_thead = bowling_div.find_next('thead', class_='ds-bg-fill-content-alternate ds-text-left ds-text-right')
                bowling_th_values = [th.string.strip() for th in bowling_thead.find_all('th')]
                bowling_tbody = bowling_thead.find_next('tbody')
                if bowling_tbody.find('td', string='T20s'):
                    bowling_t20s_values = [td.string.strip() for td in bowling_tbody.find('td', string='T20s').parent.find_all('td')]


            #Batting values
            if len(batting_fielding_th_values) > 1:
                    batting_fielding_th_values = batting_fielding_th_values[1:]
                    if len(batting_fielding_t20s_values) > 1:
                        batting_fielding_t20s_values = batting_fielding_t20s_values[1:]
                        dict_batting_val = dict(zip(batting_fielding_th_values,batting_fielding_t20s_values))
            #Bowling values
            if len(bowling_th_values) > 1:
                    bowling_th_values = bowling_th_values[1:]
                    if len(bowling_t20s_values) > 1:
                        bowling_t20s_values = bowling_t20s_values[1:]
                        dict_bowling_val = dict(zip(bowling_th_values,bowling_t20s_values))
            print("Batting & Fielding TH values:", batting_fielding_th_values)
            print("Batting & Fielding T20s values:", batting_fielding_t20s_values)
            print("Bowling TH values:", bowling_th_values)
            print("Bowling T20s values:", bowling_t20s_values)
            print(dict_batting_val)
            print(dict_bowling_val)
            if action=="bowling":
                if len(dict_bowling_val) > 1:
                    Mat = dict_bowling_val.get('Mat','NA')
                    Inns = dict_bowling_val.get('Inns','NA')
                    Balls = dict_bowling_val.get('Balls','NA')
                    Runs = dict_bowling_val.get('Runs','NA')
                    Wkts = dict_bowling_val.get('Wkts','NA')
                    BBI =  dict_bowling_val.get('BBI','NA')
                    BBM =  dict_bowling_val.get('BBM','NA')
                    Ave =  dict_bowling_val.get('Ave','NA')
                    Econ =  dict_bowling_val.get('Econ','NA')
                    SR =  dict_bowling_val.get('SR','NA')
                    fourW =  dict_bowling_val.get('4w','NA')
                    fiveW =  dict_bowling_val.get('5w','NA')
                    tenW =  dict_bowling_val.get('10w','NA')
                    cur.execute('''INSERT OR IGNORE INTO '''+table_name_bowl+ ''' (player ,matches_played,innings_bowled_in,
                    balls_bowled ,runs_conceded ,wickets_taken ,
                    best_bowling_in_an_innings ,best_bowling_in_a_match,bowling_average ,economy_rate ,bowling_strike_rate ,
                    four_wkts_exactly_in_an_inns ,five_wickets_in_an_inns,ten_wickets_in_an_inns)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(player_name,Mat,Inns,Balls,Runs,Wkts,BBI,BBM,Ave,Econ,SR,fourW,fiveW,tenW))
                    sqlite_conn.commit()
                    
            elif action =='batting':
                if len(dict_batting_val) > 1:
                    Mat = dict_batting_val.get('Mat','NA')
                    Inns = dict_batting_val.get('Inns','NA')
                    NO = dict_batting_val.get('NO','NA')
                    Runs = dict_batting_val.get('Runs','NA')
                    HS = dict_batting_val.get('HS','NA')
                    Ave = dict_batting_val.get('Ave','NA')
                    BF = dict_batting_val.get('BF','NA')
                    SR =  dict_batting_val.get('SR','NA')
                    No100s = dict_batting_val.get('100s','NA')
                    No50s =  dict_batting_val.get('50s','NA')
                    Fours = dict_batting_val.get('4s','NA')
                    Sixes = dict_batting_val.get('6s','NA')
                    Catches = dict_batting_val.get('Ct','NA')
                    Stumps = dict_batting_val.get('St','NA')
                    cur.execute('''INSERT OR IGNORE INTO '''+table_name_bat+''' (player ,matches_played ,
                    innings_batted ,not_outs, runs_scored ,highest_innings_score ,batting_average ,
                    balls_faced ,batting_strike_rate ,hundreds_scored ,scores_between_50_and_99  ,
                    boundary_fours ,boundary_sixes,Catches_taken, Stumping)VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(player_name,Mat,Inns,NO,Runs,HS,Ave,BF,
                    SR,No100s,No50s,Fours,Sixes,Catches,Stumps))
                    sqlite_conn.commit()
        except Exception as e:
            print('Exception error for below player:',e)
            traceback.print_exc()
            logger.info(play)
        

def main():    
    
    global url
    global year
    global dbname
    global match_type
    global logger
    ##Setup logger
    
    logger=logging.getLogger(__name__)
    
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler = RotatingFileHandler('cricket_parser.log',maxBytes=10485760,backupCount=20)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    #print("Process Start at {}".format(str(datetime.datetime.now())))
    
    #[australia,bangladesh,england,india,new-zealand,pakistan,south-africa,sri-lanka,west-indies,zimbabwe,afghanistan]
    ##Argument parser
    # parser = argparse.ArgumentParser(description='Cricket Performance Data Parser')

    # parser.add_argument('-d', '--databasename', dest='databasename',default='CRICKET_PERF',
    #                     help='Sqlite Master Database name to store the details')
    # parser.add_argument('-t', '--typeofmatch', dest='typeofmatch', default='ALL',
    #                     help='enter ODI/T20/ALL to fetch corresponding data')
    # parser.add_argument('-c', '--countries', dest='countries',default='ALL',nargs='*',
    #                     help='valid entries =  [australia,bangladesh,england,india,new-zealand,pakistan,south-africa,sri-lanka,west-indies,zimbabwe,afghanistan].Players performance from mentioned countries data would be updated in database,default = ALL to update all players from all countries')

    # args = parser.parse_args()
    # dbname = args.databasename
    # countries = args.countries
    # match_type = args.typeofmatch
    
    selected_countries =  ['Australia','Bangladesh','England','India','New Zealand','Pakistan','South Africa','Sri Lanka','West Indies','Zimbabwe','Afghanistan']
    url = 'https://www.espncricinfo.com/team'
    
    page = requests.get(url)
    
    ##Check if webpage is active
    if page.status_code == 200:
        #print('Url status code indicates active status,proceeding with webscraping')
        ##creating BeautifulSoup Object
        soup=BeautifulSoup(page.text,"html.parser")
        anchor_tags = soup.find_all('a')
        country_map={}
        # Extract href and text from each anchor tag
        for tag in anchor_tags:
            href = tag.get('href').split('-')[-1]
            text = tag.find('span').text if tag.find('span') else ''
            country_map[text] = href
    
        country_lin=soup.find_all('a',href=re.compile('/team/'))

        url_values = []
    
        for country_li in country_lin:
            url_values.append(country_li.get('href'))

        # Find the div with the specified class
        divs = soup.findAll('div', class_='ds-flex ds-flex-row ds-items-center ds-space-x-2 lg:ds-p-6 ds-px-4 ds-py-2 ds-border-line ds-border-b odd:ds-border-r')
        country_links=list()
        # Find the span with the specified class within the div
        for div in divs:
            country_links.append(div.find('span', class_='ds-text-title-s ds-font-bold').text)
    
        ##Create necessary tables in database for insertion of stats data
        with get_db_conn(dbname) as sqlite_conn:
            cur = sqlite_conn.cursor()
            cur.execute('''CREATE TABLE IF NOT EXISTS Countries
                (country_id INTEGER PRIMARY KEY,country TEXT)''')
        
            cur.execute('''CREATE TABLE IF NOT EXISTS Players
                (country_id INTEGER,player_id INTEGER UNIQUE,player TEXT,odi_cap TEXT,t20_cap TEXT,play_link TEXT)''')
            cur.execute('''CREATE TABLE IF NOT EXISTS Batting_Stats_Odi (player TEXT,matches_played TEXT,
                    innings_batted TEXT,not_outs TEXT, runs_scored TEXT,highest_innings_score TEXT,batting_average TEXT,
                    balls_faced TEXT,batting_strike_rate TEXT,hundreds_scored TEXT,scores_between_50_and_99 TEXT,
                    boundary_fours TEXT,boundary_sixes TEXT,Catches_taken TEXT, Stumping TEXT)''')
        
            cur.execute('''CREATE TABLE IF NOT EXISTS Bowling_Stats_Odi (player TEXT,matches_played TEXT,innings_bowled_in TEXT,
                    balls_bowled TEXT,runs_conceded TEXT,wickets_taken TEXT,
                    best_bowling_in_an_innings TEXT,best_bowling_in_a_match TEXT,bowling_average TEXT,economy_rate TEXT,bowling_strike_rate TEXT,
                    four_wkts_exactly_in_an_inns TEXT,five_wickets_in_an_inns TEXT,ten_wickets_in_an_inns TEXT)''')
            cur.execute('''CREATE TABLE IF NOT EXISTS Batting_Stats_T20 (player TEXT,matches_played TEXT,
                    innings_batted TEXT,not_outs TEXT, runs_scored TEXT,highest_innings_score TEXT,batting_average TEXT,
                    balls_faced TEXT,batting_strike_rate TEXT,hundreds_scored TEXT,scores_between_50_and_99 TEXT,
                    boundary_fours TEXT,boundary_sixes TEXT,Catches_taken TEXT, Stumping TEXT)''')
            cur.execute('''CREATE TABLE IF NOT EXISTS Bowling_Stats_T20 (player TEXT,matches_played TEXT,innings_bowled_in TEXT,
                    balls_bowled TEXT,runs_conceded TEXT,wickets_taken TEXT, 
                    best_bowling_in_an_innings TEXT,best_bowling_in_a_match TEXT, bowling_average TEXT,economy_rate TEXT,bowling_strike_rate TEXT,
                    four_wkts_exactly_in_an_inns TEXT,five_wickets_in_an_inns TEXT,ten_wickets_in_an_inns TEXT)''') 
        
        
            sqlite_conn.commit();
    
            #print('Created necessary tables in database')
    
            ##Fetch all  countires name and id and store in database
            with get_db_conn(dbname) as sqlite_conn:
                #print('Fetching select countries data')
                get_country_details(country_links,selected_countries,sqlite_conn,country_map)
                #print('Inserted data into Countries table')
    
    
            ##Fetch countries id from database and store in list
            with get_db_conn(dbname) as sqlite_conn:
                cur = sqlite_conn.cursor()
                cur.execute('SELECT country_id,country FROM Countries')
                get_player_details(url_values,sqlite_conn,[2,3]) 
                #print('Inserted data into Players table')
    
            ##select country id,name and player id,name from database and fetch player statistics
            with get_db_conn(dbname) as sqlite_conn:
                cur = sqlite_conn.cursor()
        
            cur.execute('''select a.country_id,a.country,b.player_id,b.player,b.play_link from Countries a,Players b where a.country_id=b.country_id and b.odi_cap="Y";''')
            play_listodi=list()
            for row in cur:
                play_listodi.append(row)
        
            cur.execute('''select a.country_id,a.country,b.player_id,b.player,b.play_link from Countries a,Players b where a.country_id=b.country_id and b.t20_cap="Y";''')
            play_listt20=list()
            for row in cur:
                play_listt20.append(row)
############################################################################################################
            
            with get_db_conn(dbname) as sqlite_conn:
                for action in ['batting','bowling']:
                    get_player_statistics(action,play_listodi,2,sqlite_conn)
                    get_player_statistics(action,play_listt20,3,sqlite_conn)

    
                #logger.info('Successfully collected Player bowling and batting statistics and stored in database')
                #print('Successfully collected Player bowling and batting statistics and stored in database')
    
    elif page.status_code == 404:
        logger.error("Url provided doesn't exist,exiting with error code 404")
        sys.exit(-1)
    
    
if __name__ == "__main__":
    main()

