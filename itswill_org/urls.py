from django.urls import path

from . import views

app_name = 'itswill_org'
urlpatterns = [
  path("", views.IndexView.as_view(), name="index"),
  path("pets", views.PetsView.as_view(), name="pets"),
  path("month/", views.MonthListView.as_view(), name="month_list"),
  path("month/<int:year>/<int:month>/", views.MonthView.as_view(), name="month"),
]