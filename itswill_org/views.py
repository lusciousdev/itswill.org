import calendar
import datetime
import logging
import typing

from dateutil import tz
from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from .models import *
from .tasks import *

logger = logging.getLogger("django")

# Create your views here.


class IndexView(generic.TemplateView):
    template_name = "itswill_org/index.html"


class CensusView(generic.TemplateView):
    template_name = "itswill_org/census.html"


class CensusPresentationView(generic.TemplateView):
    template_name = "itswill_org/census-presentation.html"


class MonthListView(generic.TemplateView):
    template_name = "itswill_org/monthlist.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data["monthly_recaps"] = {}

        for recap in RecapData.objects.filter(month__gte=1, twitch_user=None).all():
            if recap.year not in data["monthly_recaps"]:
                data["monthly_recaps"][recap.year] = {}

            data["monthly_recaps"][recap.year][recap.month] = {
                "month_name": datetime.datetime(
                    recap.year, recap.month, 1, 12, 0, 0
                ).strftime("%B"),
                "recap": recap,
            }

        data["monthly_recaps"] = dict(
            sorted(data["monthly_recaps"].items(), key=lambda kvp: kvp[0])
        )

        for year, month_dict in data["monthly_recaps"].items():
            data["monthly_recaps"][year] = dict(
                sorted(data["monthly_recaps"][year].items(), key=lambda kvp: kvp[0])
            )

        return data


class MonthView(generic.TemplateView):
    template_name = "itswill_org/month.html"

    def dispatch(self, request, year, month, *args, **kwargs):
        try:
            monthlyrecap = RecapData.objects.get(
                year=year, month=month, twitch_user=None
            )
            return super(MonthView, self).dispatch(
                request, year=year, month=month, *args, **kwargs
            )
        except RecapData.DoesNotExist:
            raise Http404("This months data has not been collected yet.")

    def get_context_data(self, year, month, **kwargs):
        data = super().get_context_data(**kwargs)

        try:
            monthlyrecap = RecapData.objects.get(
                year=year, month=month, twitch_user=None
            )
        except RecapData.DoesNotExist:
            logger.error("MISSING MONTHLY RECAP, NOT REDIRECTED BY DISPATCH")
            return data

        localtz = tz.gettz("America/Los_Angeles")
        monthrange = calendar.monthrange(year, month)

        start_date = datetime.datetime(year, month, 1, 0, 0, 0, 1, localtz)
        end_date = datetime.datetime(
            year, month, monthrange[1], 23, 59, 59, 999, localtz
        )

        data["start_date"] = start_date.strftime("%Y/%m/%d")
        data["end_date"] = end_date.strftime("%Y/%m/%d")

        monthlychatters = RecapData.objects.filter(year=year, month=month).exclude(
            twitch_user=None
        )

        clips = Clip.objects.filter(created_at__range=(start_date, end_date)).order_by(
            "-view_count"
        )

        data["top_clips"] = clips[:10]

        data["clip_count"] = monthlyrecap.count_clips
        data["message_count"] = monthlyrecap.count_messages
        data["clip_views"] = monthlyrecap.count_clip_views
        data["chatter_count"] = monthlyrecap.count_chatters
        data["vod_count"] = monthlyrecap.count_videos

        chatter_list = monthlychatters.order_by("-count_messages")
        clipper_list = monthlychatters.order_by("-count_clips")

        data["top_chatters"] = chatter_list[:10]
        data["top_clippers"] = clipper_list[:10]

        return data


class PetsView(generic.TemplateView):
    template_name = "itswill_org/pets.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data["acquired_pets"] = Pet.objects.filter(acquired=True).order_by("date").all()
        data["unacquired_pets"] = (
            Pet.objects.filter(acquired=False).order_by("name").all()
        )

        data["total_pets"] = Pet.objects.all().count()

        data["drinfo"] = {}

        for pet in data["acquired_pets"]:
            data["drinfo"][pet.name] = {}
            if (pet.killcount_known and pet.drop_rate_known) and (
                not pet.secondary_killcount_needed or pet.secondary_drop_rate_known
            ):
                data["drinfo"][pet.name]["show"] = True
                percent = pet.killcount / pet.drop_rate
                if pet.secondary_killcount_needed:
                    percent += pet.secondary_killcount / pet.secondary_drop_rate
                data["drinfo"][pet.name]["percent"] = percent

                divclass = "no-drop-rate-info"
                if percent < 0.1:
                    divclass = "absurdly-lucky"
                elif percent < 0.333:
                    divclass = "very-lucky"
                elif percent < 0.8:
                    divclass = "lucky"
                elif percent < 1.2:
                    divclass = "on-rate"
                elif percent < 2:
                    divclass = "unlucky"
                elif percent < 3:
                    divclass = "very-unlucky"
                else:
                    divclass = "absurdly-unlucky"

                data["drinfo"][pet.name]["class"] = divclass
            else:
                data["drinfo"][pet.name]["show"] = False
                data["drinfo"][pet.name]["percent"] = 0
                data["drinfo"][pet.name]["class"] = "no-drop-rate-info"

        return data


