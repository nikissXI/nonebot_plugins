from json import dump, load
from os import listdir, makedirs, path
from nonebot import get_driver
from nonebot.log import logger
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    # 机器人的QQ号（由于开发者多gocq连接，所以有这个设置）
    tutu_bot_qqnum: str = "0"  # 必填
    # 管理员的QQ号（别问我为什么）
    tutu_admin_qqnum: int = 0  # 必填
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
    # 网页访问地址，就是nonebot的监听地址和端口号，如 http://hahaha.com:80
    port: int = 8080
    tutu_site_url: str = f"http://127.0.0.1:{port}"
    # socks5代理地址，如 socks5://127.0.0.1:1234
    tutu_socks5_proxy: str | None = None
    # http代理地址，如 http://127.0.0.1:1234
    tutu_http_proxy: str | None = None
    # 微信图片反代地址，如 http://img.example.top:114
    tutu_wx_img_proxy: str | None = None
    # B站图片反代地址，如 http://img.example.top:514
    tutu_bili_img_proxy: str | None = None
    # 新浪图片反代地址，如 http://img.example.top:514
    tutu_sina_img_proxy: str | None = None
    # 爬取文章图片时，图片的宽或高小于多少忽略爬取
    tutu_crawler_min_width: int = 500
    tutu_crawler_min_height: int = 500
    # 自动爬取功能，文章url文件放置路径
    tutu_crawler_file_path: str = "tutu_crawler/"
    # 自动爬取功能，检测文章标题，含有其中关键字则忽略爬取
    tutu_crawler_keyword: list[str] = ["删", "薪", "敏感", "暂停", "停更", "图包"]


class Global_var:
    # 图片类别：api列表
    api_list_online: dict[str, list[str]] = {}
    # 文件名：url列表
    api_list_local: dict[str, list[str]] = {}
    # 白名单群列表
    group_list: set[int] = set()
    # 是否合并发送
    merge_send = True
    # 群频率限制
    group_cooldown: set[int] = set()
    # 用户频率限制
    user_cooldown: set[int] = set()
    # 爬取的图片缓存数据  图片序号 链接
    tmp_data: dict[int, str] = {}
    # 已发送的图片数量（用于sent_img_data的键名）
    sent_img_num = 0
    # 发送过去的图片数据  图片序号
    sent_img_apiurl_data: dict[int, str] = {}
    sent_img_imgurl_data: dict[int, str] = {}
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
    http_timeout = 20


driver = get_driver()
global_config = driver.config
plugin_config = Config.parse_obj(global_config)
var = Global_var()


def read_data():
    """
    读取配置文件
    """
    with open(f"data/{plugin_config.tutu_data_filename}", "r", encoding="utf-8") as r:
        tmp_data = load(r)
        for group_id in tmp_data[0]:
            var.group_list.add(group_id)
        var.api_list_online = tmp_data[1]
        var.merge_send = tmp_data[2]


def save_data():
    """
    保存配置文件
    """
    with open(f"data/{plugin_config.tutu_data_filename}", "w", encoding="utf-8") as w:
        dump(
            [list(var.group_list), var.api_list_online, var.merge_send],
            w,
            indent=4,
            ensure_ascii=False,
        )


def load_local_api():
    """
    读取本地图片库
    """
    var.api_list_local.clear()
    for file_name in listdir(plugin_config.tutu_local_api_path):
        with open(
            plugin_config.tutu_local_api_path + file_name, "r", encoding="utf-8"
        ) as r:
            api_list_lines = r.readlines()
        var.api_list_local[file_name] = [line.rstrip() for line in api_list_lines]


@driver.on_startup
async def on_startup():
    """
    启动时执行
    """
    if not path.exists(plugin_config.tutu_local_api_path):
        makedirs(plugin_config.tutu_local_api_path)

    if not path.exists(plugin_config.tutu_crawler_file_path):
        makedirs(plugin_config.tutu_crawler_file_path)

    if path.exists(f"data/{plugin_config.tutu_data_filename}"):
        read_data()

    load_local_api()
