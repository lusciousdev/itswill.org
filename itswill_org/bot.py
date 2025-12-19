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
from channels.layers import get_channel_layer
from channels_redis.core import RedisChannelLayer
from django.db.utils import IntegrityError
from twitchio.ext import commands as twitchio_commands
from twitchio.ext import routines as twitchio_routines

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

django.setup()

from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken
from django.conf import settings

from itswill_org.models import *
from itswill_org.tasks import *

LOGGER: logging.Logger = logging.getLogger("bot")


BOT_ID = "1062442212"
OWNER_ID = "82920215"
BROADCASTER_ID = "43246220"


class LoggerBot(twitchio_commands.Bot):
    channel_layer: RedisChannelLayer

    fragments: list[Fragment] = []

    def __init__(self):
        self.channel_layer = get_channel_layer()

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

        resp: twitchio.eventsub.SubscriptionResponse | None = (
            await self.subscribe_websocket(payload=subscriptions[0])
        )

        if resp is None:
            LOGGER.error("Failed to subscribe to chat messages.")
            raise twitchio.TwitchioException("Failed to subscribe")

    async def send_recap_update_message(
        self, year: int, month: int, data: dict[str, typing.Any]
    ):
        await self.channel_layer.group_send(
            f"{year}{month:02}", {"type": "recap_update", "data": data}
        )

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

            recaps = await sync_to_async(message_recap_queryset)(
                year, month, twitch_user.user_id
            )

            recaps_exist = await recaps.aexists()

            if recaps_exist:
                await recaps.aupdate(
                    count_messages=F("count_messages") + 1,
                    count_characters=F("count_characters") + len(message.message),
                    last_message=message,
                    count_chatters=(
                        F("count_chatters") + 1 if new_chatter else F("count_chatters")
                    ),
                )
                recaps = await sync_to_async(list)(recaps)
            else:
                recaps = await sync_to_async(get_message_recaps)(
                    year, month, twitch_user.user_id
                )

                recap: RecapData
                for recap in recaps:
                    recap.count_messages += 1
                    recap.count_characters += len(message.message)
                    recap.last_message = message
                    if new_chatter:
                        recap.count_chatters += 1

            fragments = await sync_to_async(list)(
                await sync_to_async(
                    (await sync_to_async(Fragment.objects.select_related)("group")).all
                )()
            )
            fragment_regex = {f.pretty_name: f.match_regex for f in fragments}
            new_matches: list[FragmentMatch] = []

            fragmentgroups_updated = set()
            for f in fragments:
                frag_count = len(fragment_regex[f.pretty_name].findall(message.message))
                if frag_count > 0:
                    fragmentgroups_updated.add(f.group)

                    fm = FragmentMatch(
                        fragment=f,
                        message=message,
                        count=frag_count if f.group.count_multiples else 1,
                        timestamp=message.created_at,
                        commenter_id=message.commenter.user_id,
                    )

                    new_matches.append(fm)

                    recap: RecapData
                    for recap in recaps:
                        fgc_count = await recap.fragmentgroupcounter_set.filter(
                            fragment_group=f.group
                        ).aupdate(count=F("count") + fm.count)
                        if fgc_count == 0:
                            await FragmentGroupCounter.objects.acreate(
                                recap=recap,
                                fragment_group=f.group,
                                year=recap.year,
                                month=recap.month,
                                twitch_user=twitch_user,
                                count=fm.count,
                            )

                        fc_count = await recap.fragmentcounter_set.filter(
                            fragment=f
                        ).aupdate(count=F("count") + fm.count)
                        if fc_count == 0:
                            await FragmentCounter.objects.acreate(
                                recap=recap,
                                fragment=f,
                                year=recap.year,
                                month=recap.month,
                                twitch_user=twitch_user,
                                count=fm.count,
                            )

            await FragmentMatch.objects.abulk_create(
                new_matches,
                update_conflicts=True,
                update_fields=["count", "timestamp", "commenter_id"],
            )

            fragment_recaps: list = []
            for fm in new_matches:
                rs = await sync_to_async(get_message_recaps)(
                    fm.timestamp, fm.commenter_id
                )
                for recap in rs:
                    fr = FragmentMatch.recaps.through(
                        fragmentmatch_id=fm.id, recapdata_id=recap.id
                    )

            await FragmentMatch.recaps.through.objects.abulk_create(
                fragment_recaps, batch_size=5_000
            )

            await RecapData.objects.abulk_update(
                recaps,
                fields=[
                    "count_messages",
                    "count_characters",
                    "count_chatters",
                    "last_message",
                ],
            )

            overall_recaps = filter(lambda r: r.twitch_user is None, recaps)

            for recap in overall_recaps:
                fragment_group_counters = await sync_to_async(list)(
                    await sync_to_async(
                        FragmentGroupCounter.objects.filter(
                            Q(recap=recap)
                            & Q(fragment_group__in=fragmentgroups_updated)
                        )
                        .values_list("fragment_group__group_id", "count")
                        .all
                    )()
                )
                fragment_counters = await sync_to_async(list)(
                    await sync_to_async(
                        FragmentCounter.objects.filter(
                            Q(recap=recap)
                            & Q(fragment__group__in=fragmentgroups_updated)
                        )
                        .values_list(
                            "fragment__group__group_id",
                            "fragment__fragment_id",
                            "count",
                        )
                        .all
                    )()
                )
                await self.send_recap_update_message(
                    recap.year,
                    recap.month,
                    {
                        "count_messages": recap.count_messages,
                        "count_characters": recap.count_characters,
                        "count_chatters": recap.count_chatters,
                        "last_message": message.to_json(),
                        "counters": {
                            group_id: {
                                "total": count,
                                "members": {
                                    fragment_id: count
                                    for _, fragment_id, count in filter(
                                        lambda fcd: fcd[0] == group_id,
                                        fragment_counters,
                                    )
                                },
                            }
                            for group_id, count in fragment_group_counters
                        },
                    },
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