class RecapView(generic.TemplateView):
    template_name = "itswill_org/recap.html"

    def get_context_data(self, year: int, month: int, username: str, **kwargs):
        start = time.perf_counter()
        logger.info("getting recap view context data")

        data = super().get_context_data(**kwargs)

        data["month_abbr"] = calendar.month_abbr
        all_recaps = {}

        recap_times = (
            RecapData.objects.filter(twitch_user=None)
            .order_by("year", "month")
            .values_list("year", "month")
            .all()
        )
        for y, m in recap_times:
            if y not in all_recaps:
                all_recaps[y] = []
            all_recaps[y].append(m)

        data["all_recaps"] = all_recaps

        logger.info(f"\tFetch overall: {time.perf_counter()-start:.3f}")
        start = time.perf_counter()

        if username is not None:
            username = username.strip()

            try:
                twitchuser = TwitchUser.objects.get(display_name__iexact=username)
            except TwitchUser.DoesNotExist:
                try:
                    twitchuser = TwitchUser.objects.get(login__iexact=username)
                except:
                    raise Http404("That user does not exist or has not chatted.")

            try:
                recap = (
                    RecapData.objects.select_related("twitch_user")
                    .prefetch_related("fragmentgroupcounter_set", "fragmentcounter_set")
                    .select_related("twitch_user")
                    .get(year=year, month=month, twitch_user=twitchuser)
                )
            except RecapData.DoesNotExist:
                raise Http404("No data for that user in this period.")

            data["overall_recap"] = False
            data["recap"] = recap
        else:
            try:
                recap = RecapData.objects.get(year=year, month=month, twitch_user=None)
            except RecapData.DoesNotExist:
                raise Http404("That recap does not exist (yet?).")

            data["overall_recap"] = True
            data["recap"] = recap

        logger.info(f"\tFetch recap: {time.perf_counter()-start:.3f}")
        start = time.perf_counter()

        fragment_group_counters = (
            FragmentGroupCounter.objects.filter(recap=recap)
            .select_related("fragment_group")
            .values_list("fragment_group__group_id", "count")
            .all()
        )
        fragment_counters = (
            FragmentCounter.objects.filter(recap=recap)
            .select_related("fragment")
            .values_list("fragment__group__group_id", "fragment__pretty_name", "count")
            .all()
        )

        logger.info(f"\tLoad fragment counters: {time.perf_counter()-start:.3f}")
        start = time.perf_counter()

        data["fragment_data"] = {
            group_id: {
                "total": count,
                "members": {
                    pretty_name: count
                    for _, pretty_name, count in filter(lambda fcd: fcd[0]==group_id, fragment_counters)
                },
            }
            for group_id, count in fragment_group_counters
        }
        logger.info(f"\tContextify fragment counters: {time.perf_counter()-start:.3f}")
        start = time.perf_counter()

        data["fragment_groups"] = (
            FragmentGroup.objects.order_by("ordering")
            .prefetch_related("fragment_set")
            .all()
        )

        logger.info(f"\tFetch fragments: {time.perf_counter()-start:.3f}")
        return data


