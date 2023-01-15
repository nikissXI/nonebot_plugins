from httpx import AsyncClient
from nonebot import get_bot, get_bots, get_driver, on_regex
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11.event import (
    GroupMessageEvent,
    MessageEvent,
    PrivateMessageEvent,
)
from nonebot.params import RegexGroup
from nonebot.plugin import PluginMetadata
from .config import plugin_config as pc

__plugin_meta__ = PluginMetadata(
    name="简单翻译插件",
    description="免key翻译，使用谷歌翻译",
    usage=f"""插件命令如下：
翻译/x译x  # 试试就知道怎么用了
""",
)

handle_bot: None | Bot = None


driver = get_driver()

# qq机器人连接时执行
@driver.on_bot_connect
async def on_bot_connect(bot: Bot):
    global handle_bot
    # 是否有写bot qq，如果写了只处理bot qq在列表里的
    if (
        pc.easy_translate_bot_qqnum_list
        and bot.self_id in pc.easy_translate_bot_qqnum_list
    ):
        # 如果已经有bot连了
        if handle_bot:
            # 当前bot qq 下标
            handle_bot_id_index = pc.easy_translate_bot_qqnum_list.index(
                handle_bot.self_id
            )
            # 连过俩的bot qq 下标
            new_bot_id_index = pc.easy_translate_bot_qqnum_list.index(bot.self_id)
            # 判断优先级，下标越低优先级越高
            if new_bot_id_index < handle_bot_id_index:
                handle_bot = bot

        # 没bot连就直接给
        else:
            handle_bot = bot

    # 不写就给第一个连的
    elif not handle_bot:
        handle_bot = bot


# qq机器人断开时执行
@driver.on_bot_disconnect
async def on_bot_disconnect(bot: Bot):
    global handle_bot
    # 判断掉线的是否为handle bot
    if bot == handle_bot:
        # 如果有写bot qq列表
        if pc.easy_translate_bot_qqnum_list:
            # 获取当前连着的bot列表(需要bot是在bot qq列表里)
            available_bot_id_list = [
                bot_id
                for bot_id in get_bots()
                if bot_id in pc.easy_translate_bot_qqnum_list
            ]
            if available_bot_id_list:
                # 打擂台排序？
                new_bot_index = pc.easy_translate_bot_qqnum_list.index(
                    available_bot_id_list[0]
                )
                for bot_id in available_bot_id_list:
                    now_bot_index = pc.easy_translate_bot_qqnum_list.index(bot_id)
                    if now_bot_index < new_bot_index:
                        new_bot_index = now_bot_index
                # 取下标在qq列表里最小的bot qq为新的handle bot
                handle_bot = get_bot(pc.easy_translate_bot_qqnum_list[new_bot_index])
            else:
                handle_bot = None

        # 不写就随便给一个连着的(如果有)
        elif handle_bot:
            try:
                new_bot = get_bot()
                handle_bot = new_bot
            except ValueError:
                handle_bot = None


async def message_check(event: MessageEvent, bot: Bot) -> bool:
    if isinstance(event, PrivateMessageEvent):
        return True
    elif isinstance(event, GroupMessageEvent):
        return bot == handle_bot
    else:
        return False


fanyi = on_regex(r"^(翻译|(.)译(.))\s*([\s\S]*)?", rule=message_check)


@fanyi.handle()
async def handle_fanyi(matchgroup=RegexGroup()):
    in_ = matchgroup[3]
    if not in_:
        await fanyi.finish("翻译/x译x [内容]\n直接翻译是自动识别，x是指定语言\nx支持：中（简中）、繁（繁中）、英、日、韩、法、俄、德")

    dd = {
        "中": "zh-CN",
        "繁": "zh-TW",
        "英": "en",
        "日": "ja",
        "韩": "ko",
        "法": "fr",
        "俄": "ru",
        "德": "de",
    }

    if matchgroup[0] == "翻译":
        from_ = "auto"
        to_ = "auto"
    else:
        try:
            from_ = dd[matchgroup[1]]
            to_ = dd[matchgroup[2]]
        except KeyError:
            await fanyi.finish("不支持该语种")

    data = {"data": [in_, from_, to_]}
    async with AsyncClient(verify=False, follow_redirects=True) as c:
        resp = await c.post(
            "https://hf.space/embed/mikeee/gradio-gtr/+/api/predict", json=data
        )
        if resp.status_code != 200:
            await fanyi.finish(f"翻译接口调用失败\n错误代码{resp.status_code},{resp.text}")

        result = resp.json()
        result = result["data"][0]

    await fanyi.finish(result)

    # 有道 免key翻译
    # params = {"q": in_mess, "from": ff, "to": tt}
    # async with AsyncClient(
    #     verify=False,
    # ) as client:
    #     res = await client.get(f"https://aidemo.youdao.com/trans", params=params)
