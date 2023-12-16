import os
from dotenv import load_dotenv
import base64
from requests import post, get
import json
import networkx as nx
from tm_keys import TM_KEY
import itertools

# Oauth2 authentification
load_dotenv()

client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIFY_URL = "https://api.spotify.com/v1/artists/"
TM_URL = "https://app.ticketmaster.com/discovery/v2/"

ARTIST_CACHE = 'aritst_cache.json'
EVENT_CACHE = 'event_cache.json'
GRAPH_FILE = 'track_graph.gpickle'

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
  query = f"attractions.json?keyword={keyword}"
  api_key = f"&apikey={key}"
  uri = TM_URL + query + api_key
  response = get(uri)
  json_result = json.loads(response.content)
  return json_result['_embedded']['attractions'][0]['id']

# use Ticketmaster event endpoint
def get_event(keyword, key):
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

# cache functions
def cache_artists(result):
  pass

def load_cache(file_path):
  pass
   
# build graph based on data
def build_graph(data):
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