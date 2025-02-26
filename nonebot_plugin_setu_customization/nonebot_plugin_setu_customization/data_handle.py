from asyncio import sleep
from json import dumps, loads
from random import choice
from re import search
from typing import Optional, Tuple
from urllib.parse import unquote, urljoin

from aiohttp import ClientSession, ClientTimeout

from .config import pc, var


def url_diy_replace(img_url: str) -> str:
    """
    图片url自定义替换，可根据自己需求自己改
    """
    # pixiv图片缩小尺寸以及pixiv反代地址
    if "/img-original/img/" in img_url:
        img_url_group = img_url.replace("//", "").split("/")
        img_url_group.pop(0)
        if pc.tutu_pixiv_proxy:
            img_url = pc.tutu_pixiv_proxy + "/" + "/".join(img_url_group)
        else:
            img_url = "https://i.pixiv.re/" + "/".join(img_url_group)

        # 缩小图片大小
        img_url = img_url.replace("/img-original/img/", "/img-master/img/")
        ext = img_url.split(".")[-1]
        img_url = img_url.replace(f".{ext}", "_master1200.jpg")

    return unquote(img_url)


def extract_img_url(text: str) -> Optional[str]:
    # 判断有没有original关键字，有就找原图
    if '"original"' in text:
        original_exists = True
    else:
        original_exists = False

    # 尝试反序列化，如果序列化成功再变带缩进的序列号字符串，方便正则找url
    try:
        tmp_data = dumps(loads(text), indent=4, ensure_ascii=False)
        if original_exists:
            img_url = search(
                r"original.+(?P<MSG>(?:http)?s?:?\\?/\\?/[^\"]*)", tmp_data
            )
        else:
            img_url = search(r"(?P<MSG>(?:http)?s?:?\\?/\\?/[^\"]*)", tmp_data)
    except:
        img_url = search(r"(?P<MSG>(?:http)?s?:?\\?/\\?/[^\"]*)", text)

    try:
        if not img_url:
            raise IndexError
        else:
            # 去掉反斜杠
            img_url = img_url.group("MSG").replace("\\", "")
            # 没有协议头补上https
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            return img_url
    except IndexError:
        return None


async def get_img_url(api_url: str) -> Tuple[bool, str, str]:
    """
    向API发起请求，获取返回的图片url
    返回   请求成功失败, 图片地址, debug信息
    """

    if "本地图库" in api_url:
        filename = api_url[4:]
        if filename not in var.local_imgs:
            return False, "", f"本地图库{filename}不存在"

        img_url = choice(var.local_imgs[filename])
        return True, img_url, ""

    retried = False
    while True:
        try:
            async with ClientSession(
                headers=var.headers, timeout=ClientTimeout(var.http_timeout)
            ) as session:
                async with session.get(
                    api_url.replace("tutuNoProxy", ""),
                    allow_redirects=False,
                    ssl=False,
                    proxy=None if "tutuNoProxy" in api_url else pc.tutu_http_proxy,
                ) as resp:
                    resp_status = resp.status

                    if resp_status > 400:
                        return (
                            False,
                            "",
                            f"{api_url}\n响应异常，\n响应码：{resp_status}",
                        )

                    elif 300 <= resp_status < 400:
                        img_url = resp.headers["location"]
                        if "//" not in img_url[:10]:
                            img_url = urljoin(api_url, img_url)
                    else:
                        img_url = extract_img_url(await resp.text())
                        if not img_url:
                            return (
                                False,
                                "",
                                f"{api_url}\n找不到图片地址，\n响应码：{resp_status}",
                            )

                    return True, url_diy_replace(img_url), ""

        except Exception as e:
            if retried is False:
                retried = True
                await sleep(1)
                continue

            return False, "", f"{api_url}\n请求出错：{repr(e)}"
