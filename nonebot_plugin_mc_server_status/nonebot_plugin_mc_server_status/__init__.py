from re import findall
from mcstatus import BedrockServer, JavaServer
from nonebot import on_fullmatch, on_regex, get_driver, get_bot, get_bots
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import MessageSegment as MS
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent
from nonebot.log import logger
from nonebot.params import RegexGroup
from nonebot.plugin import PluginMetadata
from .config import group_list, plugin_config as pc, save_file
from asyncio import gather

__plugin_meta__ = PluginMetadata(
    name="MC服务器查询插件",
    description="如名",
    usage=f"""插件命令如下：
信息  # 字面意思
添加服务器  # 字面意思
删除服务器  # 字面意思
信息数据  # 查看已启用群以及服务器信息
""",
)

handle_bot: None | Bot = None


driver = get_driver()

# qq机器人连接时执行
@driver.on_bot_connect
async def on_bot_connect(bot: Bot):
    global handle_bot
    # 是否有写bot qq，如果写了只处理bot qq在列表里的
    if pc.mc_status_bot_qqnum_list and bot.self_id in pc.mc_status_bot_qqnum_list:
        # 如果已经有bot连了
        if handle_bot:
            # 当前bot qq 下标
            handle_bot_id_index = pc.mc_status_bot_qqnum_list.index(handle_bot.self_id)
            # 连过俩的bot qq 下标
            new_bot_id_index = pc.mc_status_bot_qqnum_list.index(bot.self_id)
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
        if pc.mc_status_bot_qqnum_list:
            # 获取当前连着的bot列表(需要bot是在bot qq列表里)
            available_bot_id_list = [
                bot_id for bot_id in get_bots() if bot_id in pc.mc_status_bot_qqnum_list
            ]
            if available_bot_id_list:
                # 打擂台排序？
                new_bot_index = pc.mc_status_bot_qqnum_list.index(
                    available_bot_id_list[0]
                )
                for bot_id in available_bot_id_list:
                    now_bot_index = pc.mc_status_bot_qqnum_list.index(bot_id)
                    if now_bot_index < new_bot_index:
                        new_bot_index = now_bot_index
                # 取下标在qq列表里最小的bot qq为新的handle bot
                handle_bot = get_bot(pc.mc_status_bot_qqnum_list[new_bot_index])
            else:
                handle_bot = None

        # 不写就随便给一个连着的(如果有)
        elif handle_bot:
            try:
                new_bot = get_bot()
                handle_bot = new_bot
            except ValueError:
                handle_bot = None


async def group_check(event: GroupMessageEvent, bot: Bot) -> bool:
    return event.group_id in group_list and bot == handle_bot


async def admin_check(event: MessageEvent, bot: Bot) -> bool:
    return bot == handle_bot and event.user_id == pc.mc_status_admin_qqnum


xinxi = on_fullmatch("信息", rule=group_check)
add_server = on_regex(r"^添加服务器\s*((\d+)\s+(\S+)\s+(\S+)\s+(\S+))?", rule=admin_check)
del_server = on_regex(r"^删除服务器\s*((\d+)\s+(\S+))?", rule=admin_check)
list_all = on_fullmatch("信息数据", rule=admin_check)


@xinxi.handle()
async def handle_xinxi(event: GroupMessageEvent):
    group = event.group_id
    task_list = []
    for server_name in group_list[group]:
        server_host = group_list[group][server_name][0]
        server_type = group_list[group][server_name][1]
        task_list.append(
            check_mc_status(
                server_name,
                server_host,
                server_type,
            )
        )
    result = await gather(*task_list)
    count = 0
    msg = ""
    for r in result:
        count += 1
        if count > 1:
            msg += "\n=== 分割线 ===\n"
        msg += r
    await xinxi.finish(msg)


@add_server.handle()
async def handle_add_server(matchgroup=RegexGroup()):
    if not matchgroup[0]:
        await add_server.finish(
            f"添加服务器 [群号] [名称] [服务器地址] [类型]\n类型写js或bds，js是Java服务器，bds是基岩服务器\n服务器地址如果知道端口号把端口加上，否则查询速度会慢一点\n添加例子：\nexp1: 添加服务器 114514 哈皮咳嗽 mc.hypixel.net js\nexp2: 添加服务器 114514 某基岩服 mc.bds.net bds\nexp3: 添加服务器 114514 某Java服 mc.java.net:25577 js"
        )
    else:
        group = int(matchgroup[1])
        new_server_name = matchgroup[2]
        server_host = matchgroup[3]
        server_type = matchgroup[4].lower()

    if server_type not in ["js", "bds"]:
        await add_server.finish("类型请填js或bds")

    if group not in group_list:
        group_list[group] = {new_server_name: [server_host, server_type]}
    else:
        for server_name in group_list[group]:
            if new_server_name == server_name:
                await add_server.finish("有同名服务器啦！")
        group_list[group][new_server_name] = [server_host, server_type]
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
        await del_server.finish("这个群没有添加服务器")
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
            server_host, server_type = group_list[group_id][server_name]
            msg += f"{server_name} {server_host} {server_type}\n"
        msg += "\n"
    if not msg:
        msg = "无数据"
    await list_all.finish(f"mc_status数据\n{msg}")


async def check_mc_status(name: str, host: str, server_type: str) -> str:
    try:
        if server_type == "js":
            js = await JavaServer.async_lookup(host, timeout=5)
            status = js.status()
            # if status.description.strip():
            #     print(f"des: {status.description}")
            version_list = findall(r"\d+\.\d+(?:\.[\dxX]+)?", status.version.name)
            if len(version_list) != 1:
                version = f"{version_list[0]}-{version_list[-1]}"
            else:
                version = version_list[0]

            online = f"{status.players.online}/{status.players.max}"
            player_list = []
            if status.players.online:
                if status.players.sample:
                    player_list = [
                        p.name
                        for p in status.players.sample
                        if p.id != "00000000-0000-0000-0000-000000000000"
                    ]
                if player_list:
                    player_list = ", ".join(player_list)
                else:
                    player_list = "没返回玩家列表"
            else:
                player_list = "没人在线"
            latency = round(status.latency)
            # base64图标
            if status.favicon:
                aa, bb = status.favicon.split("base64,")
                icon = MS.image(f"base64://{bb}") + "\n"
            else:
                icon = ""
            msg = f"{icon}名称：{name} 【{version}】\n在线：{online}  延迟：{latency}ms\n◤ {player_list} ◢"

        else:
            if host.find(":") != -1:
                host, port = host.split(":")
            else:
                host, port = host, 19132
            bds = BedrockServer(host="mc.nikiss.top", port=int(port))
            status = await bds.async_status()
            online = f"{status.players_online}/{status.players_max}"
            latency = round(status.latency)
            version = status.version.version
            msg = f"名称：{name} 【{version}】\n在线：{online}  延迟：{latency}ms"
    except Exception as e:
        msg = f"名称：{name} 查询失败！\n错误：{repr(e)}"

    return msg
