from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    MessageEvent,
    PrivateMessageEvent,
)
from nonebot.permission import SUPERUSER

from .config import pc, var

talk_cmd = pc.eop_ai_talk_cmd
talk_p_cmd = pc.eop_ai_talk_p_cmd
reset_cmd = pc.eop_ai_reset_cmd
enable_cmd = pc.eop_ai_group_enable_cmd
reply_type_cmd = pc.eop_ai_reply_type_cmd


def bot_check(bot: Bot) -> bool:
    return pc.eop_ai_bot_qqnum_list == ["all"] or bot == var.handle_bot


async def talk_keyword_rule(event: MessageEvent, bot: Bot) -> bool:
    if isinstance(event, PrivateMessageEvent):
        return True

    if isinstance(event, GroupMessageEvent):
        if (
            pc.eop_ai_all_group_enable is True
            or event.group_id in var.enable_group_list
        ) and bot_check(bot):
            return True

    return False


async def talk_tome_rule(event: MessageEvent) -> bool:
    if isinstance(event, PrivateMessageEvent):
        return False

    elif isinstance(event, GroupMessageEvent):
        if (event.is_tome() and pc.eop_ai_talk_tome) and (
            pc.eop_ai_all_group_enable is True
            or event.group_id in var.enable_group_list
        ):
            return True

    return False


async def baga_rule(event: MessageEvent, bot: Bot) -> bool:
    if isinstance(event, PrivateMessageEvent):
        return True

    elif isinstance(event, GroupMessageEvent) and bot_check(bot):
        return True

    return False


async def admin_rule(event: MessageEvent, bot: Bot) -> bool:
    if not await SUPERUSER(bot, event):
        return False

    if isinstance(event, PrivateMessageEvent):
        return True
    else:
        return bot_check(bot)
