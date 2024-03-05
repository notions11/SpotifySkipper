from __future__ import print_function
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tokens import *
from information import *
from modify_playlist import *
import pytz
from datetime import datetime
from collections import defaultdict


def add_to_sheet(sheet, current_track_info, currenttime):
    info = [current_track_info["track_name"], current_track_info["artists"], currenttime]
    sheet.append_row(info)


def update_approved_users(people_uid_sheet, approved_users, people_rankings_detailed_sheet):
    approved_people = people_uid_sheet.get_all_records(numericise_ignore=['all'])
    if len(approved_people) == len(approved_users):
        return
    index = 2
    for user in approved_people:
        user_id = str(user['uid'])
        if user_id not in approved_users.keys():
            approved_users[user_id] = {
                'index': index,
                'name': user['name'],
                'yes_songs': 0,
                'no_songs': 0,
                'plays': 0,
                'denied': 0
            }
            to_be_written = [user_id, user['name'], 0, 0, 0, 0]
            people_rankings_detailed_sheet.append_row(to_be_written)
        index += 1


def move_song_in_recommended(queue_sheet, all_songs, approved_users, all_songs_detailed_sheet, access_token, people_rankings_detailed_sheet):
    queue_song_helper = []

    recommended_songs_playlist_items = get_playlist_items(access_token, playlist_ids['recommended'])
    for song in recommended_songs_playlist_items:
        queue_song_helper.append(song)

    if len(queue_song_helper) == 0:
        return

    while len(queue_song_helper) != 0:
        amount = 50
        ctr = 0
        song_ids_removal = []
        songs_ids_removal_info = []
        songs_ids_add = []
        songs_ids_add_info = []
        songds_ids_added_by = []
        queue_paste = []
        all_songs_paste = []
        update_denied_users = set()
        while ctr < amount and len(queue_song_helper) != 0:
            ctr += 1
            song = queue_song_helper.pop() # make this .pop(0) eventually

            song_name = song[0]
            song_artists = song[1]
            song_tuple = (song_name, song_artists)
            song_added_by = str(song[2])
            song_id = song[3]
            song_type = song[4]

            song_ids_removal.append('{\"uri\":\"spotify:' + song_type + ':' + str(song_id) + '\"}')
            songs_ids_removal_info.append({
                'track_name': song_name,
                'artists': song_artists,
            })
            if song_type != 'track':
                print("!Failure to add: " + song_name + " by " + song_artists + " recommended from " + song_added_by)
                print("Reason: Song is not a track")
                continue
            if song_added_by not in approved_users.keys():
                print("Added user " + str(song_added_by) + " to approved")
                people_rankings_detailed_sheet.append_row(str(song_added_by), str(song_added_by), 0, 0, 0, 0)
                max_index = -1
                for user in approved_users:
                    tempindex = approved_users[user]
                    if tempindex > max_index:
                        max_index = tempindex
                max_index += 1
                person_data = {
                    'index': max_index,
                    'name': song_added_by,
                    'yes_songs': 0,
                    'no_songs': 0,
                    'plays': 0,
                    'denied': 0
                 }
                approved_users[song_added_by] = person_data
            if song_tuple in all_songs.keys() or song_tuple in songs_ids_add:
                print("!Failure to add: " + song_name + " by " + song_artists + " recommended from " + song_added_by)
                print("Reason: Song already has been added")
                approved_users[song_added_by]['denied'] += 1
                update_denied_users.add(song_added_by)
                continue

            songs_ids_add.append(song_id)
            songds_ids_added_by.append(song_added_by)
            songs_ids_add_info.append({
                'track_name': song_name,
                'artists': song_artists,
            })
            print("Success: " + song_name + " by " + song_artists + " recommended from " + song_added_by)

        if len(update_denied_users) != 0:
            for u in update_denied_users:
                update_only_private_user_rankings(people_rankings_detailed_sheet, u, approved_users[u])

        if len(songs_ids_add) != 0:
            tracks_info = get_tracks_by_id(access_token, songs_ids_add)

            for track_info, song_addedby in zip(tracks_info, songds_ids_added_by):
                song_name = track_info['track_name']
                song_artists = track_info['artists']
                song_tuple = (song_name, song_artists)
                song_quick_info = {
                    "added_by": song_added_by,
                    "duration": track_info['duration'],
                    "link": track_info['link'],
                    "plays": 0,
                    "added_time_stamp": 'N/A',
                    "removed_time_stamp": 'N/A',
                    "song_id": track_info['track_id'],
                    "current_playlist": playlist_ids['judgement']
                }
                all_songs[song_tuple] = song_quick_info

                queue_to_be_written = [song_name, song_artists, approved_users[song_addedby]['name'], track_info['link']]
                queue_paste.append(queue_to_be_written)

                all_songs_to_be_written = [song_name, song_artists, song_added_by, song_quick_info['duration'],
                                           song_quick_info['link'], 0, 'N/A', 'N/A',
                                           song_quick_info['song_id'], playlist_ids['judgement']]
                all_songs_paste.append(all_songs_to_be_written)

        if len(queue_paste) != 0:
            queue_sheet.append_rows(queue_paste)
        if len(all_songs_paste) != 0:
            all_songs_detailed_sheet.append_rows(all_songs_paste)
        if len(songs_ids_add) != 0:
            add_songs_to_playlist(access_token, playlist_ids['judgement'], songs_ids_add, songs_ids_add_info)
        remove_songs_from_playlist(access_token, playlist_ids['recommended'], song_ids_removal, songs_ids_removal_info)



