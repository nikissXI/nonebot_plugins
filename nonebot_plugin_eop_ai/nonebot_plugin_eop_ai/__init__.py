from nonebot.plugin import PluginMetadata
from nonebot.log import logger
from .matchers import usage, talk_keyword, talk_tome, talk_p, reset, group_enable


__plugin_meta__ = PluginMetadata(
    name="talk with eop ai",
    description="Nonebot2 一款调用eop api的AI聊天插件",
    type="application",
    homepage="https://github.com/nikissXI/nonebot_plugins/tree/main/nonebot_plugin_eop_ai",
    supported_adapters={"~onebot.v11"},
    usage=usage,
)
logger.success("eop ai插件已加载，" + usage)
