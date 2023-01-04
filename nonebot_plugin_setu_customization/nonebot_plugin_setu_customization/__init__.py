from asyncio import gather, sleep
from datetime import datetime, timedelta
from io import BytesIO
from os import listdir
from random import choice
from urllib.parse import unquote
from httpx import AsyncClient
from httpx_socks import AsyncProxyTransport
from nonebot import on_fullmatch, on_regex
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11 import MessageSegment as MS
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, helpers
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import RegexGroup
from nonebot.plugin import PluginMetadata
from .config import load_local_api, plugin_config, save_data, var
from .data_handle import (
    get_art_img_url,
    get_img_url,
    load_crawler_files,
    send_img_msg,
    to_node_msg,
    url_diy_replace,
    download_img,
)
from .web import app

__plugin_meta__ = PluginMetadata(
    name="图图插件",
    description="如名",
    usage=f"""发 图图 就有图辣
图图帮助 看图图的详细命令格式
图图插件群管理 增删群
图图插件接口管理 增删API接口
图图插件接口测试 测试API接口
开爬 上传指定格式的文件让nb爬
文章爬取 直接发文章url就行
爬取合并 是否将爬取结果合并发送（默认合并）
图片序号 查看之前发送的图片url
图片删除 删除本地库的某张图片
图片测试 测试图片
""",
)

# 群判断
async def group_check(event: GroupMessageEvent, bot: Bot) -> bool:
    return (
        event.group_id in var.group_list and bot.self_id == plugin_config.tutu_bot_qqnum
    )


# 管理员判断
async def admin_check(event: MessageEvent, bot: Bot) -> bool:
    return (
        event.user_id == plugin_config.tutu_admin_qqnum
        and bot.self_id == plugin_config.tutu_bot_qqnum
    )


tutu = on_regex(r"^图图\s*(帮助|\d+)?(\s+[^合并]\S+)?\s*(合并)?$", rule=group_check)
group_manage = on_regex(r"^图图插件群管理\s*((\+|\-)\s*(\d*))?$", rule=admin_check)
api_manage = on_regex(
    r"^图图插件接口管理\s*((\S+)(\s+(\+|\-)?\s+([\s\S]*)?)?)?", rule=admin_check
)
api_test = on_regex(r"^图图插件接口测试\s*(\S+)?", rule=admin_check)
tutu_kaipa = on_regex(r"^开爬\s*(停止|暂停|终止)?", rule=admin_check)
art_paqu = on_regex(
    r"^(文章爬取|https://mp.weixin.qq.com/s\S+|https://www.bilibili.com/read/cv\S+)\s*(\S+)?",
    rule=admin_check,
)
recall_paqu = on_regex(r"^撤销图片\s*(\d+)?", rule=admin_check)
paqu_hebing = on_regex(r"^爬取合并(打开|关闭)?$", rule=admin_check)
paqu_resend = on_fullmatch("爬取重放", rule=admin_check)
img_no = on_regex(r"^图片序号\s*(\d+)?$", rule=admin_check)
img_del = on_regex(r"^图片删除\s*((\S+)\s+(\S+)\s*(\S+)?)?", rule=admin_check)
img_test = on_regex(r"^图片测试\s*(\S+)?$", rule=admin_check)


