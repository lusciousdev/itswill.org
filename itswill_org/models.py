from django.db import models
import django.contrib.admin as admin
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete
from django.dispatch import receiver
import datetime
import re
import typing
import json

from .util.timeutil import *

DEFAULT_DATETIME = datetime.datetime(1971, 1, 1, 0, 0, 1, tzinfo = datetime.timezone.utc)

# Create your models here.

class CountField(models.IntegerField):
  match_list : typing.List[str] = []
  match_regex : re.Pattern = None
  use_images : bool = True
  
  def __init__(self, match_list = [], emote_list = None, use_images = True, *args, **kwargs):
    self.match_list = match_list
    self.match_regex = re.compile(re.compile(fr"(?<![^\s_-]){'|'.join(self.match_list)}(?![^\s_-])", re.IGNORECASE))
    self.emote_list = self.match_list if emote_list is None else emote_list
    self.use_images = use_images
    
    super().__init__(*args, **kwargs)
    
  @property
  def non_db_attrs(self):
    return super().non_db_attrs + ("match_list", "match_regex", "use_matches_as_images")

class RecapDataMixin(models.Model):
  class Meta:
    abstract = True
  
  count_messages = models.IntegerField(verbose_name = "Messages sent:", default = 0)
  count_clips = models.IntegerField(verbose_name = "Clips created:", default = 0)
  count_clip_views = models.IntegerField(verbose_name = "Views on those clips:", default = 0)
  count_chatters = models.IntegerField(verbose_name = "Number of chatters:", default = 0)
  count_videos = models.IntegerField(verbose_name = "Number of videos:", default = 0)
  
  first_message = models.CharField(verbose_name = "First message:", max_length = 1024, default = "")
  
  count_seven   = CountField(match_list = ["itswill7", "itswillFreeTrial"], default = 0)
  count_pound   = CountField(match_list = ["itswillPound", "itswill4"], default = 0)
  count_love    = CountField(match_list = ["itswillL", "hannLOVE", "peepoLove", "itswillLove"], default = 0)
  count_sad     = CountField(match_list = ["itswillSad", "Sadge", "widepeepoSad", "hannSadge", "peepoSad"], default = 0)
  count_mad     = CountField(match_list = ["UltraMad", "ReallyGun", "MadgeLate"], default = 0)
  
  count_etsmg   = CountField(match_list = ["itswillEndTheStreamMyGuy"], default = 0)
  count_ksmg    = CountField(match_list = ["itswillEndTheStreamMyGuy"], default = 0)
  count_stsmg   = CountField(match_list = ["itswillKeepStreamingMyGuy"], default = 0)
  
  count_pog     = CountField(match_list = ["Pog", "PogChamp", "POGGIES", "POGGERS", "itswillPog", "PagU", "PagMan"], emote_list = ["Pog", "PogChamp", "POGCHAMP2", "POGGIES", "POGGERS", "itswillPog", "PagU", "PagMan"], default = 0)
  count_shoop   = CountField(match_list = ["ShoopDaWhoop"], default = 0)
  count_gasp    = CountField(match_list = ["D\\:", "hannD"], emote_list = ["GASP", "hannD"], default = 0)
  count_pogo    = CountField(match_list = ["PogO", "WeirdChamp", "itswillO", "itswillWeird", "WeirdPause", "UHM"], default = 0)
  count_monka   = CountField(match_list = ["monkaS", "monkaW", "monkaEyes", "monkaGun", "monkaSTEER", "monkaH", "MONKA"], default = 0)
  
  count_ijbol   = CountField(match_list = ["IJBOL"], default = 0)
  count_lmao    = CountField(match_list = ["LMAO"], default = 0)
  count_hehe    = CountField(match_list = ["hehe"], default = 0)
  count_giggle  = CountField(match_list = ["x0r6ztGiggle", "willGiggle", "itswillGiggle"], default = 0)
  count_lul     = CountField(match_list = ["LUL", "LULW", "OMEGALUL", "OMEGADANCE", "OMEGALULftCloudWizard"], default = 0)
  
  count_sneak   = CountField(match_list = ["itswillSneak", "itswillFollow", "Sneak"], default = 0)
  count_sit     = CountField(match_list = ["itswillSit"], default = 0)
  
  count_sludge  = CountField(match_list = ["SLUDGE"], default = 0)
  count_gludge  = CountField(match_list = ["GLUDGE"], default = 0)
  
  count_mmylc   = CountField(match_list = ["MusicMakeYouLoseControl"], default = 0)
  count_nessie  = CountField(match_list = ["nessiePls"], default = 0)
  count_happi   = CountField(match_list = ["Happi"], default = 0)
  count_goodboy = CountField(match_list = ["GoodBoy"], default = 0)
  count_dance   = CountField(match_list = ["itswillPls", "pepeD", "PepePls", "daemonDj", "willDJ", "SourPls"], default = 0)
  count_vvkool  = CountField(match_list = ["VVKool", "VVotate", "VVKoolMini"], default = 0)
  
  count_spin    = CountField(match_list = ["itswillSpin", "willSpin", "borpaSpin", "YourMom"], default = 0)
  count_chicken = CountField(match_list = ["chickenWalk"], default = 0)
  count_sonic   = CountField(match_list = ["itsWillCoolSonic", "CoolSonic"], emote_list = ["CoolSonic"], default = 0)
  count_chedda  = CountField(match_list = ["MrChedda"], default = 0)
  count_glorp   = CountField(match_list = ["glorp"], default = 0)
  count_wlorp   = CountField(match_list = ["Wlorp"], default = 0)
  count_joel    = CountField(match_list = ["Joel", "EvilJoel", "Joelver", "Jlorp"], default = 0)
  count_cinema  = CountField(match_list = ["Cinema", "Cheddama"], default = 0)
  count_lift    = CountField(match_list = ["antLift", "WillLift"], default = 0)
  count_dankies = CountField(match_list = ["DANKIES", "HYPERS"], default = 0)
  
  count_cum     = CountField(match_list = ["cum", "cumming", "cumb", "cummies", "cumshot"], use_images = False, verbose_name = "Number of cum mentions:", default = 0)
  
  def zero(self, exclude = [], save = True):
    for f in self._meta.get_fields():
      if (f.get_internal_type() == "IntegerField") and (f.name not in exclude):
        setattr(self, f.name, 0)
    
    if save:
      self.save()
  
  def add(self, other_recap : "RecapDataMixin", exclude = [], save = True):
    for f in self._meta.get_fields():
      if (f.get_internal_type() == "IntegerField") and (f.name not in exclude):
        setattr(self, f.name, getattr(self, f.name) + getattr(other_recap, f.name));
    
    if save:
      self.save()
    
  def process_message(self, message : str, save = True):
    self.count_messages += 1
    
    for f in self._meta.get_fields():
      if (type(f) == CountField):
        setattr(self, f.name, getattr(self, f.name) + len(f.match_regex.findall(message)))
    
    if save:
      self.save()
  
