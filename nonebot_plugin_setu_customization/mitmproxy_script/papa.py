from mitmproxy.http import HTTPFlow
from bs4 import BeautifulSoup
from ujson import loads
from re import search
from html import unescape
from os import path, makedirs, listdir, remove
from asyncio import create_task, sleep
import sys
from httpx import AsyncClient
from traceback import format_exc

"""
代理服务器模块
"""
from mitmproxy import options
from mitmproxy.tools.dump import DumpMaster
from asyncio import run


class SelfAddon:
    result_path = "result"
    history_url: dict[str, list[str]] = dict()
    biz_nickname_dict: dict[str, str] = dict()
    new_data_nickname: set[str] = set()
    html_data_save = False
    bilibili_list: set[str] = set()

    def __init__(self):
        # 创建结果输出目录
        if not path.exists(self.result_path):
            makedirs(self.result_path)

        # 遍历结果目录
        files = listdir(self.result_path)
        for nickname in files:
            if path.exists(f"{self.result_path}/{nickname}/new_data_{nickname}"):
                exit(
                    f"****** WARNING ******\n【{nickname}】上次爬取的新数据还没合并到 history_data_{nickname} 中\n合并后删除该文件再爬取\n****** WARNING ******"
                )

            # 读取biz
            if nickname.find("B站_") == -1:
                if path.exists(f"{self.result_path}/{nickname}/biz_{nickname}"):
                    with open(
                        f"{self.result_path}/{nickname}/biz_{nickname}",
                        "r",
                        encoding="utf-8",
                    ) as r:
                        self.biz_nickname_dict[r.read()] = nickname
                else:
                    exit(f"{nickname}没找到biz")
            elif path.exists(f"{self.result_path}/{nickname}/Done"):
                self.bilibili_list.add(nickname)
                print(f"{nickname}有Done文件，忽略爬取")

            # 读取爬取历史
            if path.exists(f"{self.result_path}/{nickname}/history_data_{nickname}"):
                self.history_url[nickname] = []
                with open(
                    f"{self.result_path}/{nickname}/history_data_{nickname}",
                    "r",
                    encoding="utf-8",
                ) as r:
                    lines = r.readlines()

                for line in lines:
                    if line:
                        tt, uu = line.split(" *** ")
                        self.history_url[nickname].append(uu.strip())
                print(f"读取【{nickname}】历史数据{len(self.history_url[nickname])}条")

    def response(self, flow: HTTPFlow):
        req_url = flow.request.url
        if flow.response and flow.response.text:
            # 微信查看历史文章首次进入
            if (
                req_url.find("https://mp.weixin.qq.com/mp/profile_ext?action=home&")
                != -1
            ):
                # 获取公众号biz和名称
                biz = req_url[
                    req_url.find("&__biz=") + 7 : req_url.find("&__biz=") + 23
                ]
                nickname = search(
                    '.*var nickname = "(?P<MSG>[^"]*)', flow.response.text
                )
                if nickname:
                    nickname = nickname.group("MSG")
                    # 如果目录不存在就创建，并保存biz
                    if not path.exists(f"{self.result_path}/{nickname}"):
                        makedirs(f"{self.result_path}/{nickname}")
                        self.history_url[nickname] = []
                        self.biz_nickname_dict[biz] = nickname
                        with open(
                            f"{self.result_path}/{nickname}/biz_{nickname}",
                            "w",
                            encoding="utf-8",
                        ) as w:
                            w.write(biz)
                        with open(
                            f"{self.result_path}/{nickname}/history_data_{nickname}",
                            "w",
                            encoding="utf-8",
                        ) as w:
                            w.write("")
                else:
                    exit("没匹配到公众号名称")

                # 首次进入的页面数据
                if self.html_data_save:
                    with open(
                        f"{self.result_path}/{nickname}/first.html",
                        "w",
                        encoding="utf-8",
                    ) as w:
                        w.write(f"{req_url}\n\n" + flow.response.text)

                aa = search(".*var msgList = '(?P<MSG>[^']*)", flow.response.text)
                if not aa:
                    exit("首次进入没找到mglist数据")
                bb = loads(unescape(unescape(aa.group("MSG"))))
                self.get_art_url(bb["list"], nickname, 0)

            # 历史文章后续滚动
            if (
                req_url.find("https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&")
                != -1
            ):
                # 获取公众号biz
                biz = req_url[
                    req_url.find("&__biz=") + 7 : req_url.find("&__biz=") + 23
                ]
                nickname = self.biz_nickname_dict[biz]

                if not path.exists(f"{self.result_path}/{nickname}"):
                    exit("目录不存在")

                # 后续进入的页面数据
                if self.html_data_save:
                    with open(
                        f"{self.result_path}/{nickname}/second.html",
                        "w",
                        encoding="utf-8",
                    ) as w:
                        w.write(f"{req_url}\n\n" + flow.response.text)

                aa = loads(flow.response.text)["general_msg_list"]
                bb = loads(unescape(aa))
                self.get_art_url(bb["list"], nickname, 0)

            # 微信公众号平台爬取缓存biz和昵称
            if (
                req_url.find(
                    "https://mp.weixin.qq.com/cgi-bin/searchbiz?action=search_biz&"
                )
                != -1
            ):
                aa = loads(flow.response.text)
                if aa["list"]:
                    for i in aa["list"]:
                        biz = i["fakeid"]
                        nickname = i["nickname"]
                        self.biz_nickname_dict[biz] = nickname
                else:
                    exit("公众号平台爬取缓存biz和昵称获取list数据失败")

            # 微信公众号平台爬取
            if (
                req_url.find("https://mp.weixin.qq.com/cgi-bin/appmsg?action=list_ex&")
                != -1
            ):
                # 获取公众号biz
                biz = req_url[
                    req_url.find("&fakeid=") + 8 : req_url.find("&fakeid=") + 24
                ]
                if biz not in self.biz_nickname_dict:
                    exit(f"{biz}没在biz_nickname_dict中")

                nickname = self.biz_nickname_dict[biz]
                # 如果目录不存在就创建，并保存biz
                if not path.exists(f"{self.result_path}/{nickname}"):
                    makedirs(f"{self.result_path}/{nickname}")
                    self.history_url[nickname] = []
                    self.biz_nickname_dict[biz] = nickname
                    with open(
                        f"{self.result_path}/{nickname}/biz_{nickname}",
                        "w",
                        encoding="utf-8",
                    ) as w:
                        w.write(biz)
                    with open(
                        f"{self.result_path}/{nickname}/history_data_{nickname}",
                        "w",
                        encoding="utf-8",
                    ) as w:
                        w.write("")

                # 首次进入的页面数据
                if self.html_data_save:
                    with open(
                        f"{self.result_path}/{nickname}/first.html",
                        "w",
                        encoding="utf-8",
                    ) as w:
                        w.write(f"{req_url}\n\n" + flow.response.text)

                aa = loads(flow.response.text)
                try:
                    aa["app_msg_list"]
                except:
                    exit("没找到app_msg_list数据，被封了吧")

                self.get_art_url(aa["app_msg_list"], nickname, 1)

            # B站专栏爬取
            if (
                req_url.find("https://api.bilibili.com/x/space/wbi/article?") != -1
                and req_url.find("&sort=publish_time&") != -1
            ):
                aa = loads(flow.response.text)
                bb = aa["data"]["articles"]
                author = ""
                for i in bb:
                    author = "B站_" + i["author"]["name"]
                    break
                if not author:
                    exit("B站专栏没有找到作者")

                if author not in self.bilibili_list:
                    self.bilibili_list.add(author)

                    # 如果目录不存在就创建
                    if not path.exists(f"{self.result_path}/{author}"):
                        makedirs(f"{self.result_path}/{author}")
                        self.history_url[author] = []

                        with open(
                            f"{self.result_path}/{author}/history_data_{author}",
                            "w",
                            encoding="utf-8",
                        ) as w:
                            w.write("")

                    create_task(self.bilibili(req_url, author))

    def get_art_url(self, dict_data, nickname, tt: int):
        # 获取数据
        tmp_art_list = []
        end = False
        # 微信历史文章分析
        if tt == 0:
            for i in dict_data:
                tmp_art_list.append(
                    (
                        i["app_msg_ext_info"]["title"],
                        i["app_msg_ext_info"]["content_url"],
                    )
                )
                if i["app_msg_ext_info"]["multi_app_msg_item_list"]:
                    for j in i["app_msg_ext_info"]["multi_app_msg_item_list"]:
                        tmp_art_list.append((j["title"], j["content_url"]))
        # 公众号平台分析
        elif tt == 1:
            for i in dict_data:
                tmp_art_list.append(
                    (
                        i["title"],
                        i["link"],
                    )
                )
        # B站专栏分析
        else:
            for i in dict_data:
                tmp_art_list.append(
                    (
                        i["title"],
                        f"https://www.bilibili.com/read/cv{i['id']}",
                    )
                )

        for title, url in tmp_art_list:
            title = title.replace("\n", "").replace("<em>", "").replace("</em>", "")
            url = url.replace("http://", "https://")
            if tt != 2:
                url = url[: url.find("&chksm=")]
            if url not in self.history_url[nickname] and title and url:
                self.new_data_nickname.add(nickname)
                msg = f"{title} *** {url}\n"
                with open(
                    f"{self.result_path}/{nickname}/new_data_{nickname}",
                    "a",
                    encoding="utf-8",
                ) as a:
                    a.write(msg)
                self.history_url[nickname].append(url)
            else:
                end = True
        return end

    async def bilibili(self, url: str, author: str):
        tou = url[: url.find("&pn=") + 4]
        wei = url[url.find("&ps=") :]
        page_num = 1

        while True:
            with open(
                f"{self.result_path}/{author}/Loading_page{page_num}",
                "w",
                encoding="utf-8",
            ) as w:
                w.write("")
            next_url = f"{tou}{page_num}{wei}"
            try:
                async with AsyncClient(
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54",
                    },
                    timeout=10,
                    verify=False,
                ) as c:
                    res = await c.get(next_url)
            except:
                remove(f"{self.result_path}/{author}/Loading_page{page_num}")
                exit(f"{url}\n请求出错\n{format_exc()}")

            aa = loads(res.text)
            bb = aa["data"]
            if "articles" not in bb:
                remove(f"{self.result_path}/{author}/Loading_page{page_num}")
                with open(
                    f"{self.result_path}/{author}/Done",
                    "w",
                    encoding="utf-8",
                ) as w:
                    w.write("")
                break

            end = self.get_art_url(bb["articles"], author, 2)
            await sleep(2)
            remove(f"{self.result_path}/{author}/Loading_page{page_num}")
            page_num += 1
            if end:
                with open(
                    f"{self.result_path}/{author}/Done",
                    "w",
                    encoding="utf-8",
                ) as w:
                    w.write("")
                break


addon = SelfAddon()


async def start_proxy(port):
    opts = options.Options(listen_host="0.0.0.0", listen_port=port)
    m = DumpMaster(opts)
    m.addons.add(addon)
    await m.run()


if __name__ == "__main__":
    try:
        port = 8080
        for i in sys.argv[1:]:
            if i.find("-p") != -1:
                port = int(i[2:])
        print(f"开始监听{port}端口")
        run(start_proxy(port))
    except KeyboardInterrupt:
        if addon.new_data_nickname:
            msg = "\n".join([i for i in addon.new_data_nickname])
            print(f"停止，以下文件夹有新数据\n{msg}")
        else:
            print(f"停止，没有新数据")