@tutu.handle(parameterless=[helpers.Cooldown(cooldown=3, prompt="我知道你很急，但你先别急")])
async def handle_tutu(
    event: MessageEvent, matcher: Matcher, bot: Bot, matchgroup=RegexGroup()
):
    if not var.api_list_online:
        await tutu.finish("没有图片api呢")
    # CD
    if isinstance(event, GroupMessageEvent):
        if event.group_id in var.group_cooldown:
            await tutu.finish("之前的都还没发完啊")
    else:
        if event.user_id in var.user_cooldown:
            await tutu.finish("之前的都还没发完啊")

    send_num = matchgroup[0]
    api_type = matchgroup[1]
    if matchgroup[2]:
        merge_send = True
    else:
        merge_send = False

    if not send_num:
        send_num = 1
    elif send_num == "帮助":
        await tutu.finish(
            "图图 [数量] [类型] [合并]\n如以下格式发送（注意空格）：\n图图\n图图 10 合并\n图图 二次元 合并\n图图 3 三次元 合并"
        )
    else:
        send_num = int(send_num)
        if send_num > 10:
            await tutu.finish("太多啦，顶不住！♀")
        else:
            await tutu.send("制作中，请稍后...♀")

    if isinstance(event, GroupMessageEvent):
        if api_type:
            api_type = api_type.strip()
            if api_type not in var.api_list_online:
                await tutu.finish(f"【{api_type}】类型不存在，支持的类型{list(var.api_list_online)}")
            elif api_type == plugin_config.tutu_r18_name:
                await tutu.finish(f"群聊不能用这个类型！")
            else:
                api_type = [api_type]
        else:
            api_type = list(var.api_list_online)
            if plugin_config.tutu_r18_name in api_type:
                api_type.remove(plugin_config.tutu_r18_name)
        var.group_cooldown.add(event.group_id)
    else:
        if api_type:
            api_type = api_type.strip()
            if api_type not in var.api_list_online:
                await tutu.finish(f"【{api_type}】类型不存在，支持的类型{list(var.api_list_online)}")
            else:
                api_type = [api_type]
        else:
            api_type = list(var.api_list_online)
            if plugin_config.tutu_r18_name in api_type:
                api_type.remove(plugin_config.tutu_r18_name)
        var.user_cooldown.add(event.user_id)

    msg_list = []
    if isinstance(event, GroupMessageEvent):
        msg_list.append(to_node_msg(MS.text("消息会在一分钟后撤回，注意时间哦~")))

    task_list = []
    for i in range(send_num):
        api_url = choice(var.api_list_online[choice(api_type)])
        task_list.append(get_img_url(api_url))

    gather_result = await gather(*task_list)

    for success, text, img_num in gather_result:
        if isinstance(event, GroupMessageEvent) or merge_send:
            if not success:
                msg_list.append(to_node_msg(MS.text(text)))
            else:
                ds, result = await download_img(text)
                if ds:
                    msg_list.append(
                        to_node_msg(
                            MS.text(f"No.{img_num}") + MS.image(result, timeout=30)
                        )
                    )
                else:
                    msg_list.append(to_node_msg(MS.text(f"No.{img_num}\n{result}")))
        else:
            if not success:
                msg_list.append(tutu.send(text))
            else:
                msg_list.append(send_img_msg(matcher, img_num, text))

    # 群聊
    if isinstance(event, GroupMessageEvent):
        try:
            message_id = (
                await bot.send_group_forward_msg(
                    group_id=event.group_id, messages=msg_list
                )
            )["message_id"]
        except Exception as e:
            var.group_cooldown.discard(event.group_id)
            await tutu.finish(f"图片（合并消息）发送失败 {repr(e)}")

        var.group_cooldown.discard(event.group_id)
        await sleep(80)
        await bot.delete_msg(message_id=message_id)
        await tutu.finish()

    # 私聊合并
    elif merge_send:
        try:
            await bot.send_private_forward_msg(user_id=event.user_id, messages=msg_list)
        except Exception as e:
            await tutu.send(f"图片（合并消息）发送失败 {repr(e)}")
        finally:
            var.user_cooldown.discard(event.user_id)
            await tutu.finish()

    # 私聊单发
    else:
        await gather(*msg_list)
        var.user_cooldown.discard(event.user_id)
        await tutu.finish("发送完毕~如果还有图没出来可能在路上哦")


@group_manage.handle()
async def handle_group_manage(event: MessageEvent, matchgroup=RegexGroup()):
    if not matchgroup[0]:
        group_list = "\n".join([str(i) for i in var.group_list])
        await group_manage.finish(f"图图插件群管理 +/-[群号]\n已启用的QQ群\n" + group_list)
    else:
        choice = matchgroup[1]
        if not matchgroup[2]:
            if isinstance(event, GroupMessageEvent):
                group = event.group_id
            else:
                await group_manage.finish("缺少群号")
        else:
            group = int(matchgroup[2])

    if choice == "+":
        if group not in var.group_list:
            var.group_list.add(group)
            save_data()
            await group_manage.finish("添加成功")
        else:
            await group_manage.finish("已经添加过了")
    else:
        if group in var.group_list:
            var.group_list.discard(group)
            save_data()
            await group_manage.finish("删除成功")
        else:
            await group_manage.finish("你是来拉屎的吧？")


