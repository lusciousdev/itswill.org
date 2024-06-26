
from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views import generic
from django.conf import settings

import typing
import datetime
import calendar
import pytz

from .models import *

# Create your views here.

class IndexView(generic.TemplateView):
  template_name = "itswill_org/index.html"
  
class MonthListView(generic.TemplateView):
  template_name = "itswill_org/monthlist.html"
  
  def get_context_data(self, **kwargs):
    data = super().get_context_data(**kwargs)
    
    data["monthly_recaps"] = {}
    
    for recap in OverallRecapData.objects.filter(month__gte = 1).all():
      if recap.year not in data["monthly_recaps"]:
        data["monthly_recaps"][recap.year] = {}
        
      
      data["monthly_recaps"][recap.year][recap.month] = {
        "month_name": datetime.datetime(recap.year, recap.month, 1, 12, 0, 0).strftime("%B"),
        "recap": recap,
      }
      
    data["monthly_recaps"] = dict(sorted(data["monthly_recaps"].items(), key = lambda kvp: kvp[0]))
    
    for year, month_dict in data["monthly_recaps"].items():
      data["monthly_recaps"][year] = dict(sorted(data["monthly_recaps"][year].items(), key = lambda kvp: kvp[0]))
      
    return data
  
class MonthView(generic.TemplateView):
  template_name = "itswill_org/month.html"
  
  def dispatch(self, request, year, month, *args, **kwargs):
    try:
      monthlyrecap = OverallRecapData.objects.get(year = year, month = month)
      return super(MonthView, self).dispatch(request, year = year, month = month, *args, **kwargs)
    except OverallRecapData.DoesNotExist:
      raise Http404("This months data has not been collected yet.")
  
  def get_context_data(self, year, month, **kwargs):
    data = super().get_context_data(**kwargs)
    
    try:
      monthlyrecap = OverallRecapData.objects.get(year = year, month = month)
    except OverallRecapData.DoesNotExist:
      print("ERROR: MISSING MONTHLY RECAP, NOT REDIRECTED BY DISPATCH")
      return data
    
    localtz = pytz.timezone("America/Los_Angeles")
    monthrange = calendar.monthrange(year, month)
    
    start_date = datetime.datetime(year, month, 1, 0, 0, 0, 1, localtz)
    end_date = datetime.datetime(year, month, monthrange[1], 23, 59, 59, 999, localtz)
    
    data["start_date"] = start_date.strftime("%Y/%m/%d")
    data["end_date"] = end_date.strftime("%Y/%m/%d")
    
    monthlychatters = monthlyrecap.userrecapdata_set
    
    clips = Clip.objects.filter(created_at__range = (start_date, end_date)).order_by("-view_count")
    
    data["top_clips"] = clips[:10]
    
    data["clip_count"] = monthlyrecap.count_clips
    data["message_count"] = monthlyrecap.count_messages
    data["clip_views"] = monthlyrecap.count_clip_views
    data["chatter_count"] = monthlyrecap.count_chatters
    data["vod_count"] = monthlyrecap.count_videos
    
    chatter_list = monthlychatters.order_by("-count_messages")
    clipper_list = monthlychatters.order_by("-count_clips")
    
    data['top_chatters'] = chatter_list[:10]
    data['top_clippers'] = clipper_list[:10]
    
    return data
  
class PetsView(generic.TemplateView):
  template_name = "itswill_org/pets.html"
  
  def get_context_data(self, **kwargs):
    data = super().get_context_data(**kwargs)
    
    data["acquired_pets"] = Pet.objects.filter(acquired = True).order_by("date").all()
    data["unacquired_pets"] = Pet.objects.filter(acquired = False).order_by("name").all()
    
    data["total_pets"] = Pet.objects.all().count()
    
    return data
  
class RecapView(generic.TemplateView):
  template_name = "itswill_org/recap.html"
  
  def get_context_data(self, year : int, month : int, username : str, **kwargs):
    data = super().get_context_data(**kwargs)
    
    data["month_abbr"] = calendar.month_abbr
    data["all_recaps"] = {}
    
    for yearrecap in OverallRecapData.objects.filter(month = 0).order_by("year").all():
      data["all_recaps"][yearrecap.year] = {
        "recap": yearrecap,
        "month_recaps": {}
      }
      
      for monthrecap in OverallRecapData.objects.filter(year = yearrecap.year, month__gte = 1).order_by("month").all():
        data["all_recaps"][monthrecap.year]["month_recaps"][monthrecap.month] = {
          "month_name": calendar.month_abbr[monthrecap.month],
          "recap": monthrecap
        }
    
    try:
      overallrecap = OverallRecapData.objects.get(year = year, month = month)
    except OverallRecapData.DoesNotExist:
      raise Http404("That recap does not exist (yet?).")
    
    if username is None:
      data["overall_recap"] = True
      data["recap_data"] = overallrecap
      return data
    else:
      try:
        twitchuser = TwitchUser.objects.get(display_name__iexact = username)
      except TwitchUser.DoesNotExist:
        raise Http404("That user does not exist or has not chatted.")
      
      try:
        userrecap = UserRecapData.objects.get(overall_recap = overallrecap, twitch_user = twitchuser)
      except UserRecapData.DoesNotExist:
        raise Http404("No data for that user in this period.")
      
      data["overall_recap"] = False
      data["recap_data"] = userrecap
      data["twitchuser"] = twitchuser
      
      return data
    
