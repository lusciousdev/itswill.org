import os
import django
from django.core.exceptions import ValidationError
import sys
import json
import luscioustwitch
import datetime
from django.conf import settings

sys.path.append(".")
  
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from itswill_org.models import *

datapath = "./itswill_org/util"
chatlogfiles = [
  f"{datapath}/2023-01.json",
  f"{datapath}/2023-02.json",
  f"{datapath}/2023-03.json",
  f"{datapath}/2023-04.json",
  f"{datapath}/2023-05.json",
  f"{datapath}/2023-06.json",
  f"{datapath}/2023-07.json",
  f"{datapath}/2023-08.json",
  f"{datapath}/2023-09.json",
  f"{datapath}/2023-10.json",
  f"{datapath}/2023-11.json",
  f"{datapath}/2023-12.json",
  f"{datapath}/2024-01.json",
  f"{datapath}/2024-02.json",
]

def load_chatlog(filename):
  with open(filename, 'r') as f:
    data = json.load(f)
    msgcount = data['count']
    msgs = data['list']
    return msgcount, msgs

twitch_api = luscioustwitch.TwitchAPI({ "CLIENT_ID" : settings.TWITCH_API_CLIENT_ID, "CLIENT_SECRET": settings.TWITCH_API_CLIENT_SECRET })

for chatfile in chatlogfiles:
  print(f"Loading {chatfile}")
  chatcount, chatlogs = load_chatlog(chatfile)
  
  i = 0
  for chatmsg in chatlogs:
    i += 1
    if (i % 500 == 0):
      print(f"{i}/{chatcount}")
    try:
      commenterid = int(chatmsg["commenter"]["id"])
    except:
      continue
    
    try:
      frags = chatmsg["message"]["fragments"]
      if len(frags) == 0:
        continue
    except:
      continue
    
    msgtext = ""
    for frag in frags:
      msgtext += frag["text"]
      
    try:
      commentor = TwitchUser.objects.get(user_id = commenterid)
      
    except TwitchUser.DoesNotExist:
      try:
        userdata = twitch_api.get_user_info(id = commenterid)
      
        commentor = TwitchUser(
          user_id = commenterid,
          login = userdata['login'],
          display_name = userdata['display_name'],
          user_type = userdata['type'],
          broadcaster_type = userdata['broadcaster_type'],
          description = userdata['description'],
          profile_image_url = userdata['profile_image_url'],
          offline_image_url = userdata['offline_image_url'],
          created_at = datetime.datetime.strptime(userdata['created_at'], luscioustwitch.TWITCH_API_TIME_FORMAT).replace(tzinfo = datetime.timezone.utc),
        )
      except:
        commentor = TwitchUser(
          user_id = commenterid,
          login = chatmsg["commenter"]["login"],
          display_name = chatmsg["commenter"]["displayName"],
          created_at = datetime.datetime(1971, 1, 1, 0, 0, 1).replace(tzinfo = datetime.timezone.utc)
        )
      
      commentor.save()
      
    chatmsgid = chatmsg['id']
    
    chatmsgtime = None
    try:
      chatmsgtime = datetime.datetime.strptime(chatmsg["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo = datetime.timezone.utc)
    except ValueError:
      chatmsgtime = datetime.datetime.strptime(chatmsg["createdAt"], luscioustwitch.TWITCH_API_TIME_FORMAT).replace(tzinfo = datetime.timezone.utc)
    
    try:
      chatmsgmodel = ChatMessage(
        commentor = commentor,
        message_id = chatmsg["id"],
        content_offset = chatmsg["contentOffsetSeconds"],
        created_at = chatmsgtime,
        message = msgtext,
      )
      
      chatmsgmodel.save()
    except ValidationError as e:
      print(e)