@api_manage.handle()
async def handle_api_manage(bot: Bot, matchgroup=RegexGroup()):
    if not matchgroup[0]:
        api_list_online_text = "\n".join(
            [
                f"【{api_type}】图片接口 数量：{len(var.api_list_online[api_type])}\n"
                + "\n".join(var.api_list_online[api_type])
                for api_type in var.api_list_online
            ]
        )
        api_list_local_text = "\n".join(
            [
                f"{filename} 数量：{len(var.api_list_local[filename])}"
                for filename in var.api_list_local
            ]
        )
        if not api_list_local_text:
            api_list_local_text = "空"
        if var.api_list_online:
            show_api_type_text = f"{list(var.api_list_online)}/"
        else:
            show_api_type_text = ""
        await api_manage.finish(
            f"图图插件接口管理 {show_api_type_text}新类型/刷新本地 +/- [接口url/本地图库<文件名>]\n{api_list_online_text}\n【本地图片库】\n{api_list_local_text}"
        )
    else:
        api_type: str = matchgroup[1]
        choice: str = matchgroup[3]
        todo_api_url: str = matchgroup[4]

    if api_type == "刷新本地":
        load_local_api()
        api_list_local_text = "\n".join(
            [
                f"{filename} 数量：{len(var.api_list_local[filename])}"
                for filename in var.api_list_local
            ]
        )
        await api_manage.finish(f"已刷新本地图片库\n{api_list_local_text}")
    elif not matchgroup[2]:
        await api_manage.finish("参数缺失或格式错误")

    todo_api_url = todo_api_url.replace("&amp;", "&").replace("\\", "")
    if choice == "-":
        todo_api_url_list = todo_api_url.split()
        for todo_api_url in todo_api_url_list:
            if api_type not in var.api_list_online:
                await api_manage.send(f"不存在【{api_type}】类型api，删除失败")
                continue
            else:
                if todo_api_url.find("本地图库") != -1:
                    filename = todo_api_url[4:]
                    todo_api_url = f"http://127.0.0.1:{plugin_config.port}/img_api?fw=1&fn={filename}"
                if todo_api_url in var.api_list_online[api_type]:
                    var.api_list_online[api_type].remove(todo_api_url)
                    if not var.api_list_online[api_type]:
                        var.api_list_online.pop(api_type)
                        msg = f"【{api_type}】类型已无api，删除该类型"
                    else:
                        msg = f"{todo_api_url}\n已从【{api_type}】类型删除"
                    save_data()
                    await api_manage.send(msg)
                else:
                    await api_manage.send(f"{todo_api_url}\n不存在，删除失败")
        await api_manage.finish("api删除操作完毕")

    elif choice == "+":
        todo_api_url_list = todo_api_url.split()
        for todo_api_url in todo_api_url_list:
            if todo_api_url.find("本地图库") != -1:
                filename = todo_api_url[4:]
                if filename not in var.api_list_local:
                    await api_manage.send(
                        f"不存在名为【{filename}】的本地图库，如未加载请使用“图图插件接口管理 刷新本地”"
                    )
                    continue
                else:
                    todo_api_url = f"http://127.0.0.1:{plugin_config.port}/img_api?fw=1&fn={filename}"

            if api_type in var.api_list_online:
                if todo_api_url not in var.api_list_online[api_type]:
                    var.api_list_online[api_type].append(todo_api_url)
                    msg = f"{todo_api_url}\n添加到【{api_type}】"
                else:
                    await api_manage.send(f"{todo_api_url}\n已经添加过了")
                    continue
            else:
                var.api_list_online[api_type] = [todo_api_url]
                msg = f"新增【{api_type}】类别，为其添加新的api成功"
            save_data()
            await api_manage.send(msg + "\n开始对api测试")

            success, text, ext_msg = await get_img_url(todo_api_url)
            if success:
                msg = f"API: {todo_api_url}\nimg_url: {text}\n{ext_msg}"
                await api_manage.send(msg)
        await api_manage.finish("api添加操作完毕")


@api_test.handle()
async def handle_api_test(matchgroup=RegexGroup()):
    if not matchgroup[0]:
        await api_test.finish(f"图图插件接口测试 [接口url/all]")
    else:
        api_url = matchgroup[0]
        api_url = api_url.replace("&amp;", "&").replace("\\", "")
        if api_url == "all":
            await api_test.send("开始测试，请稍后")
            msg_list = []
            all_api_url = []
            for api_type in var.api_list_online:
                all_api_url += var.api_list_online[api_type]

            task_list = []
            for api_url in all_api_url:
                task_list.append(get_img_url(api_url, 10))
            gather_result = await gather(*task_list)

            for success, text, api_url in gather_result:
                if not success:
                    msg_list.append(f"API: {api_url}\n错误信息: {text}")
                else:
                    msg_list.append(f"API: {api_url}\nimg_url: {text}")
            msg = "\n".join(msg_list)
            await api_test.finish(msg)

        else:
            success, text, ext_msg = await get_img_url(api_url, 1)
            if success:
                msg = f"API: {api_url}\nimg_url: {text}\n{ext_msg}"
                await api_test.finish(msg)


