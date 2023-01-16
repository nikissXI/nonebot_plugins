from nonebot import on_regex
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent
from nonebot.adapters.onebot.v11 import MessageSegment as MS
from nonebot.exception import RejectedException
from nonebot.log import logger
from nonebot.params import Arg
from nonebot.plugin import PluginMetadata
from nonebot.typing import T_State
from .config import pc, var, handle_bot
from .data_handle import add_menu, del_menu, text_to_img
from nonebot import get_bot, get_bots, get_driver

__plugin_meta__ = PluginMetadata(
    name="喵喵自记菜谱",
    description="记录生活中的小菜谱",
    usage=f"""插件命令如下：
菜谱  # 字面意思
""",
)


driver = get_driver()

# qq机器人连接时执行
@driver.on_bot_connect
async def on_bot_connect(bot: Bot):
    global handle_bot
    # 是否有写bot qq，如果写了只处理bot qq在列表里的
    if pc.nya_cook_bot_qqnum_list and bot.self_id in pc.nya_cook_bot_qqnum_list:
        # 如果已经有bot连了
        if handle_bot:
            # 当前bot qq 下标
            handle_bot_id_index = pc.nya_cook_bot_qqnum_list.index(handle_bot.self_id)
            # 连过俩的bot qq 下标
            new_bot_id_index = pc.nya_cook_bot_qqnum_list.index(bot.self_id)
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
        if pc.nya_cook_bot_qqnum_list:
            # 获取当前连着的bot列表(需要bot是在bot qq列表里)
            available_bot_id_list = [
                bot_id for bot_id in get_bots() if bot_id in pc.nya_cook_bot_qqnum_list
            ]
            if available_bot_id_list:
                # 打擂台排序？
                new_bot_index = pc.nya_cook_bot_qqnum_list.index(
                    available_bot_id_list[0]
                )
                for bot_id in available_bot_id_list:
                    now_bot_index = pc.nya_cook_bot_qqnum_list.index(bot_id)
                    if now_bot_index < new_bot_index:
                        new_bot_index = now_bot_index
                # 取下标在qq列表里最小的bot qq为新的handle bot
                handle_bot = get_bot(pc.nya_cook_bot_qqnum_list[new_bot_index])
            else:
                handle_bot = None

        # 不写就随便给一个连着的(如果有)
        elif handle_bot:
            try:
                new_bot = get_bot()
                handle_bot = new_bot
            except ValueError:
                handle_bot = None


# 管理员判断
async def rule_check(event: MessageEvent, bot: Bot) -> bool:
    return event.user_id in pc.nya_cook_user_list and bot == handle_bot


caipu = on_regex(r"^菜谱$", permission=rule_check)


@caipu.handle()
async def handle_caipu(state: T_State):
    await caipu.send("欢迎使用喵喵菜谱！进入菜谱交互模式~\n发送“帮助”查看命令说明")
    state["content"] = Message("菜谱")


@caipu.got("content")
async def handle_caipu_got(content: Message = Arg()):
    text = content.extract_plain_text().strip()

    if text == "0":
        await caipu.finish("ByeBye~")

    if text == "帮助":
        await caipu.reject(
            "发送“菜谱”返回所有菜谱列表\n发送对应菜名数字获取做法\n直接发“关键字”搜索菜谱\n增加菜谱发：增加 [菜名] [做法]\n删除菜谱发：删除 [菜谱id]\n发“0”退出交互"
        )

    if text == "菜谱":
        if var.cook_menu_data_dict:
            text = "喵喵菜谱~\n" + "\n".join(
                [
                    f"No.{id}  {var.cook_menu_data_dict[id][0]}"
                    for id in var.cook_menu_data_dict
                ]
            )
        else:
            text = "还没有任何菜谱呢，请先添加菜谱喵~\n增加 [菜名] [做法]"

        await caipu.reject(MS.image(text_to_img(text)))

    if text[:2] == "增加":
        text = text[2:].strip()
        blank_pos = text.strip().find(" ")
        menu_name = text[:blank_pos].strip()
        menu_recipe = text[blank_pos:].strip()
        id = add_menu(menu_name, menu_recipe)
        await caipu.reject(f"增加成功喵~，No.{id}")

    if text[:2] == "删除":
        id = text[2:].strip()
        menu_name = del_menu(id)
        if menu_name:
            await caipu.reject(f"【{menu_name}】删除成功喵~")
        else:
            await caipu.reject("菜谱序号不存在喵~")

    try:
        int(text)
        is_id = True
    except (RejectedException, ValueError):
        is_id = False

    # 获取菜谱
    if is_id:
        id = text
        if id not in var.cook_menu_data_dict:
            await caipu.reject("菜谱序号不存在喵~")

        menu_name, menu_recipe = var.cook_menu_data_dict[id]
        text = f"【{menu_name}】\n*** 做法 ***\n{menu_recipe}"
        await caipu.reject(text)

    # 搜索菜谱
    else:
        keyword = text.strip()
        search_result = "\n".join(
            [
                f"No.{id}  {var.cook_menu_data_dict[id][0]}"
                for id in var.cook_menu_data_dict
                if var.cook_menu_data_dict[id][0].find(keyword) != -1
            ]
        )
        if search_result:
            await caipu.reject(MS.image(text_to_img("喵喵菜谱搜索结果~\n" + search_result)))
        else:
            await caipu.reject(f"没有包含关键字【{keyword}】的菜名喵~\n发送“0”退出交互模式")
