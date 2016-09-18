#!/usr/bin/env python

import json
import pprint
from gmusicapi import Mobileclient
import pychromecast
from time import sleep
import boto3

pp = pprint.PrettyPrinter(indent=4)
config_file = open('config.json', 'r')
config = json.loads(config_file.read())
config_file.close()

api = Mobileclient()
api.login(config['google_user'], config['google_password'], Mobileclient.FROM_MAC_ADDRESS)

sqs = boto3.resource('sqs',
        aws_access_key_id=config['aws_access_key_id'],
        aws_secret_access_key=config['aws_secret_access_key'],
        region_name='us-east-1'
        )
queue = sqs.get_queue_by_name(QueueName=config['sqs_name'])

def setup(chromecast_name):
    chromecastList = list(pychromecast.get_chromecasts_as_dict().keys())
    if chromecastList == []:
        print("We didn't find any Chromecasts...")
        setup(chromecast_name)
    else:
        print ("Found ChromeCast: " + str(chromecastList))

    cast = pychromecast.get_chromecast(friendly_name=chromecast_name)
    return cast

cast = setup(config['chromecast_name'])

# Runs Inital Setup for Default Chromecast

def play_song(song):
    cast.wait()
    mc = cast.media_controller
    url = api.get_stream_url(song['nid'])
    song_id = song['nid']
    title = song['title']
    artist = song['artist']
    album = song['album']
    print("song id is %s" % song)
    print("url is %s" % url)
    print("Now playing\n  Title: %s\n  Artist: %s\n  Album: %s\n Id: %s" % (title, artist, album, song_id))

    mc.play_media(url, 'audio/mp3')
    sleep(5)
    print(mc.status)

def media_control(desired_state):
    cast.wait()
    mc = cast.media_controller
    if mc.is_active:
        if desired_state == "pause" or desired_state == "play":
            if mc.is_paused:
                mc.play()
            if mc.is_playing:
                mc.pause()
        if desired_state == "stop":
            mc.stop()

def search(query=''):
    print("Searching for %s" % query)
    try:
        search = api.search(query, max_results=1)
        song = search['song_hits'][0]['track']
    except:
        print("Couldn't find the song")
        return None

    return song

def check_queue():
    messages = queue.receive_messages(
        WaitTimeSeconds=5,
        MessageAttributeNames=['All']
        )
    for message in messages:
        print("Message received: {0}".format(message.body))
        if message.message_attributes is not None:
            try:
                message_type = message.message_attributes.get('type')['StringValue']
                print("Message type: {0}".format(message_type))
            except:
                print("No Message type")
                break

        if message_type == "query":
            song = search(message.body)
            if (song != None):
                play_song(song)
        if message_type == "stop_request":
            media_control('stop')
        if message_type == "pause_request" or message_type == "resume_request":
            media_control('pause')

        message.delete()

while True:
    check_queue()
