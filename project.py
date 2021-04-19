import requests
import json
from opencage.geocoder import OpenCageGeocode
import sqlite3
import secrets
from bs4 import BeautifulSoup
import csv
import re
from fuzzywuzzy import fuzz

geocoder = OpenCageGeocode(secrets.OCG_API_KEY)

CACHE_FILENAME = 'city_pollution.json'

def open_cache():
    ''' opens the cache file if it exists and loads the JSON into
    a dictionary, which it then returns.
    if the cache file doesn't exist, creates a new cache dictionary
    Parameters
    ----------
    None
    Returns
    -------
    The opened cache
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' saves the current state of the cache to disk
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

CACHE = open_cache()

def get_pollution_data(city):
    if city in CACHE:
        return CACHE[city]
    else:
        results = geocoder.geocode(city)[0]['geometry']
        lat = results['lat']
        lon = results['lng']
        BASE_URL = 'http://api.openweathermap.org/data/2.5/air_pollution/history?'
        response = requests.get(BASE_URL + f'lat={lat}&lon={lon}&start=1606266000&end=1616817600&appid={secrets.OWM_API_KEY}')
        data = response.json()
        CACHE[city] = data['list']
        save_cache(CACHE)
        return data['list']

def create_country_code_dict():
    country_code_dict = {}
    html = requests.get("https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3").text
    soup = BeautifulSoup(html, "html.parser")
    list_items = soup.find(class_='plainlist')
    for item in list_items.find_all('li'):
        code_name = item.text
        code = code_name[0:3]
        name = code_name[5:]
        country_code_dict[name] = code
    return country_code_dict

def create_alt_country_names_dict():
    alt_names_codes_dict = {}
    html = requests.get("https://en.wikipedia.org/wiki/List_of_alternative_country_names").text
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all(class_ = "wikitable")
    for table in tables:
        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            code = cells[0].text.strip()
            name = cells[1].text.strip()
            alt_name = cells[2].text.strip()
            simple_name = re.sub(r"\([^()]*\)", "", name)
            simple_alt_name = re.sub(r"\([^()]*\)", "", alt_name) 
            alt_name_code = {}
            alt_name_code['code'] = code
            alt_name_code['alt_names'] = simple_alt_name.strip()
            alt_names_codes_dict[simple_name.strip()] = alt_name_code
    return alt_names_codes_dict

if __name__ == "__main__":
    #inp = input("Enter a city name, state (optional), and country: ")
    #data = get_pollution_data(inp.lower())
    
    connection = sqlite3.connect("CO2_air_pollution.sqlite")
    cursor = connection.cursor()

    ### add air pollution per country to database ###
    with open('air_pollution.csv') as file:
        rows = csv.reader(file, delimiter=',')
        cursor.execute("CREATE TABLE IF NOT EXISTS air_pollution (country CHAR(30), country_code CHAR(3), '1990' FLOAT, '2005' FLOAT, '2017' FLOAT)")
        line_count = 0
        for row in rows:
            if line_count < 5:
                pass
            else:
                vals = (row[0], row[1], row[34], row[49], row[61])
                query = "INSERT INTO air_pollution (country, country_code, '1990', '2005', '2017') VALUES(?, ?, ?, ?, ?)"
                cursor.execute(query, vals)
                connection.commit()
            line_count += 1
    
    ### get CO2 data form wikipedia ###
    html = requests.get('https://en.wikipedia.org/wiki/List_of_countries_by_carbon_dioxide_emissions').text
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='wikitable')
    country_names = []
    emissions_1990 = []
    emissions_2005 = []
    emissions_2017 = []
    rows = table.find_all('tr')[5:]
    for row in rows:
        cells = row.find_all('td')
        name = cells[0]
        country_names.append(name.text.strip())

        e_1990 = cells[1]
        emissions_1990.append(e_1990.text.strip())

        e_2005 = cells[2]
        emissions_2005.append(e_2005.text.strip())

        e_2017 = cells[3]
        emissions_2017.append(e_2017.text.strip())

    ### add CO2 data per country to database ###
    cursor.execute("CREATE TABLE IF NOT EXISTS emissions (country CHAR(30), country_code CHAR(3), '1990' FLOAT, '2005' FLOAT, '2017' FLOAT)")
    query2 = "INSERT INTO emissions (country, country_code, '1990', '2005', '2017') VALUES(?, ?, ?, ?, ?)"
    country_code_dict = create_country_code_dict()
    alt_names_codes = create_alt_country_names_dict()
    count = 0
    for country in country_names:
        query1 = "SELECT country_code FROM air_pollution WHERE country=?"
        cursor.execute(query1, (country,))
        code_unformatted = cursor.fetchall()
        if code_unformatted == []:
            for name1 in alt_names_codes:
                if country == name1 or country in alt_names_codes[name1]['alt_names']:
                    code = alt_names_codes[name1]['code']
            for name2 in country_code_dict:
                similarity = fuzz.ratio(name2, country)
                if country == name2 or similarity > 77 or name2 in country or country in name2:
                    code = country_code_dict[name2]
        else:
            code = code_unformatted[0][0]
        vals = (country, code, emissions_1990[count], emissions_2005[count], emissions_2017[count])
        cursor.execute(query2, vals)
        connection.commit()
        count += 1


