from json import dump, load
from os import listdir, makedirs, path
from typing import Dict, List, Optional, Set

from nonebot import get_bot, get_bots, get_driver, get_plugin_config
from nonebot.adapters import Bot
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    # 机器人的QQ号（如果写了就按优先级响应，否则就第一个连上的响应） ['1234','5678','6666']
    tutu_bot_qqnum_list: List[str] = []
    # 图图命令CD时间（秒）
    tutu_cooldown: int = 3
    # 危险图库，危险图库的图片无法在群聊发送
    tutu_danger_gallery: List[str] = []
    # 本地图片库的路径
    tutu_local_api_path: str = "data/tutu_local_img_lib/"
    # 插件数据文件名
    tutu_data_filename: str = "tutu_data.json"
    # pixiv图片反代地址 备选 https://i.pixiv.re/ 、 https://i.pixiv.cat/ 、 https://i.loli.best/ 、 pimg.rem.asia 、 https://c.jitsu.top/
    tutu_pixiv_proxy: Optional[str] = None
    # http代理地址，如 http://127.0.0.1:1234
    tutu_http_proxy: Optional[str] = None


class Var:
    # 处理bot
    handle_bot: Optional[Bot] = None
    # 图库接口   图库名：api列表
    gallery_list: Dict[str, List[str]] = {}
    # 本地图库   文件名：图片url列表
    local_imgs: Dict[str, List[str]] = {}
    # 图图白名单群列表
    group_list: Set[int] = set()
    # 请求头
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54",
    }
    # http请求超时
    http_timeout = 10


driver = get_driver()
var = Var()
pc = get_plugin_config(Config)


def read_data():
    """
    读取配置文件
    """
    with open(f"data/{pc.tutu_data_filename}", "r", encoding="utf-8") as r:
        tmp_data = load(r)
        for group_id in tmp_data[0]:
            var.group_list.add(group_id)
        var.gallery_list = tmp_data[1]


def save_data():
    """
    保存配置文件
    """
    with open(f"data/{pc.tutu_data_filename}", "w", encoding="utf-8") as w:
        dump(
            [
                list(var.group_list),
                var.gallery_list,
            ],
            w,
            indent=4,
            ensure_ascii=False,
        )


def load_local_api():
    """
    读取本地图片库
    """
    var.local_imgs.clear()
    for file_name in listdir(pc.tutu_local_api_path):
        with open(pc.tutu_local_api_path + file_name, "r", encoding="utf-8") as r:
            api_list_lines = r.readlines()
        var.local_imgs[file_name] = [line.rstrip() for line in api_list_lines]


@driver.on_startup
async def on_startup():
    """
    启动时执行
    """
    if not path.exists(pc.tutu_local_api_path):
        makedirs(pc.tutu_local_api_path)

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
            # 新连接的bot qq 下标
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
