from httpx import AsyncClient
from asyncio import run


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

    async def query_song(self, keyword: str, page: str = "1", items: str = "30"):
        """
        根据关键字搜歌
        keyword: 关键字
        page: 页数
        items: 每页返回的数量
        """
        search_url = "http://www.kuwo.cn/api/www/search/searchMusicBykeyWord?"
        search_data = {
            "key": keyword,
            # 页数
            "pn": page,
            # 每页的结果
            "rn": items,
            # "httpsStatus": "1",
            "reqId": self.reqId,
        }
        try:
            resp = await self.session.get(search_url, params=search_data, timeout=5)
            resp_json = resp.json()

            # print(resp_json)
            songs_data = resp_json["data"]["list"]
            resp_total = resp_json["data"]["total"]
            # print(type(resp_total))
            if int(resp_total) <= 0:
                print(f"无结果")
            else:
                print(f"共{resp_total}个结果")
                text = []
                for i in songs_data:
                    text.append(f"{i}\n")
                with open("resp.txt", "w", encoding="utf-8") as w:
                    w.writelines(text)
                print("搜索结果已保存到result.txt")
                text = []
                for i in songs_data:
                    print(type(i))

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
                    print(pic)

                    text.append(f"{rid}\t{song_name}\t{singer}\t{album}\n")

                with open("result.txt", "w", encoding="utf-8") as w:
                    w.writelines(text)
                print("搜索结果已保存到result.txt")

        except Exception as e:
            print(f"{repr(e)}")

    async def get_song_url(self, rid: int):
        """
        获取下载歌曲的地址
        rid: 歌曲rid
        """
        music_url = f"http://www.kuwo.cn/api/v1/www/music/playUrl?mid={rid}&type=convert_url3&httpsStatus=1&reqId={self.reqId}"
        resp = await self.session.get(music_url)
        resp_json = resp.json()
        if resp_json["code"] != 200:
            print("rid不存在")
        else:
            song_url = resp_json["data"]["url"]
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


# 实例化对象
song = Song()


if __name__ == "__main__":
    # mode是1的时候是搜索，其他是下载
    mode = 1
    if mode == 1:
        # 搜歌
        keyword = "sincerely"
        run(song.query_song(keyword))
    else:
        # 下载歌曲，rid在result.txt拿
        rid = 234498357
        run(song.get_song_url(rid))
