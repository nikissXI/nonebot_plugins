from nonebot import on_message, on_fullmatch
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
)
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from .config import pc, var
from .data_handle import req_chatgpt
from nonebot.typing import T_State
from html import unescape
from nonebot.permission import SUPERUSER

talk_cmd = pc.talk_with_chatgpt_talk_cmd
talk_p_cmd = pc.talk_with_chatgpt_talk_p_cmd
reset_cmd = pc.talk_with_chatgpt_reset_cmd
prompt_cmd = pc.talk_with_chatgpt_prompt_cmd
enable_cmd = pc.talk_with_chatgpt_group_enable_cmd

__plugin_meta__ = PluginMetadata(
    name="talk with chatgpt",
    description="一个简单的基于accessToken验证的ChatGPT对话插件",
    usage=f"""插件命令如下
{talk_cmd}  # 开始对话，默认群里@机器人也可以
{reset_cmd}  # 重置对话（不会重置预设）
{prompt_cmd}  # 设置预设（人格），设置后会重置对话
{enable_cmd}  # 如果关闭所有群启用，则用这个命令启用
""",
)


def get_id(event: MessageEvent) -> str:
    """获取会话id"""
    if isinstance(event, GroupMessageEvent):
        if pc.talk_with_chatgpt_group_share:
            id = f"{event.group_id}-share"
        else:
            id = f"{event.group_id}-{event.user_id}"
    elif isinstance(event, PrivateMessageEvent):
        id = str(event.user_id)
    else:
        id = ""
    # 记录id
    if id not in var.session_data:
        var.session_data[id] = ["", "", "默认"]
    return id


async def rule_check(event: MessageEvent, bot: Bot) -> bool:
    """对话响应判断"""
    # bot判断
    if pc.talk_with_chatgpt_bot_qqnum_list != ["all"] and bot != var.handle_bot:
        return False

    # 获取纯文本
    text = event.get_plaintext().strip()

    if isinstance(event, GroupMessageEvent):
        # 判断是否启用
        if (
            pc.talk_with_chatgpt_all_group_enable is False
            and event.group_id not in var.enable_group_list
        ):
            return False

        # 仅艾特但没发内容
        if event.is_tome() and pc.talk_with_chatgpt_talk_at:
            if text:
                return True
            else:
                return False

        return text[: len(talk_cmd)] == talk_cmd

    elif isinstance(event, PrivateMessageEvent):
        # 判断前缀
        return text[: len(talk_cmd)] == talk_cmd

    return False


async def rule_check2(event: MessageEvent, bot: Bot) -> bool:
    """其他命令判断"""
    if not (
        isinstance(event, GroupMessageEvent) or isinstance(event, PrivateMessageEvent)
    ):
        return False

    if pc.talk_with_chatgpt_bot_qqnum_list == ["all"]:
        return True
    else:
        return bot == var.handle_bot


async def rule_check3(event: MessageEvent, bot: Bot) -> bool:
    """预设权限判断"""
    if not (
        isinstance(event, GroupMessageEvent) or isinstance(event, PrivateMessageEvent)
    ):
        return False

    if pc.talk_with_chatgpt_bot_qqnum_list != ["all"] and bot != var.handle_bot:
        return False

    if pc.talk_with_chatgpt_prompt_admin_only and not await SUPERUSER(bot, event):
        return False
    else:
        # 判断是否启用
        if (
            isinstance(event, GroupMessageEvent)
            and pc.talk_with_chatgpt_all_group_enable is False
            and event.group_id not in var.enable_group_list
        ):
            return False

        return True


async def rule_admin(event: GroupMessageEvent, bot: Bot) -> bool:
    if pc.talk_with_chatgpt_bot_qqnum_list != ["all"] and bot != var.handle_bot:
        return False
    if not await SUPERUSER(bot, event):
        return False
    return True


#################
### 响应器
#################
talk = on_message(rule=rule_check)
talk_p = on_fullmatch(talk_p_cmd, rule=rule_check2)
reset = on_fullmatch(reset_cmd, rule=rule_check2)
prompt_set = on_fullmatch(prompt_cmd, permission=rule_check3)
enable_group = on_fullmatch(enable_cmd, rule=rule_admin)


@talk.handle()
async def _(event: MessageEvent):
    # 获取信息
    text = unescape(event.get_plaintext().strip())
    # 把命令前缀截掉
    if text[: len(talk_cmd)] == talk_cmd:
        text = text[len(talk_cmd) :]
    # 无内容
    if not text:
        await talk.finish(
            f"""插件命令如下
{talk_cmd} 【内容】 # 发送问题，群里@机器人接内容也可以
{talk_p_cmd}  # 进入沉浸式对话模式，仅私聊可用
{reset_cmd}  # 清空聊天记录（不影响预设）
{prompt_cmd}  # 设置预设（人格），设置后会清空聊天记录"""
        )
    # 获取用户id
    id = get_id(event)

    # 根据配置是否发出提示
    if pc.talk_with_chatgpt_reply_notice:
        await talk.send("响应中...")

    result = await req_chatgpt(id, text)
    await talk.finish(result, at_sender=True)


