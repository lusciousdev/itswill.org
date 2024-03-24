from django.db import models
import datetime

DEFAULT_DATETIME = datetime.datetime(1971, 1, 1, 0, 0, 1, tzinfo = datetime.timezone.utc)

# Create your models here.
  
class MonthlyRecap(models.Model):
  year = models.IntegerField(default = 1971)
  month = models.IntegerField(default = 1)
  
  total_messages = models.IntegerField(default = 0)
  total_clips = models.IntegerField(default = 0)
  total_clip_views = models.IntegerField(default = 0)
  total_chatters = models.IntegerField(default = 0)
  total_videos = models.IntegerField(default = 0)
  
  class Meta:
    unique_together = ('year', 'month')
  
class TwitchUser(models.Model):
  user_id = models.IntegerField(primary_key = True, editable = False)
  
  login = models.CharField(max_length = 255, default = "missing username")
  display_name = models.CharField(max_length = 255, default = "missing display name")
  user_type = models.CharField(max_length = 255, default = "")
  broadcaster_type = models.CharField(max_length = 255, default = "")
  description = models.CharField(max_length = 512, default = "")
  profile_image_url = models.CharField(max_length = 512, default = "missing profile image url")
  offline_image_url = models.CharField(max_length = 512, default = "missing offline image url")
  created_at = models.DateTimeField("created at", default = DEFAULT_DATETIME)
    
class MonthlyUserData(models.Model):
  monthly_recap = models.ForeignKey(MonthlyRecap, on_delete = models.CASCADE)
  twitch_user = models.ForeignKey(TwitchUser, on_delete = models.DO_NOTHING)
  
  message_count = models.IntegerField(default = 0)
  clip_count = models.IntegerField(default = 0)
  clip_views = models.IntegerField(default = 0)
  
  class Meta:
    unique_together = ('monthly_recap', 'twitch_user')
  
  
class ChatMessage(models.Model):
  commenter = models.ForeignKey(TwitchUser, on_delete = models.CASCADE)
  
  message_id = models.CharField(max_length = 255, primary_key = True, editable = False)
  content_offset = models.IntegerField(default = 0)
  created_at = models.DateTimeField("created at", default = DEFAULT_DATETIME)
  message = models.TextField(default = "")
  
class Clip(models.Model):
  clip_id = models.CharField(max_length = 255, primary_key = True, editable = False)
  
  creator = models.ForeignKey(TwitchUser, on_delete = models.CASCADE)
  
  url = models.CharField(max_length = 512, default = "missing clip url")
  embed_url = models.CharField(max_length = 512, default = "missing embed url")
  broadcaster_id = models.IntegerField(default = -1)
  broadcaster_name = models.CharField(max_length = 64, default = "missing broadcaster name")
  video_id = models.CharField(max_length = 255, default = "")
  game_id = models.CharField(max_length = 255, default = "missing game id")
  language = models.CharField(max_length = 255, default = "en")
  title = models.CharField(max_length = 255, default = "missing clip title")
  view_count = models.IntegerField(default = 0)
  created_at = models.DateTimeField("created at", default = DEFAULT_DATETIME)
  thumbnail_url = models.CharField(max_length = 512, default = "missing thumbnail url")
  duration = models.FloatField(default = 0.0)
  vod_offset = models.IntegerField(default = 0)

class Video(models.Model):
  vod_id = models.CharField(max_length = 255, primary_key = True, editable = False)
  
  stream_id = models.CharField(max_length = 255, default = "")
  user_id = models.CharField(max_length = 255, default = "")
  user_login = models.CharField(max_length = 255, default = "")
  user_name = models.CharField(max_length = 255, default = "")
  title = models.CharField(max_length = 255, default = "")
  description = models.CharField(max_length = 512, default = "")
  created_at = models.DateTimeField("created at", default = datetime.datetime.now)
  published_at = models.DateTimeField("published at", default = datetime.datetime.now)
  url = models.CharField(max_length = 512, default = "")
  thumbnail_url = models.CharField(max_length = 255, default = "")
  viewable = models.CharField(max_length = 255, default = "")
  view_count = models.IntegerField(default = 0)
  language = models.CharField(max_length = 255, default = "")
  vod_type = models.CharField(max_length = 255, default = "")
  duration = models.CharField(max_length = 255, default = "")
  
class Pet(models.Model):
  acquired = models.BooleanField(default = True)
  
  image = models.FileField(upload_to="petimg/", blank = True)
  name = models.CharField(max_length = 255, default = "")
  
  killcount_known = models.BooleanField(default = True)
  killcount = models.IntegerField(default = 0)
  kill_term = models.CharField(max_length = 255, default = "killcount")
  kill_term_pluralize = models.CharField(max_length = 255, default = "", blank = True)
  
  secondary_killcount_needed = models.BooleanField(default = False)
  secondary_killcount = models.IntegerField(default = 0)
  secondary_kill_term = models.CharField(max_length = 255, default = "killcount")
  secondary_kill_term_pluralize = models.CharField(max_length = 255, default = "", blank = True)
  
  date_known = models.BooleanField(default = True)
  date = models.DateTimeField(default = datetime.datetime.now)
  
  clip_url = models.CharField(max_length = 512, default = "", blank = True)
  tweet_url = models.CharField(max_length = 512, default = "", blank = True)
  
  def __str__(self):
    return self.name