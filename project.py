import requests
import json
from opencage.geocoder import OpenCageGeocode
import sqlite3
import secrets
from bs4 import BeautifulSoup
import csv
import re
from fuzzywuzzy import fuzz
import plotly.graph_objs as go
import pygal
import pycountry

CITY_POLLUTION_CACHE_FILENAME = 'city_pollution.json'
ALT_COUNTRY_NAMES_CACHE_FILENAME = 'alt_country_names.json'

def open_cache(CACHE_FILENAME):
    ''' opens the cache file if it exists and loads the JSON into
    a dictionary, which it then returns.
    if the cache file doesn't exist, creates a new cache dictionary
    Parameters
    ----------
    Cache filename

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

def save_cache(cache_dict, CACHE_FILENAME):
    ''' saves the current state of the cache to disk
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    Cache filename

    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

CITY_POLLUTION_CACHE = open_cache(CITY_POLLUTION_CACHE_FILENAME)
ALT_COUNTRY_NAMES_CACHE = open_cache(ALT_COUNTRY_NAMES_CACHE_FILENAME)

def get_pollution_data(city):
    '''
    Gets air pollution data for one city for November 27, 2020 - March 27, 2021
    and returns it. Checks cache for the data. If no data is found in the cache, 
    then the retrieved data is stored in the cache.

    Parameters
    ----------
    city: string
        city name

    Returns
    -------
    String stating that the city name is invalid
    OR
    city_dict: dict
        dictionary of air pollution data
    '''

    if city in CITY_POLLUTION_CACHE:
        return CITY_POLLUTION_CACHE[city]
    else:
        geocoder = OpenCageGeocode(secrets.OCG_API_KEY)
        response = geocoder.geocode(city)
        if response == []:
            return f"Invalid city name: {city}."
        else:
            results = response[0]['geometry']
            lat = results['lat']
            lon = results['lng']
            BASE_URL = 'http://api.openweathermap.org/data/2.5/air_pollution/history?'
            response = requests.get(BASE_URL + f'lat={lat}&lon={lon}&start=1606266000&end=1616817600&appid={secrets.OWM_API_KEY}')
            data = response.json()
            raw_data = data['list']
            count = 0
            aqi_sum = 0
            co_sum = 0
            no_sum = 0
            no2_sum = 0
            o3_sum = 0
            so2_sum = 0
            pm2_5_sum = 0
            pm10_sum = 0
            nh3_sum = 0
            for item in raw_data:
                aqi_sum += item["main"]["aqi"]
                co_sum += item["components"]["co"]
                no_sum += item["components"]["no"]
                no2_sum += item["components"]["no2"]
                o3_sum += item["components"]["o3"]
                so2_sum += item["components"]["so2"]
                pm2_5_sum += item["components"]["pm2_5"]
                pm10_sum += item["components"]["pm10"]
                nh3_sum += item["components"]["nh3"]
                count += 1
            avg_aqi = aqi_sum/count
            avg_co = co_sum/count
            avg_no = no_sum/count
            avg_no2 = no2_sum/count
            avg_o3 = o3_sum/count
            avg_so2 = so2_sum/count
            avg_pm2_5 = pm2_5_sum/count
            avg_pm10 = pm10_sum/count
            avg_nh3 = nh3_sum/count
            city_dict = {"AQI": avg_aqi,
                    "CO": avg_co,
                    "NO": avg_no,
                    "NO2": avg_no2,
                    "O3": avg_o3,
                    "SO2": avg_so2,
                    "PM 2.5": avg_pm2_5,
                    "PM 10": avg_pm10,
                    "NH3": avg_nh3}
            CITY_POLLUTION_CACHE[city] = city_dict
            save_cache(CITY_POLLUTION_CACHE, CITY_POLLUTION_CACHE_FILENAME)
            return city_dict

