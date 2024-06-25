from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from .config import Config
from .matchers import group_enable, reset, talk_keyword, talk_p, talk_tome, usage

__plugin_meta__ = PluginMetadata(
    name="talk with eop ai",
    description="Nonebot2 一款调用eop api的AI聊天插件",
    type="application",
    homepage="https://github.com/nikissXI/nonebot_plugins/tree/main/nonebot_plugin_eop_ai",
    supported_adapters={"~onebot.v11"},
    config=Config,
    usage=usage,
)
logger.success("eop ai插件已加载，" + usage)
