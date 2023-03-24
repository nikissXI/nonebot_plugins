from nonebot import on_fullmatch
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    GroupMessageEvent,
)
from nonebot.adapters.onebot.v11 import MessageSegment as MS
from nonebot.params import Arg
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State
from .data_handle import get_query_result, Song, text_to_img

__plugin_meta__ = PluginMetadata(
    name="喵喵点歌",
    description="可以听歌和下载，音乐源是酷我音乐",
    usage=f"""插件命令如下：
点歌  # 字面意思
""",
)

# 实例化对象
song = Song()

diange = on_fullmatch("点歌")


@diange.handle()
async def _(state: T_State):
    await diange.send("欢迎使用喵喵点歌！你已进入交互模式~\n发送“帮助”查看命令说明")
    state["content"] = Message("帮助")
    state["result"] = dict()
    state["keyword"] = ""
    state["now_page"] = 1
    state["total_page"] = 0


@diange.got("content")
async def _(bot: Bot, event: MessageEvent, state: T_State, content: Message = Arg()):
    text = content.extract_plain_text().strip()
    keyword: str = state["keyword"]
    now_page: int = state["now_page"]
    total_page: int = state["total_page"]
    result: dict[int, tuple[int, str, str, str, str]] = state["result"]

    if text == "0" or text[:2] == "退出":
        await diange.finish("ByeBye~")

    if text[:2] == "帮助" or text[:2] == "点歌":
        await diange.reject(
            MS.image(
                text_to_img(
                    "点歌命令教程，【XX】是命令参数，括号只是告诉你这是参数\n搜索 【关键字】\n下 （下一页）\n上 （上一页）\n翻页 【页数】 （跳转到指定页数）\n播放 【歌曲序号】\n下载 【歌曲序号】\n发“0”或“退出”结束交互\n超过2分钟没对话自动退出交互"
                )
            )
        )

    if text[:2] == "搜索" or text[:2] == "翻页" or text == "下" or text == "上":
        new_search = False
        if text[:2] == "搜索":
            keyword = text[2:].strip()
            if not keyword:
                await diange.reject("关键词呢？")
            page = 1
            new_search = True
        elif not keyword:
            await diange.reject("还没有结果喵！")
        elif text[:2] == "翻页":
            page = text[2:].strip()
            if page.isnumeric():
                page = int(page)
            else:
                await diange.reject("请正确输入数字！")

        elif text == "下":
            page = now_page + 1
        # text == "上"
        else:
            page = now_page - 1

        if not new_search and not (1 <= page <= total_page):
            await diange.reject("页数超出范围喵！")

        data = await get_query_result(song, keyword, str(page), state, new_search)
        if isinstance(data, str):
            await diange.reject(data)
        else:
            if new_search:
                if state["keyword"]:
                    await diange.send("之前的搜索结果已清空喵~")
                state["keyword"] = keyword
            await diange.reject(MS.image(data))

    if text[:2] == "播放":
        song_no = text[2:].strip()
        if not result:
            await diange.reject("还没有结果喵！")
        if not song_no.isnumeric():
            await diange.reject("请输入正确的序号喵！")

        song_no = int(song_no)
        if song_no not in result:
            await diange.reject(f"没有序号为【{song_no}】的歌曲")

        rid, song_name, singer, album, pic = result[song_no]
        song_url = await song.get_song_url(rid)
        await diange.reject(
            MS(
                "music",
                {
                    "type": "custom",
                    "subtype": "kuwo",
                    "url": song_url,
                    "voice": song_url,
                    "title": song_name,
                    "content": singer,
                    "image": pic,
                },
            )
        )

    if text[:2] == "下载":
        song_no = text[2:].strip()
        if not result:
            await diange.reject("还没有结果喵！")
        if not song_no.isnumeric():
            await diange.reject("请输入正确的序号喵！")
        song_no = int(song_no)
        if song_no not in result:
            await diange.reject(f"没有序号为【{song_no}】的歌曲")

        rid, song_name, singer, album, pic = result[song_no]
        song_url = await song.get_song_url(rid)

        # 下载文件
        file_name = f"{song_name} - {singer}.mp3"
        await diange.send(f"{file_name}下载中，请稍后喵~")
        try:
            file_path = await bot.download_file(url=song_url)
            file_path = file_path["file"]
        except Exception as e:
            await diange.reject(f"{file_name}下载失败！{e}")

        # 如果是群聊则通过私聊bot发送
        if isinstance(event, GroupMessageEvent):
            try:
                await bot.upload_private_file(
                    user_id=event.user_id,
                    file=file_path,
                    name=f"{song_name} - {singer}.mp3",
                )
            except Exception as e:
                await diange.reject(f"{file_name}上传失败！\n{e}\n直接提供MP3链接\n{song_url}")

            await diange.reject()

        # 如果是私聊直接发送
        else:
            try:
                await bot.upload_private_file(
                    user_id=event.user_id,
                    file=file_path,
                    name=f"{song_name} - {singer}.mp3",
                )
            except Exception as e:
                await diange.reject(f"{file_name}上传失败！\n{e}\n直接提供MP3链接\n{song_url}")

            await diange.reject()

    else:
        await diange.reject("喵？")
