from hashlib import sha256
from os import makedirs, path
from re import search
from html import unescape
from typing import Optional
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageEvent, Bot
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot import get_driver
from nonebot.exception import FinishedException
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
    # 读取数据
    if path.exists(f"data/{pc.eop_ai_data}"):
        with open(f"data/{pc.eop_ai_data}", "r", encoding="utf-8") as r:
            (
                var.enable_group_list,
                var.session_data,
            ) = load(r)
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
            [
                var.enable_group_list,
                var.session_data,
            ],
            w,
            indent=4,
            ensure_ascii=False,
        )


# from traceback import format_exc
# from nonebot import get_driver
# driver = get_driver()
# @driver.on_startup
# async def _():
#     pass


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


async def get_answer(
    matcher: Matcher, event: MessageEvent, bot: Bot, immersive=False
) -> str:
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

        answer = ""
        async with var.httpx_client.stream(
            "POST", f"/bot/{eop_id}/talk", json={"q": question}
        ) as response:
            async for chunk in response.aiter_lines():
                data = loads(chunk)
                if data["type"] == "msg_info":
                    continue
                if data["type"] == "response":
                    if data["data"]["complete"]:
                        answer = data["data"]["content"]
                    else:
                        continue
                else:
                    var.session_lock[id] = False
                    if data["type"] == "deleted":
                        var.session_data[id] = ""
                        await matcher.finish(f"原会话失效，已自动刷新会话，请重新发起对话")

                    await matcher.finish(f"生成回答异常，类型：{data['type']}：{data['data']}")

        var.session_lock[id] = False
        return answer

    except FinishedException:
        await matcher.finish()

    except RequestError as e:
        await matcher.finish(str(e))

    except Exception as e:
        await matcher.finish(str(e))


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


async def http_request(method: str, url: str, **params) -> dict:
    try:
        resp = await var.httpx_client.request(method, url, **params)
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
        return await http_request(method, url, **params)

    if resp.status_code == 204:
        return {}

    if resp.status_code != 200:
        raise RequestError(method, url, resp.status_code, resp.json())

    return resp.json()


async def get_pasted_url(content: str) -> str:
    resp = await var.httpx_client.get("https://paste.mozilla.org/")
    if resp.status_code != 200:
        raise Exception(f"访问https://paste.mozilla.org/失败，响应码：{resp.status_code}")

    match = search(
        r'<input[^>]+name="csrfmiddlewaretoken"[^>]+value="([^"]+)"', resp.text
    )
    if match:
        csrfmiddlewaretoken: str = match.group(1)
    else:
        raise Exception("未找到csrfmiddlewaretoken")

    data = {
        "csrfmiddlewaretoken": csrfmiddlewaretoken,
        "title": "",
        "lexer": "_markdown",
        "expires": 86400,
        "content": content,
    }
    resp = await var.httpx_client.post(
        "https://paste.mozilla.org/",
        headers={
            "Origin": "https://paste.mozilla.org",
            "Referer": "https://paste.mozilla.org/",
        },
        data=data,
    )
    if resp.status_code == 302:
        location = resp.headers.get("Location")
        return f"https://paste.mozilla.org{location}"
    else:
        raise Exception("提交后响应码非302")
