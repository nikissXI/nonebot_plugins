from .config import pc, var
from nonebot.log import logger
from asyncio import Future, Queue, create_task
from nonebot import get_driver
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from random import choice
from string import ascii_letters, digits

# from traceback import format_exc

driver = get_driver()


@driver.on_startup
async def _():
    """处理队列协程"""
    task = create_task(req_queue(), name="req_queue")
    var.background_tasks.add(task)
    task.add_done_callback(var.background_tasks.discard)


def generate_random_string():
    """生成随机字符串"""
    letters = ascii_letters + digits
    return "".join(choice(letters) for i in range(20))


async def req_queue():
    """请求队列"""
    var.queue = Queue()
    while True:
        # 获取队列元素
        q = await var.queue.get()
        result = await handle_req(q["id"], q["req_text"], q["op"])
        # 保存结果
        q["result"] = result
        q["future"].set_result(result)
        # 标记完成
        var.queue.task_done()


async def handle_req(id: str, req_text: str, op: str) -> str:
    """请求chatgpt"""
    if var.poe is None:
        return "poe ai账号未登录"

    try:
        # 防止预设被删了
        if var.session_data[id][1] not in var.prompt_list:
            var.session_data[id][1] = "默认"

        # 如果会话ID为空则新建
        if not var.session_data[id][0]:
            handle = generate_random_string()
            var.session_data[id][0] = handle
            await var.poe.create_bot(
                handle=handle,
                prompt=var.prompt_list[var.session_data[id][1]],
                suggested_replies=False,
            )

        if op == "reset":
            await var.poe.delete_bot_conversation(
                url_botname=var.session_data[id][0], del_all=True
            )
            result = ""

        elif op == "prompt":
            await var.poe.edit_bot(
                url_botname=var.session_data[id][0],
                prompt=var.prompt_list[var.session_data[id][1]],
            )
            result = ""

        else:
            # 流输出
            result = ""
            async for message in var.poe.ask_stream(
                url_botname=var.session_data[id][0],
                question=req_text,
                suggest_able=False,
            ):
                # print(message, end="")
                result += message

    except Exception as e:
        err_msg = str(e)
        logger.error(err_msg)
        # 如果不存在则创建
        if (
            "The bot doesn't exist or isn't accessible" in err_msg
            or "Failed to create a bot with error: handle_already_taken" in err_msg
            or "Failed to get bot chat_data from https://poe.com/_next/data/" in err_msg
        ):
            # 重置handle，重新请求
            var.session_data[id][0] = ""
            return await handle_req(id, req_text, op)

        elif (
            "Failed to extract 'viewer' or 'user_id' from 'next_data'." in err_msg
            or "Failed to get basedata from home." in err_msg
        ):
            var.poe = None
            result = "登陆凭证无效"
        else:
            result = f"请求出错：{err_msg}"

    return result


async def put_in_req_queue(id: str, req_text: str, op: str = "talk") -> str:
    """把请求塞入队列并等结果返回"""
    # typing报错所以加上
    if not var.queue:
        return ""

    # 把事件塞入队列，等待结果返回
    future = Future()
    item = {"id": id, "req_text": req_text, "op": op, "future": future}
    await var.queue.put(item)
    # 返回结果
    resp_text: str = await future

    return resp_text


# 文字转图片
def text_to_img(text: str, font_path: str = pc.talk_with_poe_ai_font_path) -> BytesIO:
    """
    字转图片
    """
    lines = text.splitlines()
    line_count = len(lines)
    # 读取字体
    font = ImageFont.truetype(font_path, pc.talk_with_poe_ai_font_size)
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
