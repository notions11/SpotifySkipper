import requests
import tokens
import time

def get_track_by_id(access_token, track_id):
    url = "https://api.spotify.com/v1/tracks/" + str(track_id)
    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    if str(response) != "<Response [200]>":
        print("error in get_track_by_id : " + str(response))
        if str(response) == "<Response [429]>":
            print("Retry-after: " + response.headers["Retry-After"])
            time.sleep(int(response.headers["Retry-After"]))
            return get_track_by_id(access_token, track_id)
        return None
    json_resp = response.json()

    track_id = json_resp['id']
    track_name = str(json_resp['name'])
    artists = [artist for artist in json_resp['artists']]
    duration = json_resp['duration_ms']
    link = json_resp['external_urls']['spotify']
    artist_names = ', '.join([artist['name'] for artist in artists])
    artists_names_unformatted = [artist['name'] for artist in artists]
    artists_links = [artist['external_urls']['spotify'] for artist in artists]
    available_markets = set(market for market in json_resp['available_markets'])

    current_track_info = {
        "track_id": track_id,
        "track_name": track_name,
        "artists": artist_names,
        "duration": duration,
        "link": link,
        "artists_unformatted": artists_names_unformatted,
        "artists_links": artists_links,
        "available_markets": available_markets
    }

    return current_track_info


def get_tracks_by_id(access_token, tracks_id):
    track_ids_list = ""
    for track in tracks_id:
        track_ids_list += str(track) + ","
    track_ids = "ids=" + track_ids_list[:-1]
    url = "https://api.spotify.com/v1/tracks"
    response = requests.get(
        url,
        params=track_ids,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    if str(response) != "<Response [200]>":
        print("error in get_trackS_by_id : " + str(response))
        if str(response) == "<Response [429]>":
            print("Retry-after: " + response.headers["Retry-After"])
            time.sleep(int(response.headers["Retry-After"]))
            return get_tracks_by_id(access_token, tracks_id)
        return None
    json_resp = response.json()
    list_tracks = [track for track in json_resp['tracks']]
    result = []
    for track in list_tracks:
        track_id = track['id']
        track_name = str(track['name'])
        artists = [artist for artist in track['artists']]
        duration = track['duration_ms']
        link = track['external_urls']['spotify']
        artist_names = ', '.join([artist['name'] for artist in artists])
        artists_names_unformatted = [artist['name'] for artist in artists]
        artists_links = [artist['external_urls']['spotify'] for artist in artists]
        available_markets = set(market for market in track['available_markets'])

        current_track_info = {
            "track_id": track_id,
            "track_name": track_name,
            "artists": artist_names,
            "duration": duration,
            "link": link,
            "artists_unformatted": artists_names_unformatted,
            "artists_links": artists_links,
            "available_markets": available_markets
        }
        result.append(current_track_info)

    return result


def get_current_track(access_token, current_track_url):
    response = requests.get(
        current_track_url,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    if str(response) != "<Response [200]>":
        if str(response) == "<Response [204]>":
            return None
        print("error in get_current_track : " + str(response))
        if str(response) == "<Response [429]>":
            print("Retry-after: " + response.headers["Retry-After"])
            time.sleep(int(response.headers["Retry-After"]))
            return get_current_track(access_token, current_track_url)
        return None
    json_resp = response.json()
    if 'currently_playing_type' in json_resp.keys():
        if json_resp['currently_playing_type'] != 'track':
            return {'is_playing': False}

    if json_resp['context'] != None:
        # we're not listening in a playlist
        source_uri = json_resp['context']['uri']
    else:
        source_uri = None
    track_id = json_resp['item']['id']
    track_name = str(json_resp['item']['name'])
    artists = [artist for artist in json_resp['item']['artists']]
    progress = json_resp['progress_ms']
    duration = json_resp['item']['duration_ms']
    is_playing = json_resp['is_playing']
    link = json_resp['item']['external_urls']['spotify']
    artist_names = ', '.join([artist['name'] for artist in artists])

    current_track_info = {
        "source_uri": source_uri,
        "track_id": track_id,
        "track_name": track_name,
        "artists": artist_names,
        "progress": progress,
        "duration": duration,
        "link": link,
        "is_playing": is_playing
    }

    return current_track_info


def get_recently_played(access_token, url):
    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    if str(response) != "<Response [200]>":
        print("error in get_recently_played : " + str(response))
        return None
    json_resp = response.json()

    track_names = []
    ctr = 0
    for i in json_resp['items']:
        name = i['track']['name']
        ctr += 1
        track_names.append(name)

    return track_names


def get_playlist_items(access_token, playlist_id, next=""):
    if next == "":
        url = "https://api.spotify.com/v1/playlists/" + playlist_id + "/tracks"
    else:
        url = next
    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    if str(response) != "<Response [200]>":
        print("error in get_playlist_items: " + str(response))
        if str(response) == "<Response [429]>":
            print("Retry-after: " + response.headers["Retry-After"])
        return None
    json_resp = response.json()

    track_data = [track for track in json_resp['items']]
    tracks = []
    for track in track_data:
        title = str(track['track']['name'])
        artists = [artist for artist in track['track']['artists']]
        artist_names = ', '.join([artist['name'] for artist in artists])
        added_by = track['added_by']['id']
        track_id = track['track']['id']
        track_type = track['track']['type']
        tracks.append((title, artist_names, added_by, track_id, track_type))

    tracks.reverse()
    if 'next' in json_resp:
        if json_resp['next'] == None:
            return tracks
        tracks_cont = get_playlist_items(access_token, playlist_id, json_resp['next'])
        return tracks_cont + tracks

    return tracks

def get_playlist_info_by_id(access_token, playlist_id):
    url = "https://api.spotify.com/v1/playlists/" + playlist_id
    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    if str(response) != "<Response [200]>":
        return "error in get_playlist_name_by_id"
    json_resp = response.json()

    playlist_name = json_resp['name']
    playlist_count = len(get_playlist_items(access_token, playlist_id))

    playlist_info = {
        "name": playlist_name,
        "items_count": playlist_count
    }
    return playlist_info

def get_current_device(access_token):
    url = "https://api.spotify.com/v1/me/player/devices"
    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    if str(response) != "<Response [200]>":
        return "error in get_current_device"
    json_resp = response.json()

    for device in json_resp["devices"]:
        if device['is_active']:
            return device['id']
