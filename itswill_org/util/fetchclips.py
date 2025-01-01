import os
import django
from django.core.exceptions import ValidationError
import sys
import json
import luscioustwitch
import datetime
from django.conf import settings
from dateutil import tz
import time

sys.path.append(".")
  
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from itswill_org.models import *

twitch_api = luscioustwitch.TwitchAPI({ "CLIENT_ID" : settings.TWITCH_API_CLIENT_ID, "CLIENT_SECRET": settings.TWITCH_API_CLIENT_SECRET })

start_datetime = datetime.datetime(2023, 1, 1, 0, 0, 1)
end_datetime = datetime.datetime(2024, 6, 1, 0, 0, 1)

broadcaster_id = twitch_api.get_user_id("itswill")

num_clips = 0
clip_ids = []
continue_fetching = True

clip_params = {
  "first": 50,
  "broadcaster_id": broadcaster_id,
  "started_at": start_datetime.astimezone(tz.UTC).strftime(luscioustwitch.TWITCH_API_TIME_FORMAT),
  "ended_at": end_datetime.astimezone(tz.UTC).strftime(luscioustwitch.TWITCH_API_TIME_FORMAT)
}

while continue_fetching:
  clips, cursor = twitch_api.get_clips(params=clip_params)

  if cursor != "":
    clip_params["after"] = cursor
  else:
    continue_fetching = False
    
  most_recent_clip_view_count = 0

  for clip in clips:
    if clip['id'] in clip_ids:
      print(f"Got clip {clip['id']} twice while fetching")
      continue
    
    clip_id = clip["id"]
    creator_id = int(clip["creator_id"])
      
    try:
      creator = TwitchUser.objects.get(user_id = creator_id)
    except TwitchUser.DoesNotExist:
      try:
        userdata = twitch_api.get_user_info(id = creator_id)
      
        creator = TwitchUser(
          user_id = creator_id,
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
        creator = TwitchUser(
          user_id = creator_id,
          login = clip["creator_name"],
          display_name = clip["creator_name"]
        )
      
      creator.save()
      
    try:
      clip_inst = Clip(
        clip_id = clip_id,
        creator = creator,
        url = clip["url"],
        embed_url = clip["embed_url"],
        broadcaster_id = int(clip["broadcaster_id"]),
        broadcaster_name = clip["broadcaster_name"],
        video_id = clip["video_id"],
        game_id = clip["game_id"],
        language = clip["language"],
        title = clip["title"],
        view_count = int(clip["view_count"]),
        created_at = datetime.datetime.strptime(clip["created_at"], luscioustwitch.TWITCH_API_TIME_FORMAT).replace(tzinfo = datetime.timezone.utc),
        thumbnail_url = clip["thumbnail_url"],
        duration = float(clip["duration"]),
        vod_offset = -1 if (clip["vod_offset"] == "null" or clip["vod_offset"] is None) else int(clip["vod_offset"])
      )
      
      clip_inst.save()
    except ValidationError as e:
      print(e)
      
    num_clips += 1
    clip_ids.append(clip['id'])

    most_recent_clip_view_count = int(clip["view_count"])
    if most_recent_clip_view_count < 1:
      continue_fetching = False
      break
    
  print(f"Most recent clip view count: {most_recent_clip_view_count}")