from html import unescape
from nonebot import on_fullmatch, on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11 import MessageSegment as MS
from nonebot.adapters.onebot.v11 import PrivateMessageEvent
from nonebot.matcher import Matcher
from nonebot_plugin_htmlrender import md_to_pic
from .config import pc, var
from .rules import (
    enable_cmd,
    reset_cmd,
    rule_admin,
    rule_check,
    rule_check2,
    talk_cmd,
    talk_p_cmd,
)
from .utils import RequestError, get_answer, get_id, get_pasted_url, http_request

#################
### 响应器
#################
talk = on_message(rule=rule_check)
talk_p = on_fullmatch(talk_p_cmd, rule=rule_check2)
reset = on_fullmatch(reset_cmd, rule=rule_check2)
enable_group = on_fullmatch(enable_cmd, rule=rule_admin)


@talk.handle()
async def _(matcher: Matcher, event: MessageEvent):
    # 获取信息
    text = unescape(event.get_plaintext().strip())
    # 把命令前缀截掉
    if text[: len(talk_cmd)] == talk_cmd:
        text = text[len(talk_cmd) :]
    # 无内容
    if not text:
        await talk.finish(
            f"""插件命令如下
{talk_cmd} 【内容】 # 发送问题，群里@机器人接内容也可以
{talk_p_cmd}  # 进入沉浸式对话模式，仅私聊可用
{reset_cmd}  # 清空聊天记录
"""
        )

    answer = await get_answer(matcher, event, text)
    if pc.eop_ai_reply_with_img:
        await talk.finish(
            MS.image(await md_to_pic(md=answer))
            + MS.text("原文：" + await get_pasted_url(answer))
        )

    await talk.finish(answer, at_sender=True)


@talk_p.got("msg", prompt="进入沉浸式对话模式，发送“退出”结束对话")
async def _(matcher: Matcher, event: PrivateMessageEvent):
    # 获取信息
    text = unescape(event.get_plaintext().strip())
    if text == "退出":
        await talk_p.finish("Bye~")

    answer = await get_answer(matcher, event, text,True)
    if pc.eop_ai_reply_with_img:
        await talk_p.reject(
            MS.image(await md_to_pic(md=answer))
            + MS.text("原文：" + await get_pasted_url(answer))
        )

    await talk_p.reject(answer)


@reset.handle()
async def _(event: MessageEvent):
    # 获取用户id
    id = get_id(event)
    eop_id = var.session_data[id]
    if not eop_id:
        await reset.finish("还没聊过呢", at_sender=True)

    try:
        await http_request("delete", f"/bot/{eop_id}")

    except RequestError as e:
        if not (e.data and e.data["code"] == 2005):
            await reset.finish(str(e))

    except Exception as e:
        await reset.finish(str(e))

    var.session_data[id] = ""
    await reset.finish("已重置会话", at_sender=True)


@enable_group.handle()
async def _(event: GroupMessageEvent):
    if pc.eop_ai_all_group_enable is True:
        await enable_group.finish("当前配置是所有群都启用，此命令无效")

    if event.group_id in var.enable_group_list:
        var.enable_group_list.remove(event.group_id)
        await enable_group.finish("eop ai已禁用")
    else:
        var.enable_group_list.append(event.group_id)
        await enable_group.finish("eop ai已启用")
