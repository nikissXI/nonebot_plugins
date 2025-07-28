from nonebot import on_regex
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11.event import (
    GroupMessageEvent,
    MessageEvent,
    PrivateMessageEvent,
)
from nonebot.params import RegexGroup
from nonebot.plugin import PluginMetadata

from .config import Config, pc, var
from .gtranslate.client import Translator

__plugin_meta__ = PluginMetadata(
    name="简单翻译插件",
    description="免key翻译，使用谷歌翻译，但需要梯子",
    type="application",
    homepage="https://github.com/nikissXI/nonebot_plugins/tree/main/nonebot_plugin_setu_customization",
    supported_adapters={"~onebot.v11"},
    config=Config,
    usage=f"""插件命令如下：
翻译/x译x  # 试试就知道怎么用了
""",
)


async def message_check(event: MessageEvent, bot: Bot) -> bool:
    if isinstance(event, PrivateMessageEvent):
        return True
    elif isinstance(event, GroupMessageEvent):
        return bot == var.handle_bot
    else:
        return False


fanyi = on_regex(r"^(翻译|(.)译(.))\s*([\s\S]*)?", rule=message_check)


@fanyi.handle()
async def handle_fanyi(matchgroup=RegexGroup()):
    in_ = matchgroup[3]
    if not in_:
        await fanyi.finish(
            "翻译/x译x [内容]\n直接翻译是自动识别，x是指定语言\nx支持：中（简中）、繁（繁中）、英、日、韩、法、俄、德"
        )

    dd = {
        "中": "zh-cn",
        "繁": "zh-tw",
        "英": "en",
        "日": "ja",
        "韩": "ko",
        "法": "fr",
        "俄": "ru",
        "德": "de",
    }

    if matchgroup[0] == "翻译":
        src = "auto"
        dest = "zh-cn"
    else:
        try:
            src = dd[matchgroup[1]]
            dest = dd[matchgroup[2]]
        except KeyError:
            await fanyi.finish("不支持该语种")

    try:
        result = (
            await Translator(proxies=pc.easy_translate_http_proxy).translate(
                in_, dest=dest, src=src
            )
        ).text
    except Exception as e:
        result = repr(e)

    await fanyi.finish(result)
