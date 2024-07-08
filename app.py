import spotipy
from flask import Flask, render_template, jsonify,request
import requests
import os
import json 
from spotipy.oauth2 import SpotifyOAuth 
import pandas as pd

app = Flask(__name__)

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_SECRET_ID = os.getenv('SPOTIFY_SECRET_ID')
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5000"

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

lyrics_df = pd.read_csv('./lyrics.csv')

@app.route('/')
def index():
    return render_template('index.html')

def analyze_mood(lyrics, max_tokens=100, temperature=0.7):
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
        return response.json()['generations'][0]['text'].strip()
    else:
        return f"Error: {response.status_code} - {response.text}"

@app.route('/recommend', methods=['GET','POST'])
def recommend():
    if request.method == 'POST':
        moods = {
            'Happy':['excitement','playful', 'joy'],
            'Sad':[],
            'Energetic':['energy','confident','powerful','confidence', 'boldness', 'fearless','resilience'],
            'Romantic':['emotional','love','romance','romantic','relationship','longing']
        }
        mood = request.form['mood']
        #matched_tracks = ['3B9CL5t32mM2SDdps2IhYM', '6EB454nVg2u6sbeCvWAPej', '6aQIGqAo9PxRKjUkhYtR6R', '6udC4b4jOSnHb9ItnXgKLR', '0b07JTxNfAE0evB53q0eO3', '3WVHfTd7xz9VPYJQFpOp8j', '6FahmzZYKH0zb2f9hrVsvw', '2uMh5DHeh70RoQ572k5oPI', '1hhLL2eWsnPtYCdDjbiRIU', '6NwEpX2JUWHVKWfDDfcqC4', '5PNZX8yqzqqAMPpl3UAoaP', '5urYiIXu1ZhfMAOsp7WDTc', '3wwLWFRLiReDf5AqgmAJwT', '4vlMdXsRpAIXYggwbNHZSv']
        matched_tracks = []
        top_tracks = spotify.current_user_top_tracks(limit=20)
        for track in top_tracks['items']:
            track_name = track['name']
            track_name = track_name.replace('"', "'")
            lyrics = lyrics_df[lyrics_df['name'] == track_name]
            analyzed_mood = analyze_mood(lyrics)
            print(analyzed_mood)
            if any(submood in analyzed_mood for submood in moods[mood]):
                matched_tracks.append(track['id'])
        
        print(matched_tracks)
        print([track['id'] for track in top_tracks['items']])
        if len(matched_tracks) == 0: 
            recommendations = 'You are not/rarely listening to '+ mood + ' songs!'
            return render_template('index.html', submitted=True, recommendations = [recommendations], found=False)
        elif len(matched_tracks) > 5:
            matched_tracks = matched_tracks[:5]
            recommendations = spotify.recommendations(seed_tracks=matched_tracks, limit=5)
            recommended_tracks = [track['id'] for track in recommendations['tracks']]
            create_playlist(recommended_tracks)
            return render_template('index.html', submitted=True, recommendations = [track['name'] for track in recommendations['tracks']], found=True)
        else:
            recommendations = spotify.recommendations(seed_tracks=matched_tracks, limit=5)
            recommended_tracks = [track['id'] for track in recommendations['tracks']]
            create_playlist(recommended_tracks)
            return render_template('index.html', submitted=True, recommendations = [track['name'] for track in recommendations['tracks']], found=True)
    return render_template('index.html', submitted=False)

def create_playlist(recommended_tracks):
    spotify_profile = spotify.me()
    spotify_id = spotify_profile['id']
    print('recom--->',recommended_tracks)

    playlist_name = 'MySpotify Tracks(Chill & Thrill)'
    playlist_description = 'Playlist created from My Spotify-Recommendation(Mood-Based Tracks)'
    playlist = spotify.user_playlist_create(user=spotify_id, name=playlist_name, public=True, description=playlist_description)

    # Access the playlist ID
    playlist_id = playlist['id']
    print(f"Created playlist with ID: {playlist_id}")

    # Add tracks to the playlist
    spotify.playlist_add_items(playlist_id=playlist_id, items=recommended_tracks)

    print(f"Added tracks to playlist: {playlist_name}")
    return

if __name__ == '__main__':
    app.run(debug=True)