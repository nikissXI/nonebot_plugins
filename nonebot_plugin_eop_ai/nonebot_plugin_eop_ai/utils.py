from asyncio import create_task, gather
from html import unescape
from json import dump, load, loads
from os import makedirs, path
from re import search
from traceback import format_exc
from typing import Optional

from nonebot import get_driver, require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11 import MessageSegment as MS
from nonebot.exception import FinishedException
from nonebot.log import logger
from nonebot.matcher import Matcher

from .config import Session, pc, var

require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender.data_source import (
    TEMPLATES_PATH,
    get_new_page,
    markdown,
    read_tpl,
)
from nonebot_plugin_htmlrender.data_source import (
    env as htmlrender_env,
)

driver = get_driver()


@driver.on_startup
async def _():
    """
    启动时执行
    """
    # 如果eop_ai_group_share为true该选项强制为true
    if pc.eop_ai_group_share is False:
        logger.warning("因eop_ai_group_share为False，eop_ai_reply_at_user改为True")
        pc.eop_ai_reply_at_user = True

    # 读取数据
    if path.exists(f"data/{pc.eop_ai_data}"):
        with open(f"data/{pc.eop_ai_data}", "r", encoding="utf-8") as r:
            _ = load(r)
            version = _["version"]

        if version != pc.eop_ai_version:
            logger.warning("配置文件版本不对应哦~")
        else:
            var.enable_group_list = _["enable_group_list"]
            for uid, s in _["session_data"].items():
                var.session_data[uid] = Session(**s)
            var.reply_type = _["reply_type"]
            var.default_bot = _["default_bot"]
    else:
        if not path.exists("data"):
            makedirs("data")

    # 验证access_token
    try:
        await http_request("GET", "/user/info")
        logger.success(f"eop ai认证成功")
    except Exception as e:
        logger.error(f"eop ai认证失败：{repr(e)}")


@driver.on_shutdown
async def _():
    """
    关闭时执行
    """
    _session_data = {}
    for uid, s in var.session_data.items():
        _session_data[uid] = s.dict()

    with open(f"data/{pc.eop_ai_data}", "w", encoding="utf-8") as w:
        dump(
            {
                "version": pc.eop_ai_version,
                "enable_group_list": var.enable_group_list,
                "session_data": _session_data,
                "reply_type": var.reply_type,
                "default_bot": var.default_bot,
            },
            w,
            indent=4,
            ensure_ascii=False,
        )


async def md_to_pic(md_text: str) -> bytes:
    """markdown 转 图片

    Args:
        md (str): markdown 格式文本

    Returns:
        bytes: 图片, 可直接发送
    """
    template = htmlrender_env.get_template("markdown.html")
    md = markdown.markdown(
        md_text,
        extensions=[
            "pymdownx.tasklist",
            "tables",
            "fenced_code",
            "codehilite",
            "mdx_math",
            "mdx_truly_sane_lists",
            "mdx_breakless_lists",
        ],
        extension_configs={
            "mdx_math": {"enable_dollar_delimiter": True},
            "mdx_truly_sane_lists": {
                "nested_indent": 2,
                "truly_sane": True,
            },
        },
    )

    extra = ""
    if "math/tex" in md:
        katex_css = await read_tpl("katex/katex.min.b64_fonts.css")
        katex_js = await read_tpl("katex/katex.min.js")
        mathtex_js = await read_tpl("katex/mathtex-script-type.min.js")
        extra = (
            f'<style type="text/css">{katex_css}</style>'
            f"<script defer>{katex_js}</script>"
            f"<script defer>{mathtex_js}</script>"
        )

    css = await read_tpl("github-markdown-light.css") + await read_tpl(
        "pygments-default.css"
    )

    html = await template.render_async(md=md, css=css, extra=extra)
    async with get_new_page(
        2, viewport={"width": pc.eop_ai_img_width, "height": 10}
    ) as page:
        await page.goto(f"file://{TEMPLATES_PATH}")
        await page.set_content(html, wait_until="networkidle")
        img_raw = await page.screenshot(full_page=True, type="png")

    return img_raw


