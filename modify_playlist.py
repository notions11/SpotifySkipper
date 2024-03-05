import requests
import tokens
from information import *


def remove_song_from_playlist(access_token, playlist_id, song_id):
    url = "https://api.spotify.com/v1/playlists/" + playlist_id + "/tracks"
    song_uri = '{\"tracks\":[{\"uri\":\"spotify:track:' + song_id + '\"}]}'
    requests.delete(
        url,
        data=song_uri,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    track_info = get_track_by_id(access_token, song_id)
    # playlist_info = get_playlist_info_by_id(access_token, playlist_id)
    if track_info is not None:
        print('Removed: "' + track_info['track_name'] + '" by ' + track_info['artists'] + " from " + playlist_id)
    else:
        print("error in remove song")


def remove_songs_from_playlist(access_token, playlist_id, song_ids, songs_info):
    url = "https://api.spotify.com/v1/playlists/" + playlist_id + "/tracks"
    all_uris = []

    for song_id in song_ids:
        all_uris.append(song_id)

    all_uris_str = ', '.join([uri for uri in all_uris])
    songs_uri = '{\"tracks\":[' + all_uris_str + ']}'
    requests.delete(
        url,
        data=songs_uri,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    # playlist_info = get_playlist_info_by_id(access_token, playlist_id)
    for track_info in songs_info:
        if track_info is not None:
            print('Removed: "' + track_info['track_name'] + '" by ' + track_info['artists'] + " from " + playlist_id)
        else:
            print("error in remove songSS")

def add_song_to_playlist(access_token, playlist_id, song_id):
    url = "https://api.spotify.com/v1/playlists/" + playlist_id + "/tracks?uris=spotify%3Atrack%3A" + song_id
    requests.post(
        url,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    track_info = get_track_by_id(access_token, song_id)
    # playlist_info = get_playlist_info_by_id(access_token, playlist_id)
    if track_info is not None:
        print('Added: "' + track_info['track_name'] + '" by ' + track_info['artists'] + " to " + playlist_id)
    else:
        print("error in adding song")


def add_songs_to_playlist(access_token, playlist_id, song_ids, songs_info):
    url = "https://api.spotify.com/v1/playlists/" + playlist_id + "/tracks"
    all_uris = []

    for song_id in song_ids:
        all_uris.append('\"spotify:track:' + str(song_id) + '\"')

    all_uris_str = ', '.join([uri for uri in all_uris])
    songs_uri = '{\"uris\":[' + all_uris_str + ']}'
    requests.post(
        url,
        data=songs_uri,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    # playlist_info = get_playlist_info_by_id(access_token, playlist_id)
    for track_info in songs_info:
        if track_info is not None:
            print('Added: "' + track_info['track_name'] + '" by ' + track_info['artists'] + " to " + playlist_id)
        else:
            print("error in adding song")