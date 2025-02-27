from random import choice

from nonebot import on_fullmatch, on_regex
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    MessageEvent,
    PrivateMessageEvent,
    helpers,
)
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import RegexGroup
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from .config import Config, load_local_api, pc, save_data, var
from .data_handle import check_api, get_img, send_img

__plugin_meta__ = PluginMetadata(
    name="动态API色图插件",
    description="Nonebot2 可动态管理API的setu(色图)插件",
    type="application",
    homepage="https://github.com/nikissXI/nonebot_plugins/tree/main/nonebot_plugin_setu_customization",
    supported_adapters={"~onebot.v11"},
    config=Config,
    usage="""图图插件帮助
图图 出图，后面可接图库和数量，如“图图10”、“图图二次元”、“图图10二次元”
* 下方是管理员命令
图图插件群管理 增删群
图图插件接口管理 增删API接口
图图插件刷新本地图库 刷新本地图库文件
图图插件接口测试 测试API接口
图图插件图片测试 测试图片
""",
)


# 群判断
async def tutu_permission_check(event: MessageEvent, bot: Bot) -> bool:
    if isinstance(event, PrivateMessageEvent):
        return event.sub_type == "friend"

    if isinstance(event, GroupMessageEvent):
        if pc.tutu_bot_id:
            return (
                event.group_id in var.group_list and int(bot.self_id) == pc.tutu_bot_id
            )

        return event.group_id in var.group_list

    return False


async def admin_permission_check(event: MessageEvent, bot: Bot) -> bool:
    if not SUPERUSER(bot, event):
        return False

    if isinstance(event, PrivateMessageEvent):
        return True

    if isinstance(event, GroupMessageEvent):
        if pc.tutu_bot_id:
            return int(bot.self_id) == pc.tutu_bot_id

        return True

    return False


tutu_help = on_fullmatch("图图插件帮助", rule=tutu_permission_check)
tutu = on_regex(r"^图图(?!插件)\s*(\d+)?\s*(\S+)?", rule=tutu_permission_check)

group_manage = on_regex(
    r"^图图插件群管理\s*((\+|\-)\s*(\d*))?", rule=admin_permission_check
)
api_manage = on_regex(
    r"^图图插件接口管理\s*(\S+)?\s*(?:(\+|\-)\s*(\S*))?", rule=admin_permission_check
)
tutu_flush_local = on_fullmatch("图图插件刷新本地图库", rule=admin_permission_check)
api_test = on_regex(r"^图图插件接口测试\s*(\d+)?\s*(\S+)?", rule=admin_permission_check)
img_test = on_regex(r"^图图插件图片测试\s*(\S+)?", rule=admin_permission_check)


@tutu_help.handle()
async def _(event: MessageEvent):
    await tutu_help.finish("""图图插件帮助
图图 出图，后面可接图库和数量，如“图图10”、“图图二次元”、“图图10二次元”
* 下方是管理员命令
图图插件群管理 增删群
图图插件接口管理 增删API接口
图图插件刷新本地图库 刷新本地图库文件
图图插件接口测试 测试API接口
图图插件图片测试 测试图片""")


@tutu.handle(
    parameterless=[
        helpers.Cooldown(cooldown=pc.tutu_cooldown, prompt="我知道你很急，但你先别急")
    ]
)
async def _(matcher: Matcher, event: MessageEvent, mg=RegexGroup()):
    if not var.gallery_list:
        await tutu.finish("还没有图片api呢")

    img_num = int(mg[0]) if mg[0] else 1
    if img_num > 10:
        await tutu.finish("数量是否太多了？")

    fix_gallery = False
    if gallery := mg[1]:
        if gallery not in var.gallery_list:
            await tutu.finish(
                f"不存在图库【{gallery}】，可用图库如下：\n"
                + "\n".join(list(var.gallery_list))
            )
        fix_gallery = True

    if isinstance(event, GroupMessageEvent) and gallery in pc.tutu_danger_gallery:
        await tutu.finish("危险图库在群聊中不可用")

    await tutu.send("图片下载中。。。")

    gallery_list_filtered = [
        item for item in list(var.gallery_list) if item not in pc.tutu_danger_gallery
    ]

    for i in range(img_num):
        if fix_gallery is False:
            gallery = choice(gallery_list_filtered)

        api_url = choice(var.gallery_list[gallery])
        success, img, debug_info = await get_img(api_url)
        if not success:
            await tutu.send(debug_info)
            continue

        await send_img(matcher, api_url, img)

    if img_num > 1:
        await tutu.send("图片已发送完毕")


@group_manage.handle()
async def _(event: MessageEvent, mg=RegexGroup()):
    if not mg[0]:
        group_list = "\n".join([str(i) for i in var.group_list])
        await group_manage.finish(
            f"图图插件群管理 +/-[群号]\n如果是在群聊中发送不用带群号\n已启用的QQ群\n{group_list if group_list else 'None'}"
        )

    choice = mg[1]
    group_id = mg[2]
    if not group_id:
        if not isinstance(event, GroupMessageEvent):
            await group_manage.finish("缺少群号")

        group = event.group_id
    else:
        group = int(group_id)

    if choice == "+":
        if group in var.group_list:
            await group_manage.finish("已经添加过了")
        var.group_list.add(group)
        save_data()
        await group_manage.finish("添加成功")

    else:
        if group not in var.group_list:
            await group_manage.finish("你是来拉屎的吧？")
        var.group_list.discard(group)
        save_data()
        await group_manage.finish("删除成功")


