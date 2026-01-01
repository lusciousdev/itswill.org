import time
from random import choice, randint

import humanize
import requests
from celery import Celery, shared_task
from celery.schedules import crontab
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import *
from .tasks import get_random_message, post_random_message


@csrf_exempt
def get_random_message_api(request):
    if request.method != "GET":
        return HttpResponse("Invalid request type.", 501)

    altuser = request.GET.get("otheruser", "")
    user_id = request.GET.get("userid", "43246220")

    altuser = altuser.strip("@")

    try:
        user_id = int(user_id)
    except ValueError:
        user_id = 43246220

    user = None
    if altuser == "?":
        user = None
    elif altuser != "" and altuser != "null" and altuser is not None:
        try:
            user = TwitchUser.objects.get(login=altuser)
        except TwitchUser.DoesNotExist:
            return HttpResponse(f'User "{altuser}" does not exist.', 404)
    else:
        try:
            user = TwitchUser.objects.get(user_id=user_id)
        except TwitchUser.DoesNotExist:
            return HttpResponse("No messages found for this user.", 404)

    nightbot_response_url = request.META.get("HTTP_NIGHTBOT_RESPONSE_URL", "")

    if nightbot_response_url != "":
        post_random_message.delay(
            -1 if user == None else user.user_id, nightbot_response_url
        )
        return HttpResponse(" ", 200)

    return HttpResponse(get_random_message(user), 200)


@csrf_exempt
def get_random_user_api(request):
    if request.method != "GET":
        return HttpResponse("Invalid request type.", 501)

    user_id = TwitchUser.objects.all().values_list("user_id", flat=True)
    return HttpResponse(TwitchUser.objects.get(user_id=choice(user_id)).login, 200)


@csrf_exempt
def get_random_clip(request):
    if request.method != "GET":
        return HttpResponse("Invalid request type.", 501)

    clips = Clip.objects.filter(view_count__gte=100)

    clip_count = clips.count()
    random_clip = clips.all()[randint(0, clip_count - 1)]

    return HttpResponse(random_clip.url, 200)


@csrf_exempt
def get_pets_message(request):
    total_pet_count = Pet.objects.all().count()
    acquired_pet_count = Pet.objects.filter(acquired=True).count()

    return HttpResponse(
        f"{acquired_pet_count}/{total_pet_count} https://itswill.org/pets", 200
    )


@csrf_exempt
def get_most_recent_pet(request):
    most_recent_pet = (
        Pet.objects.filter(acquired=True, date_known=True).order_by("-date").first()
    )

    respstr = ""

    if most_recent_pet.date_known:
        respstr += f"{most_recent_pet.date.strftime('[%Y-%m-%d]')} "

    respstr += f"{ most_recent_pet.name }"

    if most_recent_pet.killcount_known:
        respstr += f" ({ most_recent_pet.killcount_str() })"
    if most_recent_pet.clip_url != "":
        respstr += f" { most_recent_pet.clip_url }"

    return HttpResponse(respstr, 200)


@csrf_exempt
def get_pets_left(request):
    pets_left = Pet.objects.filter(acquired=False).order_by("name").all()
    ret = ", ".join([str(pet) for pet in pets_left]) + f" ({len(pets_left)} remaining)"
    return HttpResponse(ret, 200)


@csrf_exempt
def get_random_garfield(request):
    if request.method != "GET":
        return HttpResponse("Invalid request type.", 501)

    garf_asciis = Ascii.objects.filter(is_garf=True)

    ascii_count = garf_asciis.count()
    random_garf = garf_asciis.all()[randint(0, ascii_count - 1)]

    return HttpResponse(random_garf.text, content_type="charset=utf-8")


@csrf_exempt
def get_live_at_five_record(request):
    if request.method != "GET":
        return HttpResponse("Invalid request type.", 501)

    year = request.GET.get("year", None)

    if year is None:
        year = datetime.datetime.now(TIMEZONE).year

    record = requests.get(f"https://liveatfive.net/api/v1/record/?period={year}")

    return JsonResponse(record.json())


@csrf_exempt
def get_boss_count(request):
    if request.method != "GET":
        return HttpResponse("Invalid request type.", 501)

    humanize_response = "humanize" in request.GET

    response: requests.Response = requests.get(
        "https://secure.runescape.com/m=hiscore_oldschool/index_lite.json?player=Suede"
    )
    hiscores_data: dict = response.json()

    total_kc = 0
    for activity in hiscores_data.get("activities", []):
        if any(
            [
                activity["name"].startswith(part)
                for part in [
                    "League",
                    "Deadman",
                    "Bounty",
                    "Clue",
                    "LMS",
                    "PvP",
                    "Soul Wars",
                    "Rifts",
                    "Colosseum Glory",
                    "Collections Logged",
                ]
            ]
        ):
            continue

        total_kc += activity["score"]

    if humanize_response:
        return HttpResponse(humanize.intcomma(total_kc))
    else:
        return HttpResponse(total_kc)


