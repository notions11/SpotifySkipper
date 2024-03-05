from keep_alive import keep_alive
import requests
import time
from tokens import *
from information import *
from modify_playlist import *
from modify_spreadsheets import *
from initialization import *
import datetime
import pytz
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import traceback
import sys, os


def current_milli_time():
    return round(time.time() * 1000)


def current_song_tuple(song_info):
    current_song_name = song_info['track_name']
    current_song_artists = song_info['artists']
    current_song_id = song_info['track_id']
    current_song_playlist = song_info['source_uri']
    current_song_remaining = song_info["duration"] - song_info['progress']
    current_song_duration = song_info["duration"]
    return current_song_name, current_song_artists, current_song_id, current_song_playlist, current_song_remaining, current_song_duration


def now_playing_debug(current_track_info, current_song, previous_song, playlist):
    print('Now playing: "' + current_track_info['track_name'] + '" by ' + current_track_info['artists'] + " in " + str(playlist))
    print("Current Song: " + str(current_song))
    print("Previous Song: " + str(previous_song))
    print()


def add_or_update_artists(all_artists, song_id, access_tokens, approved, new):
    song_info = get_track_by_id(access_tokens['modify_playlist'], song_id)
    song_artists_list = song_info['artists_unformatted']
    artists_links_list = song_info['artists_links']
    for a in range(len(song_artists_list)):
        artist = song_artists_list[a]
        link = artists_links_list[a]
        if artist not in all_artists.keys():
            all_artists[artist] = {
                'plays': 0,
                'yes_songs': 0,
                'no_songs': 0,
                'link': link
            }

        if approved and new:
            all_artists[artist]['yes_songs'] += 1
        elif not approved and new:
            all_artists[artist]['no_songs'] += 1
        elif not approved and not new:
            all_artists[artist]['yes_songs'] -= 1
            all_artists[artist]['no_songs'] += 1

        all_artists[artist]['plays'] += 1

