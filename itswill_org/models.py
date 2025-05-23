from django.db import models
import django.contrib.admin as admin
import datetime
import re
import typing
import luscioustwitch

from .util.timeutil import *

DEFAULT_DATETIME = datetime.datetime(1971, 1, 1, 0, 0, 1, tzinfo = datetime.timezone.utc)
ASCII_REGEX = re.compile(r'[\u2800-\u28ff \r\n]{10,}')

# Create your models here.

class StatField(models.IntegerField):
  show_recap : bool = True
  show_leaderboard : bool = True
  short_name : str = ""
  unit : str = ""
  
  def __init__(self, short_name = "", show_recap = True, show_leaderboard = True, unit : str = "", *args, **kwargs):
    self.short_name = short_name
    self.show_recap = show_recap
    self.show_leaderboard = show_leaderboard
    self.unit = unit
    
    super().__init__(*args, **kwargs)
    
  @property
  def non_db_attrs(self):
    return super().non_db_attrs + ("show_recap", "show_leaderboard")
    
class BigStatField(models.BigIntegerField):
  show_recap : bool = True
  show_leaderboard : bool = True
  short_name : str = ""
  unit : str = ""
  
  def __init__(self, short_name = "", show_recap = True, show_leaderboard = True, unit : str = "", *args, **kwargs):
    self.short_name = short_name
    self.show_recap = show_recap
    self.show_leaderboard = show_leaderboard
    self.unit = unit
    
    super().__init__(*args, **kwargs)
    
  @property
  def non_db_attrs(self):
    return super().non_db_attrs + ("show_recap", "show_leaderboard")
    
class StringCountField(StatField):
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
    return super().non_db_attrs + ("match_list", "match_regex", "use_images", "show_recap")

