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

from .util.timeutil import *
from .models import *

def get_word_count(text : str, word : str) -> int:
  word_regex = re.compile(fr"(?<![^\s_-]){word}(?![^\s_-])", re.IGNORECASE)
  return len(word_regex.findall(text))

def get_mult_word_count(text : str, words : list) -> int:
  return get_word_count(text, "|".join(words))

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
          commenter, _ = TwitchUser.objects.update_or_create(
            user_id = commenterid,
            login = chatmsg["commenter"]["login"],
            display_name = chatmsg["commenter"]["displayName"],
            created_at = datetime.datetime(1971, 1, 1, 0, 0, 1).replace(tzinfo = datetime.timezone.utc)
          )
        
      commenter.save()
      
      chatmsgtime = None
      try:
        chatmsgtime = datetime.datetime.strptime(chatmsg["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo = datetime.timezone.utc)
      except ValueError:
        chatmsgtime = datetime.datetime.strptime(chatmsg["createdAt"], luscioustwitch.TWITCH_API_TIME_FORMAT).replace(tzinfo = datetime.timezone.utc)
      
      chatmsgmodel, new_msg = ChatMessage.objects.update_or_create(
        commenter = commenter,
        message_id = chatmsg["id"],
        content_offset = chatmsg["contentOffsetSeconds"],
        created_at = chatmsgtime,
        message = msgtext,
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
def calculate_yearly_stats(year = None):
  if year is None:
    year = datetime.datetime.now(TIMEZONE).year
  
  yearrecap, _ = OverallRecapData.objects.get_or_create(year = year, month = 0)
  yearrecap.zero()
  
  localtz = pytz.timezone("America/Los_Angeles")
  start_date = datetime.datetime(year, 1, 1, 0, 0, 0, 1, localtz)
  end_date   = datetime.datetime(year, 12, 31, 23, 59, 59, 999, localtz)
  
  firstmsg = ChatMessage.objects.filter(created_at__range = (start_date, end_date)).order_by("created_at").first()
  yearrecap.first_message = "" if firstmsg is None else firstmsg.message

  monthrecaps = OverallRecapData.objects.filter(year = year, month__gte = 1).prefetch_related("userrecapdata_set").all()
  
  for userrecap in yearrecap.userrecapdata_set.all():
    userrecap.zero()
  
  for recap in monthrecaps:
    yearrecap.add(recap)
    
    for userrecap in recap.userrecapdata_set.all():
      useryear, _ = UserRecapData.objects.get_or_create(overall_recap = yearrecap, twitch_user = userrecap.twitch_user)
      useryear.add(userrecap)
      useryear.save()
  
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
  
  for chatter in TwitchUser.objects.prefetch_related("chatmessage_set", "clip_set").all():
    chatter_messages = chatter.chatmessage_set.filter(created_at__range = (start_date, end_date)).order_by("created_at")
    chatter_clips    = chatter.clip_set.filter(created_at__range = (start_date, end_date))
    
    chatter_msg_count  = chatter_messages.count()
    chatter_clip_count = chatter_clips.count()
    
    chatter_clip_views = 0
    for clip in chatter_clips:
      chatter_clip_views += clip.view_count
    
    if chatter_msg_count > 0 or chatter_clip_count > 0:
      monthrecap.count_messages   = F("count_messages")   + chatter_msg_count
      monthrecap.count_clips      = F("count_clips")      + chatter_clip_count
      monthrecap.count_clip_views = F("count_clip_views") + chatter_clip_views
      monthrecap.count_chatters   = F("count_chatters")   + 1
      
      chatter_recap, _ = UserRecapData.objects.get_or_create(overall_recap = monthrecap, twitch_user = chatter)
      
      chatter_recap.zero()
        
      chatter_recap.count_messages   = chatter_msg_count
      chatter_recap.count_clips      = chatter_clip_count
      chatter_recap.count_clip_views = chatter_clip_views
      
      firstmsg = chatter_messages.first()
      chatter_recap.first_message = "" if firstmsg is None else firstmsg.message
      
      for msg in chatter_messages:
        chatter_recap.count_seven   = F("count_seven")   + get_mult_word_count(msg.message, ["itswill7", "itswillFreeTrial"])
        chatter_recap.count_pound   = F("count_pound")   + get_mult_word_count(msg.message, ["itswillPound", "itswill4"])
        chatter_recap.count_etsmg   = F("count_etsmg")   + get_word_count(msg.message, "itswillEndTheStreamMyGuy")
        chatter_recap.count_ksmg    = F("count_ksmg")    + get_word_count(msg.message, "itswillKeepStreamingMyGuy")
        chatter_recap.count_sneak   = F("count_sneak")   + get_mult_word_count(msg.message, ["itswillSneak", "itswillFollow", "Sneak"])
        chatter_recap.count_sit     = F("count_sit")     + get_word_count(msg.message, "itswillSit")
        chatter_recap.count_love    = F("count_love")    + get_mult_word_count(msg.message, ["itswillL", "hannLOVE", "peepoLove"])
        chatter_recap.count_pog     = F("count_pog")     + get_mult_word_count(msg.message, ["Pog", "PogChamp", "POGGIES", "POGGERS", "itswillPog", "PagU", "PagMan"])
        chatter_recap.count_shoop   = F("count_shoop")   + get_word_count(msg.message, "ShoopDaWhoop")
        chatter_recap.count_mmylc   = F("count_mmylc")   + get_word_count(msg.message, "MusicMakeYouLoseControl")
        chatter_recap.count_giggle  = F("count_giggle")  + get_mult_word_count(msg.message, ["x0r6ztGiggle", "willGiggle", "itswillGiggle"])
        chatter_recap.count_vvkool  = F("count_vvkool")  + get_mult_word_count(msg.message, ["VVKool", "VVotate", "VVKoolMini"])
        chatter_recap.count_gasp    = F("count_gasp")    + get_mult_word_count(msg.message, ["D\\:", "hannD"])
        chatter_recap.count_monka   = F("count_monka")   + get_mult_word_count(msg.message, ["monkaS", "monkaW", "monkaEyes", "monkaGun", "monkaSTEER", "monkaH"])
        chatter_recap.count_pogo    = F("count_pogo")    + get_mult_word_count(msg.message, ["PogO", "WeirdChamp", "itswillO", "itswillWeird", "WeirdPause"])
        chatter_recap.count_cum     = F("count_cum")     + get_mult_word_count(msg.message, ["cum", "cumming", "cumb", "cummies", "cumshot"])
        chatter_recap.count_spin    = F("count_spin")    + get_mult_word_count(msg.message, ["itswillSpin", "willSpin", "borpaSpin", "YourMom"])
        chatter_recap.count_chicken = F("count_chicken") + get_word_count(msg.message, "chickenWalk")
        chatter_recap.count_sonic   = F("count_sonic")   + get_mult_word_count(msg.message, ["itsWillCoolSonic", "CoolSonic"])
        chatter_recap.count_lul     = F("count_lul")     + get_mult_word_count(msg.message, ["LUL", "LULW", "OMEGALUL", "OMEGADANCE"])
        chatter_recap.count_stsmg   = F("count_stsmg")   + get_word_count(msg.message, "StartTheStreamMyGuy")
        chatter_recap.count_dance   = F("count_dance")   + get_mult_word_count(msg.message, ["itswillPls", "pepeD", "PepePls", "daemonDj", "willDJ", "nessiePls", "Happi", "GoodBoy", "SourPls"])
        chatter_recap.count_dankies = F("count_dankies") + get_mult_word_count(msg.message, ["DANKIES", "HYPERS"])
      
      chatter_recap.save()
      
      monthrecap.count_seven   = F("count_seven")   + chatter_recap.count_seven
      monthrecap.count_pound   = F("count_pound")   + chatter_recap.count_pound
      monthrecap.count_etsmg   = F("count_etsmg")   + chatter_recap.count_etsmg
      monthrecap.count_ksmg    = F("count_ksmg")    + chatter_recap.count_ksmg
      monthrecap.count_sneak   = F("count_sneak")   + chatter_recap.count_sneak
      monthrecap.count_sit     = F("count_sit")     + chatter_recap.count_sit
      monthrecap.count_love    = F("count_love")    + chatter_recap.count_love
      monthrecap.count_pog     = F("count_pog")     + chatter_recap.count_pog
      monthrecap.count_shoop   = F("count_shoop")   + chatter_recap.count_shoop
      monthrecap.count_mmylc   = F("count_mmylc")   + chatter_recap.count_mmylc
      monthrecap.count_giggle  = F("count_giggle")  + chatter_recap.count_giggle
      monthrecap.count_vvkool  = F("count_vvkool")  + chatter_recap.count_vvkool
      monthrecap.count_gasp    = F("count_gasp")    + chatter_recap.count_gasp
      monthrecap.count_monka   = F("count_monka")   + chatter_recap.count_monka
      monthrecap.count_pogo    = F("count_pogo")    + chatter_recap.count_pogo
      monthrecap.count_cum     = F("count_cum")     + chatter_recap.count_cum
      monthrecap.count_spin    = F("count_spin")    + chatter_recap.count_spin
      monthrecap.count_chicken = F("count_chicken") + chatter_recap.count_chicken
      monthrecap.count_sonic   = F("count_sonic")   + chatter_recap.count_sonic
      monthrecap.count_lul     = F("count_lul")     + chatter_recap.count_lul
      monthrecap.count_stsmg   = F("count_stsmg")   + chatter_recap.count_stsmg
      monthrecap.count_dance   = F("count_dance")   + chatter_recap.count_dance
      monthrecap.count_dankies = F("count_dankies") + chatter_recap.count_dankies
      
  monthrecap.save()