@csrf_exempt
def get_recap(request):
  year = str(datetime.datetime.now().year)
  month = str(0)
  username = None
  if request.method == 'POST':
    year     = request.POST.get("year", year)
    month    = request.POST.get("month", month)
    username = request.POST.get("username", username)
  if request.method == "GET":
    year     = request.GET.get("year", year)
    month    = request.GET.get("month", month)
    username = request.GET.get("username", username)
    
  username = None if username == "" else username
  try:
    year = int(year)
  except:
    year = datetime.datetime.now().year
    
  try:
    month = int(month)
  except:
    month = 0
  
  if username is None:
    if month > 0:
      return HttpResponseRedirect(reverse("itswill_org:recap_month", kwargs = { 'year': year, 'month': month }))
    else:
      return HttpResponseRedirect(reverse("itswill_org:recap_year", kwargs = { 'year': year }))
  else:
    if month > 0:
      return HttpResponseRedirect(reverse("itswill_org:recap_month_user", kwargs = { 'year': year, 'month': month, 'username': username }))
    else:
      return HttpResponseRedirect(reverse("itswill_org:recap_year_user", kwargs = { 'year': year, 'username': username }))
  
class LeaderboardView(generic.TemplateView):
  template_name = "itswill_org/leaderboard.html"
  
  def get_context_data(self, year : int, month : int, **kwargs):
    data = super().get_context_data(**kwargs)
    
    data["month_abbr"] = calendar.month_abbr
    data["all_recaps"] = {}
    
    for yearrecap in OverallRecapData.objects.filter(month = 0).order_by("year").all():
      data["all_recaps"][yearrecap.year] = {
        "recap": yearrecap,
        "month_recaps": {}
      }
      
      for monthrecap in OverallRecapData.objects.filter(year = yearrecap.year, month__gte = 1).order_by("month").all():
        data["all_recaps"][monthrecap.year]["month_recaps"][monthrecap.month] = {
          "month_name": calendar.month_abbr[monthrecap.month],
          "recap": monthrecap
        }
    
    try:
      overallrecap = OverallRecapData.objects.get(year = year, month = month)
    except OverallRecapData.DoesNotExist:
      raise Http404("That recap does not exist (yet?).")
    
    data["recap_data"] = overallrecap
    
    userrecapset = overallrecap.userrecapdata_set.all()
    
    data["top_messages"] = userrecapset.order_by("-count_messages")[:10]
    data["top_clips"]    = userrecapset.order_by("-count_clips")[:10]
    data["top_views"]    = userrecapset.order_by("-count_clip_views")[:10]
    
    data["top_seven"] = userrecapset.order_by("-count_seven")[:10]
    data["top_pound"] = userrecapset.order_by("-count_pound")[:10]
    data["top_love"]  = userrecapset.order_by("-count_love")[:10]
    
    data["top_etsmg"] = userrecapset.order_by("-count_etsmg")[:10]
    data["top_ksmg"]  = userrecapset.order_by("-count_ksmg")[:10]
    data["top_stsmg"] = userrecapset.order_by("-count_stsmg")[:10]
    
    data["top_pog"]   = userrecapset.order_by("-count_pog")[:10]
    data["top_shoop"] = userrecapset.order_by("-count_shoop")[:10]
    data["top_gasp"]  = userrecapset.order_by("-count_gasp")[:10]
    data["top_pogo"]  = userrecapset.order_by("-count_pogo")[:10]
    data["top_monka"] = userrecapset.order_by("-count_monka")[:10]
    
    data["top_giggle"] = userrecapset.order_by("-count_giggle")[:10]
    data["top_lul"]    = userrecapset.order_by("-count_lul")[:10]
    
    data["top_sneak"] = userrecapset.order_by("-count_sneak")[:10]
    data["top_sit"]   = userrecapset.order_by("-count_sit")[:10]
    
    data["top_mmylc"]  = userrecapset.order_by("-count_mmylc")[:10]
    data["top_dance"]  = userrecapset.order_by("-count_dance")[:10]
    data["top_vvkool"] = userrecapset.order_by("-count_vvkool")[:10]
    
    data["top_spin"]    = userrecapset.order_by("-count_spin")[:10]
    data["top_chicken"] = userrecapset.order_by("-count_chicken")[:10]
    data["top_sonic"]   = userrecapset.order_by("-count_sonic")[:10]
    data["top_dankies"] = userrecapset.order_by("-count_dankies")[:10]
    
    data["top_cum"] = userrecapset.order_by("-count_cum")[:10]
    
    return data
  
class CopyPasteView(generic.ListView):
  model = CopyPasteGroup
  template_name = "itswill_org/pasta.html"
  
  ordering = ['title']
  
class AsciiView(generic.ListView):
  model = Ascii
  template_name = "itswill_org/ascii.html"
  
  ordering = ['title']