class OverallRecapData(RecapDataMixin):
  year = models.IntegerField(default = 1971)
  month = models.IntegerField(default = 1)
  
  leaderboards = models.JSONField(default = dict)
  
  class Meta:
    unique_together = ('year', 'month')
    
  def zero(self, exclude = ["year", "month"]):
    super().zero(exclude)
  
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
    
class UserRecapData(RecapDataMixin):
  overall_recap = models.ForeignKey(OverallRecapData, on_delete = models.CASCADE)
  twitch_user = models.ForeignKey(TwitchUser, on_delete = models.DO_NOTHING)
  
  class Meta:
    unique_together = ('overall_recap', 'twitch_user')
  
class ChatMessage(models.Model):
  commenter = models.ForeignKey(TwitchUser, on_delete = models.CASCADE)
  
  message_id = models.CharField(max_length = 255, primary_key = True, editable = False)
  content_offset = models.IntegerField(default = 0)
  created_at = models.DateTimeField("created at", default = DEFAULT_DATETIME)
  message = models.CharField(max_length = 1024, default = "")
  
  class Meta:
    ordering = ( "created_at", )
  
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
  
  class Meta:
    ordering = ( "view_count", )

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
  
  class Meta:
    ordering = ( "created_at", )
  
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
  
  class Meta:
    ordering = ( "date", "name", )
  
  def __str__(self):
    return self.name
  
  def killcount_str(self):
    kcstr = f"{self.killcount:,} {self.kill_term}" + ("" if self.killcount < 1 else self.kill_term_pluralize)
    
    if self.secondary_killcount_needed:
      kcstr += f", {self.secondary_killcount:,} {self.secondary_kill_term}" + ("" if self.secondary_killcount < 1 else self.secondary_kill_term_pluralize)
      
    return kcstr
  
class CopyPasteGroup(models.Model):
  title = models.CharField(max_length = 255, unique = True)
  description = models.TextField(blank = True)
  
class CopyPaste(models.Model):
  group = models.ForeignKey(CopyPasteGroup, on_delete = models.CASCADE)
  
  title = models.CharField(max_length = 256, blank = True)
  text = models.TextField(blank = True)
  
class CopyPasteInline(admin.TabularInline):
  model = CopyPaste
  extra = 1
  
class CopyPasteGroupAdmin(admin.ModelAdmin):
  list_display = ('title', )
  search_fields = ['title', 'description']
  inlines = ( CopyPasteInline, )
  ordering = ( 'title', )
  
class Ascii(models.Model):
  title = models.CharField(max_length = 255, unique = True)
  text = models.TextField()
  
  is_garf = models.BooleanField(default = False)
  
  def __str__(self):
    return self.title
  
class AsciiAdmin(admin.ModelAdmin):
  list_display = ('title', )
  search_fields = ['title']
  ordering = ( 'title', )