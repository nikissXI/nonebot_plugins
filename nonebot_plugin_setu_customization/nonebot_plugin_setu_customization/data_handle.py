from asyncio import gather, sleep
from datetime import datetime, timedelta
from functools import wraps
from io import BytesIO
from os import listdir, remove, rename, rmdir
from random import choice, randint
from re import findall, search
from traceback import format_exc
from typing import Optional, Tuple, Union
from urllib.parse import unquote
from bs4 import BeautifulSoup
from httpx import AsyncClient, Response
from httpx_socks import AsyncProxyTransport
from nonebot.adapters.onebot.v11 import ActionFailed, Bot, Message, MessageEvent
from nonebot.adapters.onebot.v11 import MessageSegment as MS
from nonebot.adapters.onebot.v11 import NetworkError
from nonebot.exception import FinishedException, RejectedException
from nonebot.log import logger
from nonebot.matcher import Matcher
from PIL import Image, ImageDraw, ImageFont
from ujson import dumps, loads
from .config import pc, var

###################################
# 异常处理
###################################
def handle_exception(name: str):
    def wrapper(func):
        @wraps(func)
        async def inner(**kwargs):
            now = datetime.now()
            time_str = f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"
            try:
                await func(**kwargs)
            except ActionFailed as e:
                if e.info["wording"] == "消息不存在":
                    return
                msg = f"{time_str}\n{name} 处理器信息发送失败！\n失败原因：{e.info['msg']}  {e.info['wording']}"
                logger.error(msg)
                await send_error_msg(msg)
            except NetworkError:
                msg = f"{time_str}\n{name} 处理器信息发送超时！"
                logger.error(msg)
                await send_error_msg(msg)
            except (FinishedException, RejectedException):
                raise
            except Exception:
                # 代码本身出问题
                error_msg = format_exc()
                msg = f"{time_str}\n{name} 处理器执行出错!\n错误追踪:"
                logger.error(msg + f"\n{error_msg}")
                await send_error_msg(msg + MS.image(text_to_img(error_msg)))

        return inner

    return wrapper


def text_to_img(text: str, font_path: str = pc.tutu_font_path) -> BytesIO:
    """
    字转图片
    """
    lines = text.splitlines()
    line_count = len(lines)
    # 读取字体
    font = ImageFont.truetype(font_path, pc.tutu_font_size)
    # 获取字体的行高
    left, top, width, line_height = font.getbbox("a")
    # 增加行距
    line_height += 3
    # 获取画布需要的高度
    height = line_height * line_count + 20
    # 获取画布需要的宽度
    width = int(max([font.getlength(line) for line in lines])) + 25
    # 字体颜色
    black_color = (0, 0, 0)
    red_color = (211, 38, 38)
    # 生成画布
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    # 按行开画，c是计算写到第几行
    c = 0
    for line in lines:
        if line.find("img_url: ") == -1:
            color = black_color
        else:
            color = red_color
        draw.text((10, 6 + line_height * c), line, font=font, fill=color)
        c += 1
    img_bytes = BytesIO()
    image.save(img_bytes, format="jpeg")
    return img_bytes


def pixiv_reverse_proxy(img_url: str, resize: bool = True) -> str:
    # pixiv图片缩小尺寸以及pixiv反代地址
    if img_url.find("/img-original/img/") != -1:
        img_url_group = img_url.replace("//", "").split("/")
        img_url_group.pop(0)
        if pc.tutu_pixiv_proxy:
            img_url = pc.tutu_pixiv_proxy + "/".join(img_url_group)
        else:
            img_url = f"https://{choice('abcdi')}.jitsu.top/" + "/".join(img_url_group)

        # 缩小图片大小
        if resize:
            img_url = img_url.replace("/img-original/img/", "/img-master/img/")
            ext = img_url.split(".")[-1]
            img_url = img_url.replace(f".{ext}", f"_master1200.jpg")
    return img_url