@talk_p.got("msg", prompt="进入沉浸式对话模式，发送“退出”结束对话")
async def _(event: PrivateMessageEvent):
    # 获取信息
    text = unescape(event.get_plaintext().strip())
    if text == "退出":
        await talk_p.finish("Bye~")
    # 获取用户id
    id = get_id(event)

    # 根据配置是否发出提示
    if pc.talk_with_chatgpt_reply_notice:
        await talk_p.send("响应中...")

    result = await req_chatgpt(id, text)
    await talk_p.reject(result)


@reset.handle()
async def _(event: MessageEvent):
    # 获取用户id
    id = get_id(event)
    # 尝试删除（需api支持）
    await req_chatgpt(id, "", "delete")
    # 清空会话id
    var.session_data[id][0] = ""
    var.session_data[id][1] = ""
    await reset.send("已清空聊天记录", at_sender=True)


@prompt_set.got(
    "msg",
    prompt=f"发送以下选项执行相应功能\n查看 #查看当前及可用预设\n增加 #新增自定义预设(同名则覆盖原有的)\n删除 #删除自定义预设\n发送非预期命令则退出",
)
async def _(event: MessageEvent, s: T_State):
    # 获取用户id
    id = get_id(event)
    # 获取信息
    text = unescape(event.get_plaintext().strip())
    # 上一次输入的内容
    if "last" not in s:
        s["last"] = ""
    if s["last"]:
        if s["last"] == "增加":
            if text == "开发者模式":
                s["last"] = ""
                await prompt_set.reject(f"预设“开发者模式”不能删除或修改，如要改动请改源码", at_sender=True)
            s["new_prompt"] = text
            s["last"] = "新预设名称"
            await prompt_set.reject(f"请输入预设内容", at_sender=True)

        if s["last"] == "新预设名称":
            prompt_name = s["new_prompt"]
            s["last"] = ""
            var.prompt_list[prompt_name] = text
            await prompt_set.reject(f"已新增预设“{prompt_name}”", at_sender=True)

        if s["last"] == "删除":
            prompt_name = text
            s["last"] = ""
            if prompt_name == "默认":
                await prompt_set.reject(f"预设“默认”不能删除！只能修改", at_sender=True)
            if prompt_name == "开发者模式":
                await prompt_set.reject(f"预设“开发者模式”不能删除或修改，如要改动请改源码", at_sender=True)
            var.prompt_list.pop(prompt_name)
            await prompt_set.reject(f"已删除预设“{prompt_name}”", at_sender=True)

    # 查看预设列表
    if text == "查看":
        out_msg = (
            "当前会话预设："
            + var.session_data[id][2]
            + "\n可用预设："
            + "、".join(var.prompt_list.keys())
            + "\n查看 [预设] #查看预设内容\n选择 [预设] #使用该预设"
        )
        await prompt_set.reject(out_msg, at_sender=True)

    # 查看预设详情
    if text[:2] == "查看":
        prompt_name = text[2:].strip()
        prompt_text = var.prompt_list[prompt_name]
        await prompt_set.reject(f"预设：{prompt_name}\n内容：{prompt_text}", at_sender=True)

    # 选择预设
    if text[:2] == "选择":
        prompt_name = text[2:].strip()
        if not prompt_name:
            await prompt_set.reject("格式：选择 [预设]", at_sender=True)

        if prompt_name not in var.prompt_list.keys():
            await prompt_set.reject(f"不存在预设“{prompt_name}”", at_sender=True)
        # 尝试删除（需api支持）
        await req_chatgpt(id, "", "delete")
        # 清空会话id
        var.session_data[id] = ["", "", prompt_name]
        # 设置预设
        await prompt_set.send("测试预设响应，请稍后...", at_sender=True)
        result = await req_chatgpt(id, var.prompt_list[prompt_name])
        await prompt_set.reject(
            f"已设置预设为“{prompt_name}”并清空聊天记录\n预设响应内容：{result}", at_sender=True
        )

    # 增加预设
    if text == "增加":
        s["last"] = "增加"
        await prompt_set.reject(f"请输入预设名称", at_sender=True)

    # 删除预设
    if text == "删除":
        s["last"] = "删除"
        await prompt_set.reject(f"请输入预设名称", at_sender=True)

    # 退出
    await prompt_set.finish(f"未知命令“{text}”，已退出", at_sender=True)


@enable_group.handle()
async def _(event: GroupMessageEvent):
    if pc.talk_with_chatgpt_all_group_enable is True:
        await enable_group.finish("当前配置是所有群都启用，此命令无效")

    if event.group_id in var.enable_group_list:
        var.enable_group_list.remove(event.group_id)
        await enable_group.finish("chatgpt已禁用")
    else:
        var.enable_group_list.append(event.group_id)
        await enable_group.finish("chatgpt已启用")
