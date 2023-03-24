from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from .config import pc
from httpx import AsyncClient
from typing import Tuple, Dict, Union


# 文字转图片
def text_to_img(text: str, font_path: str = pc.nya_music_menu_font_path) -> BytesIO:
    """
    字转图片
    """
    lines = text.splitlines()
    line_count = len(lines)
    # 读取字体
    font = ImageFont.truetype(font_path, pc.nya_music_menu_font_size)
    # 获取字体的行高
    left, top, width, line_height = font.getbbox("a")
    # 增加行距
    line_height += 6
    # 获取画布需要的高度
    height = line_height * line_count + 20
    # 获取画布需要的宽度
    width = int(max([font.getlength(line) for line in lines])) + 25
    # 字体颜色
    black_color = (0, 0, 0)
    # 生成画布
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    # 按行开画，c是计算写到第几行
    c = 0
    for line in lines:
        draw.text((10, 6 + line_height * c), line, font=font, fill=black_color)
        c += 1
    img_bytes = BytesIO()
    image.save(img_bytes, format="jpeg")
    return img_bytes


class Song:
    def __init__(self) -> None:
        self.session = AsyncClient()
        self.session.headers.update(
            {
                "accept": "application/json, text/plain, */*",
                "accept-encoding": "gzip, deflate",
                "accept-language": "zh - CN, zh;q = 0.9",
                "cache-control": "no - cache",
                "Connection": "keep-alive",
                "csrf": "HH3GHIQ0RYM",
                "Referer": "http://www.kuwo.cn/search/list?key=%E5%91%A8%E6%9D%B0%E4%BC%A6",
                "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/99.0.4844.51 Safari/537.36",
                "Cookie": "_ga=GA1.2.218753071.1648798611; _gid=GA1.2.144187149.1648798611; _gat=1; "
                "Hm_lvt_cdb524f42f0ce19b169a8071123a4797=1648798611; "
                "Hm_lpvt_cdb524f42f0ce19b169a8071123a4797=1648798611; kw_token=HH3GHIQ0RYM",
            }
        )
        self.reqId = "858597c1-b18e-11ec-83e4-9d53d2ff08ff"
        self.page_items = pc.nya_music_page_items

    async def query_song(
        self, keyword: str, page: str = "1"
    ) -> Union[Tuple[int, Dict[int, Tuple[int, str, str, str, str]]], Tuple[str, str]]:
        """
        根据关键字搜歌
        keyword: 关键字
        page: 页数
        """
        search_url = "http://www.kuwo.cn/api/www/search/searchMusicBykeyWord?"
        search_data = {
            "key": keyword,
            # 页数
            "pn": page,
            # 每页的结果
            "rn": self.page_items,
            # "httpsStatus": "1",
            "reqId": self.reqId,
        }
        try:
            resp = await self.session.get(search_url, params=search_data, timeout=5)
            resp_json = resp.json()
            # 歌曲列表
            songs_data = resp_json["data"]["list"]
            # 歌曲总数
            resp_total = resp_json["data"]["total"]
            # 无结果
            if int(resp_total) <= 0:
                return "", ""

            result_dict: Dict[int, Tuple[int, str, str, str, str]] = dict()
            num = (int(page) - 1) * self.page_items
            for i in songs_data:
                num += 1
                # 歌手
                singer = i["artist"]
                # 歌名
                song_name = i["name"]
                # 专辑
                album = i["album"]
                # print(f"{song_name}\n\t{singer}\t{album}\n")

                # rid，下载用的
                rid = i["rid"]
                # pic，歌曲图片
                pic = i["pic"] if "pic" in i else ""
                result_dict[num] = (rid, song_name, singer, album, pic)

            return resp_total, result_dict

        except Exception as e:
            return "", repr(e)

    async def get_song_url(self, rid: int) -> str:
        """
        获取下载歌曲的地址
        rid: 歌曲rid
        """
        music_url = f"http://www.kuwo.cn/api/v1/www/music/playUrl?mid={rid}&type=convert_url3&httpsStatus=1&reqId={self.reqId}"
        resp = await self.session.get(music_url)
        resp_json = resp.json()
        if resp_json["code"] != 200:
            return "rid不存在"

        song_url = resp_json["data"]["url"]
        return song_url

        print(f"歌曲下载url：{song_url}")
        # await self.download_song(song_url)

    async def download_song(self, url: str):
        """
        下载歌曲
        url: 歌曲url
        """
        print("正在下载")
        resp = await self.session.get(url)
        with open("song.mp3", "wb") as wb:
            wb.write(resp.content)
        print(f"下载完成，文件名 song.mp3")


async def get_query_result(
    song: Song, keyword: str, page: str, state: Dict, new_search
) -> Union[str, BytesIO]:
    result_count, result = await song.query_song(keyword, page)
    if isinstance(result, str):
        if not result:
            return f"【{keyword}】没有结果"
        else:
            return f"出错！{result}"
    else:
        # 总结果数
        result_count = int(result_count)
        # 计算总页数
        total_page = (
            result_count // song.page_items
            if result_count % song.page_items == 0
            else result_count // song.page_items + 1
        )
        state["now_page"] = int(page)
        state["total_page"] = total_page
        # 更新结果
        if new_search:
            state["result"].clear()
        state["result"].update(result)
        text = f"共{result_count}个结果\n\n"
        for k, v in result.items():
            rid, song_name, singer, album, pic = v
            text += f"No.{k} >> {song_name} - {singer}\n"
        text += f"\n页数{page}/{total_page}"
        return text_to_img(text)
