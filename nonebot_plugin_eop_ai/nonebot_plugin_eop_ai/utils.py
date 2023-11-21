from hashlib import sha256
from os import makedirs, path
from re import search
from html import unescape
from typing import Optional
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent, Bot
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot import get_driver, require
from nonebot.exception import RejectedException, FinishedException
from nonebot.adapters.onebot.v11 import MessageSegment as MS
from asyncio import gather, create_task

require("nonebot_plugin_htmlrender")
from nonebot_plugin_htmlrender.data_source import (
    env as htmlrender_env,
    markdown,
    read_tpl,
    TEMPLATES_PATH,
    get_new_page,
)
from .config import pc, var

try:
    from ujson import dump, load, loads
except:
    from json import dump, load, loads

driver = get_driver()


@driver.on_startup
async def _():
    """
    启动时执行
    """
    # 如果eop_ai_group_share为true该选项强制为true
    if pc.eop_ai_group_share:
        pc.eop_ai_reply_at_user = True

    # 读取数据
    if path.exists(f"data/{pc.eop_ai_data}"):
        with open(f"data/{pc.eop_ai_data}", "r", encoding="utf-8") as r:
            _ = load(r)
            version = _["version"]

        if version != pc.eop_ai_version:
            logger.warning(f"配置文件版本不对应哦~")
        else:
            var.enable_group_list = _["enable_group_list"]
            var.session_data = _["session_data"]
            var.reply_type = _["reply_type"]
    else:
        if not path.exists("data"):
            makedirs("data")


@driver.on_shutdown
async def _():
    """
    关闭时执行
    """
    with open(f"data/{pc.eop_ai_data}", "w", encoding="utf-8") as w:
        dump(
            {
                "version": pc.eop_ai_version,
                "enable_group_list": var.enable_group_list,
                "session_data": var.session_data,
                "reply_type": var.reply_type,
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
        raise Exception(f"访问https://paste.mozilla.org/失败，响应码：{resp.status_code}")

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


def get_id(event: MessageEvent) -> str:
    """获取会话id"""
    if isinstance(event, GroupMessageEvent):
        if pc.eop_ai_group_share:
            id = f"{(event.group_id)}-share"
        else:
            id = f"{event.user_id}"
    else:
        id = f"{event.user_id}"
    # 记录id
    if id not in var.session_data:
        var.session_data[id] = ""
    return id


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
                        msg += f"@{user_name}"  # 保持给bot看到的内容与真实用户看到的一致
    return msg


async def get_answer(matcher: Matcher, event: MessageEvent, bot: Bot, immersive=False):
    """ "从api获取回答"""
    # 获取问题
    question = unescape(await gen_chat_text(event, bot))

    # 获取用户id
    id = get_id(event)

    # 判断是否有回答没完成
    if id in var.session_lock and var.session_lock[id]:
        if immersive:
            await matcher.reject("上一个回答还没完成呢")

        await matcher.finish("上一个回答还没完成呢")

    # 根据配置是否发出提示
    if pc.eop_ai_reply_notice:
        await matcher.send("响应中...")

    eop_id = var.session_data[id]

    try:
        # 检查登陆权限
        await http_request("get", "/user/info")

        # 检查会话列表是否有
        if not eop_id:
            resp_data = await http_request("get", "/bot/list")
            for b in resp_data["bots"]:
                if id == b["alias"]:
                    eop_id = b["eop_id"]
                    break

        # 没有就创建新的
        if not eop_id:
            resp_data = await http_request(
                "post",
                "/bot/create",
                json={"model": "ChatGPT", "prompt": "", "alias": id},
            )
            eop_id: str = resp_data["bot_info"]["eop_id"]

        var.session_data[id] = eop_id
        # 上锁
        var.session_lock[id] = True
        # 获取回答
        answer = ""
        async with var.httpx_client.stream(
            "POST", f"/bot/{eop_id}/talk", json={"q": question}
        ) as response:
            async for chunk in response.aiter_lines():
                data = loads(chunk)
                if data["type"] == "msg_info" or data["type"] == "end":
                    continue
                if data["type"] == "response":
                    answer = data["data"]
                else:
                    var.session_lock[id] = False
                    if data["type"] == "deleted":
                        var.session_data[id] = ""
                        await matcher.finish(f"原会话失效，已自动刷新会话，请重新发起对话")

                    await matcher.finish(f"生成回答异常，类型：{data['type']}：{data['data']}")

        # 转图片并粘贴到剪切板
        async def _reply_with_img(answer: str):
            answer_image, answer_text_link = await gather(
                md_to_pic(answer), get_pasted_url(answer, id)
            )
            return MS.image(answer_image) + MS.text("文本：" + answer_text_link)

        # 沉浸式对话
        if not immersive:
            if pc.eop_ai_reply_type:
                await matcher.finish(await _reply_with_img(answer))
            await matcher.finish(answer, at_sender=True)
        # 普通对话
        else:
            if pc.eop_ai_reply_type:
                await matcher.reject(await _reply_with_img(answer))
            await matcher.reject(answer, at_sender=True)

    except (RejectedException, FinishedException) as e:
        raise e

    except RequestError as e:
        await matcher.finish(str(e))

    except Exception as e:
        await matcher.finish(str(e))

    finally:
        # 解锁
        var.session_lock[id] = False


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

    # 非登录时验证异常尝试重新验证
    if url != "/user/login" and (resp.status_code == 401 or resp.status_code == 403):
        hash_object = sha256()
        hash_object.update(pc.eop_ai_passwd.encode("utf-8"))
        resp_data = await http_request(
            "post",
            "/user/login",
            json={"user": pc.eop_ai_user, "passwd": hash_object.hexdigest()},
        )
        var.access_token = resp_data["access_token"]
        var.httpx_client.headers.update({"Authorization": f"Bearer {var.access_token}"})
        # 重新请求
        return await http_request(method, url, **kwargs)

    if resp.status_code == 204:
        return {}

    if resp.status_code != 200:
        raise RequestError(method, url, resp.status_code, resp.json())

    return resp.json()
