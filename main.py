import os
from dotenv import load_dotenv
import base64
from requests import post, get
import json
import networkx as nx
from tm_keys import TM_KEY
import itertools
import pickle

# Oauth2 authentification
load_dotenv()

client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIFY_URL = "https://api.spotify.com/v1/artists/"
TM_URL = "https://app.ticketmaster.com/discovery/v2/"

ARTIST_CACHE = './artist_cache.json'
EVENT_CACHE = './event_cache.json'
GRAPH_FILE = './artist_graph.pkl'

def get_token():
  auth_string = client_id + ":" + client_secret
  auth_bytes = auth_string.encode("utf-8")
  auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

  url = "https://accounts.spotify.com/api/token"
  headers = {
    "Authorization": "Basic " + auth_base64,
    "Content-Type": "application/x-www-form-urlencoded"
  }
  data = {"grant_type": "client_credentials"}
  result = post(url, headers=headers, data=data)
  json_result = json.loads(result.content)
  token = json_result["access_token"]
  return token

def get_auth_header(token):
  return { "Authorization": "Bearer " + token }

token = get_token()

# use Spotify search endpoint
def search_and_recommend_artists(token, artist_name):
  """
  Searches for an artist on Spotify using the artist name. Retrieves information about a list of related artists using helper function get_artist_related_artist()

  Parameters:
  - token (str): The Spotify API token for authentication.
  - artist_name (str): The name of the artist.

  Returns:
  - list: A list of tuples representing related artists. Each tuple contains the name of the artist and a list of genres associated with that artist. Returns None if no artist is found.
  """
  url = "https://api.spotify.com/v1/search"
  headers = get_auth_header(token)
  query = f"?q={artist_name}&type=artist&limit=1"

  query_url = url + query
  result = get(query_url, headers=headers)
  json_result = json.loads(result.content)["artists"]["items"]

  if len(json_result) == 0:
    print("No artist with this name exsits")
    return None
  
  related_artists = get_artist_related_artist(token, json_result[0]['id']) # returns a list of tuples, [(name,[genres])]

  return related_artists

# use Spotify artists endpoint
def get_artist_related_artist(token, artist_id):
  """
  Retrieves a list of related artists for a given artist ID on Spotify.

  Parameters:
  - token (str): The Spotify API token for authentication.
  - artist_id (str): The unique Spotify ID of the artist for whom related artists are to be retrieved.

  Returns:
  - list: A list of dictionaries, each representing a related artist. Each dictionary contains the name of the artist,
    a list of genres associated with that artist, and the unique Spotify ID of the artist.

  Example:
  >>> token = "your_spotify_api_token"
  >>> artist_id = "6eUKZXaKkcviH0Ku9w2n3V"  # Example artist ID for Ed Sheeran
  >>> get_artist_related_artist(token, artist_id)
  [{'Taylor Swift': (['pop', 'country'], '06HL4z0CvFAxyc27GXpf02')}, {'Imagine Dragons': (['pop', 'rock'], '53XhwfbYqKCa1cC15pYq2q')}, ...]
  """
  endpoint = f"{artist_id}/related-artists?country=US"
  uri = SPOTIFY_URL + endpoint
  headers = get_auth_header(token)
  result = get(uri, headers=headers)
  json_result = json.loads(result.content)["artists"]
  artists = []
  for idx, artist in enumerate(json_result):
    artists.append({artist['name']: (artist['genres'], artist['id'])})
  return artists
      
# use Ticketmaster search endpoint
def get_attraction_id(keyword, key):
  """
  Searches for an attraction (e.g., artist, venue) using the Ticketmaster API and retrieves the ID of the first
  matching attraction.

  Parameters:
  - keyword (str): The keyword to search for in attractions.
  - key (str): The Ticketmaster API key for authentication.

  Returns:
  - str: The ID of the first matching attraction.
    If no matching attraction is found, returns a string indicating that the artist does not exist in Ticketmaster's system.

  Example:
  >>> keyword = "Ed Sheeran"
  >>> api_key = "your_ticketmaster_api_key"
  >>> get_attraction_id(keyword, api_key)
  'K8vZ9171oC7'
  """
  query = f"attractions.json?keyword={keyword}"
  api_key = f"&apikey={key}"
  uri = TM_URL + query + api_key
  response = get(uri)
  json_result = json.loads(response.content)
  try:
    return json_result['_embedded']['attractions'][0]['id']
  except:
     return f"artist does not exsit in ticketmaster's system"

