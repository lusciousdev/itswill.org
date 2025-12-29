from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from allauth.socialaccount.providers.twitch.provider import (
    TwitchAccount,
    TwitchProvider,
)

from .views import TwitchChatbotOAuth2Adapter


class TwitchChatbotProvider(TwitchProvider):
    id = "twitch_chatbot"
    name = "Twitch Chatbot"
    oauth2_adapter_class = TwitchChatbotOAuth2Adapter

    def get_default_scope(self):
        return ["user:read:chat", "user:write:chat", "user:bot"]


provider_classes = [TwitchChatbotProvider]