@csrf_exempt
def get_random_letterboxd_review(request):
    if request.method != "GET":
        return HttpResponse("Invalid request type.", 501)

    review_pks = LetterboxdReview.objects.values_list("pk", flat=True)
    lbreview = LetterboxdReview.objects.get(pk=randint(1, len(review_pks)))

    review_str = ""
    if lbreview.member_rating is None:
        if lbreview.film_year is None:
            review_str = f"{lbreview.film_title} - No rating: {lbreview.description}"
        else:
            review_str = f"{lbreview.film_title} ({lbreview.film_year}) - No rating: {lbreview.description}"
    else:
        if lbreview.film_year is None:
            review_str = f"{lbreview.film_title} - {lbreview.member_rating:g}/5: {lbreview.description}"
        else:
            review_str = f"{lbreview.film_title} ({lbreview.film_year}) - {lbreview.member_rating:g}/5: {lbreview.description}"

    if len(review_str) > 400:
        return HttpResponse(f"{review_str[:395]}...")
    else:
        return HttpResponse(review_str)


@csrf_exempt
def get_recap_data(request):
    if request.method != "GET":
        return JsonResponse({"error": "Invalid request type."}, status=501)

    year = request.GET.get("year", 0)
    month = request.GET.get("month", 0)
    user = request.GET.get("user", None)

    if type(year) == str:
        year = int(year)
    if type(month) == str:
        month = int(month)

    current_year = datetime.datetime.now(TIMEZONE).year
    year = 0 if year <= 0 else max(2023, min(current_year, year))
    month = 0 if year == 0 else max(0, min(12, month))

    if user is not None:
        try:
            recap = RecapData.objects.get(year=year, month=month, twitch_user_id=user)
        except RecapData.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=404)
    else:
        recap = RecapData.objects.get(year=year, month=month, twitch_user=None)

    fragment_group_counters = (
        FragmentGroupCounter.objects.filter(recap=recap)
        .select_related("fragment_group")
        .values_list("fragment_group__group_id", "count")
        .all()
    )
    fragment_counters = (
        FragmentCounter.objects.filter(recap=recap)
        .select_related("fragment")
        .values_list("fragment__group__group_id", "fragment__fragment_id", "count")
        .all()
    )

    data = {
        "count_messages": recap.count_messages,
        "count_characters": recap.count_characters,
        "count_clips": recap.count_clips,
        "count_clip_watch": recap.count_clip_watch,
        "count_clip_views": recap.count_clip_views,
        "count_chatters": recap.count_chatters,
        "count_video": recap.count_videos,
        "first_message": None if recap.first_message is None else recap.first_message.to_json(),
        "last_message": None if recap.last_message is None else recap.last_message.to_json(),
        "counters": {
            group_id: {
                "total": count,
                "members": {
                    fragment_id: count
                    for _, fragment_id, count in filter(
                        lambda fcd: fcd[0] == group_id, fragment_counters
                    )
                },
            }
            for group_id, count in fragment_group_counters
        },
    }

    return JsonResponse(data, status=200)


@csrf_exempt
def test_endpoint(request):
    if request.method != "GET":
        return HttpResponse("Invalid request type.", 501)

    altuser = request.GET.get("otheruser", "")
    user_id = request.GET.get("userid", "43246220")

    altuser = altuser.strip("@")

    try:
        user_id = int(user_id)
    except ValueError:
        user_id = 43246220

    user = None
    if altuser != "" and altuser != "null" and altuser is not None:
        try:
            user = TwitchUser.objects.get(login=altuser)
        except TwitchUser.DoesNotExist:
            return HttpResponse(f'User "{altuser}" does not exist.', 404)
    else:
        try:
            user = TwitchUser.objects.get(user_id=user_id)
        except TwitchUser.DoesNotExist:
            return HttpResponse("No messages found for this user.", 404)

    nightbot_response_url = request.META.get("HTTP_NIGHTBOT_RESPONSE_URL", "")

    if nightbot_response_url != "":
        post_random_message.delay(user.user_id, nightbot_response_url)
        return HttpResponse(" ", 200)

    return HttpResponse(get_random_message(user), 200)