class RecapDataMixin(models.Model):
  class Meta:
    abstract = True
  
  count_messages = StatField(short_name = "messages", verbose_name = "Messages sent:", default = 0)
  count_characters = BigStatField(short_name = "characters", show_recap = False, show_leaderboard = True, verbose_name = "Characters typed:", unit = "chatter", default = 0)
  count_clips = StatField(short_name = "clips", verbose_name = "Clips created:", unit = "clip", default = 0)
  count_clip_watch = BigStatField(short_name = "watchtime", show_recap = False, show_leaderboard = False, verbose_name = "Clip watch time:", unit = "second", default = 0)
  count_clip_views = StatField(short_name = "views", verbose_name = "Clip views:", unit = "clip view", default = 0)
  count_ascii = StatField(short_name = "ascii", verbose_name = "ASCIIs sent:", unit = "ASCII", default = 0)
  count_chatters = StatField(short_name = "chatters", verbose_name = "Number of chatters:", unit = "chatter", default = 0)
  count_videos = StatField(short_name = "videos", verbose_name = "Number of videos:", unit = "video", default = 0)
  
  first_message = models.CharField(verbose_name = "First message:", max_length = 1024, default = "")
  last_message = models.CharField(verbose_name = "Last message:", max_length = 1024, default = "")
  
  count_seven   = StringCountField(short_name = "seven", match_list = ["itswill7", "itswillFreeTrial"], unit = "itswill7", default = 0)
  count_pound   = StringCountField(short_name = "pound", match_list = ["itswillPound", "itswill4"], unit = "pounder", default = 0)
  count_love    = StringCountField(short_name = "love", match_list = ["itswillL", "hannLOVE", "peepoLove", "itswillLove"], unit = "love emote", default = 0)
  count_sad     = StringCountField(short_name = "sad", match_list = ["itswillSad", "Sadge", "widepeepoSad", "hannSADGE", "peepoSad"], unit = "sad emote", default = 0)
  count_mad     = StringCountField(short_name = "mad", match_list = ["UltraMad", "ReallyGun", "MadgeLate"], unit = "mad emote", default = 0)
  
  count_etsmg   = StringCountField(short_name = "ETSMG", match_list = ["itswillEndTheStreamMyGuy"], unit = "itswillEndTheStreamMyGuy", default = 0)
  count_ksmg    = StringCountField(short_name = "KSMG", match_list = ["itswillKeepStreamingMyGuy"], unit = "itswillKeepStreamingMyGuy", default = 0)
  count_stsmg   = StringCountField(short_name = "STSMG", match_list = ["StartTheStreamMyGuy"], unit = "StartTheStreamMyGuy", default = 0)
  
  count_pog     = StringCountField(short_name = "pog", match_list = ["Pog", "PogChamp", "POGGIES", "POGGERS", "itswillPog", "PagU", "PagMan"], unit = "Pog", emote_list = ["Pog", "PogChamp", "POGCHAMP2", "POGGIES", "POGGERS", "itswillPog", "PagU", "PagMan"], default = 0)
  count_goop    = StringCountField(short_name = "gooper", match_list = ["GooperGang"], unit = "GooperGang", default = 0)
  count_bork    = StringCountField(short_name = "bork", match_list = ["hannBORK", "hannAAAA"], unit = "hannBORK", default = 0)
  count_shoop   = StringCountField(short_name = "shoop", match_list = ["ShoopDaWhoop"], unit = "ShoopDaWhoop", default = 0)
  count_gasp    = StringCountField(short_name = "gasp", match_list = ["D\\:", "hannD"], emote_list = ["GASP", "hannD"], unit = "gasp emote", default = 0)
  count_what    = StringCountField(short_name = "what", match_list = ["WHAT"], unit = "WHAT", default = 0)
  count_pogo    = StringCountField(short_name = "pogo", match_list = ["PogO", "WeirdChamp", "itswillO", "itswillWeird", "WeirdPause", "UHM"], unit = "weird emote", default = 0)
  count_monka   = StringCountField(short_name = "monka", match_list = ["monkaS", "monkaW", "monkaEyes", "monkaGun", "monkaSTEER", "monkaH"], unit = "monka", default = 0)
  count_monka2  = StringCountField(short_name = "eek", match_list = ["MONKA", "EEK"], unit = "EEK", default = 0)
  
  count_ijbol   = StringCountField(short_name = "IJBOL", match_list = ["IJBOL"], unit = "IJBOL", default = 0)
  count_lmao    = StringCountField(short_name = "lmao", match_list = ["LMAO"], unit = "LMAO", default = 0)
  count_hehe    = StringCountField(short_name = "hehe", match_list = ["hehe"], unit = "hehe", default = 0)
  count_giggle  = StringCountField(short_name = "giggle", match_list = ["x0r6ztGiggle", "willGiggle", "itswillGiggle"], unit = "giggle", default = 0)
  count_lul     = StringCountField(short_name = "lul", match_list = ["LUL", "LULW", "OMEGALUL", "OMEGADANCE", "OMEGALULftCloudWizard"], unit = "LUL", default = 0)
  
  count_first   = StringCountField(short_name = "chatter", match_list = ["FirstTimeChadder", "FirstTimeChedda", "LastTimeChatter"], unit = "first time chatter emote", default = 0)
  
  count_sneak   = StringCountField(short_name = "sneak", match_list = ["itswillSneak", "itswillFollow", "Sneak"], unit = "sneak emote", default = 0)
  count_sit     = StringCountField(short_name = "sit", match_list = ["itswillSit"], unit = "itswillSit", default = 0)
  
  count_sludge  = StringCountField(short_name = "sludge", match_list = ["SLUDGE"], unit = "SLUDGE", default = 0)
  count_gludge  = StringCountField(short_name = "gludge", match_list = ["GLUDGE"], unit = "GLUDGE", default = 0)
  
  count_mmylc   = StringCountField(short_name = "MMYLC", match_list = ["MusicMakeYouLoseControl"], unit = "MusicMakeYouLoseControl", default = 0)
  count_nessie  = StringCountField(short_name = "nessie", match_list = ["nessiePls"], unit = "nessie", default = 0)
  count_happi   = StringCountField(short_name = "happi", match_list = ["Happi"], unit = "Happi", default = 0)
  count_goodboy = StringCountField(short_name = "goodboy", match_list = ["GoodBoy"], unit = "GoodBoy", default = 0)
  count_dance   = StringCountField(short_name = "dance", match_list = ["itswillPls", "pepeD", "PepePls", "daemonDj", "willDJ", "SourPls"], unit = "dance emote", default = 0)
  count_vvkool  = StringCountField(short_name = "vvkool", match_list = ["VVKool", "VVotate", "VVKoolMini"], unit = "VVKool", default = 0)
  
  count_spin    = StringCountField(short_name = "spin", match_list = ["itswillSpin", "willSpin", "borpaSpin", "YourMom"], unit = "spin emote", default = 0)
  count_burger  = StringCountField(short_name = "burger", match_list = ["BURGER"], unit = "BURGER", default = 0)
  count_chicken = StringCountField(short_name = "chicken", match_list = ["chickenWalk"], unit = "chickenWalk", default = 0)
  count_sonic   = StringCountField(short_name = "sonic", match_list = ["itsWillCoolSonic", "CoolSonic"], emote_list = ["CoolSonic"], unit = "CoolSonic", default = 0)
  count_chedda  = StringCountField(short_name = "chedda", match_list = ["MrChedda"], unit = "MrChedda", default = 0)
  count_glorp   = StringCountField(short_name = "glorp", match_list = ["glorp"], unit = "glorp", default = 0)
  count_wlorp   = StringCountField(short_name = "wlorp", match_list = ["Wlorp"], unit = "Wlorp", default = 0)
  count_kirb    = StringCountField(short_name = "kirb", match_list = ["Kirbeter"], unit = "Kirbeter", default = 0)
  count_goose   = StringCountField(short_name = "goose", match_list = ["GriddyGoose", "GriddyCrow"], unit = "griddy emote", default = 0)
  count_joel    = StringCountField(short_name = "joel", match_list = ["Joel", "EvilJoel", "Joelver", "jlorp"], unit = "Joel emote", default = 0)
  count_cinema  = StringCountField(short_name = "cinema", match_list = ["Cinema", "Cheddama", "Willema"], unit = "cinema emote", default = 0)
  count_lift    = StringCountField(short_name = "lift", match_list = ["antLift", "WillLift"], unit = "lift emote", default = 0)
  count_dankies = StringCountField(short_name = "dankies", match_list = ["DANKIES", "HYPERS"], unit = "DANKIES & HYPERS", default = 0)
  
  count_cum     = StringCountField(short_name = "cum", match_list = ["cum", "cumming", "cumb", "cummies", "cumshot"], unit = "cum mention", use_images = False, verbose_name = "Number of cum mentions:", default = 0)
  
  count_caw     = StringCountField(short_name = "caw", match_list = ["caw"], use_images = False, show_recap = True, show_leaderboard = True, verbose_name = "CAW:", unit = "CAW", default = 0)
  count_400     = StringCountField(short_name = "400k", match_list = ["400k"], use_images = False, show_recap = False, show_leaderboard = False, verbose_name = "400k:", unit = "400k", default = 0)
  count_plus1   = StringCountField(short_name = "plusone", match_list = ["+1"], use_images = False, show_recap = False, show_leaderboard = False, verbose_name = "+1:", unit = "+1", default = 0)
  count_at_bot  = StringCountField(short_name = "bot", match_list = ["@itswillChat"], use_images = False, show_recap = True, show_leaderboard = True, verbose_name = "Replies to itswillChat:", unit = "@itswillChat", default = 0)
  count_yt      = StringCountField(short_name = "youtube", match_list = ["(https://)?(www\\.)?youtube.com[/A-Za-z0-9_\\-=]+", "(https://)?(www\\.)?youtu.be[/A-Za-z0-9_\\-=\\?]+"], use_images = False, show_recap = False, show_leaderboard = False, verbose_name = "YouTube links:", unit = "YouTube link", default = 0)
  count_q       = StringCountField(short_name = "questions", match_list = ["^\\?+$"], use_images = False, show_recap = True, show_leaderboard = True, verbose_name = "???:", unit = "question mark message", default = 0)
  
  def zero(self, exclude = [], save = True):
    for f in self._meta.get_fields():
      if (f.get_internal_type() == "IntegerField" or f.get_internal_type() == "BigIntegerField") and (f.name not in exclude):
        setattr(self, f.name, 0)
    
    if save:
      self.save()
  
  def add(self, other_recap : "RecapDataMixin", exclude = [], save = True):
    for f in self._meta.get_fields():
      if (f.get_internal_type() == "IntegerField" or f.get_internal_type() == "BigIntegerField") and (f.name not in exclude):
        setattr(self, f.name, getattr(self, f.name) + getattr(other_recap, f.name))
    
    if save:
      self.save()
    
  def process_message(self, message : str, save = True):
    self.count_messages += 1
    self.count_characters += len(message)
    
    if len(message) > 200 and len(ASCII_REGEX.findall(message)) > 0:
      self.count_ascii += 1
    
    for f in self._meta.get_fields():
      if (type(f) == StringCountField):
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
  
  is_bot = models.BooleanField(default = False)
  
  class Meta:
    indexes = [
      models.Index(fields = [ "login", ]),
      models.Index(fields = [ "created_at", ]),
    ]
  
  def to_json(self):
    return {
      "user_id": self.user_id,
      "login": self.login,
      "display_name": self.display_name,
      "user_type": self.user_type,
      "broadcaster_type": self.broadcaster_type,
      "description": self.description,
      "profile_image_url": self.profile_image_url,
      "offline_image_url": self.offline_image_url,
      "created_at": self.created_at.astimezone(TIMEZONE).strftime(luscioustwitch.TWITCH_API_TIME_FORMAT),
    }
    
