from django.conf import settings
from celery import Celery, shared_task
from celery.schedules import crontab
import luscioustwitch
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db.models import F, Q, Count, Max, Sum, Prefetch, OuterRef, Subquery
from django.db.models.functions import Coalesce

import datetime
from dateutil import tz
import calendar
import re
import humanize
import feedparser
import requests
from random import randint, choice
import time

from .util.timeutil import *
from .models import *

def get_word_count(text : str, word : str) -> int:
  word_regex = re.compile(fr"(?<![^\s_-]){word}(?![^\s_-])", re.IGNORECASE)
  return len(word_regex.findall(text))

def get_mult_word_count(text : str, words : list) -> int:
  return get_word_count(text, "|".join(words))

def get_random_message(user):
  messages = ChatMessage.objects
  if user != None:
    messages = messages.filter(commenter = user)
    
  message_pks = messages.values_list('pk', flat=True)
  try:
    if user == None:
      random_message = messages.get(pk = randint(1, len(message_pks) - 1))
    else:
      random_message = messages.get(pk = choice(list(message_pks)))
  except ChatMessage.DoesNotExist:
    return "ERROR: randomly selected private key does not exist. ID sequence must be sparsely populated. That's no bueno."
  
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
def get_letterboxd_reviews():
  feed : feedparser.FeedParserDict = feedparser.parse("https://letterboxd.com/itswill/rss")
  REVIEW_REGEX = re.compile("letterboxd-review-[0-9]+")
  LETTERBOXD_PUB_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
  LETTERBOXD_WATCH_DATE_FORMAT = "%Y-%m-%d"
  SUMMARY_REGEX = re.compile('<.+?>')
  
  entry : feedparser.FeedParserDict
  for entry in feed.get("entries", []):
    review_id_match : re.Match = REVIEW_REGEX.match(entry.get("id", ""))
    if not review_id_match:
      continue
    
    title = entry.get("title", "")
    review_id = review_id_match.group(0)
    link = entry.get("link", "")
    pub_date = datetime.datetime.strptime(entry.get("published", datetime.datetime.now().strftime(LETTERBOXD_PUB_FORMAT)), LETTERBOXD_PUB_FORMAT)
    watched_date = datetime.datetime.strptime(entry.get("letterboxd_watcheddate", datetime.datetime.now().strftime(LETTERBOXD_WATCH_DATE_FORMAT)), LETTERBOXD_WATCH_DATE_FORMAT)
    film_title = entry.get("letterboxd_filmtitle", "")
    film_year = entry.get("letterboxd_filmyear", None)
    film_year = None if film_year is None else int(film_year)
    member_rating = entry.get("letterboxd_memberrating", None)
    member_rating = None if member_rating is None else float(member_rating)
    movie_id = entry.get("tmdb_movieid", None)
    movie_id = None if movie_id is None else int(movie_id)
    raw_description = entry.get("summary", "")
    description : str = re.sub(SUMMARY_REGEX, ' ', raw_description)
    description = description.strip()
    creator = entry.get("author", "")
    
    obj, created = LetterboxdReview.objects.update_or_create(
      review_id = review_id,
      defaults = {
        "title": title,
        "link": link,
        "pub_date": pub_date,
        "watched_date": watched_date,
        "film_title": film_title,
        "film_year": film_year,
        "member_rating": member_rating,
        "movie_id": movie_id,
        "description": description,
        "creator": creator
      }
    )
    
    if created:
      print(f"New review: { film_title } - { member_rating } stars: { description }")
    else:
      print(f"Old review: { film_title } - { member_rating } stars: { description }")
  