@tutu_kaipa.handle()
async def handle_tutu_kaipa(
    event: PrivateMessageEvent, matcher: Matcher, bot: Bot, matchgroup=RegexGroup()
):
    if var.crawler_task:
        if matchgroup[0]:
            var.crawler_task = False
            await tutu_kaipa.finish("停止中，请稍后")

        now = datetime.now() + timedelta(
            seconds=(var.paqu_cooldown + 0.5)
            * (var.crawler_current_msg[1] - var.crawler_current_msg[2])
        )
        finish_time = f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"
        await tutu_kaipa.finish(
            f"当前任务信息\n文件名：{var.crawler_current_msg[0]}\n爬取进度：{var.crawler_current_msg[2]}/{var.crawler_current_msg[1]}\n已收录图片：{var.crawler_current_msg[3]}张\n入库文件名：{var.crawler_current_msg[4]}\n预计完成时间：{finish_time}\n\n发送 开爬停止 可停止任务"
        )

    if not listdir(plugin_config.tutu_crawler_file_path):
        await tutu_kaipa.finish(f"{plugin_config.tutu_crawler_file_path}里没有任何文件夹")

    while True:
        path_name = listdir(plugin_config.tutu_crawler_file_path)
        if path_name:
            await load_crawler_files(path_name[0], matcher, event, bot)
        else:
            break

    var.crawler_task = False
    var.crawler_current_msg.clear()
    await tutu_kaipa.finish(f"所有爬取任务已完成")


@art_paqu.handle()
async def handle_wx_paqu(
    event: PrivateMessageEvent, matcher: Matcher, bot: Bot, matchgroup=RegexGroup()
):
    # if not matchgroup[0]:
    #     await matcher.finish(f"微信文章爬取 [url] （添加到本地api {plugin_config.tutu_self_cosplay_lib}）")
    # else:
    img_url = matchgroup[0]
    if img_url == "文章爬取":
        await art_paqu.finish(
            "发送微信或B站的文章url\n微信文章 https://mp.weixin.qq.com/s 开头\nB站专栏文章 https://www.bilibili.com/read/cv 开头"
        )
    filename = matchgroup[1]
    if not filename:
        await art_paqu.finish(
            f"请给出本地库名称\n快捷名称：2是{plugin_config.tutu_self_anime_lib}，3是{plugin_config.tutu_self_cosplay_lib}"
        )
    elif filename == "2":
        filename = plugin_config.tutu_self_anime_lib
    elif filename == "3":
        filename = plugin_config.tutu_self_cosplay_lib

    img_url = img_url.replace("&amp;", "&").replace("\\", "")
    await get_art_img_url(img_url, filename, matcher, event, bot)


@recall_paqu.handle()
async def handle_recall_paqu(matchgroup=RegexGroup()):
    if not var.tmp_data:
        await recall_paqu.finish("没有爬取记录呢")

    if not matchgroup[0]:
        await recall_paqu.finish("撤销图片 [图片序号]")
    else:
        img_num = int(matchgroup[0])

    if img_num == 0 or img_num not in var.tmp_data:
        await recall_paqu.finish("没有该序号的图片")
    filename = var.tmp_data[0]
    img_url = var.tmp_data[img_num]
    var.tmp_data.pop(img_num)
    var.api_list_local[filename].remove(img_url)
    with open(
        f"{plugin_config.tutu_local_api_path}/{filename}",
        "w",
        encoding="utf-8",
    ) as w:
        w.writelines([i + "\n" for i in var.api_list_local[filename]])

    await recall_paqu.finish(f"已从{filename}撤销图片url\n{img_url}")


@paqu_hebing.handle()
async def handle_miaobixitong(matchgroup=RegexGroup()):
    if not matchgroup[0]:
        await paqu_hebing.finish("爬取合并打开/关闭")
    else:
        in_mess = matchgroup[0]
    if in_mess == "打开":
        var.merge_send = True
        save_data()
        await paqu_hebing.finish("爬取合并已打开")
    else:
        var.merge_send = False
        save_data()
        await paqu_hebing.finish("爬取合并已关闭")


@paqu_resend.handle()
async def handle_paqu_resend(bot: Bot, event: PrivateMessageEvent):
    if not var.tmp_data:
        await paqu_resend.finish("没有爬取数据呢")

    msg_list = []
    img_url_msg_list = []
    task_list = []
    for img_num, value in var.tmp_data.items():
        if img_num == 0:
            continue

        img_url = value
        if var.merge_send:
            msg_list.append(to_node_msg(MS.text(f"序号：{img_num}  {img_url}")))
            msg_list.append(to_node_msg(MS.image(img_url, timeout=30)))
        else:
            img_url_msg_list.append(f"序号：{img_num}  {img_url}")
            task_list.append(
                paqu_resend.send(
                    MS.text(f"序号：{img_num}") + MS.image(img_url, timeout=30)
                )
            )
    if var.merge_send:
        await paqu_resend.send(f"正在合并消息准备发送")
        await bot.send_private_forward_msg(user_id=event.user_id, messages=msg_list)
    else:
        await paqu_resend.send("\n".join(img_url_msg_list))
        await gather(*task_list)
        await paqu_resend.send(f"图片发送完毕")


