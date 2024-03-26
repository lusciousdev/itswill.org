from django.conf import settings
from celery import Celery, shared_task
from celery.schedules import crontab
import luscioustwitch

import datetime
import pytz
import calendar
import re

from .models import *

def get_word_count(text : str, word : str) -> int:
  word_regex = re.compile(fr"(?<![^\s_-]){word}(?![^\s_-])", re.IGNORECASE)
  return len(word_regex.findall(text))

def get_mult_word_count(text : str, words : list) -> int:
  return get_word_count(text, "|".join(words))

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
def calculate_yearly_stats(year):
  try:
    yearrecap = OverallRecapData.objects.get(year = year, month = 0)
  except OverallRecapData.DoesNotExist:
    yearrecap = OverallRecapData(year = year, month = 0)
    yearrecap.save()
    
  yearrecap.zero()
  
  localtz = pytz.timezone("America/Los_Angeles")
  start_date = datetime.datetime(year, 1, 1, 0, 0, 0, 1, localtz)
  end_date   = datetime.datetime(year, 12, 31, 23, 59, 59, 999, localtz)
  
  firstmsg = ChatMessage.objects.filter(created_at__range = (start_date, end_date)).order_by("created_at").first()
  yearrecap.first_message = "" if firstmsg is None else firstmsg.message

  monthrecaps = OverallRecapData.objects.filter(year = year, month__gte = 1).all()
  
  for userrecap in yearrecap.userrecapdata_set.all():
    userrecap.zero()
    userrecap.save()
    
  yearrecap.save()
  
  for recap in monthrecaps:
    yearrecap.add(recap)
    
    for userrecap in recap.userrecapdata_set.all():
      try:
        useryear = UserRecapData.objects.get(overall_recap = yearrecap, twitch_user = userrecap.twitch_user)
      except UserRecapData.DoesNotExist:
        useryear = UserRecapData(
          overall_recap = yearrecap,
          twitch_user = userrecap.twitch_user,
        )
        useryear.save()
      
      useryear.add(userrecap)
      useryear.save()
  
  yearrecap.count_chatters = yearrecap.userrecapdata_set.all().count()
  yearrecap.save()
        