def create_city_pollution_bar_chart(city1, component=None, city2=None, city3=None):
    '''
    Generates a bar chart based of one, two, or three cities.
    If one city is selected, then the chart displays all 9 air air pollution components.
    If more than one city is selected, then a component will need to be provided. The bar
    chart displays the values for the selected component across the multiple cities.

    Parameters
    ----------
    city1: string
        first city
    component: string
        number corresponing to the selected component (1-9)
    city2: string
        second city
    city3: string
        third city

    Returns
    -------
    String stating that the city name is invalid
    OR
    fig: Plotly figure
        the bar chart
    '''
    if component == None:
        city_data = get_pollution_data(city1)
        if isinstance(city_data, str):
            return city_data
        else:
            xvals = ["CO", "NO", "NO2", "O3", "SO2", "PM 2.5", "PM 10", "NH3"]
            yvals = [city_data["CO"], city_data["NO"], city_data["NO2"], city_data["O3"], city_data["SO2"],
                    city_data["PM 2.5"], city_data["PM 10"], city_data["NH3"]]
            bar_data = go.Bar(x=xvals, y=yvals)
            layout = go.Layout(title=f"Air Pollution of {city1.title()} in μg/m^3")
            fig = go.Figure(data=bar_data, layout=layout)
            return fig
    else:
        components = {"1": "AQI (1-5)", "2": "CO (μg/m^3)", "3": "NO (μg/m^3)",
                    "4": "NO2 (μg/m^3)", "5": "O3 (μg/m^3)", "6": "SO2 (μg/m^3)",
                    "7": "PM 2.5 (μg/m^3)", "8": "PM 10 (μg/m^3)", "9": "NH3 (μg/m^3)"}
        city1_data = get_pollution_data(city1)
        if isinstance(city1_data, str):
            return city1_data
        else:
            if city2 != None:
                city2_data = get_pollution_data(city2)
                if isinstance(city2_data, str):
                    return city2_data
                else:
                    if city3 == None:
                        xvals = [city1.title(), city2.title()]
                        yvals = [city1_data[components[component]], city2_data[components[component]]]
                        layout = go.Layout(title=f"Comparing {components[component]} of {city1.title()} and {city2.title()}")
                        bar_data = go.Bar(x=xvals, y=yvals)
                        fig = go.Figure(data=bar_data, layout=layout)
                        return fig
                    else:
                        city3_data = get_pollution_data(city3)
                        if isinstance(city3_data, str):
                            return city3_data
                        else:
                            xvals = [city1.title(), city2.title(), city3.title()]
                            yvals = [city1_data[components[component]], city2_data[components[component]], city3_data[components[component]]]
                            layout = go.Layout(title=f"Comparing {component} of {city1.title()}, {city2.title()}, and {city3.title()}")
                            bar_data = go.Bar(x=xvals, y=yvals)
                            fig = go.Figure(data=bar_data, layout=layout)
                            return fig

def create_country_code_dict():
    '''
    Scrapes country three-letter country codeds from Wikipedia
    Parameters
    ----------
    none

    Returns
    -------
    country_code_dict: dict
        dictionary with country names and corresponding codes
    '''

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

def get_alt_country_names_dict():
    '''
    Checks cache file for data. If not found,
    scrapes alternative country names and codes from Wikipedia

    Parameters
    ----------
    none

    Returns
    -------
    alt_names_codes_dict: dict
        dictionay containing official country name, alternative names, and code
    '''

    if ALT_COUNTRY_NAMES_CACHE:
        return ALT_COUNTRY_NAMES_CACHE
    else:
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
        save_cache(alt_names_codes_dict, ALT_COUNTRY_NAMES_CACHE_FILENAME)
        return alt_names_codes_dict

def create_database():
    '''
    Creates database of CO2 emissions per country and air pollution per country.
    Air pollution is from a local csv file.
    Emissions is scraped from Wikipedia.
    Codes for the each country in the emissions table are found.
    Air pollution is from a local csv file.

    Parameters
    ----------
    none

    Returns
    -------
    none
    '''
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
    query = "INSERT INTO emissions (country, country_code, '1990', '2005', '2017') VALUES(?, ?, ?, ?, ?)"
    country_code_dict = create_country_code_dict()
    alt_names_codes = get_alt_country_names_dict()
    count = 0
    for country in country_names:
        if 'France' in country:
            code = 'FRA'
        elif 'Italy' in country:
            code = 'ITA'
        elif 'Switzerland' in country:
            code = 'CHE'
        else:
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
        cursor.execute(query, vals)
        connection.commit()
        count += 1

def generate_world_map(map_type, year):
    '''
    Generates a world map with either CO2 emissions or air pollution data
    for a given year.

    Parameters
    ----------
    map_type: int
        1 for emissions, 2 for air pollution
    year: int
        1 for 1990, 2 for 2005, or 3 for 2017

    Returns
    -------
    none
    '''
    worldmap_chart = pygal.maps.world.World()
    connection = sqlite3.connect("CO2_air_pollution.sqlite")
    cursor = connection.cursor()
    years = {1 : '1990', 2: '2005', 3: '2017'}
    if map_type == 1:
        worldmap_chart.title = f"CO2 Emissions by Country in {years[year]}"
        cursor.execute("SELECT * FROM emissions")
        code_emissions_dict = {}
        for row in cursor:
            try:
                country = pycountry.countries.get(alpha_3=row[1].strip())
                new_code = country.alpha_2
            except:
                pass
            code_emissions_dict[new_code.lower()] = int(float(str(row[year + 1]).replace(',', '')))
        worldmap_chart.add('Mt CO2', code_emissions_dict)
        worldmap_chart.render_in_browser()
    elif map_type == 2:
        worldmap_chart.title = f"Air Pollution by Country in {years[year]}"
        cursor.execute("SELECT * FROM air_pollution")
        code_pollution_dict = {}
        for row in cursor:
            try:
                country = pycountry.countries.get(alpha_3=row[1].strip())
                new_code = country.alpha_2
            except:
                pass
            if row[year + 1] == '':
                pass
            else:
                code_pollution_dict[new_code.lower()] = int(row[year+1])
        worldmap_chart.add("Annual Exposure", code_pollution_dict)
        worldmap_chart.render_in_browser()

