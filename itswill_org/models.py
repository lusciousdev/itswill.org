from django.db import models
import datetime

from .util.timeutil import *

DEFAULT_DATETIME = datetime.datetime(1971, 1, 1, 0, 0, 1, tzinfo = datetime.timezone.utc)

# Create your models here.
  
class OverallRecapData(models.Model):
  year = models.IntegerField(default = 1971)
  month = models.IntegerField(default = 1)
  
  count_messages = models.IntegerField(default = 0)
  count_clips = models.IntegerField(default = 0)
  count_clip_views = models.IntegerField(default = 0)
  count_chatters = models.IntegerField(default = 0)
  count_videos = models.IntegerField(default = 0)
  
  first_message = models.CharField(max_length = 1024, default = "")
  
  count_seven   = models.IntegerField(default = 0)
  count_pound   = models.IntegerField(default = 0)
  count_love    = models.IntegerField(default = 0)
  
  count_etsmg   = models.IntegerField(default = 0)
  count_ksmg    = models.IntegerField(default = 0)
  count_stsmg   = models.IntegerField(default = 0)
  
  count_pog     = models.IntegerField(default = 0)
  count_shoop   = models.IntegerField(default = 0)
  count_gasp    = models.IntegerField(default = 0)
  count_pogo    = models.IntegerField(default = 0)
  count_monka   = models.IntegerField(default = 0)
  
  count_giggle  = models.IntegerField(default = 0)
  count_lul     = models.IntegerField(default = 0)
  
  count_sneak   = models.IntegerField(default = 0)
  count_sit     = models.IntegerField(default = 0)
  
  count_mmylc   = models.IntegerField(default = 0)
  count_dance   = models.IntegerField(default = 0)
  count_vvkool  = models.IntegerField(default = 0)
  
  count_spin    = models.IntegerField(default = 0)
  count_chicken = models.IntegerField(default = 0)
  count_sonic   = models.IntegerField(default = 0)
  count_dankies = models.IntegerField(default = 0)
  
  count_cum     = models.IntegerField(default = 0)
  
  def zero(self):
    self.count_messages   = 0
    self.count_clips      = 0
    self.count_clip_views = 0
    self.count_chatters   = 0
    self.count_videos     = 0
    
    self.count_seven   = 0
    self.count_pound   = 0
    self.count_love    = 0
    
    self.count_etsmg   = 0
    self.count_ksmg    = 0
    self.count_stsmg   = 0
    
    self.count_pog     = 0
    self.count_shoop   = 0
    self.count_gasp    = 0
    self.count_pogo    = 0
    self.count_monka   = 0
    
    self.count_giggle  = 0
    self.count_lul     = 0
    
    self.count_sneak   = 0
    self.count_sit     = 0
    
    self.count_mmylc   = 0
    self.count_dance   = 0
    self.count_vvkool  = 0
    
    self.count_spin    = 0
    self.count_chicken = 0
    self.count_sonic   = 0
    self.count_dankies = 0
    
    self.count_cum     = 0
    
    self.save()
  
  def add(self, other_recap : "OverallRecapData"):
    self.count_messages   += other_recap.count_messages
    self.count_clips      += other_recap.count_clips
    self.count_clip_views += other_recap.count_clip_views
    self.count_chatters   += other_recap.count_chatters
    self.count_videos     += other_recap.count_videos
    
    self.count_seven   += other_recap.count_seven
    self.count_pound   += other_recap.count_pound
    self.count_love    += other_recap.count_love
    
    self.count_etsmg   += other_recap.count_etsmg
    self.count_ksmg    += other_recap.count_ksmg
    self.count_stsmg   += other_recap.count_stsmg
    
    self.count_pog     += other_recap.count_pog
    self.count_shoop   += other_recap.count_shoop
    self.count_gasp    += other_recap.count_gasp
    self.count_pogo    += other_recap.count_pogo
    self.count_monka   += other_recap.count_monka
    
    self.count_giggle  += other_recap.count_giggle
    self.count_lul     += other_recap.count_lul
    
    self.count_sneak   += other_recap.count_sneak
    self.count_sit     += other_recap.count_sit
    
    self.count_mmylc   += other_recap.count_mmylc
    self.count_dance   += other_recap.count_dance
    self.count_vvkool  += other_recap.count_vvkool
    
    self.count_spin    += other_recap.count_spin
    self.count_chicken += other_recap.count_chicken
    self.count_sonic   += other_recap.count_sonic
    self.count_dankies += other_recap.count_dankies
    
    self.count_cum     += other_recap.count_cum
    
    self.save()
  
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
    