# use Ticketmaster event endpoint
def get_event(keyword, key):
  """
  Retrieves a list of events associated with a given attraction (e.g., artist, venue) using the Ticketmaster API.

  Parameters:
  - keyword (str): The keyword to search for in attractions.
  - key (str): The Ticketmaster API key for authentication.

  Returns:
  - list: A list of dictionaries representing events associated with the given attraction.
    If no events are found, returns None.

  Example:
  >>> keyword = "Ed Sheeran"
  >>> api_key = "your_ticketmaster_api_key"
  >>> get_event(keyword, api_key)
  [{'name': 'Ed Sheeran: The Mathematics Tour', 'date': '2023-07-15', 'venue': 'Madison Square Garden', ...}, ...]
  """  
  id = get_attraction_id(keyword, key)
  query = f"events.json?attractionId={id}"
  country = f"&countryCode=US"
  api_key = f"&apikey={key}"
  uri = TM_URL + query + country + api_key
  response = get(uri)
  json_result = json.loads(response.content)
  try:
    return json_result['_embedded']['events']
  except:
    return None
   
# build graph based on data
def build_graph(data):
  """
  Builds a graph representing relationships between artists based on shared genres.

  Parameters:
  - data (list): A list of dictionaries where each dictionary represents an artist and their associated genres.

  Returns:
  - networkx.Graph: A networkx Graph object representing the artist network with weighted edges based on shared genres.
  """
  graph = nx.Graph()
  artists_data = [(artist, genres[0]) for artist_dict in data for artist, genres in artist_dict.items()]

  for artist, genres in artists_data:
      graph.add_node(artist, genres=genres)
  for artist1, genres1 in artists_data:
      for artist2, genres2 in artists_data:
          if artist1 != artist2:
              shared_genres = set(genres1) & set(genres2)
              weight = len(shared_genres)
              if weight > 0:
                  graph.add_edge(artist1, artist2, weight=weight)
  return graph

def find_top_5_similar_artists(graph):
  """
  Finds the top 5 artists with the highest Jaccard similarity based on shared genres in the provided graph.

  Parameters:
  - graph (networkx.Graph): A networkx Graph object representing the artist network with weighted edges based on shared genres.

  Returns:
  - list: A list of up to 5 artist names with the highest Jaccard similarity.
  """  
  similarities = {}
  for pair in itertools.combinations(graph.nodes, 2):
      artist1, artist2 = pair
      genres1 = set(graph.nodes[artist1]['genres'])
      genres2 = set(graph.nodes[artist2]['genres'])
      jaccard_similarity = len(genres1.intersection(genres2)) / len(genres1.union(genres2))
      similarities[pair] = jaccard_similarity

  # Find the pair with the highest Jaccard similarity
  sorted_dict = dict(sorted(similarities.items(), key=lambda item: item[1], reverse=True))

  keys = list(sorted_dict.keys())
  unique_artists = []
  for a1, a2 in keys:
      if a1 not in unique_artists:
          unique_artists.append(a1)
      if a2 not in unique_artists:
          unique_artists.append(a2)
  return unique_artists[:5]

def get_event_list(artist_list, key):
  """
  Retrieves a list of events for a given list of artists using the Ticketmaster API.

  Parameters:
  - artist_list (list): A list of artist names for which events are to be retrieved.
  - key (str): The Ticketmaster API key for authentication.

  Returns:
  - list: A list of tuples, each containing event information and URL.
    Each tuple has the format (event_info, event_url). If no events are found for an artist, the event_info
    will indicate that no event was found, and the event_url will be None.

  Example:
  >>> artist_list = ['Ed Sheeran', 'Taylor Swift', ...]
  >>> api_key = "your_ticketmaster_api_key"
  >>> events = get_event_list(artist_list, api_key)
  >>> print(events)
  [('Ed Sheeran: The Mathematics Tour at Madison Square Garden, New York, NY on 2023-07-15', 'https://www.ticketmaster.com/...'), ...]
  """
  events = []
  for a in artist_list:
    event = get_event(a, key)
    if event is not None:
        for data in event:
          line =  f"{data['name']} at {data['_embedded']['venues'][0]['name']}, {data['_embedded']['venues'][0]['city']['name']}, {data['_embedded']['venues'][0]['state']['stateCode']} on {data['dates']['start']['localDate']}"
          events.append((line, data['url']))
    else: 
      line = f"No event found for {a}"
      events.append((line, None))
  return events

# cache functions
def cache_or_load_graph(filepath, graph=None):
  try:
    with open(filepath, 'rb') as cache_file:
      g = pickle.load(cache_file)
  except:
    with open(filepath, 'wb') as cache_file:
      pickle.dump(graph, cache_file)
  return g

def cache_or_load_artists(token, artist_name):
  if os.path.exists(ARTIST_CACHE):
    with open(ARTIST_CACHE, 'r') as f:
      artists = json.load(f)
  else:
    artists = search_and_recommend_artists(token, artist_name)
    with open(ARTIST_CACHE, 'w') as f:
      json.dump(artists, f)
  return artists

def cache_or_load_events(key=TM_KEY):
  if os.path.exists(EVENT_CACHE):
    with open(EVENT_CACHE, 'r') as f:
      events = json.load(f)
  else:
    g = cache_or_load_graph(GRAPH_FILE)
    top5 = find_top_5_similar_artists(g)
    events = get_event_list(top5, key)
    with open(EVENT_CACHE, 'w') as f:
      json.dump(events, f)
  return events