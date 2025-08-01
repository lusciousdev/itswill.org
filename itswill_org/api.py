from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from celery import Celery, shared_task
from celery.schedules import crontab
import requests
from random import randint, choice
import time
import humanize

from .tasks import get_random_message, get_last_message, post_random_message
from .models import *

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
      user = TwitchUser.objects.get(login = altuser)
    except TwitchUser.DoesNotExist:
      return HttpResponse(f"User \"{altuser}\" does not exist.", 404)
  else:
    try:
      user = TwitchUser.objects.get(user_id = user_id)
    except TwitchUser.DoesNotExist:
      return HttpResponse("No messages found for this user.", 404)
  
  nightbot_response_url = request.META.get("HTTP_NIGHTBOT_RESPONSE_URL", "")
  
  if (nightbot_response_url != ""):
    post_random_message.delay(-1 if user == None else user.user_id, nightbot_response_url)
    return HttpResponse(" ", 200)
  
  return HttpResponse(get_random_message(user), 200)

@csrf_exempt
def get_random_user_api(request):
  if request.method != "GET":
    return HttpResponse("Invalid request type.", 501)
  
  user_id = TwitchUser.objects.all().values_list('user_id', flat=True)
  return HttpResponse(TwitchUser.objects.get(user_id = choice(user_id)).login, 200)

@csrf_exempt
def get_last_message_api(request):
  if request.method != "GET":
    return HttpResponse("Invalid request type.", 501)
  
  altuser = request.GET.get("user", "")
  altuser = altuser.strip("@")

  user = None
  if altuser == "":
    user = None
  elif altuser != "" and altuser != "null" and altuser is not None:
    try:
      user = TwitchUser.objects.get(login = altuser)
    except TwitchUser.DoesNotExist:
      return HttpResponse(f"User \"{altuser}\" does not exist.", 404)
  
  return HttpResponse(get_last_message(user))

@csrf_exempt
def get_last_message_2024_api(request):
  if request.method != "GET":
    return HttpResponse("Invalid request type.", 501)
  
  altuser = request.GET.get("user", "")
  altuser = altuser.strip("@")

  user = None
  if altuser == "":
    user = None
  elif altuser != "" and altuser != "null" and altuser is not None:
    try:
      user = TwitchUser.objects.get(login = altuser)
    except TwitchUser.DoesNotExist:
      return HttpResponse(f"User \"{altuser}\" does not exist.", 404)
  
  return JsonResponse(get_last_message(user, (datetime.datetime(2024, 1, 1, 0, 0, 0, 1, TIMEZONE), datetime.datetime(2025, 1, 1, 0, 0, 0, 1, TIMEZONE)), True))
  

@csrf_exempt
def get_random_clip(request):
  if request.method != "GET":
    return HttpResponse("Invalid request type.", 501)
  
  clips = Clip.objects.filter(view_count__gte = 100)
    
  clip_count = clips.count()
  random_clip = clips.all()[randint(0, clip_count - 1)]
  
  return HttpResponse(random_clip.url, 200)

@csrf_exempt
def get_pets_message(request):
  total_pet_count = Pet.objects.all().count()
  acquired_pet_count = Pet.objects.filter(acquired = True).count()
  
  return HttpResponse(f"{acquired_pet_count}/{total_pet_count} https://itswill.org/pets", 200)

@csrf_exempt
def get_most_recent_pet(request):
  most_recent_pet = Pet.objects.filter(acquired = True, date_known = True).order_by("-date").first()
  
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
  pets_left = Pet.objects.filter(acquired = False).order_by("name").all()
  ret = ", ".join([str(pet) for pet in pets_left]) + f" ({len(pets_left)} remaining)"
  return HttpResponse(ret, 200)

@csrf_exempt
def get_random_garfield(request):
  if request.method != "GET":
    return HttpResponse("Invalid request type.", 501)
  
  garf_asciis = Ascii.objects.filter(is_garf = True)
    
  ascii_count = garf_asciis.count()
  random_garf = garf_asciis.all()[randint(0, ascii_count - 1)]
  
  return HttpResponse(random_garf.text, content_type = "charset=utf-8")

@csrf_exempt
def get_live_at_five_record(request):
  if request.method != "GET":
    return HttpResponse("Invalid request type.", 501)
  
  record = requests.get("https://liveatfive.net/api/v1/record/?year=2024")
  
  return JsonResponse(record.json())

@csrf_exempt
def get_boss_count(request):
  if request.method != "GET":
    return HttpResponse("Invalid request type.", 501)
  
  humanize_response = ("humanize" in request.GET)
  
  response : requests.Response = requests.get("https://secure.runescape.com/m=hiscore_oldschool/index_lite.json?player=Suede")
  hiscores_data : dict = response.json()
  
  total_kc = 0
  for activity in hiscores_data.get("activities", []):
    if any([activity["name"].startswith(part) for part in ["League", "Deadman", "Bounty", "Clue", "LMS", "PvP", "Soul Wars", "Rifts", "Colosseum Glory", "Collections Logged"]]):
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
  
  review_pks = LetterboxdReview.objects.values_list('pk', flat=True)
  lbreview = LetterboxdReview.objects.get(pk = randint(1, len(review_pks)))
  
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
    return JsonResponse({ "error": "Invalid request type." }, status = 501)
  
  year = request.GET.get("year", 0)
  month = request.GET.get("month", 0)
  user = request.GET.get("user", None)
  
  if type(year) == str:
    year = int(year)
  if type(month) == str:
    month = int(month)
    
  year = 0 if year <= 0 else max(2023, min(2025, year))
  month = 0 if year == 0 else max(0, min(12, month))
  
  recap = OverallRecapData.objects.get(year = year, month = month)
  
  if user is not None:
    overallrecap = recap
    try:
      recap = UserRecapData.objects.get(overall_recap = overallrecap, twitch_user_id = user)
    except UserRecapData.DoesNotExist:
      return JsonResponse({ "error": "User not found." }, status = 404)
    
  data = {
    "count_messages": recap.count_messages,
    "count_characters": recap.count_characters,
    "count_clips": recap.count_clips,
    "count_clip_watch": recap.count_clip_watch,
    "count_clip_views": recap.count_clip_views,
    "count_chatters": recap.count_chatters,
    "count_video": recap.count_videos,
    "first_message": recap.first_message,
    "last_message": recap.last_message,
    "counters": recap.counters,
  }
  
  return JsonResponse(data, status = 200)
  

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
      user = TwitchUser.objects.get(login = altuser)
    except TwitchUser.DoesNotExist:
      return HttpResponse(f"User \"{altuser}\" does not exist.", 404)
  else:
    try:
      user = TwitchUser.objects.get(user_id = user_id)
    except TwitchUser.DoesNotExist:
      return HttpResponse("No messages found for this user.", 404)
  
  nightbot_response_url = request.META.get("HTTP_NIGHTBOT_RESPONSE_URL", "")
  
  if (nightbot_response_url != ""):
    post_random_message.delay(user.user_id, nightbot_response_url)
    return HttpResponse(" ", 200)
  
  return HttpResponse(get_random_message(user), 200)