class UserRecapData(models.Model):
  overall_recap = models.ForeignKey(OverallRecapData, on_delete = models.CASCADE)
  twitch_user = models.ForeignKey(TwitchUser, on_delete = models.DO_NOTHING)
  
  count_messages   = models.IntegerField(default = 0)
  count_clips      = models.IntegerField(default = 0)
  count_clip_views = models.IntegerField(default = 0)
  
  first_message = models.CharField(max_length = 1024, default = "")
  
  count_seven   = models.IntegerField(default = 0)
  count_pound   = models.IntegerField(default = 0)
  count_love    = models.IntegerField(default = 0)
  
  count_etsmg   = models.IntegerField(default = 0)
  count_ksmg    = models.IntegerField(default = 0)
  count_stsmg   = models.IntegerField(default = 0)
  
  count_pog     = models.IntegerField(default = 0)
  count_shoop   = models.IntegerField(default = 0)
  count_gasp    = models.IntegerField(default = 0)
  count_pogo    = models.IntegerField(default = 0)
  count_monka   = models.IntegerField(default = 0)
  
  count_giggle  = models.IntegerField(default = 0)
  count_lul     = models.IntegerField(default = 0)
  
  count_sneak   = models.IntegerField(default = 0)
  count_sit     = models.IntegerField(default = 0)
  
  count_mmylc   = models.IntegerField(default = 0)
  count_dance   = models.IntegerField(default = 0)
  count_vvkool  = models.IntegerField(default = 0)
  
  count_spin    = models.IntegerField(default = 0)
  count_chicken = models.IntegerField(default = 0)
  count_sonic   = models.IntegerField(default = 0)
  count_dankies = models.IntegerField(default = 0)
  
  count_cum     = models.IntegerField(default = 0)
  
  def zero(self):
    self.count_messages   = 0
    self.count_clips      = 0
    self.count_clip_views = 0
    
    self.count_seven   = 0
    self.count_pound   = 0
    self.count_love    = 0
    
    self.count_etsmg   = 0
    self.count_ksmg    = 0
    self.count_stsmg   = 0
    
    self.count_pog     = 0
    self.count_shoop   = 0
    self.count_gasp    = 0
    self.count_pogo    = 0
    self.count_monka   = 0
    
    self.count_giggle  = 0
    self.count_lul     = 0
    
    self.count_sneak   = 0
    self.count_sit     = 0
    
    self.count_mmylc   = 0
    self.count_dance   = 0
    self.count_vvkool  = 0
    
    self.count_spin    = 0
    self.count_chicken = 0
    self.count_sonic   = 0
    self.count_dankies = 0
    
    self.count_cum     = 0
    
    self.save()
  
  def add(self, other_recap : "UserRecapData"):
    self.count_messages   += other_recap.count_messages
    self.count_clips      += other_recap.count_clips
    self.count_clip_views += other_recap.count_clip_views
    
    self.count_seven   += other_recap.count_seven
    self.count_pound   += other_recap.count_pound
    self.count_love    += other_recap.count_love
    
    self.count_etsmg   += other_recap.count_etsmg
    self.count_ksmg    += other_recap.count_ksmg
    self.count_stsmg   += other_recap.count_stsmg
    
    self.count_pog     += other_recap.count_pog
    self.count_shoop   += other_recap.count_shoop
    self.count_gasp    += other_recap.count_gasp
    self.count_pogo    += other_recap.count_pogo
    self.count_monka   += other_recap.count_monka
    
    self.count_giggle  += other_recap.count_giggle
    self.count_lul     += other_recap.count_lul
    
    self.count_sneak   += other_recap.count_sneak
    self.count_sit     += other_recap.count_sit
    
    self.count_mmylc   += other_recap.count_mmylc
    self.count_dance   += other_recap.count_dance
    self.count_vvkool  += other_recap.count_vvkool
    
    self.count_spin    += other_recap.count_spin
    self.count_chicken += other_recap.count_chicken
    self.count_sonic   += other_recap.count_sonic
    self.count_dankies += other_recap.count_dankies
    
    self.count_cum     += other_recap.count_cum
    
    self.save()
  
  class Meta:
    unique_together = ('overall_recap', 'twitch_user')
  
  
class ChatMessage(models.Model):
  commenter = models.ForeignKey(TwitchUser, on_delete = models.CASCADE)
  
  message_id = models.CharField(max_length = 255, primary_key = True, editable = False)
  content_offset = models.IntegerField(default = 0)
  created_at = models.DateTimeField("created at", default = DEFAULT_DATETIME)
  message = models.CharField(max_length = 1024, default = "")
  
  def __str__(self):
    timestr = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
    
    return f"[{timestr}] {self.commenter.display_name}: {self.message}"
  
  def localtz_str(self, localtz = TIMEZONE):
    local_created_at = utc_to_local(self.created_at, localtz)
    timestr = local_created_at.strftime("%Y-%m-%d %H:%M:%S")
    
    return f"[{timestr}] {self.commenter.display_name}: {self.message}"
  
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
  
  def killcount_str(self):
    kcstr = f"{self.killcount:,} {self.kill_term}" + ("" if self.killcount < 1 else self.kill_term_pluralize)
    
    if self.secondary_killcount_needed:
      kcstr += f", {self.secondary_killcount:,} {self.secondary_kill_term}" + ("" if self.secondary_killcount < 1 else self.secondary_kill_term_pluralize)
      
    return kcstr