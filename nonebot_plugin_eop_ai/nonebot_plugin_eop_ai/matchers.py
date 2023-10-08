from nonebot import on_fullmatch, on_message, on_startswith
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, Bot
from nonebot.matcher import Matcher
from .config import pc, var
from .rules import (
    enable_cmd,
    reset_cmd,
    admin_rule,
    talk_keyword_rule,
    talk_tome_rule,
    talk_cmd,
    talk_p_cmd,
    reply_type_cmd,
    baga_rule,
)
from .utils import RequestError, get_answer, get_id, http_request

usage = f"""插件命令如下
{talk_cmd}   # 触发对话关键字，默认群里@机器人也可以
{talk_p_cmd}   # 沉浸式对话（仅限私聊）
{reset_cmd}   # 重置对话（不会重置预设）
{enable_cmd}   # 如果关闭所有群启用，则用这个命令启用
{reply_type_cmd}   # AI回答输出类型切换，仅对使用命令的会话生效"""


talk_keyword = on_startswith(talk_cmd, rule=talk_keyword_rule)
talk_tome = on_message(rule=talk_tome_rule)

talk_p = on_fullmatch(talk_p_cmd)

reset = on_fullmatch(reset_cmd, rule=baga_rule)
reply_type = on_startswith(reply_type_cmd, rule=baga_rule)

group_enable = on_fullmatch(enable_cmd, rule=admin_rule)

@talk_keyword.handle()
@talk_tome.handle()
async def _(matcher: Matcher, event: MessageEvent, bot: Bot):
    _in = event.get_plaintext()
    if not _in or _in == talk_cmd:
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
        await matcher.finish("尚未发起对话", at_sender=pc.eop_ai_reply_at_user)

    try:
        await http_request("delete", f"/bot/{eop_id}/clear")

    except RequestError as e:
        if not (e.data and e.data["code"] == 2005):
            await matcher.finish(str(e))

    except Exception as e:
        await matcher.finish(str(e))

    var.session_data[id] = ""
    await matcher.finish("已重置对话", at_sender=pc.eop_ai_reply_at_user)


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


@reply_type.handle()
async def _(matcher: Matcher, event: MessageEvent, bot: Bot):
    _in = event.get_plaintext()
    if _in == reply_type_cmd:
        await matcher.finish(usage)

