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
import math
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

def get_last_message(user, range = None, return_json = False):
  if user != None:
    user_message_set = ChatMessage.objects.filter(commenter = user).order_by("created_at")
  else:
    user_message_set = ChatMessage.objects.order_by("created_at")
    
  if range:
    user_message_set = user_message_set.filter(created_at__range = range)
    
  last_message = user_message_set.last()
  
  if return_json:
    return {
      "message": last_message.message,
      "commenter": last_message.commenter.display_name,
      "timestamp": last_message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
      "prettytime": last_message.created_at.astimezone(TIMEZONE).strftime("%b %d, %Y"),
    }
  else:
    return last_message.localtz_str()

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
    firstmsg = None
    if overallrecap.year == 0:
      firstmsg = ChatMessage.objects.order_by("created_at").first()
    else:
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
    firstmsg = None
    if userrecap.overall_recap.year == 0:
      firstmsg = ChatMessage.objects.filter(commenter = userrecap.twitch_user).order_by("created_at").first()
    else:
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
    
    chatter_clip_watch_time = 0
    
    for clip in chatter_clips:
      chatter_clip_watch_time += round(clip.duration) * clip.view_count
    
    chatter_clip_views = 0
    for clip in chatter_clips:
      chatter_clip_views += clip.view_count
    
    if chatter_msg_count > 0 or chatter_clip_count > 0:
      monthrecap.count_messages      += chatter_msg_count
      monthrecap.count_clips         += chatter_clip_count
      monthrecap.count_clip_watch    += chatter_clip_watch_time
      monthrecap.count_clip_views    += chatter_clip_views
      monthrecap.count_chatters      += 1
      
      chatter_recap, _ = UserRecapData.objects.get_or_create(overall_recap = monthrecap, twitch_user = chatter)
        
      chatter_recap.count_clips         = chatter_clip_count
      chatter_recap.count_clip_watch    = chatter_clip_watch_time
      chatter_recap.count_clip_views    = chatter_clip_views
      
      firstmsg : ChatMessage = chatter_messages.first()
      chatter_recap.first_message = "" if firstmsg is None else firstmsg.message
      
      msg : ChatMessage
      for msg in chatter_messages:
        chatter_recap.process_message(msg.message, save = False)
      
      chatter_recap.save()
      
      monthrecap.add(chatter_recap, ["year", "month", "count_messages", "count_clips", "count_clip_views", "count_clip_watch", "count_chatters"])
      
      monthrecap.save()
      
@shared_task
def calculate_all_leaderboards():
  for overallrecap in OverallRecapData.objects.all():
    leaderboards_dict = {}
    for field in overallrecap._meta.get_fields():
      if ((field.get_internal_type() == "IntegerField" or field.get_internal_type() == "BigIntegerField") and field.name not in ["year", "month", "count_chatters", "count_videos"]):
        if type(field) in [StatField, BigStatField, StringCountField]:
          if not field.show_leaderboard:
            continue
          leaderboards_dict[field.short_name] = [(userrecap.twitch_user.display_name, getattr(userrecap, field.name), userrecap.twitch_user.is_bot) for userrecap in overallrecap.userrecapdata_set.all().order_by("-" + field.name)[:250]]
        else:
          leaderboards_dict[field.name] = [(userrecap.twitch_user.display_name, getattr(userrecap, field.name), userrecap.twitch_user.is_bot) for userrecap in overallrecap.userrecapdata_set.all().order_by("-" + field.name)[:250]]
        
    overallrecap.leaderboards = leaderboards_dict
    overallrecap.save()
    
@shared_task
def calculate_everything():
  start = time.perf_counter()
  
  year = datetime.datetime.now(TIMEZONE).year
  
  for y in range(2023, year+1):
    for m in range(1, 13):
      calculate_monthly_stats(y, m)
      print(f"{y}-{m}: calc took {time.perf_counter() - start} seconds")
      start = time.perf_counter()
    calculate_yearly_stats(y)
    print(f"{y}-{m}: calc took {time.perf_counter() - start} seconds")
    start = time.perf_counter()
    
  calculate_alltime_stats()
  print(f"alltime: calc took {time.perf_counter() - start} seconds")
  start = time.perf_counter()
  
  calculate_all_leaderboards()
  print(f"leaderboards: calc took {time.perf_counter() - start} seconds")
  start = time.perf_counter()
  
  create_wrapped_data()
  print(f"wrapped: calc took {time.perf_counter() - start} seconds")
  start = time.perf_counter()
    