class UserRecapData(RecapDataMixin):
  overall_recap = models.ForeignKey(OverallRecapData, on_delete = models.CASCADE)
  twitch_user = models.ForeignKey(TwitchUser, on_delete = models.DO_NOTHING)
  
  class Meta:
    unique_together = ('overall_recap', 'twitch_user')

class WrappedDataMixin(models.Model):
  class Meta:
    abstract = True
  
  typing_time = models.CharField(max_length = 255, default = "0 seconds")
  clip_watch_time = models.CharField(max_length = 255, default = "0 seconds")
  
  jackass_count = models.IntegerField(default = 0)
  
  extra_data = models.JSONField(default = dict)
    
class OverallWrappedData(WrappedDataMixin):
  year = models.IntegerField(default = 1971)
  
  recap = models.ForeignKey(OverallRecapData, on_delete=models.CASCADE, null = True, blank = True)
  
  class Meta:
    unique_together = ('year', )
    
class UserWrappedData(WrappedDataMixin):
  overall_wrapped = models.ForeignKey(OverallWrappedData, on_delete = models.CASCADE)
  twitch_user = models.ForeignKey(TwitchUser, on_delete = models.CASCADE)
  
  recap = models.ForeignKey(UserRecapData, on_delete=models.CASCADE, null = True, blank = True)
  
  class Meta:
    unique_together = ('overall_wrapped', 'twitch_user')
  