def skip_song(access_token, check_song):
    url = "https://api.spotify.com/v1/me/player/next"
    requests.post(
        url,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    print("Can't play: " + check_song[0] + " by " + check_song[1] + " because it's been skipped before!")


def in_playlists(current_song_playlist):
    if current_song_playlist is None:
        return False
    for playlistid in playlist_ids.values():
        if playlistid in current_song_playlist:
            return True
    return False


def error_checking(all_songs, access_token):
    songs_in_sheets = all_songs.keys()

    songs_in_playlists = set()
    in_queue = get_playlist_items(access_token['modify_playlist'], playlist_ids['judgement'])
    skipped = get_playlist_items(access_token['modify_playlist'], playlist_ids['removed'])
    lifetime = get_playlist_items(access_token['modify_playlist'], playlist_ids['lifetime'])

    for song in in_queue:
        song_tuple = (song[0], song[1])
        if song_tuple in songs_in_playlists:
            print(str(song_tuple) + " is showing up as a duplicate (in_queue)")
        songs_in_playlists.add(song_tuple)

    for song in skipped:
        song_tuple = (song[0], song[1])
        if song_tuple in songs_in_playlists:
            print(str(song_tuple) + " is showing up as a duplicate (skipped)")
        songs_in_playlists.add(song_tuple)

    for song in lifetime:
        song_tuple = (song[0], song[1])
        if song_tuple in songs_in_playlists:
            print(str(song_tuple) + " is showing up as a duplicate (lifetime)")
        songs_in_playlists.add(song_tuple)

    for song in songs_in_playlists:
            if song not in songs_in_sheets:
                print(str(song) + " is in playlists but not in sheets")

def main():
    all_songs = dict()
    skipped_songs = set()
    approved_users = dict()
    all_artists = dict()
    tz = pytz.timezone('US/Pacific')
    print(f'{datetime.datetime.utcnow()-datetime.timedelta(hours=8):%Y-%m-%d %H:%M:%S%z}')

    blacklisted_devices = ['b3aecd46c924142ce49d701c70a5ed3285a71d78',
                           'f457b1598389d0e7eb38a3894ca6119c5d301cf4',
                           '98a41a2cb39abf31e855c63d939d91937b73bfbf']

    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", tokens.spreadsheet_scope)
    client = gspread.authorize(creds)
    lifetime_sheet = client.open("Spotify Skipper Data").get_worksheet(0)
    skipped_sheet = client.open("Spotify Skipper Data").get_worksheet(1)
    queue_sheet = client.open("Spotify Skipper Data").get_worksheet(2)
    artists_sheet = client.open("Spotify Skipper Data").get_worksheet(3)
    people_rankings_sheet = client.open("Spotify Skipper Data").get_worksheet(4)
    people_uid_sheet = client.open("Spotify Skipper Private").get_worksheet(0)
    all_songs_detailed_sheet = client.open("Spotify Skipper Private").get_worksheet(1)
    skipped_detailed_sheet = client.open("Spotify Skipper Private").get_worksheet(2)
    people_rankings_detailed_sheet = client.open("Spotify Skipper Private").get_worksheet(3)

    initialize(all_songs, skipped_songs, approved_users, all_artists, all_songs_detailed_sheet, skipped_detailed_sheet, people_rankings_detailed_sheet, artists_sheet)
    access_tokens = refresh_all_tokens(tokens.access_tokens, base_64, client_id, refresh_tokens)
    update_approved_users(people_uid_sheet, approved_users, people_rankings_detailed_sheet)
    move_song_in_recommended(queue_sheet, all_songs, approved_users, all_songs_detailed_sheet,
                             access_tokens['modify_playlist'], people_rankings_detailed_sheet)

    current_song = (None, None)
    current_song_duration = 0
    previous_song = (None, None)
    current_song_track_info = None

    start_timer = 0
    current_song_remaining = 0
    paused_counter = 0
    paused_threshold = 3600

    refresh_tokens_threshhold = 1800000
    refresh_tokens_timer_start = current_milli_time()

    current_song_name = None
    current_song_artists = None
    current_song_playlist = None
    current_song_device = None

    update_playlist_timer_bool = True
    update_tokens_timer_bool = True



    x = 0
    error_checking(all_songs, access_tokens)

    while x == 0:
        the_beginning_timer = current_milli_time()
        now = datetime.datetime.utcnow()-datetime.timedelta(hours=8)
        if now.minute == 0 and update_playlist_timer_bool:
            update_playlist_timer_bool = False
            move_song_in_recommended(queue_sheet, all_songs, approved_users, all_songs_detailed_sheet,
                                     access_tokens['modify_playlist'], people_rankings_detailed_sheet)
            current_song = (None, None)
            previous_song = (None, None)
        elif now.minute != 0:
            update_playlist_timer_bool = True

        if now.minute % 30 == 0 and update_tokens_timer_bool:
            update_tokens_timer_bool = False
            update_approved_users(people_uid_sheet, approved_users, people_rankings_detailed_sheet)
            access_tokens = refresh_all_tokens(access_tokens, base_64, client_id, refresh_tokens)
            current_song = (None, None)
            previous_song = (None, None)
        elif now.minute % 30 != 0:
            update_tokens_timer_bool = True


        current_playing_device = get_current_device(access_tokens['read_playback'])
        if str(current_playing_device) in blacklisted_devices:
            print("playing on blacklisted devices")
            time.sleep(30)
            continue

        current_track_info = get_current_track(access_tokens['currently_playing'], urls['currently_playing'])

        """
        Check if we are paused or disconnected. 
        If paused we should move the timer forward by 1 second.
        If we are disconnected we can reset the song to be more forgiving in case we accidentally start a song midway.
        """
        sleepyhours = [2, 3, 4, 5]
        if current_track_info is not None and current_track_info['is_playing'] is False:
            start_timer += 1
            if paused_counter % paused_threshold == 0:
                print("paused")
            paused_counter += 1
            if paused_counter >= paused_threshold:
                paused_counter = 0
            continue
        elif current_track_info is None:
            current_song = (None, None)
            previous_song = (None, None)
            if paused_counter % paused_threshold == 0:
                print("disconnected")
            paused_counter += 1
            if paused_counter >= paused_threshold:
                paused_counter = 0
            if now.hour in sleepyhours:
                time.sleep(600)
            time.sleep(60)
            continue
        else:
            paused_counter = 0

        check_song = (current_track_info['track_name'], current_track_info['artists'])
        if check_song in skipped_songs:
            skip_song(access_tokens['modify_playback'], check_song)
            continue

        if check_song != current_song:

            if current_song != (None, None) and current_song in all_songs.keys() \
                    and in_playlists(current_song_playlist) and current_song_device == current_playing_device:
                all_songs[(current_song_name, current_song_artists)]['plays'] += 1
                suggester = str(all_songs[(current_song_name, current_song_artists)]['added_by'])
                approved_users[suggester]['plays'] += 1
                end_timer = current_milli_time()
                song_in_playlist = all_songs[current_song]['current_playlist']
                print(current_song_remaining)
                print(current_song_duration - (end_timer - start_timer))
                if current_song_remaining > 30000 or (previous_song != (None, None) and current_song_duration - (end_timer - start_timer) > 60000):
                    print("Skipped: " + current_song_name + " by " + current_song_artists + " in playlist " + current_song_playlist)
                    if playlist_ids['lifetime'] in song_in_playlist:
                        move_lifetime_to_skipped(current_song_name, current_song_artists,
                                                 lifetime_sheet, skipped_sheet, approved_users, all_songs,
                                                 skipped_songs, all_artists, access_tokens['modify_playlist'])
                        add_or_update_artists(all_artists, current_song_id, access_tokens, False, False)
                    elif playlist_ids['judgement'] in song_in_playlist:
                        move_queue_to_skipped(current_song_name, current_song_artists,
                                                 queue_sheet, skipped_sheet, approved_users, all_songs,
                                                 skipped_songs, all_artists, access_tokens['modify_playlist'])
                        add_or_update_artists(all_artists, current_song_id, access_tokens, False, True)
                    update_removed_songs(skipped_detailed_sheet, current_song_name, current_song_artists)
                else:
                    print("Listened to: " + current_song_name + " by " + current_song_artists + " in playlist " + current_song_playlist)
                    if playlist_ids['judgement'] in song_in_playlist:
                        move_queue_to_lifetime(current_song_name, current_song_artists, queue_sheet, lifetime_sheet,
                                               approved_users, all_songs, all_artists, access_tokens['modify_playlist'])
                        add_or_update_artists(all_artists, current_song_id, access_tokens, True, True)
                    elif playlist_ids['lifetime'] in song_in_playlist:
                        update_lifetime(lifetime_sheet, all_songs, current_song_name, current_song_artists, approved_users)
                        add_or_update_artists(all_artists, current_song_id, access_tokens, True, False)
                update_all_songs(all_songs_detailed_sheet, all_songs, current_song_name, current_song_artists)
                update_user_rankings(people_rankings_sheet, people_rankings_detailed_sheet, suggester, approved_users[suggester])
                update_artists(artists_sheet, current_song_id, all_artists, access_tokens['modify_playlist'])
                print()

            previous_song = current_song
            current_song = check_song
            current_song_track_info = current_track_info
            current_song_name, current_song_artists, current_song_id, current_song_playlist, current_song_remaining, current_song_duration = current_song_tuple(current_song_track_info)
            current_song_device = current_playing_device
            now_playing_debug(current_track_info, current_song, previous_song, current_song_playlist)
            start_timer = current_milli_time()

        else:
            current_song_track_info = current_track_info
            current_song_name, current_song_artists, current_song_id, current_song_playlist, current_song_remaining, current_song_duration = current_song_tuple(
                current_song_track_info)
            current_song_device = current_playing_device

        # recently_played = get_recently_played(recently_played_token, urls['recently_played'])
        # print(recently_played)
        time.sleep(15)
        the_ending_timer = current_milli_time()
        #print((the_ending_timer - the_beginning_timer)/1000.0)

if __name__ == '__main__':
    keep_alive()
    
    while True:
        error_file = open("errorlog.txt.", 'a')
        try:
            main()
        except Exception as e:
            tz = pytz.timezone('US/Pacific')
            print(f'{datetime.datetime.utcnow()-datetime.timedelta(hours=8):%Y-%m-%d %H:%M:%S%z}')
            print(traceback.format_exc())
            error_file.write(f'{datetime.datetime.utcnow()-datetime.timedelta(hours=8):%Y-%m-%d %H:%M:%S%z}' + "\n")
            error_file.write(traceback.format_exc() + "\n")
            error_file.close()
            time.sleep(3600)

