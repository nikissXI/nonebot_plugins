from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11 import PrivateMessageEvent
from nonebot.permission import SUPERUSER
from .config import pc, var

talk_cmd = pc.eop_ai_talk_cmd
talk_p_cmd = pc.eop_ai_talk_p_cmd
reset_cmd = pc.eop_ai_reset_cmd
enable_cmd = pc.eop_ai_group_enable_cmd
reply_type_cmd = pc.eop_ai_reply_type_cmd


async def talk_keyword_rule(event: MessageEvent, bot: Bot) -> bool:
    if isinstance(event, PrivateMessageEvent):
        return True

    if isinstance(event, GroupMessageEvent):
        if (
            pc.eop_ai_all_group_enable is True
            or event.group_id in var.enable_group_list
        ) and (pc.eop_ai_bot_qqnum_list == ["all"] or bot == var.handle_bot):
            return True

    return False


async def talk_tome_rule(event: MessageEvent) -> bool:
    if isinstance(event, GroupMessageEvent):
        if (event.is_tome() and pc.eop_ai_talk_tome) and (
            pc.eop_ai_all_group_enable is True
            or event.group_id in var.enable_group_list
        ):
            return True

    return False


async def rule_admin(event: MessageEvent, bot: Bot) -> bool:
    if await SUPERUSER(bot, event) and (
        pc.eop_ai_bot_qqnum_list == ["all"] or bot == var.handle_bot
    ):
        return True

    return False
