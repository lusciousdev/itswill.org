from django.urls import path, re_path

from . import consumers

websocket_urlpatterns = [
    path("ws/recap/", consumers.RecapConsumer.as_asgi(), name="ws_recap_alltime"),
    path(
        "ws/recap/<int:year>/", consumers.RecapConsumer.as_asgi(), name="ws_recap_year"
    ),
    path(
        "ws/recap/<int:year>/<int:month>/",
        consumers.RecapConsumer.as_asgi(),
        name="ws_recap_month",
    ),
]