def url_diy_replace(img_url: str) -> str:
    """
    图片url自定义替换，根据自己需求自己改
    """
    # 没有协议头补上https
    if img_url.find("http") == -1:
        img_url = f"https:{img_url}"
    # 去掉反斜杠
    img_url = img_url.replace("\\", "")
    # pixiv反代
    img_url = pixiv_reverse_proxy(img_url)
    # 反代地址
    if img_url.find("https://hefollo.com") != -1:
        img_url = img_url.replace("https://hefollo.com", "http://mc.nikiss.top:9896")
    # 新浪图床反代地址
    if pc.tutu_sina_img_proxy and img_url.find(".sinaimg.cn") != -1:
        img_url = img_url.replace(
            img_url[: img_url.find(".sinaimg.cn") + 11],
            pc.tutu_sina_img_proxy,
        )
    # 微信图床反代地址
    if pc.tutu_wx_img_proxy and img_url.find("https://mmbiz.qpic.cn") != -1:
        img_url = img_url.replace("https://mmbiz.qpic.cn", pc.tutu_wx_img_proxy)
    # B站图床反代地址
    if pc.tutu_bili_img_proxy and img_url.find("https://i0.hdslb.com") != -1:
        img_url = img_url.replace("https://i0.hdslb.com", pc.tutu_bili_img_proxy)
    return unquote(img_url)


def to_node_msg(msg):
    """
    生成合并转发消息的json格式数据
    """
    return {
        "type": "node",
        "data": {
            "name": "喵喵喵",
            "uin": "123456",
            "content": msg,
        },
    }


def cache_sent_img(api_url: str, img_url: str) -> int:
    """
    每发一张图片都有一个编号，重启后重置，可以用于找某个图片的url，方便debug或别的
    """
    if var.sent_img_num > 100000:
        var.sent_img_num = 0
    var.sent_img_num += 1
    var.sent_img_apiurl_data[var.sent_img_num] = api_url
    var.sent_img_imgurl_data[var.sent_img_num] = img_url
    return var.sent_img_num


def fn_cache_sent_img(filename: str, img_url: str) -> int:
    """
    每发一张图片都有一个编号，重启后重置，可以用于找某个图片的url，方便debug或别的
    """
    if var.fn_sent_img_num > 100000:
        var.fn_sent_img_num = 0
    var.fn_sent_img_num += 1
    var.fn_sent_img_filename_data[var.fn_sent_img_num] = filename
    var.fn_sent_img_imgurl_data[var.fn_sent_img_num] = img_url
    return var.fn_sent_img_num


async def send_error_msg(msg: Union[str, Message]):
    if var.handle_bot:
        await var.handle_bot.send_private_msg(user_id=pc.tutu_admin_qqnum, message=msg)


async def send_img_msg(matcher: Matcher, img_num: int, img_url: str):
    try:
        if pc.tutu_img_local_download:
            ds, result = await download_img(img_url)
            if ds:
                await matcher.send(f"No.{img_num}" + MS.image(result, timeout=30))
            else:
                await matcher.send(f"No.{img_num}\n{result}")
        else:
            await matcher.send(f"No.{img_num}" + MS.image(img_url, timeout=30))

    except Exception as e:
        await matcher.send(f"No.{img_num}  {img_url}\n发送失败 {repr(e)}")