async def get_csrftoken(id: str) -> str:
    resp = await var.httpx_client.get("https://paste.mozilla.org/")
    if resp.status_code != 200:
        raise Exception(
            f"访问https://paste.mozilla.org/失败，响应码：{resp.status_code}"
        )

    match = search(
        r'<input[^>]+name="csrfmiddlewaretoken"[^>]+value="([^"]+)"', resp.text
    )
    if match:
        var.paste_csrftoken[id] = match.group(1)
        return var.paste_csrftoken[id]
    else:
        raise Exception("未找到csrfmiddlewaretoken")


async def get_pasted_url(content: str, id: str) -> str:
    if id in var.paste_csrftoken and var.paste_csrftoken[id]:
        csrfmiddlewaretoken = var.paste_csrftoken[id]
    else:
        csrfmiddlewaretoken = await get_csrftoken(id)

    resp = await var.httpx_client.post(
        "https://paste.mozilla.org/",
        headers={
            "Origin": "https://paste.mozilla.org",
            "Referer": "https://paste.mozilla.org/",
        },
        data={
            "csrfmiddlewaretoken": csrfmiddlewaretoken,
            "title": "",
            "lexer": "_markdown",
            "expires": 86400,
            "content": content,
        },
    )
    if resp.status_code == 302:
        # 缓存下一个token
        create_task(get_csrftoken(id))
        return f"https://paste.mozilla.org{resp.headers.get('Location')}/slim"
    elif resp.status_code == 403:
        # token失效
        var.paste_csrftoken[id] = ""
        return await get_pasted_url(content, id)
    else:
        raise Exception("提交后响应码非302")


def get_uid(event: MessageEvent) -> str:
    """获取对话用户的唯一标识"""
    if isinstance(event, GroupMessageEvent):
        if pc.eop_ai_group_share:
            uid = f"{(event.group_id)}-share"
        else:
            uid = f"{event.user_id}"
    else:
        uid = f"{event.user_id}"
    return uid


async def gen_chat_text(event: MessageEvent, bot: Bot) -> str:
    """生成合适的会话消息内容(eg. 将cq at 解析为真实的名字)"""
    if not isinstance(event, GroupMessageEvent):
        return event.get_plaintext()

    msg = ""
    for seg in event.message:
        if seg.is_text():
            msg += seg.data.get("text", "")

        elif seg.type == "at":
            qq = seg.data.get("qq", None)

            if qq:
                if qq == "all":
                    msg += "@全体成员"
                else:
                    user_info = await bot.get_group_member_info(
                        group_id=event.group_id,
                        user_id=event.user_id,
                        no_cache=False,
                    )
                    user_name = user_info.get("card", None) or user_info.get(
                        "nickname", None
                    )
                    if user_name:
                        msg += (
                            f"@{user_name}"  # 保持给bot看到的内容与真实用户看到的一致
                        )
    return msg


async def send_with_at(matcher: Matcher, content):
    await matcher.send(content, at_sender=pc.eop_ai_reply_at_user)


async def finish_with_at(matcher: Matcher, content):
    await matcher.finish(content, at_sender=pc.eop_ai_reply_at_user)


