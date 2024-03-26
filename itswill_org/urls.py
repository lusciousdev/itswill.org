from django.urls import path
from django.views.decorators.cache import cache_page

import datetime

from . import views

app_name = 'itswill_org'
urlpatterns = [
  path("", views.IndexView.as_view(), name="index"),
  path("pets", views.PetsView.as_view(), name="pets"),
  path("month/", views.MonthListView.as_view(), name="month_list"),
  path("month/<int:year>/<int:month>/", cache_page(60 * 60)(views.MonthView.as_view()), name="month"),
  path("recap/", views.RecapView.as_view(), kwargs = { "year": datetime.datetime.now().year, "month": -1, "username": None }, name="recap"),
  path("recap/<int:year>/", views.RecapView.as_view(), kwargs = { "month": -1, "username": None }, name="recap_year"),
  path("recap/<int:year>/<int:month>/", views.RecapView.as_view(), kwargs = { "username": None }, name = "recap_month"),
  path("recap/<int:year>/<str:username>/", views.RecapView.as_view(), kwargs = { "month": -1 }, name = "recap_year_user"),
  path("recap/<int:year>/<int:month>/<str:username>/", views.RecapView.as_view(), name = "recap_month_user"),
  path("recap/redirect/", views.get_recap, name = "recap_redirect"),
]