async def download_img(img_url: str) -> Tuple[bool, Union[BytesIO, str]]:
    # 微信图床
    if pc.tutu_wx_img_proxy and img_url.find("https://mmbiz.qpic.cn") != -1:
        headers = var.wx_headers
    # B站图床
    elif pc.tutu_bili_img_proxy and img_url.find("https://i0.hdslb.com") != -1:
        headers = var.bili_headers
    # 新浪图床
    elif pc.tutu_sina_img_proxy and img_url.find(".sinaimg.cn") != -1:
        headers = var.sina_headers
    else:
        headers = var.headers

    socks5_proxy = None
    http_proxy = None
    if img_url.find("127.0.0.1") == -1:
        if pc.tutu_socks5_proxy:
            socks5_proxy = AsyncProxyTransport.from_url(pc.tutu_socks5_proxy)
        if pc.tutu_http_proxy:
            http_proxy = pc.tutu_http_proxy

    async def _request_img(img_url: str) -> Union[str, BytesIO]:
        async with AsyncClient(
            headers=headers,
            transport=socks5_proxy,
            proxies=http_proxy,
            timeout=var.http_timeout,
            verify=False,
        ) as c:
            try:
                res = await c.get(url=img_url)
            except Exception as e:
                return f"{img_url}\n图片下载出错：{repr(e)}"
            else:
                if res.status_code == 200:
                    img_bytesio = BytesIO(res.content)
                    img = Image.open(img_bytesio)
                    try:
                        img.width
                    except Exception as e:
                        return f"{img_url}\n图片解析出错：{repr(e)}"
                    else:
                        return img_bytesio
                else:
                    return f"{img_url}\n图片响应异常：状态码{res.status_code}"

    result = await _request_img(img_url)

    if isinstance(result, BytesIO):
        return (True, result)
    else:
        logger.error(result)
        await send_error_msg(result)
        return (False, result)


def extract_img_url(text: str) -> Optional[str]:
    # 判断有没有original关键字，有就找原图
    if text.find('"original"') != -1:
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
            return img_url.group("MSG")
    except IndexError:
        return None


async def get_img_url(
    api_url: str, cache_data: bool = False, api_test: int = 0
) -> Tuple[bool, str, str]:
    """
    向API发起请求，获取返回的图片url
    """
    socks5_proxy = None
    http_proxy = None
    if api_url.find("127.0.0.1") == -1:
        if pc.tutu_socks5_proxy:
            socks5_proxy = AsyncProxyTransport.from_url(pc.tutu_socks5_proxy)
        if pc.tutu_http_proxy:
            http_proxy = pc.tutu_http_proxy

    error_times = 0

    async def _get_img_url(api_url: str) -> Union[Response, str]:
        nonlocal error_times
        async with AsyncClient(
            headers=var.headers,
            transport=socks5_proxy,
            proxies=http_proxy,
            timeout=var.http_timeout,
            verify=False,
        ) as c:
            try:
                rr = await c.get(url=api_url)
                return rr
            except Exception as e:
                error_times += 1
                if error_times < 2:
                    await sleep(1)
                    return await _get_img_url(api_url)
                else:
                    msg = f"{api_url}\n请求API出错：{repr(e)}"
                    logger.error(msg)
                    await send_error_msg(msg)
                    return msg

    rr = await _get_img_url(api_url)
    if isinstance(rr, str):
        return (False, rr, "")

    if rr.status_code == 200:
        img_url = extract_img_url(rr.text)
        if not img_url:
            msg = f"{api_url}\n找不到img_url\n响应码: {rr.status_code}\n响应内容: {rr.text}"
            logger.error(msg)
            await send_error_msg(msg)
            return (False, msg, "")
    elif 300 < rr.status_code < 310:
        img_url = rr.headers["location"]
    else:
        msg = f"{api_url}\n获取图片url出错 [{rr.status_code}]"
        logger.error(msg)
        await send_error_msg(msg)
        return (False, msg, "")

    # 没有协议头补上https
    if img_url.find("http") == -1:
        img_url = f"https:{img_url}"
    # 去掉反斜杠
    img_url = img_url.replace("\\", "")

    if api_test == 0:
        if cache_data:
            ext_msg = str(cache_sent_img(api_url, img_url))
        else:
            ext_msg = ""
    elif api_test == 1:
        res_headers = "\n".join([f"'{i}' : '{j}'" for i, j in rr.headers.items()])
        ext_msg = f"响应码: 【{rr.status_code}】\n响应头:\n{res_headers}\n响应内容:\n{rr.text}"
    else:
        ext_msg = api_url

    return (
        True,
        img_url,
        ext_msg,
    )


