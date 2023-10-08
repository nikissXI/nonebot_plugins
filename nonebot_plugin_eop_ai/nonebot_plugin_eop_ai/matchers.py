from nonebot import on_fullmatch, on_message, on_startswith
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, Bot
from nonebot.permission import SUPERUSER
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
from .utils import (
    RequestError,
    get_answer,
    get_id,
    http_request,
    finish_with_at,
)

usage = f"""插件命令如下
{talk_cmd}   # 触发对话关键字，默认群里@机器人也可以
{talk_p_cmd}   # 沉浸式对话（仅限私聊）
{reset_cmd}   # 重置对话（不会重置预设）
{reply_type_cmd}   # AI回答输出类型切换，仅对使用命令的会话生效
{enable_cmd}   # 启用/禁用该群的eop ai（仅管理员）"""


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
        await finish_with_at(matcher, usage)

    await get_answer(matcher, event, bot)


@talk_p.got("msg", prompt="进入沉浸式对话模式，发送“退出”结束对话")
async def _(matcher: Matcher, event: PrivateMessageEvent, bot: Bot):
    if event.get_plaintext() == "退出":
        await finish_with_at(matcher, "Bye~")

    await get_answer(matcher, event, bot, True)
    await matcher.reject()


@reset.handle()
async def _(matcher: Matcher, event: MessageEvent, bot: Bot):
    if (
        isinstance(event, GroupMessageEvent)
        and pc.eop_ai_group_share
        and not await SUPERUSER(bot, event)
    ):
        await finish_with_at(matcher, "群会话共享状态下仅限管理员执行")

    # 获取用户id
    id = get_id(event)
    eop_id = var.session_data[id]
    if not eop_id:
        await finish_with_at(matcher, "尚未发起对话")

    try:
        await http_request("delete", f"/bot/{eop_id}/clear")

    except RequestError as e:
        if not (e.data and e.data["code"] == 2005):
            await finish_with_at(matcher, repr(e))

    except Exception as e:
        await finish_with_at(matcher, repr(e))

    var.session_data[id] = ""
    await finish_with_at(matcher, "已重置对话")


# 如果私聊直接pass，如果是群聊，要检查share是否开启，如果开了就只能管理员，否则就pass
@reply_type.handle()
async def _(matcher: Matcher, event: MessageEvent, bot: Bot):
    if (
        isinstance(event, GroupMessageEvent)
        and pc.eop_ai_group_share
        and not await SUPERUSER(bot, event)
    ):
        await finish_with_at(matcher, "群会话共享状态下仅限管理员执行")

    _in = event.get_plaintext()[len(reply_type_cmd) :].strip()

    # 如果默认是图片回复，只能切2和3（除非管理员）
    if (
        not await SUPERUSER(bot, event)
        and pc.eop_ai_reply_type != "1"
        and _in not in ["2", "3"]
    ):
        await finish_with_at(matcher, f"{reply_type_cmd} 数字\n2 - 图片\n3 - 图片+文字")

    elif _in not in ["1", "2", "3"]:
        await finish_with_at(matcher, f"{reply_type_cmd} 数字\n1 - 文字\n2 - 图片\n3 - 图片+文字")

    var.reply_type[get_id(event)] = int(_in)
    await finish_with_at(matcher, f"回复类型切换至{_in}")


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