def generate_line_graph(country, graph_type):
    '''
    Generates a line graph based on air pollution or emissions for a given country.

    Parameters
    ----------
    country: string
        country name
    graph_type: string
        1 for emissions, 2 for air pollution
    
    Returns
    -------
    String stating that there is no data for the country
    OR
    fig: Plotly figure
        the line graph
    '''
    connection = sqlite3.connect("CO2_air_pollution.sqlite")
    cursor = connection.cursor()
    if graph_type == '1':
        cursor.execute("SELECT * FROM emissions")
        for row in cursor:
            if country.title() in row[0] or row[0] in country.title():
                if row[2] == '':
                    return f"No data for {row[0]}"
                else:
                    yvals = [row[2], row[3], row[4]]
                    xvals = ['1990', '2005', '2017']
                    line_data = go.Scatter(x=xvals, y=yvals)
                    layout = go.Layout(title=f"CO2 Emissions for {row[0]} from 1990-2017")
                    fig = go.Figure(data=line_data, layout=layout)
                    return fig
    elif graph_type == '2':
        cursor.execute("SELECT * FROM air_pollution")
        for row in cursor:
            if country.title() in row[0] or row[0] in country.title():
                if row[2] == '':
                    return f"No data for {row[0]}"
                else:
                    yvals = [row[2], row[3], row[4]]
                    xvals = ['1990', '2005', '2017']
                    line_data = go.Scatter(x=xvals, y=yvals)
                    layout = go.Layout(title=f"Air Pollution for {row[0]} from 1990-2017")
                    fig = go.Figure(data=line_data, layout=layout)
                    return fig
if __name__ == "__main__":
     create_database()
     while True:
        print("\n1. Air pollution data for one city.\n2. Comparing air pollution data for multiple cities.\n" +
        "3. Air pollution or CO2 emissions for one country from 1990-2017.\n4. Air pollution or CO2 emissions globally for one year.")
        data_type = input("\nEnter the number corresponding to the data you would like to explore or enter 'exit': ")
        if data_type.strip() == '1':
            while True:
                city1 = input("\nEnter a city name, state (optional), and country: ")
                results = create_city_pollution_bar_chart(city1)
                if isinstance(results, str):
                    print(results)
                else:
                    results.show()
                    break
        elif data_type.strip() == '2':
            while True:
                city1 = input("Enter a city name, state (optional), and country: ")
                city2 = input("Enter another: ")
                city3 = input("Enter another or enter 'done' to compare just two cities: ")
                print("\n1. Air Quality Index (AQI)\n2. Carbon Monoxide (CO)\n3. Nitrogen Monoxide (NO)\n4. Nitrogen Dioxide (NO2)\n5. Ozone (O3)\n"
                + "6. Sulphur Dioxide (SO2)\n7. Particulates < 2.5 micrometers\n8. Particulates < 10 micrometers\n9. Ammonia (NH3)")
                component = input("\nEnter the number an air polllution component from the above list to compare across the cities: ")
                if int(component) not in range(1, 10):
                    print("\nInvalid selection.")
                else:
                    if city3.strip().lower() == 'done':
                        results = create_city_pollution_bar_chart(city1, component, city2)
                        if isinstance(results, str):
                            print(results)
                        else:
                            results.show()
                            break
                    else:
                        results = create_city_pollution_bar_chart(city1, component, city2, city3)
                        if isinstance(results, str):
                            print(results)
                        else:
                            results.show()
                            break
        elif data_type.strip() == '3':
            while True:
                country = input('\nEnter a country name: ')
                print("\n1. CO2 Emissions\n2. Air Pollution")
                graph_type = input('\nEnter the number corresponding to the data you wish to explore: ')
                if int(graph_type.strip()) not in range(1,3):
                    print("\nInvalid selection.")
                else:
                    data = generate_line_graph(country, graph_type)
                    if isinstance(data, str):
                        print(data)
                    elif isinstance(data, go.Figure):
                        data.show()
                        break
                    else:
                        print("\nInvalid country name.")
        elif data_type.strip() == '4':
            while True:
                print("\n1. CO2 Emissions\n2. Air Pollution\n")
                map_type = input('Enter the number corresponding to the data you wish to explore: ')
                if int(map_type.strip()) not in range(1,3):
                    print("\nInvalid selection\n")
                else:
                    print("\n1. 1990\n2. 2005\n3. 2017\n")
                    year = input("\nEnter the number corresponding to the year you wish to explore: ")
                    if int(year.strip()) not in range(1,4):
                        print("\nInvalid selection")
                    else:
                        generate_world_map(int(map_type.strip()), int(year.strip()))
                        break
        elif data_type.strip().lower() == 'exit':
            exit()
        else:
            print("\nInvalid selection")