async def load_crawler_files(
    local_api_filename: str,
    matcher: Matcher,
    event: MessageEvent,
    bot: Bot,
):
    """
    读取待爬取的文章url文件
    """
    if not listdir(f"{pc.tutu_crawler_file_path}/{local_api_filename}"):
        rmdir(f"{pc.tutu_crawler_file_path}/{local_api_filename}")
        await matcher.send(f"{pc.tutu_crawler_file_path}/{local_api_filename}是空文件夹，已删除")
        return

    async def _rename(new_fn) -> str:
        old_pathname = f"{pc.tutu_crawler_file_path}{local_api_filename}"
        new_pathname = f"{pc.tutu_crawler_file_path}{new_fn}"
        rename(old_pathname, new_pathname)
        await matcher.send(f"[{old_pathname}]已重命名为[{new_pathname}]")
        return new_fn

    if local_api_filename == "2":
        local_api_filename = await _rename(pc.tutu_self_anime_lib)
    elif local_api_filename == "3":
        local_api_filename = await _rename(pc.tutu_self_cosplay_lib)

    var.crawler_task = True

    while True:
        files = listdir(f"{pc.tutu_crawler_file_path}/{local_api_filename}")
        if not files:
            rmdir(f"{pc.tutu_crawler_file_path}/{local_api_filename}")
            # await matcher.send(f"文件夹{local_api_filename}中的文件均爬取完成，文件夹已自动删除")
            break
        else:
            file = files[0]

        with open(
            f"{pc.tutu_crawler_file_path}/{local_api_filename}/{file}",
            "r",
            encoding="utf-8",
        ) as r:
            lines = r.readlines()

        var.crawler_current_msg = [file, len(lines), 0, 0, local_api_filename]

        if not lines:
            await matcher.send(f"文件{file}数据为空，已自动删除")

        else:
            now = datetime.now() + timedelta(
                seconds=(var.paqu_cooldown + 0.5) * var.crawler_current_msg[1]
            )
            finish_time = f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"
            await matcher.send(
                f"开始爬取 {file}\nurl数量：{var.crawler_current_msg[1]}\n入库文件名：{var.crawler_current_msg[4]}\n预计完成时间：{finish_time}"
            )

        def _save_data():
            with open(
                f"{pc.tutu_crawler_file_path}/{local_api_filename}/{file}",
                "w",
                encoding="utf-8",
            ) as w:
                w.writelines(lines)

        for line in lines[:]:
            # 去掉换行符
            url = line.strip()
            # 开始爬取图片
            try:
                img_num = await get_art_img_url(
                    url, local_api_filename, matcher, event, bot, True
                )
                error_msg = ""
            except Exception as e:
                error_msg = repr(e)
                img_num = -1
            # 如果爬取失败，终止，并保存当前的数据
            if img_num == -1:
                msg = f"文件{file}爬取中断，任务终止\n当前进度：{var.crawler_current_msg[2]}/{var.crawler_current_msg[1]}\n{local_api_filename}收录新图片：{var.crawler_current_msg[3]}张\n失败文章url：{url}\n错误信息：{error_msg}"
                var.crawler_task = False
                var.crawler_current_msg.clear()
                _save_data()
                logger.error(msg)
                await matcher.finish(msg)
            # 成功次数加一，把当前数据从列表中移除，睡眠3秒
            elif not var.crawler_task:
                msg = f"文件{file}爬取中断，任务终止\n当前进度：{var.crawler_current_msg[2]}/{var.crawler_current_msg[1]}\n{local_api_filename}收录新图片：{var.crawler_current_msg[3]}张"
                _save_data()
                var.crawler_current_msg.clear()
                await matcher.finish(msg)
            else:
                var.crawler_current_msg[2] += 1
                var.crawler_current_msg[3] += img_num
                lines.remove(line)
                await sleep(var.paqu_cooldown)

        remove(f"{pc.tutu_crawler_file_path}/{local_api_filename}/{file}")

        await matcher.send(
            f"{file} 数据爬取完成\n{local_api_filename}收录新图片：{var.crawler_current_msg[3]}张"
        )


