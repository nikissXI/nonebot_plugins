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
    try:
        pass
    except Exception as e:
        err_msg = str(e)
        logger.error(err_msg)
        return ""

    return ""


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
