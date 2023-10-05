from nonebot import on_fullmatch, on_message, on_startswith
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, Bot
from nonebot.matcher import Matcher
from .config import pc, var
from .rules import (
    enable_cmd,
    reset_cmd,
    rule_admin,
    talk_keyword_rule,
    talk_tome_rule,
    talk_cmd,
    talk_p_cmd,
)
from .utils import RequestError, get_answer, get_id, http_request

usage = f"""插件命令如下
{pc.eop_ai_talk_cmd}   # 开始对话，默认群里@机器人也可以
{pc.eop_ai_talk_p_cmd}   # 沉浸式对话（仅限私聊）
{pc.eop_ai_reset_cmd}   # 重置对话（不会重置预设）
{pc.eop_ai_group_enable_cmd}   # 如果关闭所有群启用，则用这个命令启用"""


talk_keyword = on_startswith(talk_cmd, rule=talk_keyword_rule)
talk_tome = on_message(rule=talk_tome_rule)

talk_p = on_fullmatch(talk_p_cmd)

reset = on_fullmatch(reset_cmd, rule=rule_admin)
group_enable = on_fullmatch(enable_cmd, rule=rule_admin)


@talk_keyword.handle()
@talk_tome.handle()
async def _(matcher: Matcher, event: MessageEvent, bot: Bot):
    if not event.get_plaintext():
        await matcher.finish(usage)

    await get_answer(matcher, event, bot)


@talk_p.got("msg", prompt="进入沉浸式对话模式，发送“退出”结束对话")
async def _(matcher: Matcher, event: PrivateMessageEvent, bot: Bot):
    if event.get_plaintext() == "退出":
        await matcher.finish("Bye~")

    await get_answer(matcher, event, bot, True)


@reset.handle()
async def _(matcher: Matcher, event: MessageEvent):
    # 获取用户id
    id = get_id(event)
    eop_id = var.session_data[id]
    if not eop_id:
        await matcher.finish("还没聊过呢", at_sender=True)

    try:
        await http_request("delete", f"/bot/{eop_id}/clear")

    except RequestError as e:
        if not (e.data and e.data["code"] == 2005):
            await matcher.finish(str(e))

    except Exception as e:
        await matcher.finish(str(e))

    var.session_data[id] = ""
    await matcher.finish("已重置会话", at_sender=True)


@group_enable.handle()
async def _(matcher: Matcher, event: GroupMessageEvent):
    if pc.eop_ai_all_group_enable is True:
        await matcher.finish("当前配置是所有群都启用，此命令无效")

    if event.group_id in var.enable_group_list:
        var.enable_group_list.remove(event.group_id)
        await matcher.finish("eop ai已禁用")

    else:
        var.enable_group_list.append(event.group_id)
        await matcher.finish("eop ai已启用")
