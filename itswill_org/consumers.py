import json
import logging

from allauth.socialaccount.models import SocialAccount
from asgiref.sync import async_to_sync
from channels.auth import UserLazyObject
from channels.generic.websocket import WebsocketConsumer
from django.core.exceptions import FieldDoesNotExist
from django.urls import reverse
from django.utils import timezone

from .models import *

logger = logging.getLogger("django")


class RecapConsumer(WebsocketConsumer):
    def connect(self):
        logger.debug("Connection attempt started...")

        recap_year = self.scope["url_route"]["kwargs"].get("year", 0)
        recap_month = self.scope["url_route"]["kwargs"].get("month", 0)

        recap = f"{recap_year}{recap_month:02}"
        self.group_name = recap

        logger.debug(f"Subscribing to recap {recap}")

        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

    def receive(self, text_data = None, bytes_data = None):
        pass

    def recap_update(self, event : dict):
        self.send(text_data = json.dumps(event.get("data", {})))