async def get_art_img_url(
    url: str,
    filename: str,
    matcher: Matcher,
    event: MessageEvent,
    bot: Bot,
    crawler: bool = False,
) -> Optional[int]:
    """
    爬取文章中的图片url
    """
    if url.find("https://mp.weixin.qq.com/s") != -1:
        art_type = "wx"
    elif url.find("https://www.bilibili.com/read/cv") != -1:
        art_type = "bili"
    else:
        await matcher.send(f"不支持{url}的爬取")
        return 0

    try:
        async with AsyncClient(
            headers=var.headers,
            timeout=var.http_timeout,
            verify=False,
        ) as c:
            res = await c.get(url)
    except Exception as e:
        msg = f"{url}\n请求出错：{repr(e)}"
        logger.error(msg)
        await matcher.send(msg)
        return -1

    if filename not in var.api_list_local:
        var.api_list_local[filename] = []
        await matcher.send(f"新增{filename}本地库")

    img_list: list[str] = []
    filter_count = 0
    img_found = 0
    task_list = []
    error_times = 0
    html_text = ""

    content = res.content.decode("utf-8")
    soup = BeautifulSoup(content, "lxml")

    if art_type == "wx":
        title = soup.find_all("h1", class_="rich_media_title")
        if title:
            title = title[0].text.strip()
        else:
            await matcher.send(f"{url}\n未找到标题")
            return 0

    else:
        html_text = soup.prettify()
        aa = search(r"\s+window\.__INITIAL_STATE__=(?P<MSG>.*);\(function", html_text)
        if aa:
            bb = loads(aa.group("MSG"))
            title = bb["readInfo"]["title"]
        else:
            await matcher.send(f"{url}\n获取数据字段失败")
            return 0

    # 自动爬取
    if crawler:
        for k in pc.tutu_crawler_keyword:
            if title.find(k) != -1:
                await matcher.send(f"文章：{title}\n{url}\n标题发现关键字【{k}】，忽略该文章")
                return 0

    async def _get_img_size(img_url) -> Tuple[int, int, str]:
        nonlocal error_times
        try:
            # if art_type == "wx":
            #     headers = var.wx_headers
            # else:
            #     headers = var.bili_headers

            async with AsyncClient(
                headers=var.headers,
                timeout=var.http_timeout,
                verify=False,
            ) as c:
                res = await c.get(img_url)
                img = Image.open(BytesIO(res.content))
                return (img.width, img.height, img_url)
        # except UnidentifiedImageError:
        #     get_img_size_error += 1
        #     if get_img_size_error < 10:
        #         await sleep(1)
        #         return await _get_img_size(img_url)
        #     else:
        #         error_msg = format_exc()
        #         msg = f"文章：{title}\n{url}\n获取图片尺寸请求出错\n{img_url}\n错误追踪："
        #         logger.error(msg + f"\n{error_msg}")
        #         await matcher.send(msg + MS.image(write_error_msg_img(error_msg)))
        #         return (-1, -1, "")
        # except RemoteProtocolError:
        #     remote_error += 1
        #     if remote_error < 20:
        #         await sleep(remote_error)
        #         return await _get_img_size(img_url)
        #     else:
        #         msg = f"文章：{title}\n{url}\n获取图片尺寸请求出错\n{img_url}\n错误信息\n{format_exc()}"
        #         logger.error(msg)
        #         await matcher.send(msg)
        #         return (-1, -1, "")
        except Exception as e:
            error_times += 1
            if error_times < 10:
                await sleep(error_times)
                return await _get_img_size(img_url)
            else:
                msg = f"文章：{title}\n{url}\n获取图片尺寸请求出错\n{img_url}\n错误信息：{repr(e)}"
                logger.error(msg)
                await matcher.send(msg)
                return (-1, -1, "")

    if art_type == "wx":
        img_set = soup.find_all("img")
        for node in img_set:
            try:
                if node["data-type"] == "gif" or not node["data-src"]:
                    continue
            except:
                continue
            img_found += 1
            img_src = node["data-src"]

            if img_src in var.api_list_local[filename]:
                filter_count += 1
                continue

            pp = search("mmbiz_[^/]*", img_src)
            if pp:
                img_src_ext = pp.group()
            else:
                img_src_ext = "unknown"
            if img_src_ext in ["mmbiz_jpeg", "mmbiz_jpg", "mmbiz_png", "unknown"]:
                task_list.append(_get_img_size(img_src))
    else:
        img_url_list = []
        aa = search(r"\s+window\.__INITIAL_STATE__=(?P<MSG>.*);\(function", html_text)
        if not aa:
            await matcher.send(f"{url}\n获取数据字段失败")
            return 0
        bb = loads(aa.group("MSG"))
        if bb["readInfo"]["banner_url"]:
            img_url_list.append(bb["readInfo"]["banner_url"])
        cc = findall(r"data-src=\"([^\"]*)", bb["readInfo"]["content"])
        if cc:
            for i_img in cc:
                img_url_list.append(i_img)
        for img_src in img_url_list:
            img_found += 1

            if img_src.find("http") == -1:
                img_src = f"https:{img_src}"

            if img_src in var.api_list_local[filename]:
                filter_count += 1
                continue

            task_list.append(_get_img_size(img_src))

    gather_result = await gather(*task_list)
    for width, height, img_url in gather_result:
        if width == -1:
            await matcher.finish(f"获取图片尺寸出错，终止爬取\n{img_url}")
        elif width < pc.tutu_crawler_min_width or height < pc.tutu_crawler_min_height:
            continue
        else:
            var.api_list_local[filename].append(img_url)
            img_list.append(img_url)

    if crawler:
        if img_list:
            with open(
                f"{pc.tutu_local_api_path}/{filename}",
                "a",
                encoding="utf-8",
            ) as a:
                a.writelines([i + "\n" for i in img_list])
        return len(img_list)

    elif img_list:
        with open(
            f"{pc.tutu_local_api_path}/{filename}",
            "a",
            encoding="utf-8",
        ) as a:
            a.writelines([i + "\n" for i in img_list])

        msg_list = []
        img_url_msg_list = []
        task_list = []
        img_num = 0
        var.tmp_data.clear()
        var.tmp_data[0] = filename
        for img_url in img_list:
            img_num += 1
            var.tmp_data[img_num] = img_url
            if var.merge_send:
                msg_list.append(to_node_msg(MS.text(f"序号：{img_num}  {img_url}")))
                msg_list.append(to_node_msg(MS.image(img_url, timeout=30)))
            else:
                img_url_msg_list.append(f"序号：{img_num}  {img_url}")
                task_list.append(
                    matcher.send(f"序号：{img_num}" + MS.image(img_url, timeout=30))
                )

        await matcher.send(
            f"从文章【{title}】中获取到图片{img_found}个\n收录新图片{len(img_list)}张到本地库{filename}，因重复过滤掉图片{filter_count}张\n如果爬取图片有误，可以发送“撤销图片 [图片序号] 进行撤销”，如果发送失败，发送“爬取重放”重新发送"
        )

        if var.merge_send:
            await matcher.send(f"正在合并消息准备发送")
            await bot.send_private_forward_msg(user_id=event.user_id, messages=msg_list)
        else:
            await matcher.send("\n".join(img_url_msg_list))
            await gather(*task_list)
            await matcher.send(f"图片发送完毕")
    else:
        await matcher.send(
            f"从文章【{title}】中获取到图片{img_found}个\n没有收录新图片\n因重复过滤掉图片{filter_count}张"
        )