def add_clip_to_db(twitch_api : luscioustwitch.TwitchAPI, clip : luscioustwitch.TwitchClip):
  clip_id = clip.clip_id
  creator_id = int(clip.creator_id)
    
  try:
    creator = TwitchUser.objects.get(user_id = creator_id)
  except TwitchUser.DoesNotExist:
    try:
      userdata : luscioustwitch.TwitchUser = twitch_api.get_user(id = creator_id)
    
      creator = TwitchUser(
        user_id = creator_id,
        login = userdata.login,
        display_name = userdata.display_name,
        user_type = userdata.user_type,
        broadcaster_type = userdata.broadcaster_type,
        description = userdata.description,
        profile_image_url = userdata.profile_image_url,
        offline_image_url = userdata.offline_image_url,
        created_at = userdata.created_at.replace(tzinfo = datetime.timezone.utc),
      )
    except:
      creator = TwitchUser(
        user_id = creator_id,
        login = clip.creator_name,
        display_name = clip.creator_name
      )
    
    creator.save()
    
  clip_inst, _ = Clip.objects.update_or_create(
    clip_id = clip_id,
    defaults = {
      "creator": creator,
      "url": clip.url,
      "embed_url": clip.embed_url,
      "broadcaster_id": int(clip.broadcaster_id),
      "broadcaster_name": clip.broadcaster_name,
      "video_id": clip.video_id,
      "game_id": clip.game_id,
      "language": clip.language,
      "title": clip.title,
      "view_count": int(clip.view_count),
      "created_at": clip.created_at.replace(tzinfo = datetime.timezone.utc),
      "thumbnail_url": clip.thumbnail_url,
      "duration": float(clip.duration),
      "vod_offset": -1 if (clip.vod_offset == "null" or clip.vod_offset is None) else int(clip.vod_offset)
    }
  )
  
def get_all_clips(twitch_api : luscioustwitch.TwitchAPI, sdt : datetime.datetime, edt : datetime.datetime) -> int:
  clip_params = {
    "first": 50,
    "broadcaster_id": settings.USER_ID,
    "started_at": sdt.strftime(luscioustwitch.TWITCH_API_TIME_FORMAT),
    "ended_at": edt.strftime(luscioustwitch.TWITCH_API_TIME_FORMAT)
  }
  
  continue_fetching = True
  clip_count = 0
  while continue_fetching:
    try:
      clips, cursor = twitch_api.get_clips(params=clip_params)
    except Exception as e:
      print(e)
      time.sleep(120)
      print("Continuing search...")
      continue

    if cursor != "":
      clip_params["after"] = cursor
    else:
      continue_fetching = False

    clip : luscioustwitch.TwitchClip
    for clip in clips:
      clip_count += 1
      add_clip_to_db(twitch_api, clip)
      
  
  if clip_count > 900:
    print(f"POTENTIAL ERROR: CLIPS FOUND IN RANGE {sdt.strftime(luscioustwitch.TWITCH_API_TIME_FORMAT)} to {edt.strftime(luscioustwitch.TWITCH_API_TIME_FORMAT)}: {clip_count} (API CAPS AROUND 1000)")
  else:
    print(f"Clips found in range {sdt.strftime(luscioustwitch.TWITCH_API_TIME_FORMAT)} to {edt.strftime(luscioustwitch.TWITCH_API_TIME_FORMAT)}: {clip_count}")
        

