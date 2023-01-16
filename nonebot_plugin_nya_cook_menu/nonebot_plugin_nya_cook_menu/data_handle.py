from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from .config import read_data, save_data, var, pc


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
