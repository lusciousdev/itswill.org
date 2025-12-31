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


class LoggerBot(twitchio_commands.AutoBot):
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
            if set(resp.scopes) == set(
                settings.SOCIALACCOUNT_PROVIDERS.get("twitch", {}).get("SCOPE", [])
            ):
                account = await SocialAccount.objects.aget(
                    provider="twitch", uid=resp.user_id
                )
            elif set(resp.scopes) == set(
                settings.SOCIALACCOUNT_PROVIDERS.get("twitch_chatbot", {}).get(
                    "SCOPE", []
                )
            ):
                account = await SocialAccount.objects.aget(
                    provider="twitch_chatbot", uid=resp.user_id
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
            provider="twitch_chatbot", uid=self.bot_id
        )
        bot_token = await SocialToken.objects.aget(account=bot_account)

        _ = await self.add_token(bot_token.token, bot_token.token_secret)

        user_account = await SocialAccount.objects.filter(
            provider="twitch", uid=BROADCASTER_ID
        ).afirst()

        if user_account is not None:
            user_token = await SocialToken.objects.aget(account=user_account)

            _ = await self.add_token(user_token.token, user_token.token_secret)
        else:
            raise Exception("No user token for broadcaster.")

    async def event_ready(self) -> None:
        LOGGER.debug(f"Successfully logged in as: {self.bot_id}")

        subscriptions = [
            twitchio.eventsub.ChatMessageSubscription(
                broadcaster_user_id=BROADCASTER_ID, user_id=self.bot_id
            ),
            twitchio.eventsub.ChatMessageDeleteSubscription(
                broadcaster_user_id=BROADCASTER_ID, user_id=self.bot_id
            ),
            twitchio.eventsub.ChannelBanSubscription(
                broadcaster_user_id=BROADCASTER_ID
            ),
            twitchio.eventsub.ChannelUnbanSubscription(
                broadcaster_user_id=BROADCASTER_ID
            ),
            twitchio.eventsub.ChannelPointsRewardAddSubscription(
                broadcaster_user_id=BROADCASTER_ID
            ),
            twitchio.eventsub.ChannelPointsRewardUpdateSubscription(
                broadcaster_user_id=BROADCASTER_ID
            ),
            twitchio.eventsub.ChannelPointsRewardRemoveSubscription(
                broadcaster_user_id=BROADCASTER_ID
            ),
            twitchio.eventsub.ChannelPointsRedeemAddSubscription(
                broadcaster_user_id=BROADCASTER_ID
            ),
            twitchio.eventsub.ChannelPointsRedeemUpdateSubscription(
                broadcaster_user_id=BROADCASTER_ID
            ),
            twitchio.eventsub.ChannelPollBeginSubscription(
                broadcaster_user_id=BROADCASTER_ID
            ),
            twitchio.eventsub.ChannelPollProgressSubscription(
                broadcaster_user_id=BROADCASTER_ID
            ),
            twitchio.eventsub.ChannelPollEndSubscription(
                broadcaster_user_id=BROADCASTER_ID
            ),
            twitchio.eventsub.ChannelPredictionBeginSubscription(
                broadcaster_user_id=BROADCASTER_ID
            ),
            twitchio.eventsub.ChannelPredictionProgressSubscription(
                broadcaster_user_id=BROADCASTER_ID
            ),
            twitchio.eventsub.ChannelPredictionLockSubscription(
                broadcaster_user_id=BROADCASTER_ID
            ),
            twitchio.eventsub.ChannelPredictionEndSubscription(
                broadcaster_user_id=BROADCASTER_ID
            ),
        ]

        resp: twitchio.MultiSubscribePayload = await self.multi_subscribe(
            subscriptions=subscriptions
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

    async def get_or_create_twitch_user(
        self, partial_user: twitchio.PartialUser
    ) -> typing.Tuple[TwitchUser, bool]:
        try:
            twitch_user = await TwitchUser.objects.aget(user_id=partial_user.id)
            new_chatter = False
        except TwitchUser.DoesNotExist:
            tio_user: twitchio.User = await partial_user.user()

            new_chatter = True
            twitch_user = await TwitchUser.objects.acreate(
                user_id=partial_user.id,
                login=partial_user.name,
                display_name=partial_user.display_name,
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

        return twitch_user, new_chatter

    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        twitch_user, new_chatter = await self.get_or_create_twitch_user(payload.chatter)

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
                    message.created_at, twitch_user.user_id
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

            overall_recaps = await sync_to_async(list)(
                filter(lambda r: r.twitch_user is None, recaps)
            )

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

    async def event_message_delete(self, payload: twitchio.ChatMessageDelete) -> None:
        try:
            message = await ChatMessage.objects.aget(message_id=payload.message_id)
            message.deleted = True
            await message.asave()
        except ChatMessage.DoesNotExist:
            ...

    async def event_ban(self, payload: twitchio.ChannelBan) -> None:
        print("User banned")

        twitch_user, new_user = await self.get_or_create_twitch_user(payload.user)
        moderator, new_user = await self.get_or_create_twitch_user(payload.moderator)

        ban, created = await TwitchBan.objects.aupdate_or_create(
            twitch_user=twitch_user,
            moderator=moderator,
            banned_at=payload.banned_at,
            defaults={
                "reason": payload.reason,
                "duration": (payload.ends_at - payload.banned_at).total_seconds(),
                "permanent": payload.permanent,
            },
        )

    async def event_unban(self, payload: twitchio.ChannelUnban) -> None:
        twitch_user, new_user = await self.get_or_create_twitch_user(payload.user)
        moderator, new_user = await self.get_or_create_twitch_user(payload.moderator)

        unban = await TwitchUnban.objects.acreate(
            twitch_user=twitch_user,
            moderator=moderator,
        )

    async def update_or_create_custom_reward(
        self,
        payload: typing.Union[
            twitchio.ChannelPointsRewardAdd,
            twitchio.ChannelPointsRewardUpdate,
            twitchio.ChannelPointsRewardRemove,
            twitchio.ChannelPointsReward,
        ],
        full_reward_type: bool = False,
    ) -> CustomReward:
        defaults = {
            "broadcaster_id": payload.broadcaster.id,
            "broadcaster_name": payload.broadcaster.display_name,
            "broadcaster_login": payload.broadcaster.name,
            "title": payload.title,
            "prompt": payload.prompt,
            "cost": payload.cost,
            "default_image": payload.default_image,
            "background_color": (
                None if payload.colour is None else payload.colour.hex
            ),
            "max_per_stream_setting": (
                None
                if payload.max_per_stream is None
                else {
                    "is_enabled": payload.max_per_stream.enabled,
                    "max_per_stream": payload.max_per_stream.value,
                }
            ),
            "max_per_user_per_stream_setting": (
                None
                if payload.max_per_user_per_stream is None
                else {
                    "is_enabled": payload.max_per_user_per_stream.enabled,
                    "max_per_stream": payload.max_per_user_per_stream.enabled,
                }
            ),
            "global_cooldown_setting": (
                None
                if payload.global_cooldown is None
                else {
                    "is_enabled": payload.global_cooldown.enabled,
                    "global_cooldown_seconds": payload.global_cooldown.seconds,
                }
            ),
            "redemptions_redeemed_current_stream": payload.current_stream_redeems,
            "cooldown_expires_at": payload.cooldown_until,
        }
        if full_reward_type:
            defaults["image"] = payload.image

        if payload.enabled is not None:
            defaults["is_enabled"] = payload.enabled
        if payload.paused is not None:
            defaults["is_paused"] = payload.paused
        if payload.in_stock is not None:
            defaults["is_in_stock"] = payload.in_stock
        if payload.skip_queue is not None:
            defaults["should_redemptions_skip_request_queue"] = payload.skip_queue
        if payload.input_required is not None:
            defaults["is_user_input_required"] = payload.input_required

        reward, created = await CustomReward.objects.aupdate_or_create(
            id=payload.id, defaults=defaults
        )

        return reward

    async def event_custom_reward_add(
        self, payload: twitchio.ChannelPointsRewardAdd
    ) -> None:
        _ = await self.update_or_create_custom_reward(payload)

    async def event_custom_reward_update(
        self, payload: twitchio.ChannelPointsRewardUpdate
    ) -> None:
        _ = await self.update_or_create_custom_reward(payload)

    async def event_custom_reward_remove(
        self, payload: twitchio.ChannelPointsRewardRemove
    ) -> None:
        reward = await self.update_or_create_custom_reward(payload)
        reward.removed = True
        await reward.asave()

    async def update_or_create_custom_redemption(
        self,
        payload: typing.Union[
            twitchio.ChannelPointsRedemptionAdd, twitchio.ChannelPointsRedemptionUpdate
        ],
    ) -> CustomRewardRedemption:
        reward = await self.update_or_create_custom_reward(
            payload.reward, full_reward_type=True
        )
        twitch_user, _ = await self.get_or_create_twitch_user(payload.user)

        redemption, created = await CustomRewardRedemption.objects.aupdate_or_create(
            id=payload.id,
            reward=reward,
            defaults={
                "broadcaster_id": payload.broadcaster.id,
                "broadcaster_name": payload.broadcaster.display_name,
                "broadcaster_login": payload.broadcaster.name,
                "user": twitch_user,
                "user_input": payload.user_input,
                "status": payload.status.upper(),
                "redeemed_at": payload.timestamp,
                "cost": reward.cost,
            },
        )

    async def event_custom_redemption_add(
        self, payload: twitchio.ChannelPointsRedemptionAdd
    ) -> None:
        _ = await self.update_or_create_custom_redemption(payload)

    async def event_custom_redemption_update(
        self, payload: twitchio.ChannelPointsRedemptionUpdate
    ) -> None:
        _ = await self.update_or_create_custom_redemption(payload)

    async def event_poll_begin(self, payload: twitchio.ChannelPollBegin) -> None:
        pass

    async def event_poll_progress(self, payload: twitchio.ChannelPollProgress) -> None:
        pass

    async def event_poll_end(self, payload: twitchio.ChannelPollEnd) -> None:
        pass

    async def event_prediction_begin(
        self, payload: twitchio.ChannelPredictionBegin
    ) -> None:
        prediction, created = await Prediction.objects.aupdate_or_create(
            id=payload.id,
            defaults={
                "broadcaster_id": payload.broadcaster.id,
                "broadcaster_name": payload.broadcaster.display_name,
                "broadcaster_login": payload.broadcaster.name,
                "title": payload.title,
                "prediction_window": (
                    payload.locks_at - payload.started_at
                ).total_seconds(),
                "status": "ACTIVE",
                "created_at": payload.started_at,
            },
        )

        po: twitchio.PredictionOutcome
        for po in payload.outcomes:
            prediction_outcome, created = (
                await PredictionOutcome.objects.aupdate_or_create(
                    id=po.id,
                    prediction=prediction,
                    defaults={
                        "title": po.title,
                        "users": 0 if po.users is None else po.users,
                        "channel_points": (
                            0 if po.channel_points is None else po.channel_points
                        ),
                        "color": po.colour,
                    },
                )
            )

            tp: twitchio.Predictor
            for tp in po.top_predictors:
                twitch_user, new_chatter = await self.get_or_create_twitch_user(tp.user)
                predictor, created = await Predictor.objects.aupdate_or_create(
                    prediction_outcome=prediction_outcome,
                    twitch_user_id=tp.user.id,
                    defaults={
                        "channel_points_used": tp.channel_points_used,
                        "channel_points_won": tp.channel_points_won,
                    },
                )

    async def event_prediction_progress(
        self, payload: twitchio.ChannelPredictionProgress
    ) -> None:
        prediction, created = await Prediction.objects.aupdate_or_create(
            id=payload.id,
            defaults={
                "broadcaster_id": payload.broadcaster.id,
                "broadcaster_name": payload.broadcaster.display_name,
                "broadcaster_login": payload.broadcaster.name,
                "title": payload.title,
                "prediction_window": (
                    payload.locks_at - payload.started_at
                ).total_seconds(),
                "status": "ACTIVE",
                "created_at": payload.started_at,
            },
        )

        po: twitchio.PredictionOutcome
        for po in payload.outcomes:
            prediction_outcome, created = (
                await PredictionOutcome.objects.aupdate_or_create(
                    id=po.id,
                    prediction=prediction,
                    defaults={
                        "title": po.title,
                        "users": 0 if po.users is None else po.users,
                        "channel_points": (
                            0 if po.channel_points is None else po.channel_points
                        ),
                        "color": po.colour,
                    },
                )
            )

            tp: twitchio.Predictor
            for tp in po.top_predictors:
                twitch_user, new_chatter = await self.get_or_create_twitch_user(tp.user)
                predictor, created = await Predictor.objects.aupdate_or_create(
                    prediction_outcome=prediction_outcome,
                    twitch_user_id=tp.user.id,
                    defaults={
                        "channel_points_used": tp.channel_points_used,
                        "channel_points_won": tp.channel_points_won,
                    },
                )

    async def event_prediction_lock(
        self, payload: twitchio.ChannelPredictionLock
    ) -> None:
        prediction, created = await Prediction.objects.aupdate_or_create(
            id=payload.id,
            defaults={
                "broadcaster_id": payload.broadcaster.id,
                "broadcaster_name": payload.broadcaster.display_name,
                "broadcaster_login": payload.broadcaster.name,
                "title": payload.title,
                "prediction_window": (
                    payload.locked_at - payload.started_at
                ).total_seconds(),
                "status": "LOCKED",
                "created_at": payload.started_at,
                "locked_at": payload.locked_at,
            },
        )

        po: twitchio.PredictionOutcome
        for po in payload.outcomes:
            prediction_outcome, created = (
                await PredictionOutcome.objects.aupdate_or_create(
                    id=po.id,
                    prediction=prediction,
                    defaults={
                        "title": po.title,
                        "users": 0 if po.users is None else po.users,
                        "channel_points": (
                            0 if po.channel_points is None else po.channel_points
                        ),
                        "color": po.colour,
                    },
                )
            )

            tp: twitchio.Predictor
            for tp in po.top_predictors:
                twitch_user, new_chatter = await self.get_or_create_twitch_user(tp.user)
                predictor, created = await Predictor.objects.aupdate_or_create(
                    prediction_outcome=prediction_outcome,
                    twitch_user_id=tp.user.id,
                    defaults={
                        "channel_points_used": tp.channel_points_used,
                        "channel_points_won": tp.channel_points_won,
                    },
                )

    async def event_prediction_end(
        self, payload: twitchio.ChannelPredictionEnd
    ) -> None:
        prediction, created = await Prediction.objects.aupdate_or_create(
            id=payload.id,
            defaults={
                "broadcaster_id": payload.broadcaster.id,
                "broadcaster_name": payload.broadcaster.display_name,
                "broadcaster_login": payload.broadcaster.name,
                "title": payload.title,
                "status": payload.status.upper(),
                "created_at": payload.started_at,
                "ended_at": payload.ended_at,
            },
        )

        po: twitchio.PredictionOutcome
        for po in payload.outcomes:
            prediction_outcome, created = (
                await PredictionOutcome.objects.aupdate_or_create(
                    id=po.id,
                    prediction=prediction,
                    defaults={
                        "title": po.title,
                        "users": 0 if po.users is None else po.users,
                        "channel_points": (
                            0 if po.channel_points is None else po.channel_points
                        ),
                        "color": po.colour,
                    },
                )
            )

            tp: twitchio.Predictor
            for tp in po.top_predictors:
                twitch_user, new_chatter = await self.get_or_create_twitch_user(tp.user)
                predictor, created = await Predictor.objects.aupdate_or_create(
                    prediction_outcome=prediction_outcome,
                    twitch_user_id=tp.user.id,
                    defaults={
                        "channel_points_used": tp.channel_points_used,
                        "channel_points_won": tp.channel_points_won,
                    },
                )

        prediction.winning_outcome_id = payload.winning_outcome.id
        await prediction.asave()


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
