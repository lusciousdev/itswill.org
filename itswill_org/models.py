import calendar
import datetime
import re
import typing

import django.contrib.admin as admin
import luscioustwitch
from django.db import models
from django.db.models import Count, F, Value
from django.utils import timezone

from .util.timeutil import *

DEFAULT_DATETIME = datetime.datetime(1971, 1, 1, 0, 0, 1, tzinfo=datetime.timezone.utc)
ASCII_REGEX = re.compile(r"[\u2800-\u28ff \r\n]{10,}")

# Create your models here.


class StatField(models.IntegerField):
    show_recap: bool = True
    show_leaderboard: bool = True
    short_name: str = ""
    unit: str = ""

    def __init__(
        self,
        short_name="",
        show_recap=True,
        show_leaderboard=True,
        unit: str = "",
        *args,
        **kwargs,
    ):
        self.short_name = short_name
        self.show_recap = show_recap
        self.show_leaderboard = show_leaderboard
        self.unit = unit

        super().__init__(*args, **kwargs)

    @property
    def non_db_attrs(self):
        return super().non_db_attrs + ("show_recap", "show_leaderboard")


class BigStatField(models.BigIntegerField):
    show_recap: bool = True
    show_leaderboard: bool = True
    short_name: str = ""
    unit: str = ""

    def __init__(
        self,
        short_name="",
        show_recap=True,
        show_leaderboard=True,
        unit: str = "",
        *args,
        **kwargs,
    ):
        self.short_name = short_name
        self.show_recap = show_recap
        self.show_leaderboard = show_leaderboard
        self.unit = unit

        super().__init__(*args, **kwargs)

    @property
    def non_db_attrs(self):
        return super().non_db_attrs + ("show_recap", "show_leaderboard")


class StringCountField(StatField):
    match_list: typing.List[str] = []
    match_regex: re.Pattern = None
    use_images: bool = True

    def __init__(
        self, match_list=[], emote_list=None, use_images=True, *args, **kwargs
    ):
        self.match_list = match_list
        self.match_regex = re.compile(
            re.compile(
                rf"(?<![^\s_-]){'|'.join(self.match_list)}(?![^\s_-])", re.IGNORECASE
            )
        )
        self.emote_list = self.match_list if emote_list is None else emote_list
        self.use_images = use_images

        super().__init__(*args, **kwargs)

    @property
    def non_db_attrs(self):
        return super().non_db_attrs + (
            "match_list",
            "match_regex",
            "use_images",
            "show_recap",
        )


class TwitchUser(models.Model):
    user_id = models.IntegerField(primary_key=True, editable=False)

    login = models.CharField(max_length=255, default="missing username")
    display_name = models.CharField(max_length=255, default="missing display name")
    user_type = models.CharField(max_length=255, default="")
    broadcaster_type = models.CharField(max_length=255, default="")
    description = models.CharField(max_length=512, default="")
    profile_image_url = models.CharField(
        max_length=512, default="missing profile image url"
    )
    offline_image_url = models.CharField(
        max_length=512, default="missing offline image url"
    )
    created_at = models.DateTimeField("created at", default=DEFAULT_DATETIME)

    is_bot = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "login",
                ]
            ),
            models.Index(
                fields=[
                    "created_at",
                ]
            ),
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
            "created_at": self.created_at.astimezone(TIMEZONE).strftime(
                luscioustwitch.TWITCH_API_TIME_FORMAT
            ),
        }


class TwitchEmote(models.Model):
    id = models.AutoField(primary_key=True, serialize=False)

    emote_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)


class ChatMessage(models.Model):
    id = models.AutoField(primary_key=True, serialize=False)

    commenter = models.ForeignKey(TwitchUser, on_delete=models.CASCADE)
    message_id = models.CharField(max_length=255, editable=False, unique=True)
    content_offset = models.IntegerField(default=0)
    created_at = models.DateTimeField("created at", default=DEFAULT_DATETIME)
    logged_at = models.DateTimeField("logged at", default=timezone.now)
    message = models.CharField(max_length=1024, default="")
    emotes = models.ManyToManyField(TwitchEmote)

    class Meta:
        ordering = ("created_at",)
        indexes = [
            models.Index(
                fields=[
                    "message_id",
                ]
            ),
            models.Index(
                fields=[
                    "commenter",
                ]
            ),
            models.Index(
                fields=[
                    "created_at",
                ]
            ),
            models.Index(
                fields=[
                    "logged_at",
                ]
            ),
        ]

    def __str__(self):
        timestr = self.created_at.strftime("%Y-%m-%d %H:%M:%S")

        return f"[{timestr}] {self.commenter.display_name}: {self.message}"

    def localtz_str(self, localtz=TIMEZONE):
        local_created_at = utc_to_local(self.created_at, localtz)
        timestr = local_created_at.strftime("%Y-%m-%d %H:%M:%S")

        return f"[{timestr}] {self.commenter.display_name}: {self.message}"

    def to_json(self):
        return {
            "commenter": self.commenter.to_json(),
            "content_offset": self.content_offset,
            "created_at": self.created_at.astimezone(TIMEZONE).strftime(
                luscioustwitch.TWITCH_API_TIME_FORMAT
            ),
            "message": self.message,
        }


