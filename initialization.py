from __future__ import print_function
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tokens import *
from information import *
from modify_playlist import *
import pytz
from datetime import datetime


def initialize(all_songs, skipped_songs, approved_users, all_artists, all_songs_detailed_sheet, skipped_detailed_sheet, people_rankings_detailed_sheet, artists_sheet):
    data = all_songs_detailed_sheet.get_all_records(numericise_ignore=['all'])
    for row in data:
        song_tuple = (row['Title'], str(row['Artist(s)']))
        song_data = {
            "added_by": row["Added By"],
            "duration": int(row['Duration']),
            "link": row['Link'],
            "plays": int(row['Plays']),
            "added_time_stamp": row['Added Timestamp'],
            "removed_time_stamp": row['Removed Timestamp'],
            "song_id": row['Song ID'],
            "current_playlist": row['Current Playlist']
        }
        all_songs[song_tuple] = song_data

    data = skipped_detailed_sheet.get_all_records()
    for row in data:
        song_tuple = (str(row['Title']), str(row['Artist(s)']))
        skipped_songs.add(song_tuple)

    data = people_rankings_detailed_sheet.get_all_records(numericise_ignore=['all'])
    index = 2
    for row in data:
        uid = str(row['uid'])
        person_data = {
            'index': int(index),
            'name': row['name'],
            'yes_songs': int(row['# Songs in "Lifetime"']),
            'no_songs': int(row['# Songs Skipped']),
            'plays': int(row['Plays']),
            'denied': int(row['Denied'])
        }
        approved_users[uid] = person_data
        index += 1

    data = artists_sheet.get_all_records()
    for row in data:
        artist_name = str(row['Artist'])
        artist_data = {
            'plays': int(row['Plays']),
            'yes_songs': int(row['# Songs in "Lifetime"']),
            'no_songs': int(row['# Songs Skipped']),
            'link': row['Link']
        }
        all_artists[artist_name] = artist_data