@shared_task
def get_recent_clips(max_days = 31):
  twitch_api = luscioustwitch.TwitchAPI({ "CLIENT_ID" : settings.TWITCH_API_CLIENT_ID, "CLIENT_SECRET": settings.TWITCH_API_CLIENT_SECRET })
  
  if max_days > 0:
    start_date = datetime.datetime.combine(datetime.datetime.now().date(), datetime.time(0, 0, 0, 1)) - datetime.timedelta(days = max_days)
  else:
    start_date = datetime.datetime(1971, 1, 1, 0, 0, 0, 1, tzinfo = datetime.timezone.utc)
    
  end_date = datetime.datetime.now() + datetime.timedelta(days = 1)
  
  segment_increment = datetime.timedelta(days = 4)
  segment_length = datetime.timedelta(days = 5)
  
  segment_start = start_date
  segment_end   = segment_start + segment_length

  continue_fetching = True
  while continue_fetching:
    get_all_clips(twitch_api, segment_start, segment_end)
    
    segment_start = segment_start + segment_increment
    segment_end = segment_start + segment_length
    
    if segment_end > end_date:
      segment_end = end_date
      
    if segment_start > end_date:
      continue_fetching = False
  

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
    vod_date = video.published_at.replace(tzinfo = tz.UTC)
    
    if max_days > 0 and vod_date < start_date:
      continue
    
    videofound = False
    try:
      videoinstance = Video.objects.get(vod_id = video.video_id)
      videofound = True
    except Video.DoesNotExist:
      None
      
    if skip_known_vods and videofound:
      print(f"Skipping {video.video_id} as it's in our database already.")
      continue

    print(f'{video.video_id} - {utc_to_local(vod_date, TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")}')
    
    vid_chat = gql_api.get_chat_messages(video.video_id)
    
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
      
      emote_list = []
      msgtext = ""
      for frag in frags:
        if frag["emote"] is not None:
          emote, _ = TwitchEmote.objects.get_or_create(emote_id = frag["emote"]["emoteID"], defaults = { "name": frag["text"] })
          emote_list.append(emote)
        msgtext += frag["text"]
        
      try:
        commenter = TwitchUser.objects.get(user_id = commenterid)
        
        commenter.login = chatmsg['commenter']['login']
        commenter.display_name = chatmsg['commenter']['displayName']
      except TwitchUser.DoesNotExist:
        try:
          userdata : luscioustwitch.TwitchUser = twitch_api.get_user(id = commenterid)
        
          commenter, _ = TwitchUser.objects.update_or_create(
            user_id = commenterid,
            defaults = {
              "login": userdata.login,
              "display_name": userdata.display_name,
              "user_type": userdata.user_type,
              "broadcaster_type": userdata.broadcaster_type,
              "description": userdata.description,
              "profile_image_url": userdata.profile_image_url,
              "offline_image_url": userdata.offline_image_url,
              "created_at": datetime.datetime.strptime(userdata.created_at, luscioustwitch.TWITCH_API_TIME_FORMAT).replace(tzinfo = datetime.timezone.utc),
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
      
      for emote in emote_list:
        chatmsgmodel.emotes.add(emote)
      
      chatmsgmodel.save()
        
    if not videofound:
      videoinstance = Video(
        vod_id = video.video_id,
        stream_id = video.stream_id,
        user_id = video.user_id,
        user_login = video.user_login,
        user_name = video.user_name,
        title = video.title,
        description = video.description,
        created_at = video.created_at.replace(tzinfo = datetime.timezone.utc),
        published_at = video.created_at.replace(tzinfo = datetime.timezone.utc),
        url = video.url,
        thumbnail_url = video.thumbnail_url,
        viewable = video.viewable,
        view_count = video.view_count,
        language = video.language,
        vod_type = video.type,
        duration = video.duration,
      )
      videoinstance.save()

@shared_task
def get_all_first_messages():
  localtz = tz.gettz("America/Los_Angeles")
  
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
def find_fragment_matches(perf : bool = True):
  if perf: start = time.perf_counter()
  
  print("Calculating: fragments")
  
  queryset = ChatMessage.objects.values_list("id", "message", "commenter_id", "created_at").all()
  paginator = Paginator(queryset, 500_000)
  
  fragments = Fragment.objects.all()
  fragment_regex = { f.pretty_name: f.match_regex for f in fragments }
  
  message_count = 0
  for pgnum in paginator.page_range:
    page = paginator.page(pgnum)
    new_fragment_matches : list[FragmentMatch] = []
    for msg_obj_id, message, commenter_id, created_at in page.object_list:
      message_count += 1
      f : Fragment
      for f in fragments:
        frag_count = len(fragment_regex[f.pretty_name].findall(message))
        if frag_count > 0:
          fm = FragmentMatch(fragment = f, 
                             message_id = msg_obj_id, 
                             count = frag_count if f.group.count_multiples else 1, 
                             timestamp = created_at, 
                             commenter_id = commenter_id)
          new_fragment_matches.append(fm)
    FragmentMatch.objects.bulk_create(new_fragment_matches, update_conflicts = True, update_fields = [ "count", "timestamp", "commenter_id" ])
  
  if perf: print(f"fragments took {time.perf_counter() - start:.3f} seconds")

def calculate_recap_stats(year : int = None, month : int = None, user_id : int = None, return_result : bool = False, perf : bool = False):
  if perf: 
    print(f"Calculating: {year}-{month} ({user_id if user_id else 'overall'})")
    start = time.perf_counter()
  
  if year is None:
    year = datetime.datetime.now(TIMEZONE).year
  if month is None:
    month = datetime.datetime.now(TIMEZONE).month
  
  chat_messages = ChatMessage.objects
  videos = Video.objects
  clips = Clip.objects
  
  if user_id is None:
    recap, _ = OverallRecapData.objects.get_or_create(year = year, month = month)
  else:
    overall_recap, _ = OverallRecapData.objects.get_or_create(year = year, month = month)
    recap, _ = UserRecapData.objects.get_or_create(overall_recap = overall_recap, twitch_user_id = user_id)
    
    chat_messages = chat_messages.filter(commenter_id = user_id)
    clips = clips.filter(creator_id = user_id)
  
  if year > 0:
    chat_messages = chat_messages.filter(created_at__range = (recap.start_date, recap.end_date))
    videos = videos.filter(created_at__range = (recap.start_date, recap.end_date))
    clips = clips.filter(created_at__range = (recap.start_date, recap.end_date))
  
  
  recap.count_messages = chat_messages.count()
  recap.count_characters = sum([len(m) for m in chat_messages.values_list("message", flat = True).all()])
  
  firstmsg = chat_messages.order_by("created_at").first()
  recap.first_message = "" if firstmsg is None else firstmsg.message
  
  if perf: print(f"\tmessages: {time.perf_counter() - start:.3f} seconds")
  
  recap.count_clips = clips.count()
  
  cv = 0
  cw = 0
  for c in clips.all():
    cv += c.view_count
    cw += c.view_count * c.duration
    
  recap.count_clip_views = cv
  recap.count_clip_watch = int(cw)
  
  if user_id is None:
    recap.count_videos = videos.count()
    recap.count_chatters = chat_messages.values("commenter").distinct().count()
  
  if perf: print(f"\tclips: {time.perf_counter() - start:.3f} seconds")
  
  for fg in FragmentGroup.objects.order_by("ordering").all():
    recap.counters[fg.group_id] = { 
      "total": 0,
      "members": { f.pretty_name: 0 for f in fg.fragment_set.all() }
    }
    total = 0
    f : Fragment
    for f in fg.fragment_set.all():
      if user_id is None:
        fms = FragmentMatch.objects.filter(fragment = f, timestamp__range = (recap.start_date, recap.end_date)).all()
        f_count = sum([fm.count for fm in fms])
      else:
        fms = FragmentMatch.objects.filter(fragment = f, timestamp__range = (recap.start_date, recap.end_date), commenter_id = user_id).all()
        f_count = sum([fm.count for fm in fms])
      recap.counters[fg.group_id]["members"][f.pretty_name] = f_count
      total += f_count
  
      if perf: print(f"\t{f.pretty_name}: {time.perf_counter() - start:.3f} seconds")
    recap.counters[fg.group_id]["total"] = total
  
  if return_result:
    return recap
  else:
    recap.save()
  if perf: print(f"\ttotal: {time.perf_counter() - start:.3f} seconds")
  
def sum_recap_stats(year : int = None, user_id : int = None, perf : bool = False):
  if perf: start = time.perf_counter()
  
  if year is None:
    year = datetime.datetime.now(TIMEZONE).year
    
  if year == 0:
    monthrecaps = OverallRecapData.objects.filter(year__gte = 1, month__gte = 1).all()
  else:
    monthrecaps = OverallRecapData.objects.filter(year = year, month__gte = 1).all()
  
  chat_messages = ChatMessage.objects
  
  if user_id is None:
    recap, _ = OverallRecapData.objects.get_or_create(year = year, month = 0)
  else:
    overall_recap, _ = OverallRecapData.objects.get_or_create(year = year, month = 0)
    recap, _ = UserRecapData.objects.get_or_create(overall_recap = overall_recap, twitch_user_id = user_id)
    
    chat_messages = chat_messages.filter(commenter_id = user_id)
    
    monthrecaps = UserRecapData.objects.filter(overall_recap__in = monthrecaps, twitch_user_id = user_id).all()
    
  if year > 0:
    chat_messages = chat_messages.filter(created_at__range = (recap.start_date, recap.end_date))
    
  if user_id is None:
    recap.count_chatters = chat_messages.values("commenter").distinct().count()
  
  firstmsg = chat_messages.order_by("created_at").first()
  recap.first_message = "" if firstmsg is None else firstmsg.message
    
  recap.count_messages = 0
  recap.count_characters = 0
  recap.count_clips = 0
  recap.count_clip_watch = 0
  recap.count_clip_views = 0
  recap.count_videos = 0
  
  fgs = FragmentGroup.objects.order_by("ordering").prefetch_related("fragment_set").all()
  
  for fg in fgs:
    recap.counters[fg.group_id] = { 
      "total": 0,
      "members": { f.pretty_name: 0 for f in fg.fragment_set.all() }
    }
    
  for mr in monthrecaps:
    recap.count_messages += mr.count_messages
    recap.count_characters += mr.count_messages
    recap.count_clips += mr.count_clips
    recap.count_clip_watch += mr.count_clip_watch
    recap.count_clip_views += mr.count_clip_views
    recap.count_videos += mr.count_videos
    
    for fg in fgs:
      recap.counters[fg.group_id]["total"] += mr.counters.get(fg.group_id, {}).get("total", 0)
      
      f : Fragment
      for f in fg.fragment_set.all():
        recap.counters[fg.group_id]["members"][f.pretty_name] += mr.counters.get(fg.group_id, {}).get("members", {}).get(f.pretty_name, 0)
        
  recap.save()
  if perf: print(f"sum took {time.perf_counter() - start:.3f} seconds")

@shared_task
def calculate_monthly_stats(year = None, month = None, perf : bool = False):
  if perf: start = time.perf_counter()
  
  if year is None:
    year = datetime.datetime.now(TIMEZONE).year
  if month is None:
    month = datetime.datetime.now(TIMEZONE).month
    
  print(f"Calculating: {year}-{month}")
    
  localtz = tz.gettz("America/Los_Angeles")
  monthrange = calendar.monthrange(year, month)
  
  start_date = datetime.datetime(year, month, 1, 0, 0, 0, 1, localtz)
  end_date = datetime.datetime(year, month, monthrange[1], 23, 59, 59, 999, localtz)
        
  if perf: overallstart = time.perf_counter()
  
  calculate_recap_stats(year, month)
  
  if perf: print(f"\toverall: {time.perf_counter() - overallstart:.3f}s")
  if perf: usersstart = time.perf_counter()
  
  user_set = set(ChatMessage.objects.filter(created_at__range = (start_date, end_date)).values_list("commenter", flat = True).distinct().all()) | set(Clip.objects.filter(created_at__range = (start_date, end_date)).values_list("creator", flat = True).distinct().all())
  updated_recaps = []
  for user in user_set:
    recap = calculate_recap_stats(year, month, user_id = user, return_result = True)
    updated_recaps.append(recap)
    
  UserRecapData.objects.bulk_update(updated_recaps, fields = ["count_messages", "count_characters", "count_clips", "count_clip_watch", "count_clip_views", "first_message", "last_message", "counters"])
  
  if perf: print(f"\tusers: {time.perf_counter() - usersstart:.3f}s")
  if perf: print(f"\ttotal: {time.perf_counter() - start:.3f}s")
  
@shared_task
def calculate_yearly_stats(year = None, recalculate = False, perf : bool = False):
  if perf: start = time.perf_counter()
  
  if year is None:
    year = datetime.datetime.now(TIMEZONE).year
    
  print(f"Calculating: {year}")
    
  localtz = tz.gettz("America/Los_Angeles")
  start_date = datetime.datetime(year, 1, 1, 0, 0, 0, 1, localtz)
  end_date = datetime.datetime(year, 12, 31, 23, 59, 59, 999, localtz)
        
  if perf: overallstart = time.perf_counter()
  
  if recalculate:
    calculate_recap_stats(year, 0)
  else:
    sum_recap_stats(year)
    
  if perf: print(f"\toverall: {time.perf_counter() - overallstart:.3f}s")
  if perf: usersstart = time.perf_counter()
  
  user_set = set(ChatMessage.objects.filter(created_at__range = (start_date, end_date)).values_list("commenter", flat = True).distinct().all()) | set(Clip.objects.filter(created_at__range = (start_date, end_date)).values_list("creator", flat = True).distinct().all())
  if recalculate:
    for user in user_set:
      calculate_recap_stats(year, 0, user_id = user)
  else:
    for user in user_set:
      sum_recap_stats(year, user_id = user)
      
  if perf: print(f"\tusers: {time.perf_counter() - usersstart:.3f}s")
  if perf: print(f"\ttotal: {time.perf_counter() - start:.3f}s")
  
@shared_task
def calculate_alltime_stats(recalculate : bool = False, perf : bool = False):
  if perf: start = time.perf_counter()
  
  print(f"Calculating: all time")
        
  if perf: overallstart = time.perf_counter()
  
  if recalculate:
    calculate_recap_stats(0, 0)
  else:
    sum_recap_stats(0)
    
  if perf: print(f"\toverall: {time.perf_counter() - overallstart:.3f}s")
  if perf: usersstart = time.perf_counter()
  
  user_set = TwitchUser.objects.all()
  if recalculate:
    for user in user_set:
      calculate_recap_stats(0, 0, user_id = user)
  else:
    for user in user_set:
      sum_recap_stats(0, user_id = user)
      
  if perf: print(f"\tusers: {time.perf_counter() - usersstart:.3f}s")
  if perf: print(f"\ttotal: {time.perf_counter() - start:.3f}s")
      
@shared_task
def calculate_all_leaderboards(perf : bool = True):
  if perf: start = time.perf_counter()
  
  print("Calculating: leaderboards")
  
  for overallrecap in OverallRecapData.objects.all():
    leaderboards_dict = {}
    for field in overallrecap._meta.get_fields():
      if type(field) in [StatField, BigStatField] and field.name not in ["year", "month", "count_chatters", "count_videos"]:
        if not field.show_leaderboard:
          continue
        leaderboards_dict[field.short_name] = [(userrecap.twitch_user.display_name, getattr(userrecap, field.name), userrecap.twitch_user.is_bot) for userrecap in overallrecap.userrecapdata_set.all().order_by("-" + field.name)[:250]]
    
    for fg in FragmentGroup.objects.order_by("ordering").filter(show_leaderboard = True).all():
      leaderboards_dict[fg.group_id] = [(userrecap.twitch_user.display_name, userrecap.counters[fg.group_id]["total"], userrecap.twitch_user.is_bot) for userrecap in overallrecap.userrecapdata_set.order_by(f"-counters__{fg.group_id}__total")[:250]]
        
    overallrecap.leaderboards = leaderboards_dict
    overallrecap.save()
    
  if perf: print(f"leaderboards took {time.perf_counter() - start:.3f} seconds")
    
@shared_task
def calculate_everything(find_fragments : bool = False):
  year = datetime.datetime.now(TIMEZONE).year
  month = datetime.datetime.now(TIMEZONE).month
  
  if find_fragments:
    find_fragment_matches(perf = True)
  
  for y in range(2023, year+1):
    month_range = range(1, 13) if y < year else range(1, month + 1)
    for m in month_range:
      calculate_monthly_stats(y, m, perf = True)
    calculate_yearly_stats(y, perf = True)
    
  calculate_alltime_stats(perf = True)
  calculate_all_leaderboards(perf = True)
  create_wrapped_data(perf = True)
    
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
   
  if not msd_hit:
    output += f"{seconds} seconds"
  
  return output
    
@shared_task
def create_wrapped_data(year = None, skip_users = False, perf : bool = True):
  if perf: start = time.perf_counter()
  
  print("Calculating: wrapped")
  
  if year is None:
    year = datetime.datetime.now(TIMEZONE).year
  
  localtz = tz.gettz("America/Los_Angeles")
  
  try:
    overallrecap = OverallRecapData.objects.get(year = year, month = 0)
  except OverallRecapData.DoesNotExist:
    print("No recap for that year.")
    return
  
  start_year = overallrecap.start_date
  end_year = overallrecap.end_date
  
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
          f"You sent 5,757 messages that month, Nightbot only sent 4,385.",
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
          f"The whole chat followed your lead and typed it {overallrecap.count_goose:,} times.",
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
      percent_chicken = (len("chickenWalk") * userrecap.count_chicken) / max(userrecap.count_characters, 1)
      highlight = {
        "title": "chickenWalk",
        "description": [
          f"{userrecap.count_chicken:,} chickenWalks",
          f"Rank #{caw_rank} chickenWalker",
          f"chickenWalk is {percent_chicken:.0%} of your total chat history."
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
    
  if perf: print(f"wrapped took {time.perf_counter() - start:.3f} seconds")
  
def update_pretty_names():
  recaps = []
  for r in OverallRecapData.objects.all():
    if "plus1" in r.counters:
      r.counters["plus1"]["members"].pop("+1", None)
      r.counters["plus1"]["members"].pop("@itswillChat", None)
      r.counters["plus1"]["members"].pop("at_bot", None)
      if "+1" in r.counters["plus1"]["members"]:
        r.counters["plus1"]["members"]["plus1"] = r.counters["plus1"]["members"]["+1"]
        r.counters["plus1"]["members"].pop("+1", None)
    if "at_bot" in r.counters:
      r.counters["at_bot"]["members"].pop("+1", None)
      r.counters["at_bot"]["members"].pop("@itswillChat", None)
      r.counters["at_bot"]["members"].pop("plus1", None)
      if "@itswillChat" in r.counters["at_bot"]["members"]:
        r.counters["at_bot"]["members"]["at_bot"] = r.counters["at_bot"]["members"]["@itswillChat"]
        r.counters["at_bot"]["members"].pop("@itswillChat", None)
    if "q" in r.counters:
      if "???" in r.counters["q"]["members"]:
        r.counters["q"]["members"]["question_marks"] = r.counters["q"]["members"]["???"]
        r.counters["q"]["members"].pop("???", None)
    if "ascii" in r.counters:
      if "ASCII" in r.counters["ascii"]["members"]:
        r.counters["ascii"]["members"]["ascii"] = r.counters["ascii"]["members"]["ASCII"]
        r.counters["ascii"]["members"].pop("ASCII", None)
        
    recaps.append(r)
  OverallRecapData.objects.bulk_update(recaps, fields = [ "counters", ])
  recaps = []
  for r in UserRecapData.objects.all():
    if "plus1" in r.counters:
      r.counters["plus1"]["members"].pop("@itswillChat", None)
      r.counters["plus1"]["members"].pop("at_bot", None)
      if "+1" in r.counters["plus1"]["members"]:
        r.counters["plus1"]["members"]["plus1"] = r.counters["plus1"]["members"]["+1"]
        r.counters["plus1"]["members"].pop("+1", None)
    if "at_bot" in r.counters:
      r.counters["at_bot"]["members"].pop("+1", None)
      r.counters["at_bot"]["members"].pop("plus1", None)
      if "@itswillChat" in r.counters["at_bot"]["members"]:
        r.counters["at_bot"]["members"]["at_bot"] = r.counters["at_bot"]["members"]["@itswillChat"]
        r.counters["at_bot"]["members"].pop("@itswillChat", None)
    if "q" in r.counters:
      if "???" in r.counters["q"]["members"]:
        r.counters["q"]["members"]["question_marks"] = r.counters["q"]["members"]["???"]
        r.counters["q"]["members"].pop("???", None)
    if "ascii" in r.counters:
      if "ASCII" in r.counters["ascii"]["members"]:
        r.counters["ascii"]["members"]["ascii"] = r.counters["ascii"]["members"]["ASCII"]
        r.counters["ascii"]["members"].pop("ASCII", None)
    
        
    recaps.append(r)
    if len(recaps) > 1000:
      UserRecapData.objects.bulk_update(recaps, fields = ["counters", ])
      recaps = []
  UserRecapData.objects.bulk_update(recaps, fields = [ "counters", ])