@img_no.handle()
async def handle_img_no(matchgroup=RegexGroup()):
    img_num = matchgroup[0]
    if not img_num:
        await img_no.finish(f"图片序号 [序号]")
    else:
        try:
            api_url = unquote(var.sent_img_apiurl_data[int(img_num)])
            img_url = unquote(var.sent_img_imgurl_data[int(img_num)])
        except KeyError:
            await img_no.finish(f"No.{img_num}不存在")
        await img_no.finish(f"No.{img_num}\napi_url：{api_url}\nimg_url：{img_url}")


@img_del.handle()
async def handle_img_del(matchgroup=RegexGroup()):
    if not matchgroup[0]:
        await img_del.finish(
            f"图片删除 [本地库] [url]\n本地库快捷名称：2是{plugin_config.tutu_self_anime_lib}，3是{plugin_config.tutu_self_cosplay_lib}\nurl快捷名称 序号[数字]"
        )
    else:
        api_type = matchgroup[1]
        img_url = matchgroup[2]
        new_api_type = matchgroup[3]

        async def replace_apt_type_text(xx: str):
            if xx == "2":
                return plugin_config.tutu_self_anime_lib
            elif xx == "3":
                return plugin_config.tutu_self_cosplay_lib
            elif xx not in var.api_list_local:
                await img_del.finish(
                    f"不存在本地库{api_type}\n快捷名称：2是{plugin_config.tutu_self_anime_lib}，3是{plugin_config.tutu_self_cosplay_lib}"
                )
            else:
                return xx

        api_type = await replace_apt_type_text(api_type)
        if new_api_type:
            new_api_type = await replace_apt_type_text(new_api_type)

        ext_msg = ""
        if img_url.find("序号") != -1:
            try:
                img_num = int(img_url[2:])
            except ValueError:
                await img_del.finish("序号格式输入有误，如“序号123”")

            if img_num in var.sent_img_imgurl_data:
                img_url = var.sent_img_imgurl_data[img_num]

                if new_api_type and img_url not in var.api_list_local[new_api_type]:
                    var.api_list_local[new_api_type].append(img_url)
                    with open(
                        f"{plugin_config.tutu_local_api_path}/{new_api_type}",
                        "a",
                        encoding="utf-8",
                    ) as a:
                        a.write(img_url + "\n")
                    ext_msg = f"，并将该图片加入{new_api_type}"

            else:
                await img_del.finish("序号url不存在")
        else:
            img_url = matchgroup[2].replace("&amp;", "&").replace("\\", "")

        if img_url in var.api_list_local[api_type]:
            var.api_list_local[api_type].remove(img_url)
            with open(
                f"{plugin_config.tutu_local_api_path}/{api_type}",
                "w",
                encoding="utf-8",
            ) as w:
                w.writelines([i + "\n" for i in var.api_list_local[api_type]])
            await img_del.finish(f"已从{api_type}中删除{ext_msg}")
        else:
            await img_del.finish(f"没找到该url在库中，删除失败")


@img_test.handle()
async def handle_img_test(matchgroup=RegexGroup()):
    img_url = matchgroup[0]
    if not img_url:
        await img_test.finish("图片测试 [url]")
    else:
        img_url = url_diy_replace(img_url)
        if plugin_config.tutu_socks5_proxy:
            socks5_proxy = AsyncProxyTransport.from_url(plugin_config.tutu_socks5_proxy)
        else:
            socks5_proxy = None
        if plugin_config.tutu_http_proxy:
            http_proxy = plugin_config.tutu_http_proxy
        else:
            http_proxy = None
        async with AsyncClient(
            headers=var.headers,
            transport=socks5_proxy,
            proxies=http_proxy,
            timeout=var.http_timeout,
            verify=False,
        ) as c:
            try:
                rr = await c.get(url=img_url)
            except Exception as e:
                msg = f"图片请求API出错：{repr(e)}"
                logger.error(msg)
                await img_test.finish(msg)
        img_bytes = BytesIO(rr.content)
        await img_test.finish(MS.image(img_bytes, timeout=30))