def default_json_field():
    return []


class FragmentGroup(models.Model):
    name = models.CharField(max_length=256, blank=False)
    group_id = models.CharField(max_length=256, blank=False)
    unit = models.CharField(max_length=256, blank=False)

    count_multiples = models.BooleanField(default=True)
    use_images = models.BooleanField(default=True)
    show_in_recap = models.BooleanField(default=True)
    show_leaderboard = models.BooleanField(default=True)
    expandable = models.BooleanField(default=True)

    ordering = models.IntegerField(default=0)

    @property
    def match_list(self):
        return [frag.match for frag in self.fragment_set]

    @property
    def emote_list(self):
        return [frag.emote for frag in self.fragment_set]

    @property
    def match_regex(self):
        return re.compile(
            re.compile(
                rf"(?<![^\s_-]){'|'.join(self.match_list)}(?![^\s_-])", re.IGNORECASE
            )
        )

    class Meta:
        ordering = ("ordering",)


class Fragment(models.Model):
    group = models.ForeignKey(FragmentGroup, on_delete=models.CASCADE)

    fragment_id = models.CharField(max_length=512, blank=False)
    pretty_name = models.CharField(max_length=512, blank=False)
    match = models.CharField(max_length=512, blank=False)
    image = models.FileField(upload_to="fragments/", blank=True)

    case_sensitive = models.BooleanField(default=False)

    @property
    def match_regex(self):
        return re.compile(
            rf"(?<![^\s_-]){self.match}(?![^\s_-])",
            re.NOFLAG if self.case_sensitive else re.IGNORECASE,
        )

    def __str__(self):
        return f"{self.pretty_name} ({self.match})"

    class Meta:
        unique_together = (
            "group",
            "fragment_id",
        )


class FragmentInline(admin.TabularInline):
    model = Fragment
    extra = 1


class FragmentGroupAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ["name", "unit"]
    inlines = (FragmentInline,)
    ordering = ("ordering",)


class Clip(models.Model):
    clip_id = models.CharField(max_length=255, primary_key=True, editable=False)

    creator = models.ForeignKey(TwitchUser, on_delete=models.CASCADE)

    url = models.CharField(max_length=512, default="missing clip url")
    embed_url = models.CharField(max_length=512, default="missing embed url")
    broadcaster_id = models.IntegerField(default=-1)
    broadcaster_name = models.CharField(
        max_length=64, default="missing broadcaster name"
    )
    video_id = models.CharField(max_length=255, default="")
    game_id = models.CharField(max_length=255, default="missing game id")
    language = models.CharField(max_length=255, default="en")
    title = models.CharField(max_length=255, default="missing clip title")
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField("created at", default=DEFAULT_DATETIME)
    thumbnail_url = models.CharField(max_length=512, default="missing thumbnail url")
    duration = models.FloatField(default=0.0)
    vod_offset = models.IntegerField(default=0)

    class Meta:
        ordering = ("view_count",)
        indexes = [
            models.Index(
                fields=[
                    "created_at",
                ]
            ),
            models.Index(
                fields=[
                    "view_count",
                ]
            ),
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
            "created_at": self.created_at.astimezone(TIMEZONE).strftime(
                luscioustwitch.TWITCH_API_TIME_FORMAT
            ),
            "thumbnail_url": self.thumbnail_url,
            "duration": self.duration,
            "vod_offset": self.vod_offset,
        }

    def to_basic_json(self):
        return {
            "clip_id": self.clip_id,
            "creator": self.creator.display_name,
            "url": self.url,
            "title": self.title,
            "view_count": self.view_count,
            "created_at": self.created_at.astimezone(TIMEZONE).strftime(
                luscioustwitch.TWITCH_API_TIME_FORMAT
            ),
        }


