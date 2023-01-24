from json import dump, load
from os import listdir, makedirs, path
from pathlib import Path
from typing import Dict, List, Optional, Set
from nonebot import get_bot, get_bots, get_driver

from nonebot.adapters import Bot
from nonebot.log import logger
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    # 管理员的QQ号（别问我为什么）
    tutu_admin_qqnum: int = 0  # 必填

    # 机器人的QQ号（如果写了就按优先级响应，否则就第一个连上的响应） ['1234','5678','6666']
    tutu_bot_qqnum_list: List[str] = []
    # 图片下载模式，真则nonebot下载，假则协议端下载
    tutu_img_local_download: bool = True
    # 图图命令CD时间（秒）
    tutu_cooldown: int = 3
    # 一次最多发多少张图
    once_send: int = 5

    # R18类别的名称
    tutu_r18_name: str = "R18"
    # 本地图片库的路径
    tutu_local_api_path: str = "data/tutu_local_img_lib/"
    # 本地库二次元文件名称
    tutu_self_anime_lib: str = "self_anime"
    # 本地库三次元文件名称
    tutu_self_cosplay_lib: str = "self_cosplay"
    # 插件数据文件名
    tutu_data_filename: str = "tutu_data.json"
    # 字体文件路径
    tutu_font_path: str = f"{Path(__file__).parent}/font/HYWenHei-85W.ttf"
    # 字体大小
    tutu_font_size: int = 18
    # 网页访问地址，就是nonebot的监听地址和端口号，如 http://hahaha.com:80
    port: int = 8080
    tutu_site_url: str = f"http://127.0.0.1:{port}"
    # pixiv图片反代地址 备选 https://i.pixiv.re/ 、 https://i.pixiv.cat/ 、 https://i.loli.best/ 、 pimg.rem.asia 、 https://c.jitsu.top/
    tutu_pixiv_proxy: Optional[str] = None
    # http代理地址，如 http://127.0.0.1:1234
    tutu_http_proxy: Optional[str] = None
    # socks5代理地址，如 socks5://127.0.0.1:1234
    tutu_socks5_proxy: Optional[str] = None
    # 新浪图片反代地址，如 http://img.example.top:514
    tutu_sina_img_proxy: Optional[str] = "https://i0.wp.com/tvax1.sinaimg.cn/"
    # 微信图片反代地址，如 http://img.example.top:114
    tutu_wx_img_proxy: Optional[str] = None
    # B站图片反代地址，如 http://img.example.top:514
    tutu_bili_img_proxy: Optional[str] = None
    # 爬取文章图片时，图片的宽或高小于多少忽略爬取
    tutu_crawler_min_width: int = 500
    tutu_crawler_min_height: int = 500
    # 自动爬取功能，文章url文件放置路径
    tutu_crawler_file_path: str = "tutu_crawler/"
    # 自动爬取功能，检测文章标题，含有其中关键字则忽略爬取
    tutu_crawler_keyword: List[str] = [
        "删",
        "薪",
        "敏感",
        "暂停",
        "停更",
        "图包",
        "资源",
        "债",
        "工资",
        "月入",
    ]


class Var:
    # 处理bot
    handle_bot: Optional[Bot] = None
    # 图片类别：api列表
    api_list_online: Dict[str, List[str]] = {}
    # 文件名：url列表
    api_list_local: Dict[str, List[str]] = {}
    # 图图白名单群列表
    group_list: Set[int] = set()
    # 是否合并发送
    merge_send = True
    # 群频率限制
    group_cooldown: Set[int] = set()
    # 用户频率限制
    user_cooldown: Set[int] = set()
    # 爬取的图片缓存数据  图片序号 链接
    tmp_data: Dict[int, str] = {}
    # 已发送的图片数量（用于sent_img_data的键名）
    sent_img_num = 0
    fn_sent_img_num = 0
    # 发送过去的图片数据  图片序号
    sent_img_apiurl_data: Dict[int, str] = {}
    sent_img_imgurl_data: Dict[int, str] = {}
    # 网页浏览个人库时发送过去的图片数据  图片序号
    fn_sent_img_filename_data: Dict[int, str] = {}
    fn_sent_img_imgurl_data: Dict[int, str] = {}
    # 是否有爬取任务
    crawler_task = False
    # 当前任务文件名，总数，剩余数，爬取图片数量，入库名
    crawler_current_msg = []
    # 请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54",
    }
    wx_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54",
        "Referer": "https://mp.weixin.qq.com/",
    }
    bili_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54",
        "Referer": "https://www.bilibili.com/",
    }
    sina_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54",
        "Referer": "https://www.sina.com.cn/",
    }
    # 每篇文章的爬取间隔
    paqu_cooldown = 3
    # http请求超时
    http_timeout = 10


