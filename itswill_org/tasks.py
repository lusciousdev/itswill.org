from django.conf import settings
from celery import Celery, shared_task
from celery.schedules import crontab
import luscioustwitch
from django.core.exceptions import ValidationError
from django.db.models import F

import datetime
import pytz
import calendar
import re
import requests
from random import randint
import time

from .util.timeutil import *
from .models import *

def get_word_count(text : str, word : str) -> int:
  word_regex = re.compile(fr"(?<![^\s_-]){word}(?![^\s_-])", re.IGNORECASE)
  return len(word_regex.findall(text))

def get_mult_word_count(text : str, words : list) -> int:
  return get_word_count(text, "|".join(words))

def get_random_message(user):
  if user != None:
    user_message_set = ChatMessage.objects.filter(commenter = user).all()
  else:
    user_message_set = ChatMessage.objects.all()
    
  user_message_count = user_message_set.count()
  random_message = user_message_set[randint(0, user_message_count - 1)]
  
  response_str = random_message.localtz_str()
  
  if len(response_str) >= 380:
    response_str = response_str[:375] + "..."
    
  return response_str

@shared_task
def post_random_message(user_id, response_url):
  if user_id != -1:
    try:
      user = TwitchUser.objects.get(user_id = user_id)
    except TwitchUser.DoesNotExist:
      requests.post(response_url, data = { "message": "Could not find user." })
      return
  else:
    user = None
  
  rndmsg = get_random_message(user)
  
  requests.post(response_url, data = { "message": rndmsg })

@shared_task
def get_recent_clips(max_days = 31):
  twitch_api = luscioustwitch.TwitchAPI({ "CLIENT_ID" : settings.TWITCH_API_CLIENT_ID, "CLIENT_SECRET": settings.TWITCH_API_CLIENT_SECRET })
  
  if max_days > 0:
    start_date = datetime.datetime.combine(datetime.datetime.now().date(), datetime.time(0, 0, 0, 1)) - datetime.timedelta(days = max_days)
  else:
    start_date = datetime.datetime(1971, 1, 1, 0, 0, 0, 1, tzinfo = datetime.timezone.utc)
    
  end_date = datetime.datetime.now()
  
  clip_params = {
    "first": 50,
    "broadcaster_id": settings.USER_ID,
    "started_at": start_date.astimezone(pytz.utc).strftime(luscioustwitch.TWITCH_API_TIME_FORMAT),
    "ended_at": end_date.astimezone(pytz.utc).strftime(luscioustwitch.TWITCH_API_TIME_FORMAT)
  }

  continue_fetching = True
  while continue_fetching:
    clips, cursor = twitch_api.get_clips(params=clip_params)

    if cursor != "":
      clip_params["after"] = cursor
    else:
      continue_fetching = False
      
    most_recent_clip_view_count = 0

    for clip in clips:
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
        
      clip_inst, _ = Clip.objects.update_or_create(
        clip_id = clip_id,
        defaults = {
          "creator": creator,
          "url": clip["url"],
          "embed_url": clip["embed_url"],
          "broadcaster_id": int(clip["broadcaster_id"]),
          "broadcaster_name": clip["broadcaster_name"],
          "video_id": clip["video_id"],
          "game_id": clip["game_id"],
          "language": clip["language"],
          "title": clip["title"],
          "view_count": int(clip["view_count"]),
          "created_at": datetime.datetime.strptime(clip["created_at"], luscioustwitch.TWITCH_API_TIME_FORMAT).replace(tzinfo = datetime.timezone.utc),
          "thumbnail_url": clip["thumbnail_url"],
          "duration": float(clip["duration"]),
          "vod_offset": -1 if (clip["vod_offset"] == "null" or clip["vod_offset"] is None) else int(clip["vod_offset"])
        }
      )

      most_recent_clip_view_count = int(clip["view_count"])
      if most_recent_clip_view_count < 1:
        continue_fetching = False
        break
      
    print(f"Most recent clip view count: {most_recent_clip_view_count}")
  