class Video(models.Model):
    vod_id = models.CharField(max_length=255, primary_key=True, editable=False)

    stream_id = models.CharField(max_length=255, default="")
    user_id = models.CharField(max_length=255, default="")
    user_login = models.CharField(max_length=255, default="")
    user_name = models.CharField(max_length=255, default="")
    title = models.CharField(max_length=255, default="")
    description = models.CharField(max_length=512, default="")
    created_at = models.DateTimeField("created at", default=timezone.now)
    published_at = models.DateTimeField("published at", default=timezone.now)
    url = models.CharField(max_length=512, default="")
    thumbnail_url = models.CharField(max_length=255, default="")
    viewable = models.CharField(max_length=255, default="")
    view_count = models.IntegerField(default=0)
    language = models.CharField(max_length=255, default="")
    vod_type = models.CharField(max_length=255, default="")
    duration = models.CharField(max_length=255, default="")

    class Meta:
        ordering = ("created_at",)
        indexes = [
            models.Index(
                fields=[
                    "created_at",
                ]
            ),
            models.Index(
                fields=[
                    "view_count",
                ]
            ),
        ]


class RecapData(models.Model):
    year = models.IntegerField(default=1971)
    month = models.IntegerField(default=1)

    twitch_user = models.ForeignKey(
        TwitchUser, on_delete=models.CASCADE, blank=True, null=True
    )

    count_messages = StatField(
        short_name="messages", verbose_name="Messages sent:", default=0
    )
    count_characters = BigStatField(
        short_name="characters",
        show_recap=False,
        show_leaderboard=True,
        verbose_name="Characters typed:",
        unit="chatter",
        default=0,
    )
    count_clips = StatField(
        short_name="clips", verbose_name="Clips created:", unit="clip", default=0
    )
    count_clip_watch = BigStatField(
        short_name="watchtime",
        show_recap=False,
        show_leaderboard=False,
        verbose_name="Clip watch time:",
        unit="second",
        default=0,
    )
    count_clip_views = StatField(
        short_name="views", verbose_name="Clip views:", unit="clip view", default=0
    )
    count_chatters = StatField(
        short_name="chatters",
        show_leaderboard=False,
        verbose_name="Number of chatters:",
        unit="chatter",
        default=0,
    )
    count_videos = StatField(
        short_name="videos",
        show_leaderboard=False,
        verbose_name="Number of videos:",
        unit="video",
        default=0,
    )
    
    first_message = models.ForeignKey(ChatMessage, on_delete = models.SET_NULL, null=True, related_name="first_message_set")
    last_message  = models.ForeignKey(ChatMessage, on_delete = models.SET_NULL, null=True, related_name="last_message_set")

    @property
    def start_date(self) -> datetime.datetime:
        if self.year == 0:
            return None

        return datetime.datetime(
            self.year, self.month if self.month > 0 else 1, 1, 0, 0, 0, 1, TIMEZONE
        )

    @property
    def end_date(self) -> datetime.datetime:
        if self.year == 0:
            return None

        end_month = self.month if self.month > 0 else 12
        monthrange = calendar.monthrange(self.year, end_month)
        return datetime.datetime(
            self.year, end_month, monthrange[1], 23, 59, 59, 999, TIMEZONE
        )

    class Meta:
        unique_together = ("year", "month", "twitch_user")
        indexes = [
            models.Index(fields=["year", "month"]),
            models.Index(fields=["year", "month", "count_messages"]),
            models.Index(fields=["year", "month", "count_clips"]),
            models.Index(fields=["year", "month", "count_clip_views"]),
        ]


class LeaderboardCache(models.Model):
    recap = models.ForeignKey(RecapData, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    leaderboard_data = models.JSONField(default=dict)


class FragmentMatch(models.Model):
    fragment = models.ForeignKey(Fragment, on_delete=models.CASCADE)

    commenter = models.ForeignKey(
        TwitchUser, on_delete=models.SET_NULL, blank=True, null=True
    )

    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE)
    recaps = models.ManyToManyField(RecapData)

    count = models.IntegerField(default=1)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (
            "fragment",
            "message",
        )
        ordering = (
            "timestamp",
            "count",
        )
        indexes = [
            models.Index(
                fields=[
                    "timestamp",
                ]
            ),
        ]


class FragmentCounter(models.Model):
    recap = models.ForeignKey(RecapData, on_delete=models.CASCADE)
    fragment = models.ForeignKey(Fragment, on_delete=models.CASCADE)

    year = models.IntegerField(default=1971)
    month = models.IntegerField(default=0)
    twitch_user = models.ForeignKey(
        TwitchUser, on_delete=models.CASCADE, blank=True, null=True
    )

    count = models.BigIntegerField(default=0)

    class Meta:
        unique_together = ("recap", "fragment")
        indexes = [
            models.Index(
                fields=["twitch_user", "year", "month", "fragment", "count"],
                name="fragment_leaderboard_idx",
            )
        ]


