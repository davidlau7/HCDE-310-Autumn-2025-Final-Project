from authlib.integrations.requests_client import OAuth2Session
from projectsecrets import client_id, client_secret
from geopy.geocoders import Nominatim
import urllib.parse, urllib.request, urllib.error, json, time

### Spotify API Functions ###

### Function to gain authorization from user
# scope = "playlist-read-private playlist-read-collaborative"
#
# client = OAuth2Session(client_id, client_secret, scope=scope, redirect_uri="http://127.0.0.1:5000")
# authorization_endpoint = "https://accounts.spotify.com/authorize"
# uri, state = client.create_authorization_url(authorization_endpoint)
# print("Please go to this URL in your web browser and follow the prompts: {}".format(uri))
#
# authorization_response = input("Once you are redirected by your browser, copy the URL from your browser's address bar and enter it here:")
#
# token_endpoint = "https://accounts.spotify.com/api/token"
# token = client.fetch_token(token_endpoint, authorization_response=authorization_response)
#
# api_endpoint = "https://api.spotify.com/v1/"
# resp = client.get(api_endpoint + "me/playlists")
# pprint.pprint(resp.text)


### National Weather Service API Functions ###

def geocode(place):
    """
    Returns the coordinates of a given place based on the name of the location.

    Parameters
        * place: (str) Name of location.
    Returns
        * (int) Tuple of latitude and longitude of given place. If no results were found, returns None.
    """

    geolocator = Nominatim(user_agent="Forecast Player")
    location = geolocator.geocode(place)
    if location is None:
        return None
    else:
        coordinates = (location.latitude, location.longitude)
        return coordinates

def get_gridpoint(place):
    """
    Returns the API endpoint of the National Weather Service with information of the forecast for
    the next seven days in 12-hour periods using gridpoints.

    Parameters
        * place: (str) Name of location.
    Returns
        * (str) API endpoint of forecast for coordinate. If no results were found, returns None.
    """

    coordinates = geocode(place)
    if coordinates is None:
        print("No coordinates found for {}".format(place))
        return None

    url = "https://api.weather.gov/points/" + str(coordinates[0]) + "," + str(coordinates[1])
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print("Error trying to retrieve data from NWS.")
        print("Error code: " + str(e.code))
        return None
    except urllib.error.URLError as e:
        print("Failed to reach NWS Server.")
        print("Reason:", e.reason)
        return None
    return json.loads(data)["properties"]["forecast"]

def get_weather(place):
    """
    Returns the forecast for the next two 12-hour periods of a location.

    Parameters
        * place: (str) Name of location
    Returns
        * (str) List of short descriptions of forecast for the next two 12-hour periods.
    """

    url = get_gridpoint(place)
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print("Error trying to retrieve data from NWS.")
        print("Error code:", e.code)
        return None
    except urllib.error.URLError as e:
        print("Failed to reach NWS Server.")
        print("Reason:", e.reason)
        return None

    weather_data = json.loads(data)
    forecast = weather_data["properties"]["periods"]
    temp_list = []
    temp_list.append(forecast[0]["shortForecast"])
    temp_list.append(forecast[1]["shortForecast"])
    return temp_list

def main():
    """
    Function for testing other functions.
    """
    print("Getting API endpoint for Seattle.")
    print(get_gridpoint("University of Washington"))

    time.sleep(1)

    print("Getting API endpoint for Fake City.")
    print(get_gridpoint("Fake City"))

    time.sleep(1)

    print("Getting forecast for Seattle.")
    print(get_weather("University of Washington"))

    time.sleep(1)

    print("Getting forecast for Fake City.")
    print(get_weather("Fake City"))

if __name__ == "__main__":
    try:
        main()
    except (NameError, SyntaxError):
        pass
