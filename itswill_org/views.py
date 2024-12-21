
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
    
    data["drinfo"] = {}
    
    for pet in data["acquired_pets"]:
      data["drinfo"][pet.name] = {}
      if (pet.killcount_known and pet.drop_rate_known) and (not pet.secondary_killcount_needed or pet.secondary_drop_rate_known):
        data["drinfo"][pet.name]["show"] = True
        percent = (pet.killcount / pet.drop_rate)
        if pet.secondary_killcount_needed:
          percent += (pet.secondary_killcount / pet.secondary_drop_rate)
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
          
        data['drinfo'][pet.name]["class"] = divclass
      else:
        data["drinfo"][pet.name]["show"] = False
        data["drinfo"][pet.name]["percent"] = 0
        data["drinfo"][pet.name]["class"] = "no-drop-rate-info"
      
    return data
  
class RecapView(generic.TemplateView):
  template_name = "itswill_org/recap.html"
  
  def get_context_data(self, year : int, month : int, username : str, **kwargs):
    data = super().get_context_data(**kwargs)
    
    data["month_abbr"] = calendar.month_abbr
    data["all_recaps"] = {}
    
    try:
      data["all_recaps"]["alltime"] = {
        "recap": OverallRecapData.objects.get(year = 0, month = 0),
        "month_recaps": {},
      }
    except OverallRecapData.DoesNotExist:
      pass
    
    for yearrecap in OverallRecapData.objects.filter(year__gte = 1, month = 0).order_by("year").all():
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
    else:
      try:
        twitchuser = TwitchUser.objects.get(display_name__iexact = username)
      except TwitchUser.DoesNotExist:
        try:
          twitchuser = TwitchUser.objects.get(login__iexact = username)
        except:
          raise Http404("That user does not exist or has not chatted.")
      
      try:
        userrecap = UserRecapData.objects.get(overall_recap = overallrecap, twitch_user = twitchuser)
      except UserRecapData.DoesNotExist:
        raise Http404("No data for that user in this period.")
      
      data["overall_recap"] = False
      data["recap_data"] = userrecap
      data["twitchuser"] = twitchuser
    
    data["counters"] = {}
    for field in data["recap_data"]._meta.get_fields():
      if ((field.get_internal_type() == "IntegerField" or field.get_internal_type() == "BigIntegerField")):
        if (type(field) == StringCountField):
          data["counters"][field.name] = {}
          data["counters"][field.name]["label"] = field.verbose_name
          data["counters"][field.name]["count"] = getattr(data["recap_data"], field.name)
          data["counters"][field.name]["show"] = field.show_recap
          if field.use_images:
            data["counters"][field.name]["image_list"] = field.emote_list
          else:
            data["counters"][field.name]["image_list"] = None
      
    return data
    
@csrf_exempt
def get_recap(request):
  year = str(0)
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
    year = 0
    
  try:
    month = int(month)
  except:
    month = 0
  
  if username is None:
    if year > 0:
      if month > 0:
        return HttpResponseRedirect(reverse("itswill_org:recap_month", kwargs = { 'year': year, 'month': month }))
      else:
        return HttpResponseRedirect(reverse("itswill_org:recap_year", kwargs = { 'year': year }))
    else:
      return HttpResponseRedirect(reverse("itswill_org:recap"))
  else:
    if year > 0:
      if month > 0:
        return HttpResponseRedirect(reverse("itswill_org:recap_month_user", kwargs = { 'year': year, 'month': month, 'username': username }))
      else:
        return HttpResponseRedirect(reverse("itswill_org:recap_year_user", kwargs = { 'year': year, 'username': username }))
    else:
      return HttpResponseRedirect(reverse("itswill_org:recap_user", kwargs = { "username": username }))
  
class Wrapped2024View(generic.TemplateView):
  template_name = "itswill_org/2024-wrapped.html"
  
  def get_context_data(self, **kwargs):
    data = super().get_context_data(**kwargs)
    
    try:
      overall_wrapped = OverallWrappedData.objects.get(year = 2024)
    except OverallWrappedData.DoesNotExist:
      raise Http404("That recap does not exist (yet?).")
    
    data["wrapped"] = overall_wrapped
      
    return data
  
