from django.urls import path
from django.views.decorators.cache import cache_page

import datetime

from . import views
from . import api

app_name = 'itswill_org'
urlpatterns = [
  path("", views.IndexView.as_view(), name="index"),
  path("pets/", views.PetsView.as_view(), name="pets"),
  path("month/", views.MonthListView.as_view(), name="month_list"),
  path("month/<int:year>/<int:month>/", cache_page(60 * 60)(views.MonthView.as_view()), name="month"),
  
  path("recap/",                                       cache_page(60 * 60)(views.RecapView.as_view()), kwargs = { "year": datetime.datetime.now().year, "month": 0, "username": None }, name="recap"),
  path("recap/<int:year>/",                            cache_page(60 * 60)(views.RecapView.as_view()), kwargs = { "month": 0, "username": None }, name="recap_year"),
  path("recap/<int:year>/<int:month>/",                cache_page(60 * 60)(views.RecapView.as_view()), kwargs = { "username": None }, name = "recap_month"),
  path("recap/<int:year>/<str:username>/",             views.RecapView.as_view(), kwargs = { "month": 0 }, name = "recap_year_user"),
  path("recap/<int:year>/<int:month>/<str:username>/", views.RecapView.as_view(), name = "recap_month_user"),
  
  path("recap/redirect/", views.get_recap, name = "recap_redirect"),
  
  path("leaderboard/",                        cache_page(60 * 60)(views.LeaderboardView.as_view()), kwargs = { "year": datetime.datetime.now().year, "month": 0 }, name="leaderboard"),
  path("leaderboard/<int:year>/",             cache_page(60 * 60)(views.LeaderboardView.as_view()), kwargs = { "month": 0 }, name="leaderboard_year"),
  path("leaderboard/<int:year>/<int:month>/", cache_page(60 * 60)(views.LeaderboardView.as_view()), name="leaderboard_month"),
  
  path("pasta/", views.CopyPasteView.as_view(), name="pasta"),
  path("ascii/", views.AsciiView.as_view(), name="ascii"),
  
  path("api/v1/randmsg/",   api.get_random_message_api,  name = "api_random_message"),
  path("api/v1/randclip/",  api.get_random_clip,     name = "api_random_clip"),
  path("api/v1/pets/",      api.get_pets_message,    name = "api_pets_message"),
  path("api/v1/recentpet/", api.get_most_recent_pet, name = "api_recent_pet"),
  path("api/v1/petsleft/",  api.get_pets_left,       name = "api_pets_left"),
  path("api/v1/randgarf",   api.get_random_garfield, name = "api_random_garfield"),
  path("api/v1/test/",      api.test_endpoint,       name = "api_test"),
]