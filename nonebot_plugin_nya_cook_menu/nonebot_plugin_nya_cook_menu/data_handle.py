from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from .config import read_data, save_data, var, pc
from nonebot.adapters import Bot
from nonebot import get_bot, get_bots, get_driver


# 文字转图片
def text_to_img(text: str, font_path: str = pc.nya_cook_menu_font_path) -> BytesIO:
    """
    字转图片
    """
    lines = text.splitlines()
    line_count = len(lines)
    # 读取字体
    font = ImageFont.truetype(font_path, 16)
    # 获取字体的行高
    left, top, width, line_height = font.getbbox("a")
    # 增加行距
    line_height += 3
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


def add_menu(menu_name: str, menu_recipe: str) -> int:
    id = 1
    while True:
        if str(id) in var.cook_menu_data_dict:
            id += 1
            continue
        else:
            var.cook_menu_data_dict[str(id)] = (menu_name, menu_recipe)
            save_data()
            return id


def del_menu(id: str) -> str:
    if id in var.cook_menu_data_dict:
        menu_name = var.cook_menu_data_dict[id][0]
        var.cook_menu_data_dict.pop(id)
        save_data()
        read_data()
        return menu_name
    else:
        return ""


handle_bot: None | Bot = None


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