async def get_answer(matcher: Matcher, event: MessageEvent, bot: Bot, immersive=False):
    """ "从api获取回答"""
    # 获取问题
    question = unescape(await gen_chat_text(event, bot))

    # 获取用户id
    uid = get_uid(event)

    # 判断是否有回答没完成
    if uid in var.session_lock and var.session_lock[uid]:
        # 沉浸式对话
        if immersive:
            await send_with_at(matcher, "上一个回答还没完成呢")
        else:
            await finish_with_at(matcher, "上一个回答还没完成呢")
        return

    # 根据配置是否发出提示
    if pc.eop_ai_reply_notice:
        await send_with_at(matcher, "响应中...")

    try:
        # 上锁
        var.session_lock[uid] = True

        # 新的对话
        if uid not in var.session_data:
            # 检查账号的会话列表是否有title和uid一样的会话
            resp = await http_request("GET", "/user/chats/all")
            for chat in resp:
                if uid == chat["title"]:
                    resp = await http_request("GET", f"/user/chat/{chat['chatCode']}/0")
                    # 绑定session
                    var.session_data[uid] = Session(
                        botName=resp["botInfo"]["botName"],
                        chatCode=chat["chatCode"],
                        price=resp["botInfo"]["price"],
                    )
                    break
            # 没有一样的会话
            else:
                bot_name = (
                    var.default_bot[uid] if uid in var.default_bot else pc.default_bot
                )
                resp = await http_request("GET", f"/user/bot/{bot_name}")
                var.session_data[uid] = Session(
                    botName=resp["botName"], price=resp["price"]
                )

        # 拉取session元数据
        session = var.session_data[uid]

        answer = ""
        # 对话
        async with var.httpx_client.stream(
            "POST",
            f"/user/talk/{session.chatCode}",
            data={
                "botName": session.botName,
                "question": question,
                "price": session.price,
            },
        ) as resp:
            async for chunk in resp.aiter_lines():
                chunk_data = loads(chunk)
                if chunk_data["code"] != 0:
                    raise AnswerError(f"生成回答出错：{chunk_data['msg']}")

                data_type = chunk_data["data"]["dataType"]
                data_content = chunk_data["data"]["dataContent"]
                # 新会话
                if data_type == "newChat":
                    # 记录新会话的chatCode
                    session.chatCode = data_content["chatCode"]
                # 回答的内容
                if data_type == "botMessageAdd":
                    answer = data_content["text"]
                # 更新title
                if data_type == "chatTitleUpdated":
                    # 更新title为uid
                    await http_request(
                        "POST",
                        f"/user/titleUpdate/{session.chatCode}",
                        json={"title": uid},
                    )
                # 出错
                elif data_type == "talkError":
                    raise AnswerError(f"生成回答出错：{data_content['errMsg']}")

        # 转图片
        async def _reply_with_img(answer: str):
            answer_image = await md_to_pic(answer)
            return MS.image(answer_image)

        # 转图片并粘贴到剪切板
        async def _reply_with_img_and_text(answer: str):
            answer_image, answer_text_link = await gather(
                md_to_pic(answer), get_pasted_url(answer, uid)
            )
            return MS.image(answer_image) + MS.text("文本：" + answer_text_link)

        reply_type = pc.eop_ai_reply_type
        if uid in var.reply_type:
            reply_type = var.reply_type[uid]

        # 沉浸式对话
        if immersive:
            if reply_type == 1:
                await send_with_at(matcher, answer)
            elif reply_type == 2:
                await send_with_at(matcher, await _reply_with_img(answer))
            else:
                await send_with_at(matcher, await _reply_with_img_and_text(answer))

        # 普通对话
        else:
            if reply_type == 1:
                await send_with_at(matcher, answer)
            elif reply_type == 2:
                await send_with_at(matcher, await _reply_with_img(answer))
            else:
                await send_with_at(matcher, await _reply_with_img_and_text(answer))

    except FinishedException as e:
        logger.error("here")
        raise e

    except AnswerError as e:
        await finish_with_at(matcher, repr(e))

    except RequestError as e:
        if e.status_code == 402 and e.data and e.data["msg"] == "会话不存在":
            var.session_data.pop(uid)
            await finish_with_at(matcher, "原会话失效，已刷新")

        await finish_with_at(matcher, repr(e))

    except Exception as e:
        await finish_with_at(matcher, repr(e))

    finally:
        # 解锁
        var.session_lock[uid] = False


class AnswerError(Exception):
    def __init__(self, text: str):
        super().__init__(text)


class RequestError(Exception):
    def __init__(
        self, method: str, url: str, status_code: Optional[int], data: Optional[dict]
    ):
        self.method = method
        self.url = url
        self.status_code = status_code
        self.data = data
        message = f"请求 {method} {url} 时发生异常，状态码: {status_code}, 数据: {data}"
        super().__init__(message)


async def http_request(method: str, url: str, **kwargs) -> dict:
    try:
        resp = await var.httpx_client.request(method, url, **kwargs)
    except Exception as e:
        raise e

    # # 非登录时验证异常尝试重新验证
    # if url != "/user/login" and (resp.status_code == 401 or resp.status_code == 403):
    #     hash_object = sha256()
    #     hash_object.update(pc.eop_ai_passwd.encode("utf-8"))
    #     resp = await http_request(
    #         "post",
    #         "/user/login",
    #         json={"user": pc.eop_ai_user, "passwd": hash_object.hexdigest()},
    #     )
    #     var.access_token = resp["access_token"]
    #     var.httpx_client.headers.update({"Authorization": f"Bearer {var.access_token}"})
    #     # 重新请求
    #     return await http_request(method, url, **kwargs)

    if resp.status_code != 200:
        resp_json = resp.json()
        raise RequestError(method, url, resp.status_code, resp_json)

    return resp.json()["data"]