driver = get_driver()
global_config = driver.config
pc = Config.parse_obj(global_config)
var = Var()
# scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


def read_data():
    """
    读取配置文件
    """
    with open(f"data/{pc.tutu_data_filename}", "r", encoding="utf-8") as r:
        tmp_data = load(r)
        for group_id in tmp_data[0]:
            var.group_list.add(group_id)
        var.api_list_online = tmp_data[1]
        var.merge_send = tmp_data[2]


def save_data():
    """
    保存配置文件
    """
    with open(f"data/{pc.tutu_data_filename}", "w", encoding="utf-8") as w:
        dump(
            [
                list(var.group_list),
                var.api_list_online,
                var.merge_send,
            ],
            w,
            indent=4,
            ensure_ascii=False,
        )


def load_local_api():
    """
    读取本地图片库
    """
    var.api_list_local.clear()
    for file_name in listdir(pc.tutu_local_api_path):
        with open(pc.tutu_local_api_path + file_name, "r", encoding="utf-8") as r:
            api_list_lines = r.readlines()
        var.api_list_local[file_name] = [line.rstrip() for line in api_list_lines]


@driver.on_startup
async def on_startup():
    """
    启动时执行
    """
    if not path.exists(pc.tutu_local_api_path):
        makedirs(pc.tutu_local_api_path)

    if not path.exists(pc.tutu_crawler_file_path):
        makedirs(pc.tutu_crawler_file_path)

    if path.exists(f"data/{pc.tutu_data_filename}"):
        read_data()

    load_local_api()


# qq机器人连接时执行
@driver.on_bot_connect
async def on_bot_connect(bot: Bot):
    # 是否有写bot qq，如果写了只处理bot qq在列表里的
    if pc.tutu_bot_qqnum_list and bot.self_id in pc.tutu_bot_qqnum_list:
        # 如果已经有bot连了
        if var.handle_bot:
            # 当前bot qq 下标
            handle_bot_id_index = pc.tutu_bot_qqnum_list.index(var.handle_bot.self_id)
            # 连过俩的bot qq 下标
            new_bot_id_index = pc.tutu_bot_qqnum_list.index(bot.self_id)
            # 判断优先级，下标越低优先级越高
            if new_bot_id_index < handle_bot_id_index:
                var.handle_bot = bot

        # 没bot连就直接给
        else:
            var.handle_bot = bot

    # 不写就给第一个连的
    elif not pc.tutu_bot_qqnum_list and not var.handle_bot:
        var.handle_bot = bot


# qq机器人断开时执行
@driver.on_bot_disconnect
async def on_bot_disconnect(bot: Bot):
    # 判断掉线的是否为handle bot
    if bot == var.handle_bot:
        # 如果有写bot qq列表
        if pc.tutu_bot_qqnum_list:
            # 获取当前连着的bot列表(需要bot是在bot qq列表里)
            available_bot_id_list = [
                bot_id for bot_id in get_bots() if bot_id in pc.tutu_bot_qqnum_list
            ]
            if available_bot_id_list:
                # 打擂台排序？
                new_bot_index = pc.tutu_bot_qqnum_list.index(available_bot_id_list[0])
                for bot_id in available_bot_id_list:
                    now_bot_index = pc.tutu_bot_qqnum_list.index(bot_id)
                    if now_bot_index < new_bot_index:
                        new_bot_index = now_bot_index
                # 取下标在qq列表里最小的bot qq为新的handle bot
                var.handle_bot = get_bot(pc.tutu_bot_qqnum_list[new_bot_index])
            else:
                var.handle_bot = None

        # 不写就随便给一个连着的(如果有)
        elif var.handle_bot:
            try:
                new_bot = get_bot()
                var.handle_bot = new_bot
            except ValueError:
                var.handle_bot = None