def move_queue_to_lifetime(song_name, song_artists, queue_sheet, lifetime_sheet, approved_users, all_songs, all_artists, access_token):
    tz = pytz.timezone('US/Pacific')
    queued_songs = queue_sheet.get_all_records(numericise_ignore=['all'])
    index = 2
    for song in queued_songs:
        if song_name == song['Title'] and song_artists == song['Artist(s)']:
            break
        index += 1
    song_tuple = (song_name, song_artists)
    song_id = all_songs[song_tuple]['song_id']
    all_songs[song_tuple]['current_playlist'] = playlist_ids['lifetime']
    queue_sheet.delete_row(index)
    remove_song_from_playlist(access_token, playlist_ids['judgement'], song_id)

    added_by_str = str(all_songs[song_tuple]['added_by'])
    to_be_written = [song_name, song_artists, all_songs[song_tuple]['plays'],
                     approved_users[added_by_str]['name'], all_songs[song_tuple]['link']]
    lifetime_sheet.append_row(to_be_written)
    add_song_to_playlist(access_token, playlist_ids['lifetime'], song_id)

    now = datetime.now(tz)
    all_songs[song_tuple]['added_time_stamp'] = now.strftime("%m/%d/%Y %H:%M:%S")
    approved_users[added_by_str]['yes_songs'] += 1


def move_queue_to_skipped(song_name, song_artists, queue_sheet, skipped_sheet, approved_users, all_songs, skipped_songs, all_artists, access_token):
    tz = pytz.timezone('US/Pacific')
    queued_songs = queue_sheet.get_all_records(numericise_ignore=['all'])
    index = 2
    for song in queued_songs:
        if song_name == song['Title'] and song_artists == song['Artist(s)']:
            break
        index += 1
    song_tuple = (song_name, song_artists)
    song_id = all_songs[song_tuple]['song_id']
    all_songs[song_tuple]['current_playlist'] = playlist_ids['removed']

    queue_sheet.delete_row(index)
    remove_song_from_playlist(access_token, playlist_ids['judgement'], song_id)

    added_by_str = str(all_songs[song_tuple]['added_by'])
    to_be_written = [song_name, song_artists, all_songs[song_tuple]['plays'],
                     approved_users[added_by_str]['name'], all_songs[song_tuple]['link']]

    skipped_sheet.append_row(to_be_written)
    add_song_to_playlist(access_token, playlist_ids['removed'], song_id)

    now = datetime.now(tz)
    all_songs[song_tuple]['removed_time_stamp'] = now.strftime("%m/%d/%Y %H:%M:%S")
    skipped_songs.add(song_tuple)
    approved_users[added_by_str]['no_songs'] += 1


def move_lifetime_to_skipped(song_name, song_artists, lifetime_sheet, skipped_sheet, approved_users, all_songs, skipped_songs, all_artists, access_token):
    tz = pytz.timezone('US/Pacific')
    lifetime_songs = lifetime_sheet.get_all_records(numericise_ignore=['all'])
    index = 2
    for song in lifetime_songs:
        if song_name == song['Title'] and song_artists == song['Artist(s)']:
            break
        index += 1

    song_tuple = (song_name, song_artists)
    song_id = all_songs[song_tuple]['song_id']
    all_songs[song_tuple]['current_playlist'] = playlist_ids['removed']

    lifetime_sheet.delete_row(index)
    remove_song_from_playlist(access_token, playlist_ids['lifetime'], song_id)

    to_be_written = [song_name, song_artists, all_songs[song_tuple]['plays'],
                     all_songs[song_tuple]['added_by'], all_songs[song_tuple]['link']]
    skipped_sheet.append_row(to_be_written)
    add_song_to_playlist(access_token, playlist_ids['removed'], song_id)

    now = datetime.now(tz)
    all_songs[song_tuple]['removed_time_stamp'] = now.strftime("%m/%d/%Y %H:%M:%S")
    skipped_songs.add(song_tuple)
    added_by_str = str(all_songs[song_tuple]['added_by'])
    approved_users[added_by_str]['yes_songs'] -= 1
    approved_users[added_by_str]['no_songs'] += 1