def seconds_to_duration(input : int, abbr : bool = False):
  days, rem = divmod(input, (3600 * 24))
  hours, rem = divmod(rem, 3600)
  minutes, rem = divmod(rem, 60)
  seconds = rem
  
  output = ""
  
  msd_hit = False
  if days > 0:
    output += f"{days}d " if abbr else f"{days} days, "
    msd_hit = True
  if msd_hit or hours > 0:
    output += f"{hours}h " if abbr else f"{hours} hours, "
    msd_hit = True
  if msd_hit or minutes > 0:
    output += f"{minutes}m {seconds}s" if abbr else f"{minutes} minutes and {seconds} seconds"
  
  return output
    
@shared_task
def create_wrapped_data(year = None, skip_users = False):
  if year is None:
    year = datetime.datetime.now(TIMEZONE).year
  
  localtz = pytz.timezone("America/Los_Angeles")
  
  start_year = datetime.datetime(year, 1, 1, 0, 0, 0, 1, localtz)
  end_year = datetime.datetime(year, 12, 31, 23, 59, 59, 999, localtz)
  
  try:
    overallrecap = OverallRecapData.objects.get(year = year, month = 0)
  except OverallRecapData.DoesNotExist:
    print("No recap for that year.")
    return
  
  overall_wrapped, _ = OverallWrappedData.objects.get_or_create(year = year)
  
  overall_wrapped.recap = overallrecap
  
  overall_dict = {}
  
  overall_wrapped.typing_time = seconds_to_duration(overallrecap.count_characters // 5)
  overall_wrapped.clip_watch_time = seconds_to_duration(overallrecap.count_clip_watch)
  
  msgs = ChatMessage.objects.filter(created_at__range = (start_year, end_year)).order_by("created_at")
  
  firstmsg = msgs.first()
  lastmsg = msgs.last()
  
  overall_dict["first_message"] = firstmsg.to_json()
  overall_dict["last_message"] = lastmsg.to_json()
      
  jackass_messages = msgs.filter(message = "+1")
  
  jackass_count = 0
  last_jackass_timestamp : datetime.datetime = None
  for message in jackass_messages:
    if last_jackass_timestamp and (message.created_at - last_jackass_timestamp).total_seconds() < 60:
      continue
    if len(jackass_messages.filter(created_at__range = (message.created_at, message.created_at + datetime.timedelta(seconds = 30)))) > 5:
      jackass_count += 1
      last_jackass_timestamp = message.created_at
  
  overall_wrapped.jackass_count = jackass_count
  
  ijbol_messages = msgs.filter(message__iregex = ".*IJBOL.*")
  overall_dict["first_ijbol"] = ijbol_messages.first().to_json()
  
  all_combo_regex_str = r".*combo.*"
  reg_combo_regex_str = r"((.+) ruined the )?([0-9]+)x ([A-Za-z0-9:\)\(</]+) combo.*"
  big_combo_regex_str = r"you don't ruin ([0-9]+)x ([A-Za-z0-9:\)\(</]+) combos ([A-Za-z0-9_\-\.]+).*"
  reg_combo_regex = re.compile(reg_combo_regex_str, re.IGNORECASE)
  big_combo_regex = re.compile(big_combo_regex_str, re.IGNORECASE)
  
  combo_messages = msgs.filter(commenter_id = 100135110, message__iregex = all_combo_regex_str)
  
  combos = []
  emote_combo_counts = {}
  for message in combo_messages:
    msg_match = reg_combo_regex.match(message.message)
    
    if not msg_match:
      msg_match = big_combo_regex.match(message.message)
      
      if not msg_match:
        print("Message does not match either combo regex")
        print(message.message)
        continue
      
      combo_length = int(msg_match.group(1))
      emote = msg_match.group(2)
      broken_by = msg_match.group(3)
    else:
      combo_length = int(msg_match.group(3))
      emote = msg_match.group(4)
      
      broken_by = None
      if msg_match.group(2):
        broken_by = msg_match.group(2)
      
    combos.append((emote, combo_length, broken_by))
    
    if emote in emote_combo_counts:
      emote_combo_counts[emote] += 1
    else:
      emote_combo_counts[emote] = 1
    
  longest_combos = sorted(combos, key = lambda c: c[1], reverse = True)
  most_common_combos = [(k, v) for k, v in sorted(emote_combo_counts.items(), key = lambda item: item[1], reverse = True)]
  
  overall_dict["longest_combos"] = longest_combos[:10]
  overall_dict["most_common_combos"] = most_common_combos[:10]
    
  clips = Clip.objects.filter(created_at__range = (start_year, end_year)).order_by("-view_count")
  
  overall_dict["top_clips"] = [[] for i in range(0, 13)]
  overall_dict["top_clips"][0] = [clip.to_json() for clip in clips[:5]]
  
  for month in range(1, 13):
    start_range = datetime.datetime(year, month, 1, 0, 0, 0, 1, localtz)
    end_range = datetime.datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59, 999999, localtz)
    clips = Clip.objects.filter(created_at__range = (start_range, end_range)).order_by("-view_count")
    
    overall_dict["top_clips"][month] = [clip.to_json() for clip in clips[:5]]
  
  overall_wrapped.extra_data = overall_dict
  overall_wrapped.save()
  
  if skip_users:
    return
  
  print("Overall wrapped data created. Moving on to user data.")
  
  userrecap_set = overallrecap.userrecapdata_set.all()
  
  leaderboards = {}
  
  invalid_fields = ["year", "month", "count_chatters", "count_videos"]
  exclude_leaderboards = ["year", "month", "count_chatters", "count_videos", "count_clip_watch", "count_400", "count_plus1", "count_caw", "count_yt", "count_q"]
  
  for field in overallrecap._meta.get_fields():
    if ((field.get_internal_type() == "IntegerField" or field.get_internal_type() == "BigIntegerField") and field.name not in invalid_fields):
      leaderboards[field.name] = {userrecap.twitch_user.user_id: getattr(userrecap, field.name) for userrecap in overallrecap.userrecapdata_set.filter(twitch_user__is_bot = False).all().order_by("-" + field.name)}
      
  userrecap : UserRecapData
  for userrecap in userrecap_set:
    user = userrecap.twitch_user
    user_dict = {}
  
    user_wrapped, _ = UserWrappedData.objects.get_or_create(overall_wrapped = overall_wrapped, twitch_user = user)
    
    user_wrapped.recap = userrecap
    
    userclips = Clip.objects.filter(creator = user, created_at__range = (start_year, end_year)).order_by("-view_count")
    
    user_wrapped.typing_time = seconds_to_duration(userrecap.count_characters // 5)
    user_wrapped.clip_watch_time = seconds_to_duration(userrecap.count_clip_watch)
  
    msgs = ChatMessage.objects.filter(commenter = user, created_at__range = (start_year, end_year)).order_by("created_at")
    
    firstmsg = msgs.first()
    lastmsg = msgs.last()
    
    user_dict["first_message"] = "" if not firstmsg else firstmsg.to_json()
    user_dict["last_message"] = "" if not lastmsg else lastmsg.to_json()
    
    user_dict["top_clips"] = [clip.to_json() for clip in userclips[:5]] if len(userclips) > 1 else None
    
    leaderboard_positions = {}
    all_leaderboard_positions = {}
    for field in userrecap._meta.get_fields():
      if ((field.get_internal_type() == "IntegerField" or field.get_internal_type() == "BigIntegerField") and field.name not in invalid_fields):
        if user.user_id in leaderboards[field.name]:
          if leaderboards[field.name][user.user_id] > 0:
            pos = (list(leaderboards[field.name].keys()).index(user.user_id) + 1, leaderboards[field.name][user.user_id])
            if field.name not in exclude_leaderboards:
              leaderboard_positions[field.name] = pos
            all_leaderboard_positions[field.name] = pos
          
    sorted_leaderboard_positions = [(k, v) for k, v in sorted(leaderboard_positions.items(), key = lambda item: item[1][0])]
    sorted_all_leaderboard_positions = [(k, v) for k, v in sorted(all_leaderboard_positions.items(), key = lambda item: item[1][0])]
  
    user_dict["top_leaderboard_positions"] = sorted_leaderboard_positions[:5]
    
    highlight = {}
    
    if user.user_id == 444861963: # ACrowOutside
      caw_rank = -1 if 'count_caw' not in all_leaderboard_positions else all_leaderboard_positions['count_caw'][0]
      percent_caws = (3 * userrecap.count_caw) / max(userrecap.count_characters, 1)
      highlight = {
        "title": "CAW",
        "description": [
          f"CAW RANK {caw_rank} CAWs CAW", 
          f"CAW {userrecap.count_caw:,} CAWs CAW",
          f"CAW CAW made up {percent_caws:.1%} of your total chat output CAW"
        ],
      }
    elif user.user_id == 30512356: # CubsFanatic
      rank_cum = -1 if 'count_cum' not in all_leaderboard_positions else all_leaderboard_positions["count_cum"][0]
      rank_comment = "To no one's surprise, you managed to secure rank 1 cum mentions."
      if rank_cum > 1:
        rank_comment = f"I didn't think this was possible but you got dethroned as cum leader. You ended up as rank {rank_cum} on the leaderboard."
    
      highlight = {
        "title": "itswill7 cum",
        "description": [
          f"You said cum {userrecap.count_cum:,} times this year.",
          rank_comment,
          f"Can we count on you getting #1 in 2025?",
        ],
      }
    elif user.user_id == 528474814: # allknowing89
      highlight = {
        "title": "Chatter extraordinaire",
        "description": [
          f"In October you were the first (and only) person this year who sent more chat messages than both itswillChat and Nightbot in a single month.",
          f"You send 5,757 messages that month, Nightbot only sent 4,385.",
        ],
      }
    elif user.user_id == 43246220: # itswill
      highlight = {
        "title": "hello mr. streamer",
        "description": [
          f"{userrecap.count_yt:,} of your {userrecap.count_messages:,} messages were youtube video links. Shameless self promo PogO.",
          f"You typed cum {userrecap.count_cum:,} times. So much for being the cum guy."
        ],
      }
    elif user.user_id == 82920215: # lusciousdev
      highlight = {
        "title": "nerd",
        "description": [
          "you made this website you already have all the info.",
          "just go look at the database, jackass"
        ],
      }
    elif user.user_id == 185681366: # Brettdog_
      highlight = {
        "title": "Hate to be the bearer of bad news...",
        "description": [
          "but I just found out that not everyone in chat has access to the exclusive level 5 hype train emote GriddyGoose",
          f"But you do, and you typed it {userrecap.count_goose:,} times this year.",
          f"The whole chat followed your lead and typed {overallrecap.count_goose:,} times.",
          f"Can we get 5 gifted to kick off a hype train so we all have the chance to get the exclusive level 5 hype train emote the GriddyGoose?"
        ],
      }
    elif user.user_id == 32678027: # widebuh
      rank_nessie = -1 if 'count_nessie' not in all_leaderboard_positions else all_leaderboard_positions["count_nessie"][0]
      rank_comment = f"You easily got rank {rank_nessie} on the nessiePls leaderboards."
      if rank_nessie > 1:
        rank_comment = f"Wtf. You weren't rank 1 nessiePls? You ended up as rank {rank_nessie} on the leaderboard."
    
      highlight = {
        "title": "nessiePls nessiePls nessiePls",
        "description": [
          f"You went crazy with the nessiePls this year, you managed to send {userrecap.count_nessie:,}.",
          rank_comment,
        ],
      }
    elif user.user_id == 446615592: # twenty_five (ChickenWalk)
      caw_rank = -1 if 'count_chicken' not in all_leaderboard_positions else all_leaderboard_positions['count_chicken'][0]
      highlight = {
        "title": "chickenWalk",
        "description": [
          f"{userrecap.count_chicken:,} chickenWalks",
          f"Rank #{caw_rank} chickenWalker",
        ]
      }
    else:
      for (category, (rank, count)) in sorted_leaderboard_positions:
        if rank > 250:
          highlight = None
          break
        if category == "count_messages":
          highlight = {
            "title": "You chatted a whole lot this year.",
            "description": [
              f"You sent a total of {count:,} messages over the course of this year.",
              f"This placed you at rank {rank} among the entire itswill chat.",
            ],
          }
          break
        elif category == "count_clips":
          highlight = {
            "title": "Are you Clipper?",
            "description": [
              f"Wait, no, you just created {count} clips this year."
              f"You managed to reach rank #{rank} on the clipper leaderboards!"
            ],
          }
          break
        elif category == "count_clip_views":
          highlight = {
            "title": "All eyes on you.",
            "description": [
              f"Your clips got a total of {count:,} views over this past year.",
              f"That kind of mass appeal secured you rank {rank:,} on the clip view leaderboards."
            ],
          }
          break
        elif category == "count_ascii":
          highlight = {
            "title": "All pictures of Garfield I hope",
            "description": [
              f"You posted {count:,} ASCIIs this year.",
              f"All that beautiful art earned you the #{rank} spot on the ASCII leaderboard."
            ],
          }
          break
        elif category == "count_seven":
          highlight = {
            "title": "Salutations o7",
            "description": [
              f"You sent {count:,} itswill7s in the chat this year.",
              f"All those salutes put you at #{rank} on the leaderboard."
            ],
          }
          break
        elif category == "count_pound":
          highlight = {
            "title": "Any pounders in the chat?",
            "description": [
              f"You pounded your fellow chatters a total of {count:,} times this past year.",
              f"That amount of pounding earned you rank {rank} among the itswill chat.",
            ],
          }
          break
        elif category == "count_love":
          highlight = {
            "title": "Love is in the air",
            "description": [
              f"You typed itswilL, itswillLove, etc. {count:,} times this year.",
              f"You're lovely chatting got you rank {rank:,} in love emotes for 2024."
            ],
          }
          break
        elif category == "count_pog":
          highlight = {
            "title": "You had an exciting year",
            "description": [
              f"You typed the various Pog emotes {count:,} times this year",
              f"That makes you the #{rank:,} most pogged chatter!"
            ],
          }
          break
        elif category == "count_shoop":
          highlight = {
            "title": "ShoopDaWhoop supremacy",
            "description": [
              f"You typed ShoopDaWhoop {count:,} times this year. Fuck PogChamp am I right?",
              f"You were the #{rank:,} ShoopDaWhooper of the year."
            ],
          }
          break
        elif category == "count_spin":
          highlight = {
            "title": "AROUND THE WORLD",
            "description": [
              f"You posted {count:,} borpaSpin and other spin related emotes this year",
              f"That's a lot of piss breaks listening to Daft Punk.",
              f"You snagged rank {rank:,} on the leaderboard!"
            ],
          }
          break
        elif category == "count_chicken":
          highlight = {
            "title": "We chicken we walk",
            "description": [
              f"You posted {count:,} chickenWalks this year",
              f"NO BORPA YEP COCK am I right?",
              f"You earned yourself rank {rank:,} on the chickenWalk leaderboard!"
            ],
          }
          break
        elif category == "count_glorp":
          highlight = {
            "title": "Paging all glorps 📡",
            "description": [
              f"You glorped {count:,} times this year.",
              f"That was sufficient glorping to lock in rank {rank:,} overall on the glorp leaderboards."
            ]
          }
          break
          
    user_dict["highlight"] = highlight
    
    user_wrapped.extra_data = user_dict
    user_wrapped.save()