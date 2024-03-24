from django.conf import settings
from celery import Celery, shared_task
from celery.schedules import crontab
import luscioustwitch

import datetime
import pytz
import calendar

from .models import *

@shared_task
def calculate_monthly_stats(year, month):
  localtz = pytz.timezone("America/Los_Angeles")
  monthrange = calendar.monthrange(year, month)
  
  try:
    monthrecap = MonthlyRecap.objects.get(year = year, month = month)
  except MonthlyRecap.DoesNotExist:
    monthrecap = MonthlyRecap(year = year, month = month)
    monthrecap.save()
  
  start_date = datetime.datetime(year, month, 1, 0, 0, 0, 1, localtz)
  end_date = datetime.datetime(year, month, monthrange[1], 23, 59, 59, 999, localtz)
    
  chat_messages = ChatMessage.objects.filter(created_at__range = (start_date, end_date))
  clips = Clip.objects.filter(created_at__range = (start_date, end_date)).order_by("-view_count")
  videos = Video.objects.filter(created_at__range = (start_date, end_date))
  
  monthrecap.total_videos = videos.count()
  
  monthrecap.total_messages = 0
  monthrecap.total_clips = 0
  monthrecap.total_clip_views = 0
  monthrecap.total_chatters = 0
  
  for chatter in TwitchUser.objects.all():
    chatter_messages = chat_messages.filter(commenter = chatter)
    chatter_clips = clips.filter(creator = chatter)
    
    chatter_msg_count = chatter_messages.count()
    chatter_clip_count = chatter_clips.count()
    
    chatter_clip_views = 0
    for clip in chatter_clips:
      chatter_clip_views += clip.view_count
    
    if chatter_msg_count > 0 or chatter_clip_count > 0:
      monthrecap.total_messages += chatter_msg_count
      monthrecap.total_clips += chatter_clip_count
      monthrecap.total_clip_views += chatter_clip_views
      monthrecap.total_chatters += 1
      
      try:
        chatter_recap = MonthlyUserData.objects.get(monthly_recap = monthrecap, twitch_user = chatter)
        chatter_recap.message_count = chatter_msg_count
        chatter_recap.clip_count = chatter_clip_count
        chatter_recap.clip_views = chatter_clip_views
        chatter_recap.save()
      except MonthlyUserData.DoesNotExist:
        chatter_recap = MonthlyUserData(
          monthly_recap = monthrecap,
          twitch_user = chatter,
          message_count = chatter_msg_count,
          clip_count = chatter_clip_count,
          clip_views = chatter_clip_views,
        )
        chatter_recap.save()
        
  monthrecap.save()