class Wrapped2024UserView(generic.TemplateView):
  template_name = "itswill_org/2024-wrapped-user.html"
  
  def get_context_data(self, username : str, **kwargs):
    data = super().get_context_data(**kwargs)
    
    try:
      overall_wrapped = OverallWrappedData.objects.get(year = 2024)
    except OverallWrappedData.DoesNotExist:
      raise Http404("That recap does not exist (yet?).")
    
    try:
      twitchuser = TwitchUser.objects.get(display_name__iexact = username)
    except TwitchUser.DoesNotExist:
      try:
        twitchuser = TwitchUser.objects.get(login__iexact = username)
      except:
        raise Http404("That user does not exist or has not chatted.")
    
    try:
      user_wrapped = UserWrappedData.objects.get(overall_wrapped = overall_wrapped, twitch_user = twitchuser)
    except UserRecapData.DoesNotExist:
      raise Http404("No data for that user in this period.")
    
    data["wrapped"] = {}
    data["wrapped"]["overall"] = overall_wrapped
    data["wrapped"]["user"]    = user_wrapped
    
    top_boards = {}
    for field_name, (position, count) in user_wrapped.extra_data["top_leaderboard_positions"]:
      field = user_wrapped.recap._meta.get_field(field_name)
      if ((field.get_internal_type() == "IntegerField" or field.get_internal_type() == "BigIntegerField")):
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
    
@csrf_exempt
def get_wrapped(request):
  username = None
  if request.method == 'POST':
    username = request.POST.get("username", username)
  if request.method == "GET":
    username = request.GET.get("username", username)
    
  username = None if username == "" else username
  
  if username is None:
    return HttpResponseRedirect(reverse("itswill_org:wrapped"))
  else:
    return HttpResponseRedirect(reverse("itswill_org:wrapped_user", kwargs = { 'username': username }))
      
  
class LeaderboardView(generic.TemplateView):
  template_name = "itswill_org/all-leaderboards.html"
  
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
    data["limit"] = 10
    
    data["labels"] = {}
    
    for field in overallrecap._meta.get_fields():
      if ((field.get_internal_type() == "IntegerField" or field.get_internal_type() == "BigIntegerField")):
        labelkey = field.name
        if type(field) in [StatField, BigStatField, StringCountField]:
          labelkey = field.short_name
        data["labels"][labelkey] = {}
        data["labels"][labelkey]["label"] = field.verbose_name
        if (type(field) == StringCountField and field.use_images):
          data["labels"][labelkey]["image_list"] = field.emote_list
        else:
          data["labels"][labelkey]["image_list"] = None
    
    return data
  
class SingleLeaderboardView(generic.TemplateView):
  template_name = "itswill_org/single-leaderboard.html"
  
  def get_context_data(self, year : int, month : int, name : str, **kwargs):
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
    data["leaderboard_name"] = name
    
    data["labels"] = {}
    
    for field in overallrecap._meta.get_fields():
      if ((field.get_internal_type() == "IntegerField" or field.get_internal_type() == "BigIntegerField")):
        labelkey = field.name
        if type(field) in [StatField, BigStatField, StringCountField]:
          labelkey = field.short_name
        data["labels"][labelkey] = {}
        data["labels"][labelkey]["label"] = field.verbose_name
        if (type(field) == StringCountField and field.use_images):
          data["labels"][labelkey]["image_list"] = field.emote_list
        else:
          data["labels"][labelkey]["image_list"] = None
    
    return data
  
class CopyPasteView(generic.ListView):
  model = CopyPasteGroup
  template_name = "itswill_org/pasta.html"
  
  ordering = ['title']
  
class AsciiView(generic.ListView):
  model = Ascii
  template_name = "itswill_org/ascii.html"
  
  ordering = ['title']