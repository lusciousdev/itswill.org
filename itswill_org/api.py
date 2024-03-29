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
  
  return HttpResponse(str(random_message), 200)