from .config import pc, var
from nonebot.log import logger
from ujson import loads
from asyncio import Future, sleep, Queue, create_task
from ujson import dumps, loads
from uuid import uuid4
from nonebot import get_driver

driver = get_driver()


@driver.on_startup
async def _():
    # 处理队列协程
    task = create_task(req_queue(), name="req_queue")
    var.background_tasks.add(task)
    task.add_done_callback(var.background_tasks.discard)


def body(message: str, conversation_id: str, parent_message_id: str):
    """构造请求参数"""
    req_body = {
        "action": "next",
        "messages": [
            {
                "id": str(uuid4()),
                "author": {"role": "user"},
                "role": "user",
                "content": {"content_type": "text", "parts": [message]},
            }
        ],
        "parent_message_id": parent_message_id,
        "model": pc.talk_with_chatgpt_api_model,
    }
    if conversation_id:
        req_body["conversation_id"] = conversation_id

    return dumps(req_body)


async def handle_req(id: str, req_text: str):
    """请求chatgpt"""
    conversation_id = var.session_data[id][0]
    parent_msg_id = var.session_data[id][1]
    err_msg = ""
    try:
        resp = await var.httpx_client.post(
            pc.talk_with_chatgpt_api_addr,
            content=body(req_text, conversation_id, parent_msg_id),
        )
        # 先存着结果，如果报错了用于判断
        err_msg = resp.text
        # 提取回答
        json_data = loads(resp.text.split("\n\n")[-3][6:])
        var.session_data[id][0] = json_data["conversation_id"]
        var.session_data[id][1] = json_data["message"]["id"]
        result = json_data["message"]["content"]["parts"][0]

    except Exception as e:
        # 会话丢失
        if "Conversation not found" in err_msg:
            var.session_data[id][0] = ""
            var.session_data[id][1] = ""
            return await handle_req(id, req_text)
        # 冲突，等待1秒再尝试
        if "Only one message at a time" in err_msg:
            await sleep(1)
            return await handle_req(id, req_text)
        result = f"出错啦！{repr(e)}\nerr_msg: {err_msg}"

    return result


async def req_queue():
    """请求队列"""
    var.queue = Queue()
    while True:
        # 获取队列元素
        q = await var.queue.get()
        result = await handle_req(q["id"], q["req_text"])
        # 保存结果
        q["result"] = result
        q["future"].set_result(result)
        # 标记完成
        var.queue.task_done()


async def req_chatgpt(id: str, req_text: str) -> str:
    """把请求塞入队列并等结果返回"""
    # typing报错所以加上
    if not var.queue:
        return ""
    # 把事件塞入队列，等待结果返回
    future = Future()
    item = {"id": id, "req_text": req_text, "future": future}
    await var.queue.put(item)
    return await future
