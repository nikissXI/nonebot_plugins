from asyncio import Lock
from json import dump, load
from os import listdir, makedirs, path
from typing import Dict, List, Optional, Set

from nonebot import get_driver, get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    # 图图命令CD时间（秒）
    tutu_cooldown: int = 3
    # 危险图库，危险图库的图片无法在群聊发送
    tutu_danger_gallery: List[str] = []
    # 本地图片库的路径
    tutu_local_api_path: str = "data/tutu_local_img_lib/"
    # 插件数据文件名
    tutu_data_filename: str = "tutu_data.json"
    # 是否默认全部接口走代理，如果为False，则需要url末尾追加“代理翻转”才会走代理
    tutu_http_proxy_default: bool = True
    # http代理地址，如 http://127.0.0.1:1234
    tutu_http_proxy: Optional[str] = None
    # pixiv图片反代地址 备选 https://i.pixiv.re/ 、 https://i.pixiv.cat/ 、 https://i.loli.best/ 、 pimg.rem.asia 、 https://c.jitsu.top/
    tutu_pixiv_proxy: Optional[str] = None
    # 限定哪个bot响应，填bot的qq号，限定群聊只有这个bot响应，不填则均响应
    tutu_bot_id: Optional[int] = None


class Var:
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
    # 消息响应锁
    msg_lock: Lock = Lock()
    received_msg_id_set: set[int] = set()


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
