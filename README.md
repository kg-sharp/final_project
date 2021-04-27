In order to use this program, be sure to download the air_pollution.csv file and place it inside the same folder as the main program file.

There are two API keys that are needed. The first is from Open Weather Map API. You will only need the free version. Next is Open Cage Geocoding API. Again, you will only need the free version.

Required packages: OpenCageGeocode from opencage.geocoder, sqlite3, BeautifulSoup from bs4, fuzz from fuzzywuzzy, plotly.graph_obs, pygal, and pycountry.

Program description: When you start up the program, you will be presented with a menu to choose from. First, you can display air pollution data for one city or compare a single air pollution component across up to three cities. The air pollution components are an Air Quality Index (1-5, where 1 is the best), carbon monoxide, nitrogen monoxide, nitrogen dioxide, ozone, sulphur dioxide, particulates < 2.5 micrometers, particulates < 10 micrometers, and ammonia. Note that the AQI is not displayed if you choose to display only one city. This is because the AQI is on a different scale. All of the other components will be displayed for a single city. Next, you can display a line graph showing air pollution or CO2 emissions for one country from 1990-2017. Finally, you can display a world map representing air pollution or CO2 emissions for almost every country.

How to interact with the program: When entering city or country names, please ensure that you spelling them correctly or the program will not work. When a menu displays, you will be asked to simply type the number corresponding to your choice. Please enter only valid numbers. Do not spell out the numbers. Once a graph or map has been displayed, the main menu will return. You will need to enter 'exit' here to end the program. Please note that some countries may have CO2 emissions data but no air pollution data or vice versa. Thus, even if you spelled the country correctly, no maps or graphs can be displayed.

