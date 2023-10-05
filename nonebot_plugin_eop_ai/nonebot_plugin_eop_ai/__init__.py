from nonebot.plugin import PluginMetadata
from nonebot.log import logger
from .matchers import talk, talk_p, reset, enable_group
from .config import pc

usage = f"""插件命令如下
{pc.eop_ai_talk_cmd}   # 开始对话，默认群里@机器人也可以
{pc.eop_ai_talk_p_cmd}   # 沉浸式对话（仅限私聊）
{pc.eop_ai_reset_cmd}   # 重置对话（不会重置预设）
{pc.eop_ai_group_enable_cmd}   # 如果关闭所有群启用，则用这个命令启用"""

__plugin_meta__ = PluginMetadata(
    name="talk with eop ai",
    description="Nonebot2 一款调用eop api的AI聊天插件",
    type="application",
    homepage="https://github.com/nikissXI/nonebot_plugins/tree/main/nonebot_plugin_eop_ai",
    supported_adapters={"~onebot.v11"},
    usage=usage,
)
logger.success("eop ai插件已加载，" + usage)