@shared_task
def get_recent_chat_messages(max_days = -1, skip_known_vods = True):
  twitch_api = luscioustwitch.TwitchAPI({ "CLIENT_ID" : settings.TWITCH_API_CLIENT_ID, "CLIENT_SECRET": settings.TWITCH_API_CLIENT_SECRET })
  gql_api    = luscioustwitch.TwitchGQL_API()
  
  video_params = {
    "user_id": settings.USER_ID,
    "period": "all",
    "sort": "time",
    "type": "archive"
  }
  
  if max_days > 0:
    start_date = datetime.datetime.combine(datetime.datetime.now(TIMEZONE).date(), datetime.time(0, 0, 0, 1), TIMEZONE) - datetime.timedelta(days = max_days)
  
  videos = twitch_api.get_all_videos(video_params)
  
  for video in videos:
    vod_date = pytz.utc.localize(datetime.datetime.strptime(video['published_at'], luscioustwitch.TWITCH_API_TIME_FORMAT), is_dst = None)
    
    if max_days > 0 and vod_date < start_date:
      continue
    
    videofound = False
    try:
      videoinstance = Video.objects.get(vod_id = video['id'])
      videofound = True
    except Video.DoesNotExist:
      None
      
    if skip_known_vods and videofound:
      print(f"Skipping {video['id']} as it's in our database already.")
      continue

    print(f'{video["id"]} - {utc_to_local(vod_date, TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")}')
    
    vid_chat = gql_api.get_chat_messages(video['id'])
    
    for chatmsg in vid_chat:
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
        commenter = TwitchUser.objects.get(user_id = commenterid)
        
        commenter.login = chatmsg['commenter']['login']
        commenter.display_name = chatmsg['commenter']['displayName']
      except TwitchUser.DoesNotExist:
        try:
          userdata = twitch_api.get_user_info(id = commenterid)
        
          commenter, _ = TwitchUser.objects.update_or_create(
            user_id = commenterid,
            defaults = {
              "login": userdata['login'],
              "display_name": userdata['display_name'],
              "user_type": userdata['type'],
              "broadcaster_type": userdata['broadcaster_type'],
              "description": userdata['description'],
              "profile_image_url": userdata['profile_image_url'],
              "offline_image_url": userdata['offline_image_url'],
              "created_at": datetime.datetime.strptime(userdata['created_at'], luscioustwitch.TWITCH_API_TIME_FORMAT).replace(tzinfo = datetime.timezone.utc),
            },
          )
        except:
          commenter, _ = TwitchUser.objects.update_or_create(
            user_id = commenterid,
            defaults = {
              "login": chatmsg["commenter"]["login"],
              "display_name": chatmsg["commenter"]["displayName"],
              "created_at": datetime.datetime(1971, 1, 1, 0, 0, 1).replace(tzinfo = datetime.timezone.utc),
            },
          )
        
      commenter.save()
      
      chatmsgtime = None
      try:
        chatmsgtime = datetime.datetime.strptime(chatmsg["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo = datetime.timezone.utc)
      except ValueError:
        chatmsgtime = datetime.datetime.strptime(chatmsg["createdAt"], luscioustwitch.TWITCH_API_TIME_FORMAT).replace(tzinfo = datetime.timezone.utc)
      
      chatmsgmodel, new_msg = ChatMessage.objects.update_or_create(
        message_id = chatmsg["id"],
        defaults = {
          "commenter": commenter,
          "content_offset": chatmsg["contentOffsetSeconds"],
          "created_at": chatmsgtime,
          "message": msgtext,
        },
      )
      
      chatmsgmodel.save()
        
    if not videofound:
      videoinstance = Video(
        vod_id = video['id'],
        stream_id = video["stream_id"],
        user_id = video["user_id"],
        user_login = video["user_login"],
        user_name = video["user_name"],
        title = video["title"],
        description = video["description"],
        created_at = datetime.datetime.strptime(video["created_at"], luscioustwitch.TWITCH_API_TIME_FORMAT).replace(tzinfo = datetime.timezone.utc),
        published_at = datetime.datetime.strptime(video["published_at"], luscioustwitch.TWITCH_API_TIME_FORMAT).replace(tzinfo = datetime.timezone.utc),
        url = video["url"],
        thumbnail_url = video["thumbnail_url"],
        viewable = video["viewable"],
        view_count = video["view_count"],
        language = video["language"],
        vod_type = video["type"],
        duration = video["duration"],
      )
      videoinstance.save()

@shared_task
def get_all_first_messages():
  localtz = pytz.timezone("America/Los_Angeles")
  
  for overallrecap in OverallRecapData.objects.all():
    if overallrecap.month == 0:
      start_date = datetime.datetime(overallrecap.year, 1, 1, 0, 0, 0, 1, localtz)
      end_date   = datetime.datetime(overallrecap.year, 12, 31, 23, 59, 59, 999, localtz)
    else:
      monthrange = calendar.monthrange(overallrecap.year, overallrecap.month)
      start_date = datetime.datetime(overallrecap.year, overallrecap.month, 1, 0, 0, 0, 1, localtz)
      end_date   = datetime.datetime(overallrecap.year, overallrecap.month, monthrange[1], 23, 59, 59, 999, localtz)
      
    firstmsg = ChatMessage.objects.filter(created_at__range = (start_date, end_date)).order_by("created_at").first()
    overallrecap.first_message = "" if firstmsg is None else firstmsg.message
    overallrecap.save()
    
  for userrecap in UserRecapData.objects.all():
    if userrecap.overall_recap.month == 0:
      start_date = datetime.datetime(userrecap.overall_recap.year, 1, 1, 0, 0, 0, 1, localtz)
      end_date   = datetime.datetime(userrecap.overall_recap.year, 12, 31, 23, 59, 59, 999, localtz)
    else:
      monthrange = calendar.monthrange(userrecap.overall_recap.year, userrecap.overall_recap.month)
      start_date = datetime.datetime(userrecap.overall_recap.year, userrecap.overall_recap.month, 1, 0, 0, 0, 1, localtz)
      end_date   = datetime.datetime(userrecap.overall_recap.year, userrecap.overall_recap.month, monthrange[1], 23, 59, 59, 999, localtz)
      
    firstmsg = ChatMessage.objects.filter(created_at__range = (start_date, end_date), commenter = userrecap.twitch_user).order_by("created_at").first()
    userrecap.first_message = "" if firstmsg is None else firstmsg.message
    userrecap.save()

@shared_task
def set_yearly_stat_user_count(year):
  try:
    yearrecap = OverallRecapData.objects.get(year = year, month = 0)
  except OverallRecapData.DoesNotExist:
    yearrecap = OverallRecapData(year = year, month = 0)
    yearrecap.save()
      
  yearrecap.count_chatters = yearrecap.userrecapdata_set.all().count()
  yearrecap.save()
  
@shared_task
def calculate_alltime_stats():
  alltimerecap, _ = OverallRecapData.objects.get_or_create(year = 0, month = 0)
  alltimerecap.zero()
  
  firstmsg = ChatMessage.objects.order_by("created_at").first()
  
  alltimerecap.first_message = "" if firstmsg is None else firstmsg.message
  
  yearrecaps = OverallRecapData.objects.filter(year__gte = 1, month = 0).prefetch_related("userrecapdata_set").all()
  
  userrecap : UserRecapData = alltimerecap.userrecapdata_set.first()
  if userrecap:
    for field in userrecap._meta.get_fields():
      if ((field.get_internal_type() == "IntegerField" or field.get_internal_type() == "BigIntegerField") and field.name not in ["year", "month"]):
        alltimerecap.userrecapdata_set.update(**{field.name: 0})
  
  recap : OverallRecapData
  for recap in yearrecaps:
    alltimerecap.add(recap, exclude = ["year", "month", "count_chatters"])
    
    userrecap : UserRecapData
    for userrecap in recap.userrecapdata_set.all():
      useryear, _ = UserRecapData.objects.get_or_create(overall_recap = alltimerecap, twitch_user = userrecap.twitch_user)
      useryear.add(userrecap)
  
  alltimerecap.count_chatters = alltimerecap.userrecapdata_set.all().count()
  alltimerecap.save()
  

@shared_task
def calculate_yearly_stats(year = None):
  if year is None:
    year = datetime.datetime.now(TIMEZONE).year
  
  yearrecap, _ = OverallRecapData.objects.get_or_create(year = year, month = 0)
  yearrecap.zero()
  
  firstmsg = ""
  if year == 0:
    firstmsg = ChatMessage.objects.order_by("created_at").first()
  else:
    localtz = pytz.timezone("America/Los_Angeles")
    start_date = datetime.datetime(year, 1, 1, 0, 0, 0, 1, localtz)
    end_date   = datetime.datetime(year, 12, 31, 23, 59, 59, 999, localtz)
    
    firstmsg = ChatMessage.objects.filter(created_at__range = (start_date, end_date)).order_by("created_at").first()
    
  yearrecap.first_message = "" if firstmsg is None else firstmsg.message

  if (year == 0):
    monthrecaps = OverallRecapData.objects.filter(year__gte = 1, month__gte = 1).prefetch_related("userrecapdata_set").all()
  else:
    monthrecaps = OverallRecapData.objects.filter(year = year, month__gte = 1).prefetch_related("userrecapdata_set").all()
  
  userrecap : UserRecapData = yearrecap.userrecapdata_set.first()
  if userrecap:
    for field in userrecap._meta.get_fields():
      if ((field.get_internal_type() == "IntegerField" or field.get_internal_type() == "BigIntegerField") and field.name not in ["year", "month"]):
        yearrecap.userrecapdata_set.update(**{field.name: 0})
  
  recap : OverallRecapData
  for recap in monthrecaps:
    yearrecap.add(recap, exclude = ["year", "month", "count_chatters"])
    
    userrecap : UserRecapData
    for userrecap in recap.userrecapdata_set.all():
      useryear, _ = UserRecapData.objects.get_or_create(overall_recap = yearrecap, twitch_user = userrecap.twitch_user)
      useryear.add(userrecap)
  
  yearrecap.count_chatters = yearrecap.userrecapdata_set.all().count()
  yearrecap.save()
        

@shared_task
def calculate_monthly_stats(year = None, month = None):
  if year is None:
    year = datetime.datetime.now(TIMEZONE).year
  if month is None:
    month = datetime.datetime.now(TIMEZONE).month
  
  localtz = pytz.timezone("America/Los_Angeles")
  monthrange = calendar.monthrange(year, month)
  
  monthrecap, _ = OverallRecapData.objects.get_or_create(year = year, month = month)  
  monthrecap.zero()
  
  start_date = datetime.datetime(year, month, 1, 0, 0, 0, 1, localtz)
  end_date = datetime.datetime(year, month, monthrange[1], 23, 59, 59, 999, localtz)
    
  firstmsg = ChatMessage.objects.filter(created_at__range = (start_date, end_date)).order_by("created_at").first()
  videos = Video.objects.filter(created_at__range = (start_date, end_date))
  
  monthrecap.count_videos = videos.count()
  
  monthrecap.first_message = "" if firstmsg is None else firstmsg.message
  
  userrecap : UserRecapData = monthrecap.userrecapdata_set.first()
  if userrecap:
    for field in userrecap._meta.get_fields():
      if ((field.get_internal_type() == "IntegerField" or field.get_internal_type() == "BigIntegerField") and field.name not in ["year", "month"]):
        monthrecap.userrecapdata_set.update(**{field.name: 0})
  
  for chatter in TwitchUser.objects.prefetch_related("chatmessage_set", "clip_set").all():
    chatter_messages = chatter.chatmessage_set.filter(created_at__range = (start_date, end_date)).order_by("created_at")
    chatter_clips    = chatter.clip_set.filter(created_at__range = (start_date, end_date))
    
    chatter_msg_count  = chatter_messages.count()
    chatter_clip_count = chatter_clips.count()
    
    chatter_clip_views = 0
    for clip in chatter_clips:
      chatter_clip_views += clip.view_count
    
    if chatter_msg_count > 0 or chatter_clip_count > 0:
      monthrecap.count_messages   += chatter_msg_count
      monthrecap.count_clips      += chatter_clip_count
      monthrecap.count_clip_views += chatter_clip_views
      monthrecap.count_chatters   += 1
      
      chatter_recap, _ = UserRecapData.objects.get_or_create(overall_recap = monthrecap, twitch_user = chatter)
        
      chatter_recap.count_clips      = chatter_clip_count
      chatter_recap.count_clip_views = chatter_clip_views
      
      firstmsg : ChatMessage = chatter_messages.first()
      chatter_recap.first_message = "" if firstmsg is None else firstmsg.message
      
      msg : ChatMessage
      for msg in chatter_messages:
        chatter_recap.process_message(msg.message, save = False)
      
      chatter_recap.save()
      
      monthrecap.add(chatter_recap, ["year", "month", "count_messages", "count_clips", "count_clip_views", "count_chatters"])
      
      monthrecap.save()
      
@shared_task
def calculate_all_leaderboards():
  for overallrecap in OverallRecapData.objects.all():
    leaderboards_dict = {}
    for field in overallrecap._meta.get_fields():
      if ((field.get_internal_type() == "IntegerField" or field.get_internal_type() == "BigIntegerField") and field.name not in ["year", "month", "count_chatters", "count_videos"]):
        print(type(field))
        if type(field) in [StatField, BigStatField, StringCountField]:
          if not field.show_leaderboard:
            continue
          leaderboards_dict[field.short_name] = [(userrecap.twitch_user.display_name, getattr(userrecap, field.name), userrecap.twitch_user.is_bot) for userrecap in overallrecap.userrecapdata_set.all().order_by("-" + field.name)[:250]]
        else:
          leaderboards_dict[field.name] = [(userrecap.twitch_user.display_name, getattr(userrecap, field.name), userrecap.twitch_user.is_bot) for userrecap in overallrecap.userrecapdata_set.all().order_by("-" + field.name)[:250]]
          
        
    overallrecap.leaderboards = leaderboards_dict
    overallrecap.save()