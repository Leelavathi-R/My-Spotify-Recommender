import spotipy
from flask import Flask, render_template, jsonify,request
import requests
import os
import json 
from spotipy.oauth2 import SpotifyOAuth 

app = Flask(__name__)

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_SECRET_ID = os.getenv('SPOTIFY_SECRET_ID')
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5000"

moods = {
    'happy':[],
    'sad':[],
    'romance':[],
    'energetic': [],
    'calm':[]
}

spotify = spotipy.Spotify(auth_manager = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_SECRET_ID,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-library-read user-top-read playlist-modify-public",
))

COHERE_API_URL = 'https://api.cohere.com/v1/generate'
HEADERS = {
    'Authorization': f'Bearer {COHERE_API_KEY}',
    'Content-Type': 'application/json'
}

@app.route('/')
def index():
    return render_template('index.html')

def analyze_mood(lyrics, max_tokens=50, temperature=0.7):
    prompt = f"Analyze the mood of these lyrics: {lyrics}"
    payload = {
        'model': 'command-xlarge-nightly',
        'prompt': prompt,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'k': 0,
        'p': 1,
        'stop_sequences': ['\n']
    }
    response = requests.post(COHERE_API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        print("------Response:",response.json())
        return response.json()['generations'][0]['text'].strip()
    else:
        return f"Error: {response.status_code} - {response.text}"

@app.route('/recommend', methods=['POST'])
def recommend():
    mood = request.form['mood']
    top_tracks = spotify.current_user_top_tracks(limit=20)
    print([track['name'] for track in top_tracks['items']])

    with open('./lyrics.json', 'r') as file:
        lyrics_data = json.load(file)

    for track in top_tracks['items']:
        track_name = track['name']
        lyrics = lyrics_data['track_name']
        analyzed_mood = analyze_mood(lyrics)
    
    #recommendations = spotify.recommendations(seed_tracks=[track['id'] for track in top_tracks['items']], limit=10)
    
    #return render_template('recommendations.html', mood=analyzed_mood, recommendations=recommendations['tracks'])
    return 'happy'

if __name__ == '__main__':
    app.run(debug=True)
    