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
  
  path("recap/",                                       cache_page(5 * 60)(views.RecapView.as_view()), kwargs = { "year": 0, "month": 0, "username": None }, name="recap"),
  path("recap/<int:year>/",                            cache_page(5 * 60)(views.RecapView.as_view()), kwargs = { "month": 0, "username": None }, name="recap_year"),
  path("recap/<int:year>/<int:month>/",                cache_page(5 * 60)(views.RecapView.as_view()), kwargs = { "username": None }, name = "recap_month"),
  path("recap/all/<str:username>/",                    views.RecapView.as_view(), kwargs = { "year": 0, "month": 0 }, name = "recap_user"),
  path("recap/<int:year>/<str:username>/",             views.RecapView.as_view(), kwargs = { "month": 0 }, name = "recap_year_user"),
  path("recap/<int:year>/<int:month>/<str:username>/", views.RecapView.as_view(), name = "recap_month_user"),
  
  path("recap/redirect/", views.get_recap, name = "recap_redirect"),
  
  path("leaderboard/",                        cache_page(60)(views.LeaderboardView.as_view()), kwargs = { "year": 0, "month": 0 }, name="leaderboard"),
  path("leaderboard/<int:year>/",             cache_page(60)(views.LeaderboardView.as_view()), kwargs = { "month": 0 }, name="leaderboard_year"),
  path("leaderboard/<int:year>/<int:month>/", cache_page(60)(views.LeaderboardView.as_view()), name="leaderboard_month"),
  
  path("leaderboard/<str:name>/",                        cache_page(60)(views.SingleLeaderboardView.as_view()), kwargs = { "year": 0, "month": 0 }, name = "single_leaderboard"),
  path("leaderboard/<int:year>/<str:name>/",             cache_page(60)(views.SingleLeaderboardView.as_view()), kwargs = { "month": 0 }, name = "single_leaderboard_year"),
  path("leaderboard/<int:year>/<int:month>/<str:name>/", cache_page(60)(views.SingleLeaderboardView.as_view()), name = "single_leaderboard_month"),
  
  path("wrapped/", cache_page(60)(views.Wrapped2024View.as_view()), name="wrapped"),
  path("wrapped/user/<str:username>/", views.Wrapped2024UserView.as_view(), name="wrapped_user"),
  
  path("wrapped/redirect/", views.get_wrapped, name = "wrapped_redirect"),
  
  path("census/", views.CensusView.as_view(), name="census"),
  
  path("pasta/", views.CopyPasteView.as_view(), name="pasta"),
  path("ascii/", views.AsciiView.as_view(), name="ascii"),
  
  path("api/v1/randmsg/",      api.get_random_message_api,              name = "api_random_message"),
  path("api/v1/randuser/",     api.get_random_user_api,                 name = "api_random_user"),
  path("api/v1/randreview/",   api.get_random_letterboxd_review,        name = "api_movie_review"),
  path("api/v1/lastmsg/",      api.get_last_message_api,                name = "api_last_message"),
  path("api/v1/lastmsg/2024/", api.get_last_message_2024_api,           name = "api_last_message_2024"),
  path("api/v1/randclip/",     api.get_random_clip,                     name = "api_random_clip"),
  path("api/v1/pets/",         api.get_pets_message,                    name = "api_pets_message"),
  path("api/v1/recentpet/",    api.get_most_recent_pet,                 name = "api_recent_pet"),
  path("api/v1/petsleft/",     api.get_pets_left,                       name = "api_pets_left"),
  path("api/v1/randgarf/",     api.get_random_garfield,                 name = "api_random_garfield"),
  path("api/v1/five/",         api.get_live_at_five_record,             name = "api_five_record"),
  path("api/v1/totalkc/",      cache_page(10 * 60)(api.get_boss_count), name = "api_total_boss_kc"),
  path("api/v1/test/",         api.test_endpoint,                       name = "api_test"),
]