@shared_task
def calculate_monthly_stats(year, month):
  localtz = pytz.timezone("America/Los_Angeles")
  monthrange = calendar.monthrange(year, month)
  
  try:
    monthrecap = OverallRecapData.objects.get(year = year, month = month)
  except OverallRecapData.DoesNotExist:
    monthrecap = OverallRecapData(year = year, month = month)
    monthrecap.save()
    
  monthrecap.zero()
  
  start_date = datetime.datetime(year, month, 1, 0, 0, 0, 1, localtz)
  end_date = datetime.datetime(year, month, monthrange[1], 23, 59, 59, 999, localtz)
    
  chat_messages = ChatMessage.objects.filter(created_at__range = (start_date, end_date)).order_by("created_at")
  clips = Clip.objects.filter(created_at__range = (start_date, end_date)).order_by("-view_count")
  videos = Video.objects.filter(created_at__range = (start_date, end_date))
  
  monthrecap.count_videos = videos.count()
  
  firstmsg = chat_messages.first()
  monthrecap.first_message = "" if firstmsg is None else firstmsg.message
  
  for chatter in TwitchUser.objects.all():
    chatter_messages = chat_messages.filter(commenter = chatter).order_by("created_at")
    chatter_clips = clips.filter(creator = chatter)
    
    chatter_msg_count = chatter_messages.count()
    chatter_clip_count = chatter_clips.count()
    
    chatter_clip_views = 0
    for clip in chatter_clips:
      chatter_clip_views += clip.view_count
    
    if chatter_msg_count > 0 or chatter_clip_count > 0:
      monthrecap.count_messages += chatter_msg_count
      monthrecap.count_clips += chatter_clip_count
      monthrecap.count_clip_views += chatter_clip_views
      monthrecap.count_chatters += 1
      
      try:
        chatter_recap = UserRecapData.objects.get(overall_recap = monthrecap, twitch_user = chatter)
      except UserRecapData.DoesNotExist:
        chatter_recap = UserRecapData(
          overall_recap = monthrecap,
          twitch_user = chatter
        )
        chatter_recap.save()
        
      chatter_recap.count_messages   = chatter_msg_count
      chatter_recap.count_clips      = chatter_clip_count
      chatter_recap.count_clip_views = chatter_clip_views
      
      firstmsg = chatter_messages.first()
      chatter_recap.first_message = "" if firstmsg is None else firstmsg.message
      
      for msg in chatter_messages:
        chatter_recap.count_seven   += get_mult_word_count(msg.message, ["itswill7", "itswillFreeTrial"])
        chatter_recap.count_pound   += get_mult_word_count(msg.message, ["itswillPound", "itswill4"])
        chatter_recap.count_etsmg   += get_word_count(msg.message, "itswillEndTheStreamMyGuy")
        chatter_recap.count_ksmg    += get_word_count(msg.message, "itswillKeepStreamingMyGuy")
        chatter_recap.count_sneak   += get_mult_word_count(msg.message, ["itswillSneak", "itswillFollow", "Sneak"])
        chatter_recap.count_sit     += get_word_count(msg.message, "itswillSit")
        chatter_recap.count_love    += get_mult_word_count(msg.message, ["itswillL", "hannLOVE", "peepoLove"])
        chatter_recap.count_pog     += get_mult_word_count(msg.message, ["Pog", "PogChamp", "POGGIES", "POGGERS", "itswillPog", "PagU", "PagMan"])
        chatter_recap.count_shoop   += get_word_count(msg.message, "ShoopDaWhoop")
        chatter_recap.count_mmylc   += get_word_count(msg.message, "MusicMakeYouLoseControl")
        chatter_recap.count_giggle  += get_mult_word_count(msg.message, ["x0r6ztGiggle", "willGiggle", "itswillGiggle"])
        chatter_recap.count_vvkool  += get_mult_word_count(msg.message, ["VVKool", "VVotate", "VVKoolMini"])
        chatter_recap.count_gasp    += get_mult_word_count(msg.message, ["D\\:", "hannD"])
        chatter_recap.count_monka   += get_mult_word_count(msg.message, ["monkaS", "monkaW", "monkaEyes", "monkaGun", "monkaSTEER", "monkaH"])
        chatter_recap.count_pogo    += get_mult_word_count(msg.message, ["PogO", "WeirdChamp", "itswillO", "itswillWeird", "WeirdPause"])
        chatter_recap.count_cum     += get_mult_word_count(msg.message, ["cum", "cumming", "cumb", "cummies", "cumshot"])
        chatter_recap.count_spin    += get_mult_word_count(msg.message, ["itswillSpin", "willSpin", "borpaSpin", "YourMom"])
        chatter_recap.count_chicken += get_word_count(msg.message, "chickenWalk")
        chatter_recap.count_sonic   += get_mult_word_count(msg.message, ["itsWillCoolSonic", "CoolSonic"])
        chatter_recap.count_lul     += get_mult_word_count(msg.message, ["LUL", "LULW", "OMEGALUL", "OMEGADANCE"])
        chatter_recap.count_stsmg   += get_word_count(msg.message, "StartTheStreamMyGuy")
        chatter_recap.count_dance   += get_mult_word_count(msg.message, ["itswillPls", "pepeD", "PepePls", "daemonDj", "willDJ", "nessiePls", "Happi", "GoodBoy", "SourPls"])
        chatter_recap.count_dankies += get_mult_word_count(msg.message, ["DANKIES", "HYPERS"])
      
      chatter_recap.save()
      
      monthrecap.count_seven   += chatter_recap.count_seven
      monthrecap.count_pound   += chatter_recap.count_pound
      monthrecap.count_etsmg   += chatter_recap.count_etsmg
      monthrecap.count_ksmg    += chatter_recap.count_ksmg
      monthrecap.count_sneak   += chatter_recap.count_sneak
      monthrecap.count_sit     += chatter_recap.count_sit
      monthrecap.count_love    += chatter_recap.count_love
      monthrecap.count_pog     += chatter_recap.count_pog
      monthrecap.count_shoop   += chatter_recap.count_shoop
      monthrecap.count_mmylc   += chatter_recap.count_mmylc
      monthrecap.count_giggle  += chatter_recap.count_giggle
      monthrecap.count_vvkool  += chatter_recap.count_vvkool
      monthrecap.count_gasp    += chatter_recap.count_gasp
      monthrecap.count_monka   += chatter_recap.count_monka
      monthrecap.count_pogo    += chatter_recap.count_pogo
      monthrecap.count_cum     += chatter_recap.count_cum
      monthrecap.count_spin    += chatter_recap.count_spin
      monthrecap.count_chicken += chatter_recap.count_chicken
      monthrecap.count_sonic   += chatter_recap.count_sonic
      monthrecap.count_lul     += chatter_recap.count_lul
      monthrecap.count_stsmg   += chatter_recap.count_stsmg
      monthrecap.count_dance   += chatter_recap.count_dance
      monthrecap.count_dankies += chatter_recap.count_dankies
      
  monthrecap.save()