class FragmentGroupCounter(models.Model):
    recap = models.ForeignKey(RecapData, on_delete=models.CASCADE)
    fragment_group = models.ForeignKey(FragmentGroup, on_delete=models.CASCADE)

    year = models.IntegerField(default=0)
    month = models.IntegerField(default=0)
    twitch_user = models.ForeignKey(
        TwitchUser, on_delete=models.CASCADE, blank=True, null=True
    )

    count = models.BigIntegerField(default=0)

    class Meta:
        unique_together = ("recap", "fragment_group")
        indexes = [
            models.Index(fields=["year", "month"]),
            models.Index(fields=["year", "month", "fragment_group"]),
            models.Index(fields=["-count"]),
            models.Index(
                fields=["twitch_user", "year", "month", "fragment_group", "count"],
                name="fragmentgroup_leaderboard_idx",
            ),
        ]


class WrappedData(models.Model):
    recap = models.ForeignKey(
        RecapData, on_delete=models.CASCADE, null=True, blank=True
    )

    vip_gambles = models.IntegerField(default=0)
    vip_wins = models.IntegerField(default=0)

    typing_time = models.CharField(max_length=255, default="0 seconds")
    clip_watch_time = models.CharField(max_length=255, default="0 seconds")

    jackass_count = models.IntegerField(default=0)

    extra_data = models.JSONField(default=dict)

    class Meta:
        unique_together = ("recap",)


class Pet(models.Model):
    acquired = models.BooleanField(default=True)

    image = models.FileField(upload_to="petimg/", blank=True)
    name = models.CharField(max_length=255, default="")

    killcount_known = models.BooleanField(default=True)
    killcount = models.IntegerField(default=0)
    drop_rate_known = models.BooleanField(default=False)
    drop_rate = models.IntegerField(default=0)
    kill_term = models.CharField(max_length=255, default="killcount")
    kill_term_pluralize = models.CharField(max_length=255, default="", blank=True)

    secondary_killcount_needed = models.BooleanField(default=False)
    secondary_killcount = models.IntegerField(default=0)
    secondary_drop_rate_known = models.BooleanField(default=False)
    secondary_drop_rate = models.IntegerField(default=0)
    secondary_kill_term = models.CharField(max_length=255, default="killcount")
    secondary_kill_term_pluralize = models.CharField(
        max_length=255, default="", blank=True
    )

    date_known = models.BooleanField(default=True)
    date = models.DateTimeField(default=timezone.now)

    clip_url = models.CharField(max_length=512, default="", blank=True)
    tweet_url = models.CharField(max_length=512, default="", blank=True)

    class Meta:
        ordering = (
            "date",
            "name",
        )

    def __str__(self):
        return self.name

    def killcount_str(self):
        kcstr = f"{self.killcount:,} {self.kill_term}" + (
            "" if self.killcount < 1 else self.kill_term_pluralize
        )

        if self.secondary_killcount_needed:
            kcstr += f", {self.secondary_killcount:,} {self.secondary_kill_term}" + (
                ""
                if self.secondary_killcount < 1
                else self.secondary_kill_term_pluralize
            )

        return kcstr


class CopyPasteGroup(models.Model):
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)


class CopyPaste(models.Model):
    group = models.ForeignKey(CopyPasteGroup, on_delete=models.CASCADE)

    title = models.CharField(max_length=256, blank=True)
    text = models.TextField(blank=True)


class CopyPasteInline(admin.TabularInline):
    model = CopyPaste
    extra = 1


class CopyPasteGroupAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ["title", "description"]
    inlines = (CopyPasteInline,)
    ordering = ("title",)


class Ascii(models.Model):
    title = models.CharField(max_length=255, unique=True)
    text = models.TextField()

    is_garf = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class AsciiAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ["title"]
    ordering = ("title",)


class LetterboxdReview(models.Model):
    title = models.CharField(max_length=255)
    review_id = models.CharField(max_length=255)
    link = models.CharField(max_length=255)
    pub_date = models.DateTimeField()
    watched_date = models.DateField()
    film_title = models.CharField(max_length=255)
    film_year = models.IntegerField(null=True)
    member_rating = models.FloatField(null=True)
    movie_id = models.IntegerField(null=True)
    description = models.TextField()
    creator = models.CharField(max_length=255)

    class Meta:
        unique_together = ("review_id",)
        ordering = ("pub_date",)
        indexes = [
            models.Index(
                fields=[
                    "pub_date",
                ]
            ),
            models.Index(
                fields=[
                    "watched_date",
                ]
            ),
            models.Index(
                fields=[
                    "member_rating",
                ]
            ),
        ]
