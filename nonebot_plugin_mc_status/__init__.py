from asyncio import open_connection, wait_for
from asyncio.exceptions import IncompleteReadError, TimeoutError
from json import dump, load, loads
from nonebot import on_regex, on_fullmatch
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent
from nonebot.params import RegexGroup
from re import findall
from pathlib import Path
from nonebot import get_driver
from nonebot.plugin import PluginMetadata
from nonebot.permission import SUPERUSER

__plugin_meta__ = PluginMetadata(
    name="MC服务器查询插件",
    description="查询JAVA服务器的在线信息",
    usage=f"""插件命令如下：
信息  # 字面意思
添加服务器  # 字面意思
删除服务器  # 字面意思
信息数据  # 查看已启用群以及服务器信息
""",
)
file_path = Path(__file__).parent
data_filename = "mc_status_data.json"
group_list = {}


def read_file():
    # with open(f"data/{data_filename}", "r", encoding="utf-8") as r:
    with open(file_path / data_filename, "r", encoding="utf-8") as r:
        tmp_data = load(r)
        for i in tmp_data:
            group_list[int(i)] = tmp_data[i]


def save_file():
    # with open(f"data/{data_filename}", "w", encoding="utf-8") as w:
    with open(file_path / data_filename, "w", encoding="utf-8") as w:
        dump(group_list, w, indent=4, ensure_ascii=False)


driver = get_driver()


@driver.on_startup
async def on_startup():
    try:
        read_file()
    except:
        pass


async def group_check(event: GroupMessageEvent, bot: Bot) -> bool:
    return event.group_id in group_list


xinxi = on_fullmatch("信息", rule=group_check)
add_server = on_regex(r"^添加服务器\s*((\d+)\s+(.*)\s+(.*)?)?", permission=SUPERUSER)
del_server = on_regex(r"^删除服务器\s*((\d+)\s+(.*))?", permission=SUPERUSER)
list_all = on_fullmatch("信息数据", permission=SUPERUSER)


@xinxi.handle()
async def handle_xinxi(event: GroupMessageEvent):
    msg = ""
    count = 0
    group = event.group_id
    for server_name in group_list[group]:
        count += 1
        if count > 1:
            msg += "\n=== 分割线 ===\n"
        msg += await check_mc_status(
            server_name,
            group_list[group][server_name][0],
            group_list[group][server_name][1],
        )
    await xinxi.finish(msg)


@add_server.handle()
async def handle_add_server(matchgroup=RegexGroup()):
    if not matchgroup[0]:
        await add_server.finish(f"添加服务器 [群号] [名称] [服务器地址]")
    else:
        group = int(matchgroup[1])
        name = matchgroup[2]
        addr = matchgroup[3].split(":")
        if len(addr) > 1:
            ip, port = addr[0], int(addr[1])
        else:
            ip, port = addr[0], 25565

    if group not in group_list:
        group_list[group] = {name: [ip, port]}
    else:
        for server_name in group_list[group]:
            if server_name == name:
                await add_server.finish("有同名服务器啦！")
        group_list[group][name] = [ip, port]
    save_file()
    await add_server.finish("添加成功")


@del_server.handle()
async def handle_del_server(matchgroup=RegexGroup()):
    if not matchgroup[0]:
        await del_server.finish(f"删除服务器 [群号] [名称]")
    else:
        group = int(matchgroup[1])
        name = matchgroup[2]

    if group not in group_list:
        await del_server.finish("你是来拉屎的吧？")
    else:
        if name in group_list[group]:
            group_list[group].pop(name)
            if not group_list[group]:
                group_list.pop(group)
            save_file()
            await del_server.finish("删除成功")
        else:
            await del_server.finish("没找到该名称的服务器")


@list_all.handle()
async def handle_list_all():
    msg = ""
    for group_id in group_list:
        msg += f"群{group_id}服务器列表\n"
        for server_name in group_list[group_id]:
            ip, port = group_list[group_id][server_name]
            msg += f"{server_name} {ip}:{port}\n"
        msg += "\n"
    await list_all.finish(f"mc_status数据\n{msg}")


async def check_mc_status(name, host, port):
    try:
        fun_connect = open_connection(host, port)
        reader, writer = await wait_for(fun_connect, timeout=1)
    except (
        TimeoutError,
        IncompleteReadError,
        ConnectionResetError,
        ConnectionRefusedError,
    ) as e:
        msg = f"名称: {name}\n【服务器没开】"
        return msg

    try:
        writer.write(
            b"\x1a\x00\xf8\x05\x13\x6d\x63\x2e\x6e\x69\x6b\x69\x73\x73\x2e\x74\x6f\x70\x00\x46\x4d\x4c\x33\x00"
            + port.to_bytes(2, "big")
            + b"\x01"
        )
        writer.write(b"\x01\x00")
        await writer.drain()
        fun_readdata = reader.readuntil(b"protocol")
        host_data = await wait_for(fun_readdata, timeout=1)
        pos1, pos2 = host_data.find(b"\x7b\x22"), host_data.find(b"\x7d\x7d") - 9
        host_data = loads((host_data[pos1:pos2] + b"}}").decode("utf-8"))
        msg = ""
        version = findall(r"\d+\.\d+(?:\.\d+)?", host_data["version"]["name"])[0]
        msg += f"名称: {name} 【{version}】\n"
        # msg += f"简介: {host_data['description']['text']}\n"
        msg += f"玩家: {host_data['players']['online']}/{host_data['players']['max']}"
        if host_data["players"]["online"]:
            msg += (
                "\n◤ "
                + ", ".join([i["name"] for i in host_data["players"]["sample"]])
                + " ◢"
            )
    except Exception as e:
        msg = f"读取数据时代码错误: {repr(e)}"
    finally:
        writer.write_eof()
        writer.close()
        fun_close = writer.wait_closed()
        await wait_for(fun_close, timeout=2)
    return msg
