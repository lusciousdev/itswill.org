from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from celery import Celery, shared_task
from celery.schedules import crontab
import requests
from random import randint
import time

from .tasks import get_random_message, post_random_message
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
    
  start_time = time.time()
  
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
    
  user_message_set = ChatMessage.objects.filter(commenter = user).all()
  
  user_message_count = user_message_set.count()
  random_message = user_message_set[randint(0, user_message_count - 1)]
  
  response_str = random_message.localtz_str()
  
  if len(response_str) >= 380:
    response_str = response_str[:375] + "..."
  
  end_time = time.time()
  
  print(f"Response time: {end_time - start_time}")
  
  return HttpResponse(response_str, 200)

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
  return HttpResponse(", ".join([str(pet) for pet in pets_left]), 200)

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
    post_random_message.delay(user, nightbot_response_url)
    return HttpResponse("Fetching messages...", 200)
  
  return HttpResponse(get_random_message(user), 200)