class ChatMessage(models.Model):
  id = models.AutoField(primary_key = True, serialize = False)
  
  commenter = models.ForeignKey(TwitchUser, on_delete = models.CASCADE)
  message_id = models.CharField(max_length = 255, editable = False)
  content_offset = models.IntegerField(default = 0)
  created_at = models.DateTimeField("created at", default = DEFAULT_DATETIME)
  message = models.CharField(max_length = 1024, default = "")
  
  class Meta:
    ordering = ( "created_at", )
    indexes = [
      models.Index(fields = ["created_at", ]),
    ]
  
  def __str__(self):
    timestr = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
    
    return f"[{timestr}] {self.commenter.display_name}: {self.message}"
  
  def localtz_str(self, localtz = TIMEZONE):
    local_created_at = utc_to_local(self.created_at, localtz)
    timestr = local_created_at.strftime("%Y-%m-%d %H:%M:%S")
    
    return f"[{timestr}] {self.commenter.display_name}: {self.message}"
  
  def to_json(self):
    return {
      "commenter": self.commenter.to_json(),
      "content_offset": self.content_offset,
      "created_at": self.created_at.astimezone(TIMEZONE).strftime(luscioustwitch.TWITCH_API_TIME_FORMAT),
      "message": self.message,
    }
  
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
    indexes = [
      models.Index(fields = [ "created_at", ]),
      models.Index(fields = [ "view_count", ]),
    ]
    
  def to_json(self):
    return {
      "clip_id": self.clip_id,
      "creator": self.creator.to_json(),
      "url": self.url,
      "embed_url": self.embed_url,
      "broadcaster_id": self.broadcaster_id,
      "broadcaster_name": self.broadcaster_name,
      "video_id": self.video_id,
      "game_id": self.game_id,
      "language": self.language,
      "title": self.title,
      "view_count": self.view_count,
      "created_at": self.created_at.astimezone(TIMEZONE).strftime(luscioustwitch.TWITCH_API_TIME_FORMAT),
      "thumbnail_url": self.thumbnail_url,
      "duration": self.duration,
      "vod_offset": self.vod_offset,
    }

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
    indexes = [
      models.Index(fields = [ "created_at", ]),
      models.Index(fields = [ "view_count", ]),
    ]
  
class Pet(models.Model):
  acquired = models.BooleanField(default = True)
  
  image = models.FileField(upload_to="petimg/", blank = True)
  name = models.CharField(max_length = 255, default = "")
  
  killcount_known = models.BooleanField(default = True)
  killcount = models.IntegerField(default = 0)
  drop_rate_known = models.BooleanField(default = False)
  drop_rate = models.IntegerField(default = 0)
  kill_term = models.CharField(max_length = 255, default = "killcount")
  kill_term_pluralize = models.CharField(max_length = 255, default = "", blank = True)
  
  secondary_killcount_needed = models.BooleanField(default = False)
  secondary_killcount = models.IntegerField(default = 0)
  secondary_drop_rate_known = models.BooleanField(default = False)
  secondary_drop_rate = models.IntegerField(default = 0)
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
  
class LetterboxdReview(models.Model):
  title = models.CharField(max_length = 255)
  review_id = models.CharField(max_length = 255)
  link = models.CharField(max_length = 255)
  pub_date = models.DateTimeField()
  watched_date = models.DateField()
  film_title = models.CharField(max_length = 255)
  film_year = models.IntegerField(null = True)
  member_rating = models.FloatField(null = True)
  movie_id = models.IntegerField(null = True)
  description = models.TextField()
  creator = models.CharField(max_length = 255)
  
  class Meta:
    unique_together = ('review_id', )
    ordering = ( "pub_date", )
    indexes = [
      models.Index(fields = ["pub_date", ]),
      models.Index(fields = ["watched_date", ]),
      models.Index(fields = ["member_rating", ]),
    ]
    
class Census(models.Model):
  date = models.DateField()
  respondents = models.IntegerField()
  raw_results = models.JSONField()
  chart_data = models.JSONField()