@csrf_exempt
def get_recap(request):
    year = str(0)
    month = str(0)
    username = None
    if request.method == "POST":
        year = request.POST.get("year", year)
        month = request.POST.get("month", month)
        username = request.POST.get("username", username)
    if request.method == "GET":
        year = request.GET.get("year", year)
        month = request.GET.get("month", month)
        username = request.GET.get("username", username)

    username = None if username == "" else username
    try:
        year = int(year)
    except:
        year = 0

    try:
        month = int(month)
    except:
        month = 0

    if username is None:
        if year > 0:
            if month > 0:
                return HttpResponseRedirect(
                    reverse(
                        "itswill_org:recap_month", kwargs={"year": year, "month": month}
                    )
                )
            else:
                return HttpResponseRedirect(
                    reverse("itswill_org:recap_year", kwargs={"year": year})
                )
        else:
            return HttpResponseRedirect(reverse("itswill_org:recap"))
    else:
        if year > 0:
            if month > 0:
                return HttpResponseRedirect(
                    reverse(
                        "itswill_org:recap_month_user",
                        kwargs={"year": year, "month": month, "username": username},
                    )
                )
            else:
                return HttpResponseRedirect(
                    reverse(
                        "itswill_org:recap_year_user",
                        kwargs={"year": year, "username": username},
                    )
                )
        else:
            return HttpResponseRedirect(
                reverse("itswill_org:recap_user", kwargs={"username": username})
            )


class Wrapped2024View(generic.TemplateView):
    template_name = "itswill_org/2024-wrapped.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        try:
            overall_wrapped = WrappedData.objects.get(year=2024, twitch_user=None)
        except WrappedData.DoesNotExist:
            raise Http404("That recap does not exist (yet?).")

        data["wrapped"] = overall_wrapped

        return data


class Wrapped2024UserView(generic.TemplateView):
    template_name = "itswill_org/2024-wrapped-user.html"

    def get_context_data(self, username: str, **kwargs):
        data = super().get_context_data(**kwargs)

        try:
            overall_wrapped = WrappedData.objects.get(year=2024, twitch_user=None)
        except WrappedData.DoesNotExist:
            raise Http404("That recap does not exist (yet?).")

        try:
            twitchuser = TwitchUser.objects.get(display_name__iexact=username)
        except TwitchUser.DoesNotExist:
            try:
                twitchuser = TwitchUser.objects.get(login__iexact=username)
            except:
                raise Http404("That user does not exist or has not chatted.")

        try:
            user_wrapped = WrappedData.objects.get(year=2024, twitch_user=twitchuser)
        except WrappedData.DoesNotExist:
            raise Http404("No data for that user in this period.")

        data["wrapped"] = {}
        data["wrapped"]["overall"] = overall_wrapped
        data["wrapped"]["user"] = user_wrapped

        top_boards = {}
        for field_name, (position, count) in user_wrapped.extra_data[
            "top_leaderboard_positions"
        ]:
            field = user_wrapped.recap._meta.get_field(field_name)
            if (
                field.get_internal_type() == "IntegerField"
                or field.get_internal_type() == "BigIntegerField"
            ):
                top_boards[field.name] = {}
                top_boards[field.name]["label"] = field.verbose_name
                top_boards[field.name]["position"] = position
                top_boards[field.name]["count"] = count
                if (type(field) == StringCountField) and field.use_images:
                    top_boards[field.name]["image_list"] = field.emote_list
                else:
                    top_boards[field.name]["image_list"] = None

        data["wrapped"]["top_leaderboards"] = top_boards

        return data


class Wrapped2025View(generic.TemplateView):
    template_name = "itswill_org/2025_wrapped.html"


class Wrapped2025UserView(generic.TemplateView):
    template_name = "itswill_org/2025_wrapped_user.html"


@csrf_exempt
def get_wrapped(request):
    username = None
    if request.method == "POST":
        username = request.POST.get("username", username)
    if request.method == "GET":
        username = request.GET.get("username", username)

    username = None if username == "" else username

    if username is None:
        return HttpResponseRedirect(reverse("itswill_org:wrapped"))
    else:
        return HttpResponseRedirect(
            reverse("itswill_org:wrapped_user", kwargs={"username": username})
        )


