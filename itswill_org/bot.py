import asyncio
import datetime
import logging
import os
import sys
import time
import typing

import django
import luscioustwitch
import twitchio
import twitchio.authentication
import twitchio.eventsub
from asgiref.sync import async_to_sync, sync_to_async
from django.db.utils import IntegrityError
from twitchio.ext import commands as twitchio_commands
from twitchio.ext import routines as twitchio_routines

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

django.setup()

from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.conf import settings

from itswill_org.models import *

LOGGER: logging.Logger = logging.getLogger("bot")


BOT_ID = "1062442212"
OWNER_ID = "82920215"
BROADCASTER_ID = "43246220"


class LoggerBot(twitchio_commands.Bot):
    fragments: list[Fragment] = []

    def __init__(self):
        super().__init__(
            client_id=settings.TWITCH_API_CLIENT_ID,
            client_secret=settings.TWITCH_API_CLIENT_SECRET,
            bot_id=BOT_ID,
            owner_id=OWNER_ID,
            prefix="?",
        )

    async def add_token(
        self, token: str, refresh: str
    ) -> twitchio.authentication.ValidateTokenPayload:
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(
            token, refresh
        )

        account = None
        try:
            account = await SocialAccount.objects.aget(
                provider="twitch", uid=resp.user_id
            )
        except SocialAccount.DoesNotExist:
            LOGGER.debug(f"Token added for unknown user: {resp.user_id}")
            return resp

        if account:
            await SocialToken.objects.aupdate_or_create(
                account=account,
                defaults={
                    "token": token,
                    "token_secret": refresh,
                    "expires_at": datetime.datetime.now(tz=datetime.UTC)
                    + datetime.timedelta(seconds=resp.expires_in),
                },
            )

        return resp

    async def load_tokens(self, path: str | None = None) -> None:
        bot_account = await SocialAccount.objects.aget(
            provider="twitch", uid=self.bot_id
        )
        bot_token = await SocialToken.objects.aget(account=bot_account)

        _ = await self.add_token(bot_token.token, bot_token.token_secret)

    async def event_ready(self) -> None:
        LOGGER.debug(f"Successfully logged in as: {self.bot_id}")

        subscriptions = [
            twitchio.eventsub.ChatMessageSubscription(
                broadcaster_user_id=BROADCASTER_ID, user_id=self.bot_id
            ),
        ]

        resp: twitchio.eventsub.SubscriptionResponse|None = await self.subscribe_websocket(payload=subscriptions[0])

        if resp is None:
            LOGGER.error("Failed to subscribe to chat messages.")
            raise twitchio.TwitchioException("Failed to subscribe")

    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        try:
            twitch_user = await TwitchUser.objects.aget(user_id=payload.chatter.id)
            new_chatter = False
        except TwitchUser.DoesNotExist:
            tio_user: twitchio.User = await payload.chatter.user()

            new_chatter = True
            twitch_user = await TwitchUser.objects.acreate(
                user_id=payload.chatter.id,
                login=payload.chatter.name,
                display_name=payload.chatter.display_name,
                user_type=tio_user.type,
                broadcaster_type=tio_user.broadcaster_type,
                description=tio_user.description,
                profile_image_url=(
                    tio_user.profile_image if tio_user.profile_image else ""
                ),
                offline_image_url=(
                    tio_user.offline_image if tio_user.offline_image else ""
                ),
                created_at=tio_user.created_at,
            )

        new_message = True
        try:
            message: ChatMessage = await ChatMessage.objects.acreate(
                commenter=twitch_user,
                message_id=payload.id,
                content_offset=-1,
                created_at=payload.timestamp,
                message=payload.text,
            )

            emotes = []
            for frag in payload.fragments:
                if frag.emote is not None:
                    twitch_emote, _ = await TwitchEmote.objects.aget_or_create(
                        emote_id=frag.emote.id, defaults={"name": frag.text}
                    )
                    emotes.append(twitch_emote)

            await message.emotes.aadd(*emotes)
        except IntegrityError:
            new_message = False

        if new_message:
            year = datetime.datetime.now(TIMEZONE).year
            month = datetime.datetime.now(TIMEZONE).month

            alltimerecap, _ = await OverallRecapData.objects.aget_or_create(
                year=0, month=0
            )
            yearrecap, _ = await OverallRecapData.objects.aget_or_create(
                year=year, month=0
            )
            monthrecap, _ = await OverallRecapData.objects.aget_or_create(
                year=year, month=month
            )

            user_alltime, _ = await UserRecapData.objects.aget_or_create(
                overall_recap=alltimerecap, twitch_user=twitch_user
            )
            user_year, _ = await UserRecapData.objects.aget_or_create(
                overall_recap=yearrecap, twitch_user=twitch_user
            )
            user_month, _ = await UserRecapData.objects.aget_or_create(
                overall_recap=monthrecap, twitch_user=twitch_user
            )

            if new_chatter:
                for r in [alltimerecap, yearrecap, monthrecap]:
                    r.count_chatters += 1

            r: typing.Union[OverallRecapData, UserRecapData]
            for r in [
                alltimerecap,
                yearrecap,
                monthrecap,
                user_alltime,
                user_year,
                user_month,
            ]:
                r.count_messages += 1
                r.count_characters += len(message.message)
                r.last_message = message.message

            fragments = await sync_to_async(list)(
                await sync_to_async(
                    (await sync_to_async(Fragment.objects.select_related)("group")).all
                )()
            )
            fragment_regex = {f.pretty_name: f.match_regex for f in fragments}
            new_matches: list[FragmentMatch] = []
            for f in fragments:
                frag_count = len(fragment_regex[f.pretty_name].findall(message.message))
                if frag_count > 0:
                    fm = FragmentMatch(
                        fragment=f,
                        message=message,
                        count=frag_count if f.group.count_multiples else 1,
                        timestamp=message.created_at,
                        commenter_id=message.commenter.user_id,
                    )

                    new_matches.append(fm)

                    r: typing.Union[OverallRecapData, UserRecapData]
                    for r in [
                        alltimerecap,
                        yearrecap,
                        monthrecap,
                        user_alltime,
                        user_year,
                        user_month,
                    ]:
                        if f.group.group_id not in r.counters:
                            r.counters[f.group.group_id] = {"total": 0, "members": {}}

                        if f.pretty_name not in r.counters[f.group.group_id]["members"]:
                            r.counters[f.group.group_id]["members"][f.pretty_name] = 0

                        r.counters[f.group.group_id]["total"] += fm.count
                        r.counters[f.group.group_id]["members"][
                            f.pretty_name
                        ] += fm.count

            await FragmentMatch.objects.abulk_create(
                new_matches,
                update_conflicts=True,
                update_fields=["count", "timestamp", "commenter_id"],
            )
            await OverallRecapData.objects.abulk_update(
                [alltimerecap, yearrecap, monthrecap],
                fields=[
                    "count_messages",
                    "count_characters",
                    "count_chatters",
                    "last_message",
                    "counters",
                ],
            )
            await UserRecapData.objects.abulk_update(
                [user_alltime, user_year, user_month],
                fields=[
                    "count_messages",
                    "count_characters",
                    "last_message",
                    "counters",
                ],
            )


def main() -> None:
    twitchio.utils.setup_logging(level=logging.INFO)

    async def runner() -> None:
        async with LoggerBot() as bot:
            await bot.start(with_adapter=False)

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt...")


if __name__ == "__main__":
    main()
