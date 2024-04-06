from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from celery import Celery, shared_task
from celery.schedules import crontab
from random import randint

from .models import *

@csrf_exempt
def get_random_message(request):
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
    
  user_message_set = ChatMessage.objects.filter(commenter = user)
  
  user_message_count = user_message_set.count()
  random_message = user_message_set.all()[randint(0, user_message_count - 1)]
  
  response_str = random_message.localtz_str()
  
  if len(response_str) >= 380:
    response_str = response_str[:375] + "..."
  
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
def test_endpoint(request):
  if request.method != 'GET':
    return HttpResponse("Invalid request type.", 501)
  
  char_count = request.GET.get("characters", 400)
  
  try:
    char_count = int(char_count)
  except ValueError:
    char_count = 400
    
  return HttpResponse("A" * char_count, 200)