class LeaderboardView(generic.TemplateView):
    template_name = "itswill_org/all-leaderboards.html"

    def get_context_data(self, year: int, month: int, **kwargs):
        data = super().get_context_data(**kwargs)

        data["month_abbr"] = calendar.month_abbr
        data["all_recaps"] = {}

        for yearrecap in (
            RecapData.objects.filter(month=0, twitch_user=None).order_by("year").all()
        ):
            data["all_recaps"][yearrecap.year] = {
                "recap": yearrecap,
                "month_recaps": {},
            }

            for monthrecap in (
                RecapData.objects.filter(
                    year=yearrecap.year, month__gte=1, twitch_user=None
                )
                .order_by("month")
                .all()
            ):
                data["all_recaps"][monthrecap.year]["month_recaps"][
                    monthrecap.month
                ] = {
                    "month_name": calendar.month_abbr[monthrecap.month],
                    "recap": monthrecap,
                }

        try:
            overallrecap = RecapData.objects.get(
                year=year, month=month, twitch_user=None
            )
        except RecapData.DoesNotExist:
            raise Http404("That recap does not exist (yet?).")

        leaderboards = (
            LeaderboardCache.objects.filter(recap=overallrecap)
            .order_by("-created_at")
            .first()
        )

        if leaderboards is None:
            calculate_leaderboard(overallrecap.year, overallrecap.month, True)
            leaderboards = (
                LeaderboardCache.objects.filter(recap=overallrecap)
                .order_by("-created_at")
                .first()
            )
            if leaderboards is None:
                raise Http404("Failed to create leaderboard.")

        data["recap_data"] = overallrecap
        data["leaderboards"] = leaderboards.leaderboard_data
        data["limit"] = 10
        data["fragment_groups"] = (
            FragmentGroup.objects.order_by("ordering")
            .filter(show_leaderboard=True)
            .prefetch_related("fragment_set")
            .all()
        )

        data["non_fragment_leaderboards"] = {}

        for field in overallrecap._meta.get_fields():
            if type(field) in [StatField, BigStatField]:
                if field.show_leaderboard:
                    data["non_fragment_leaderboards"][
                        field.short_name
                    ] = field.verbose_name

        calculate_leaderboard.delay(overallrecap.year, overallrecap.month)
        return data


class SingleLeaderboardView(generic.TemplateView):
    template_name = "itswill_org/single-leaderboard.html"

    def get_context_data(self, year: int, month: int, name: str, **kwargs):
        data = super().get_context_data(**kwargs)

        data["month_abbr"] = calendar.month_abbr
        data["all_recaps"] = {}

        for yearrecap in (
            RecapData.objects.filter(month=0, twitch_user=None).order_by("year").all()
        ):
            data["all_recaps"][yearrecap.year] = {
                "recap": yearrecap,
                "month_recaps": {},
            }

            for monthrecap in (
                RecapData.objects.filter(
                    year=yearrecap.year, month__gte=1, twitch_user=None
                )
                .order_by("month")
                .all()
            ):
                data["all_recaps"][monthrecap.year]["month_recaps"][
                    monthrecap.month
                ] = {
                    "month_name": calendar.month_abbr[monthrecap.month],
                    "recap": monthrecap,
                }

        try:
            overallrecap = RecapData.objects.get(
                year=year, month=month, twitch_user=None
            )
        except RecapData.DoesNotExist:
            raise Http404("That recap does not exist (yet?).")

        calculate_leaderboard(overallrecap.year, overallrecap.month)
        try:
            leaderboards = LeaderboardCache.objects.get(recap=overallrecap)
        except LeaderboardCache.DoesNotExist:
            raise Http404("This recap does not have leaderboards for some reason.")

        data["recap_data"] = overallrecap
        data["leaderboard_name"] = name

        try:
            fg = FragmentGroup.objects.prefetch_related("fragment_set").get(
                group_id=name
            )

            data["fragment_group"] = fg
            data["leaderboard"] = (
                leaderboards.leaderboard_data[fg.group_id]
                if fg.group_id in leaderboards.leaderboard_data
                else []
            )
        except FragmentGroup.DoesNotExist:
            try:
                fields: list = overallrecap._meta.get_fields()
                field = list(
                    filter(
                        lambda f: hasattr(f, "short_name") and f.short_name == name,
                        fields,
                    )
                )[0]
                data["unit"] = field.verbose_name
                data["leaderboard"] = (
                    leaderboards.leaderboard_data[name]
                    if name in leaderboards.leaderboard_data
                    else []
                )
            except FieldDoesNotExist:
                raise Http404(
                    "That field either does not exist or does not have leaderboard.",
                    404,
                )

        return data


class CopyPasteView(generic.ListView):
    model = CopyPasteGroup
    template_name = "itswill_org/pasta.html"

    ordering = ["title"]


class AsciiView(generic.ListView):
    model = Ascii
    template_name = "itswill_org/ascii.html"

    ordering = ["title"]
