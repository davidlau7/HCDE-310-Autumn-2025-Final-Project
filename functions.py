import urllib.parse, urllib.request, urllib.error, json, time, requests

from geopy.geocoders import Nominatim

API_BASE_URL = "https://api.spotify.com/v1/"

###-- General Functions --###

def get_weather_playlist(token, place):
    """
    Creates and adds a Spotify playlist to the user's library based on the weather of the place the user inputted.

    Parameters
    * token: (str) Access token required to obtain user information.
    * place: (str) Place of weather to get playlist from.
    Returns
    * (JSON) JSON data of newly created playlist. If weather information could not be retrieved, return an error and
    corresponding message.
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    weather = get_weather(place)
    top_artists = get_top_artists(token)
    if not top_artists:
        return "Error: No top artists available."

    # Calculating the average popularity to use as a reference.
    total_popularity = 0
    for artist in top_artists.values():
        total_popularity += artist["Popularity"]
    total_popularity = total_popularity / len(top_artists)

    # Define keywords to check in weather string.
    cold_keywords = ["rain", "snow", "showers", "drizzle"]
    hot_keywords = ["sunny", "cloud", "clear"]

    # Check for weather keywords in weather string.
    is_cold_weather = any(keyword in weather for keyword in cold_keywords)
    is_hot_weather = any(keyword in weather for keyword in hot_keywords)

    # Calculating recommended artists if forecast contains cold weather phenomena.
    if is_cold_weather:
        recommended_artists = {}
        for key, value in top_artists.items():
            artist = top_artists[key]
            if artist["Popularity"] < total_popularity:
                recommended_artists[key] = value

        if not recommended_artists:
            print("Warning: No artists below average popularity. Using all artists.")
            recommended_artists = top_artists

        data = create_playlist(headers, "Cold Weather Playlist", "A playlist to match the weather for you! From Forecast Player")
        playlist_id = data["id"]
        uris = artist_top_tracks(token, recommended_artists)

        return add_to_playlist(token, uris, playlist_id)

    # Calculating recommended artists if forecast contains hot weather phenomena.
    if is_hot_weather:
        recommended_artists = {}
        for key, value in top_artists.items():
            artist = top_artists[key]
            if artist["Popularity"] >= total_popularity:
                recommended_artists[key] = value

        if not recommended_artists:
            print("Warning: No artists above average popularity. Using all artists.")
            recommended_artists = top_artists

        data = create_playlist(headers, "Hot Weather Playlist", "A playlist to match the weather for you! From Forecast Player")
        playlist_id = data["id"]
        uris = artist_top_tracks(token, recommended_artists)

        return add_to_playlist(token, uris, playlist_id)

    return {"Error": f"Unknown weather condition: {weather}"}

###-- Spotify API Functions --###

def get_user_id(token):
    """
    Returns the user's Spotify ID that is required for creating and adding playlists to the user's library.

    Parameters
    * token: (str) Access token required to obtain user information.
    Returns:
    * (str) User's Spotify ID
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    response = requests.get(API_BASE_URL + "me/", headers=headers)

    if not response.ok:
        raise Exception(f"Failed to fetch user profile: {response.text}")

    user_info = response.json()

    if "id" not in user_info:
        raise Exception("Unexpected Spotify API response: 'id' not found in /me response.")

    return user_info["id"]

def create_playlist(token, name, description):
    """
    Creates a new playlist and adds it to the user's Spotify library.

    Parameters
    * token: (str) Access token required to obtain user information.
    * name: (str) Name of playlist.
    * description: (str) Description of playlist.
    Returns:
    * (JSON) JSON data of newly created playlist.
    """

    user_id = get_user_id(token)

    req_body = {
        "name": name,
        "description": description,
        "public": False
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{API_BASE_URL}users/{user_id}/playlists"

    response = requests.post(url, headers=headers, json=req_body)

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "5")
        raise Exception(f"API calls limited by Spotify. Retry after {retry_after} seconds.")

    if not response.ok:
        raise Exception(f"Failed to create playlist: {response.text}")

    return response.json()

def get_top_artists(token):
    """
    Returns a dictionary of a user's top 20 artists, along with their popularity score and number of followers. If there is no
    data in JSON file, return an empty dictionary.

    Parameters
    * token: (str) Access token required to obtain user information.
    Returns
    * (Dict) Dict of artists names and their popularity score and number of followers.
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.get(API_BASE_URL + "me/top/artists", headers=headers)

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "5")
        raise Exception(f"API calls limited by Spotify. Retry after {retry_after} seconds.")

    if not response.ok:
        raise Exception(f"Failed to get top artists: {response.text}")

    data = response.json()

    if "items" not in data or not data["items"]:
        return {}

    top_artists = {}

    for artist in data["items"]:
        top_artists[artist["name"]] = {"Popularity": int(artist["popularity"]),
                                       "Followers": artist["followers"]["total"],
                                       "ID": artist["id"]}

    return top_artists

def artist_top_tracks(token, list_of_artists):
    """
    Returns a dictionary of the URIs for top 10 tracks of an artist.

    Parameters:
    * token: (str) Access token required to obtain user information.
    * list_of_artists: (Dict) Dictionary of top artists from user based on weather conditions.
    Returns
    * (dict) Dictionary of URIs for top 10 tracks of an artist.
    """

    all_uris = []
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for artist in list_of_artists.values():
        response = requests.get(
            f"{API_BASE_URL}artists/{artist['ID']}/top-tracks",
            headers=headers,
            params={"market": "US"}
        )
        data = response.json()["tracks"]

        for track in range(0, len(data), 5):
            all_uris.append(data[track]["uri"])

    return {"uris": all_uris}

def add_to_playlist(token, tracks, playlist_id):
    """
    Adds a list of tracks to a playlist. If unsuccessful, prints an error message accordingly.

    Parameters:
    * token: (str) Access token required to obtain user information.
    * tracks: (list) List of track URIs to add to playlist.
    * playlist_id: (str) ID of Spotify playlist.
    Returns:
    * (JSON) JSON data of newly added playlist.
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{API_BASE_URL}playlists/{playlist_id}/tracks",
        headers=headers,
        json=tracks
    )

    if response.status_code != 201:
        print("Error adding to playlist:", response.text)

    return response.json()

###-- National Weather Service API Functions --###

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
        return "Could not find location forecast."
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
    Returns the forecast for the next 12-hour period of a location.

    Parameters
    * place: (str) Name of location
    Returns
    * (str) A short description of forecast for the next 12-hour period.
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

    return forecast[0]["shortForecast"].lower()

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

    print(get_weather("Hawaii"))
    print(get_weather("Los Angeles"))

if __name__ == "__main__":
    try:
        main()
    except (NameError, SyntaxError):
        pass
