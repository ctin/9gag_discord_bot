# Work with Python 3.6
import discord
import pickle

from nineapi.nineapi.client import Client
import html
import collections
import asyncio
import threading
import os

lock = threading.Lock()
client = discord.Client()
gagClient = Client()
lastIds = collections.deque(maxlen=10000)
channels = set()

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return
    global channels
    global lock

    if message.content.startswith('9gag'):
        try:
            chan = message.channel
            lock.acquire()

            if message.content.startswith('9gag start'):
                print("starting")
                if chan in channels:
                    client.send_message(chan, content="error: this channel already subscribed")
                else:
                    channels.add(chan)
                    client.send_message(chan, content="ok, starting now...")
            elif message.content.startswith('9gag stop'):
                print("stopping")
                if chan in channels:
                    channels.remove(chan)
                    client.send_message(chan, content="ok, stopped now")
                else:
                    client.send_message(chan, content="error: this channel is not subscribed")
            
            with open('./chans', 'wb') as fp:
                pickle.dump(channels, fp)
            lock.release()
        except Exception as e:
            print("got e: {}".format(e))
            exit(1)

async def status_task():
    while True:
        await asyncio.sleep(1)

        global channels
        global lock
        lock.acquire()
        hasChannels = len(channels)
        lock.release()
        if hasChannels:
            try:
                posts = gagClient.get_posts()
                for post in reversed(posts):
                    global lastIds
                    ID = post.id
                    if ID in lastIds:
                        continue
                    else:
                        lastIds.append(ID)
                    with open('./ids', 'wb') as fp:
                        pickle.dump(lastIds, fp)

                    url = post.get_media_url()
                    title = html.unescape(post.title)
                    msg = '...\n...\n...\n```{}```\n{}'.format(title, post.get_media_url())
                    lock.acquire()
                    for channel in channels:
                        await client.send_message(channel, content=msg)
                    lock.release()
            except Exception as e:
                print("got e: {}".format(e))
                exit(1)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    try:
        try:
            with open('./ids', 'rb') as fp:
                global lastIds
                lastIds = pickle.load(fp)
        except Exception as e:
            print('failed to load ids')
        try:
            with open('./chans', 'rb') as fp:
                global channels
                channels = pickle.load(fp)
        except Exception as e:
            print('failed to load chans')
        
        login = os.environ["LOGIN"]
        password = os.environ["PASSWORD"]
        print("will login using login {} and password {}".format(login, password))
        gagClient.log_in(login, password)
        client.loop.create_task(status_task())
        print('9gag: logged in')
    except nineapi.client.APIException as e:
        print('Failed to log in')

print("starting...")
with open('./key.txt', 'r') as key:
    keyStr = key.read().rstrip()
    client.run(keyStr)