@api_manage.handle()
async def _(matcher: Matcher, mg=RegexGroup()):
    # 没参数，列出帮助菜单
    if not mg[0]:
        # 拼接在线接口信息
        online_gallery_info = "\n".join(
            [
                f"【{gallery}】在线图片接口 数量：{len(var.gallery_list[gallery])}\n"
                + "\n".join(var.gallery_list[gallery])
                for gallery in var.gallery_list
            ]
        )
        if not online_gallery_info:
            online_gallery_info = "空"

        # 拼接本地图库信息
        local_gallery_info = "\n".join(
            [
                f"{filename} 数量：{len(var.local_imgs[filename])}"
                for filename in var.local_imgs
            ]
        )
        if not local_gallery_info:
            local_gallery_info = "空"

        await api_manage.finish(
            f"图图插件接口管理 [图库名] [+/-] [接口url/本地图库<文件名>]\n给二次元图库添加接口示例：“图图插件接口管理 二次元 +https://api.test.org”\n给cosplay图库添加本地图库示例：“图图插件接口管理 cosplay +本地图库filename”\n{online_gallery_info}\n【本地图库如下】\n{local_gallery_info}"
        )

    gallery: str = mg[0]

    if not mg[1]:
        if gallery == "本地图库":
            # 拼接本地图库信息
            local_gallery_info = "\n".join(
                [
                    f"{filename} 数量：{len(var.local_imgs[filename])}"
                    for filename in var.local_imgs
                ]
            )
            if not local_gallery_info:
                local_gallery_info = "空"

            await api_manage.finish(
                f"图图插件接口管理 本地图库 [+/-] [本地图库<文件名>]\n【本地图库如下】\n{local_gallery_info}"
            )

        if gallery not in var.gallery_list:
            await api_manage.finish(f"不存在图库【{gallery}】")

        await api_manage.finish(
            f"图图插件接口管理 {gallery} [+/-] [接口url]\n【{gallery}】图片接口 数量{len(var.gallery_list[gallery])}\n"
            + "\n".join(var.gallery_list[gallery])
        )

    choice: str = mg[1]
    api_url: str = mg[2].replace("&amp;", "&").replace("\\", "")

    # 增加
    if choice == "+":
        # 本地图库操作
        if "本地图库" in api_url:
            filename = api_url[4:].replace("代理翻转", "")
            if filename not in var.local_imgs:
                await api_manage.finish(
                    f"本地图库中不存在【{filename}】，如未加载请发送“图图插件刷新本地图库”"
                )

        # 判断类型是否存在
        if gallery in var.gallery_list:
            if api_url in var.gallery_list[gallery]:
                await api_manage.finish(f"【{gallery}】已存在 {api_url}")

            var.gallery_list[gallery].append(api_url)
            msg = f"【{gallery}】新增 {api_url}"
        else:
            var.gallery_list[gallery] = [api_url]
            msg = f"新增图库【{gallery}】\n【{gallery}】新增 {api_url}"

        save_data()
        await api_manage.send(msg + "\n开始测试接口")
        await check_api(matcher, api_url)

    # 删除
    else:
        if gallery not in var.gallery_list:
            await api_manage.finish(f"图库【{gallery}】不存在")

        if api_url not in var.gallery_list[gallery]:
            await api_manage.finish(f"图库【{gallery}】不存在接口 {api_url}")

        var.gallery_list[gallery].remove(api_url)
        if not var.gallery_list[gallery]:
            var.gallery_list.pop(gallery)
            msg = f"图库【{gallery}】中已无接口，图库已被删除"
        else:
            msg = f"图库【{gallery}】删除接口 {api_url}"

        save_data()
        await api_manage.finish(msg)


@tutu_flush_local.handle()
async def _():
    load_local_api()
    api_list_local_text = "\n".join(
        [
            f"{filename} 数量：{len(var.local_imgs[filename])}"
            for filename in var.local_imgs
        ]
    )
    await tutu_flush_local.finish(f"已刷新本地图片库\n{api_list_local_text}")


@api_test.handle()
async def _(matcher: Matcher, mg=RegexGroup()):
    if not mg[0]:
        await api_test.finish(
            "图图插件接口测试 [数量（可选且单个接口测试的时候才有用）] [接口url/本地图库<文件名>/all]"
        )

    img_num = int(mg[0]) if mg[0] else 1
    api_url = mg[1].replace("&amp;", "&").replace("\\", "")
    await api_test.send("测试中，请稍后")

    # 单个接口测试
    if api_url != "all":
        for i in range(img_num):
            await check_api(matcher, api_url, i)
        if img_num > 1:
            await api_test.finish("测试图片发送完毕")
        await api_test.finish()

    # 所有接口测试
    for api_type in var.gallery_list:
        for api_url in var.gallery_list[api_type]:
            await check_api(matcher, api_url)

    await api_test.finish("全部测试完毕")


@img_test.handle()
async def _(matcher: Matcher, mg=RegexGroup()):
    img_url = mg[0]
    if not img_url:
        await img_test.finish("图图插件图片测试 [url]\n支持url末尾追加“代理翻转”")

    await img_test.send("图片下载中")

    await send_img(matcher, img_url, img_url.replace("代理翻转", ""))