def update_lifetime(lifetime_sheet, all_songs, song_name, song_artists, approved_users):
    index = 2
    data = lifetime_sheet.get_all_records(numericise_ignore=['all'])
    for row in data:
        if row['Title'] == song_name and row['Artist(s)'] == song_artists:
            break
        index += 1
    if index > len(data) + 1:
        "you fucked up a-a-ron"
        return

    song_tuple = (song_name, song_artists)
    lifetime_sheet.delete_row(index)
    added_by_str = str(all_songs[song_tuple]['added_by'])
    to_be_written = [song_name, song_artists, all_songs[song_tuple]['plays'],
                     approved_users[added_by_str]['name'], all_songs[song_tuple]['link']]
    lifetime_sheet.insert_row(to_be_written, index)


def update_all_songs(all_songs_detailed_sheet, all_songs, song_name, song_artists):
    index = 2
    data = all_songs_detailed_sheet.get_all_records(numericise_ignore=['all'])
    for row in data:
        if row['Title'] == song_name and row['Artist(s)'] == song_artists:
            break
        index += 1
    if index > len(data) + 1:
        "you fucked up a-a-ron"
        return
    all_songs_detailed_sheet.delete_row(index)
    song_tuple = (song_name, song_artists)
    to_be_written = [song_name, song_artists, all_songs[song_tuple]['added_by'], all_songs[song_tuple]['duration'],
                     all_songs[song_tuple]['link'], all_songs[song_tuple]['plays'],
                     all_songs[song_tuple]['added_time_stamp'], all_songs[song_tuple]['removed_time_stamp'],
                     all_songs[song_tuple]['song_id'], all_songs[song_tuple]['current_playlist']]
    all_songs_detailed_sheet.insert_row(to_be_written, index)


def update_removed_songs(skipped_detailed_sheet, song_name, song_artist):
    to_be_written = [song_name, song_artist]
    skipped_detailed_sheet.append_row(to_be_written)


def update_only_private_user_rankings(people_rankings_detailed_sheet, uid, this_user):
    index = this_user['index']
    people_rankings_detailed_sheet.delete_row(index)
    to_be_written = [uid, this_user['name'], this_user['yes_songs'],
                     this_user['no_songs'], this_user['plays'], this_user['denied']]
    people_rankings_detailed_sheet.insert_row(to_be_written, index)

def update_user_rankings(people_rankings_sheet, people_rankings_detailed_sheet, uid, this_user):
    approved_people = people_rankings_detailed_sheet.get_all_records(numericise_ignore=['all'])
    index = 2
    for user in approved_people:
        if str(user['uid']) == uid:
            break
        index += 1
    if index > len(approved_people) + 1:
        "you fucked up a-a-ron"
        return
    people_rankings_detailed_sheet.delete_row(index)
    to_be_written = [uid, this_user['name'], this_user['yes_songs'],
                     this_user['no_songs'], this_user['plays'], this_user['denied']]
    people_rankings_detailed_sheet.insert_row(to_be_written, index)

    contributers = people_rankings_sheet.get_all_records(numericise_ignore=['all'])
    index = 2
    found = False
    for person in contributers:
        if person['Name'] == this_user['name']:
            found = True
            break
        index += 1

    approved_songs = int(this_user['yes_songs'])
    removed_songs = int(this_user['no_songs'])
    approval_rate = float(approved_songs) / float(approved_songs + removed_songs)
    to_be_written = [this_user['name'], this_user['plays'],
                     approved_songs, removed_songs, "{:.4f}".format(approval_rate)]
    if found:
        people_rankings_sheet.delete_row(index)
        people_rankings_sheet.insert_row(to_be_written, index)
    else:
        index = 2
        while index <= len(contributers) + 1 and this_user['name'] > contributers[index-2]['Name']:
            index += 1
        people_rankings_sheet.insert_row(to_be_written, index)


def update_artists(artists_sheet, song_id, all_artists, access_token):
    track_info = get_track_by_id(access_token, song_id)
    artists = track_info['artists_unformatted']
    for artist in artists:
        data = artists_sheet.get_all_records(numericise_ignore=['all'])
        index = 2
        found = False
        for a in data:
            if a['Artist'] == str(artist):
                found = True
                break
            index += 1

        approved_songs = int(all_artists[artist]['yes_songs'])
        removed_songs = int(all_artists[artist]['no_songs'])
        approval_rate = float(approved_songs) / float(approved_songs + removed_songs)
        to_be_written = [artist, all_artists[artist]['plays'],
                         approved_songs, removed_songs, "{:.4f}".format(approval_rate), all_artists[artist]['link']]
        if found:
            artists_sheet.delete_row(index)
            artists_sheet.insert_row(to_be_written, index)
        else:
            index = 2
            while index <= len(data) + 1 and str(artist).lower() > (data[index-2]['Artist']).lower():
                index += 1
            artists_sheet.insert_row(to_be_written, index)
