from asyncio import gather
from pathlib import Path
from random import choice
from nonebot import get_asgi
from nonebot.log import logger
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from .config import plugin_config, soutu_options, var
from .data_handle import (
    fn_cache_sent_img,
    get_img_url,
    get_soutu_result,
    pixiv_reverse_proxy,
    url_diy_replace,
)

app = get_asgi()
app.mount(
    "/static", StaticFiles(directory=f"{Path(__file__).parent}/html"), name="static"
)
templates = Jinja2Templates(directory=f"{Path(__file__).parent}/html")


@app.get("/img_api")
async def img_api(
    request: Request,
    fn: str | None = None,
    mode: str = "随机",
    fw: int = 0,
    c: int = 1,
    api: str | None = None,
):
    img_url_list = []
    api_url_list = []
    task_list = []
    if fw:
        c = 1

    if fn:
        file_name = fn
        if file_name not in var.api_list_local:
            msg = "可用fn参数，点击可直接跳转<br />"
            if var.api_list_local:
                for ff in var.api_list_local:
                    msg += f'<a href="{plugin_config.tutu_site_url}/img_api?fn={ff}&c={c}">{ff} 数量: {len(var.api_list_local[ff])}</a><br />'
            else:
                msg += "无可用"
            return templates.TemplateResponse(
                "show_info.html",
                {
                    "request": request,
                    "style": f"{plugin_config.tutu_site_url}/static/style.css",
                    "msg": msg,
                },
            )
        else:
            # if not fw and file_name.find("wx_") != -1:
            #     return "不支持该类型，因为微信的图有防盗链，可以用重定向浏览，加参数fw=1"
            # else:
            mode = f"个人库{fn}"
            for i in range(c):
                img_url = choice(var.api_list_local[file_name])
                img_num = fn_cache_sent_img(file_name, img_url)
                img_url_list.append((True, img_url, f"fn{img_num}"))

    else:
        if api:
            for i in range(c):
                api_url_list.append(api)
        elif not var.api_list_online:
            return templates.TemplateResponse(
                "show_info.html",
                {
                    "request": request,
                    "style": f"{plugin_config.tutu_site_url}/static/style.css",
                    "msg": "没有加入任何API哦，无图图",
                },
            )
        elif mode == "随机":
            for i in range(c):
                img_type = choice(
                    [
                        img_type_i
                        for img_type_i in var.api_list_online
                        if img_type_i != plugin_config.tutu_r18_name
                    ]
                )
                api_url_list.append(
                    choice(
                        [
                            api_url_i
                            for api_url_i in var.api_list_online[img_type]
                            # if api_url_i.find("wx_") == -1
                        ]
                    )
                )
        elif mode in var.api_list_online:
            for i in range(c):
                api_url_list.append(
                    choice(
                        [
                            api_url_i
                            for api_url_i in var.api_list_online[mode]
                            # if api_url_i.find("wx_") == -1
                        ]
                    )
                )
        else:
            return templates.TemplateResponse(
                "show_info.html",
                {
                    "request": request,
                    "style": f"{plugin_config.tutu_site_url}/static/style.css",
                    "msg": "没有这个类型的图片鸭！",
                },
            )

        for api_url in api_url_list:
            task_list.append(get_img_url(api_url, cache_data=True))

        img_url_list = await gather(*task_list)

    if fw:
        return RedirectResponse(url=img_url_list[0][1])
    else:
        if fn:
            img_api_url = f"{plugin_config.tutu_site_url}/img_api?fn={fn}&c={c}"
        elif api:
            img_api_url = f"{plugin_config.tutu_site_url}/img_api?api={api}&c={c}"
        else:
            img_api_url = f"{plugin_config.tutu_site_url}/img_api?mode={mode}&c={c}"
        type_urls = ""
        img_list = ""
        for m in var.api_list_online:
            type_urls += f'<a href="{plugin_config.tutu_site_url}/img_api?mode={m}&c={c}">{"." if m == plugin_config.tutu_r18_name else m}</a> &emsp13;'
        for success, img_url, img_num in img_url_list:
            if success:
                img_url = url_diy_replace(img_url)
                #  onerror="this.src=\'{img_url}\'"
                img_list += f'<span>No.{img_num}</span><br /><p><img alt="点我重新加载试试" src="{img_url}" onclick="this.src=this.src+\'?\'" loading="lazy"></p><br />'
            else:
                img_list += (
                    f"<span>No.{img_num}</span><br /><span>{img_url}</span><br />"
                )
        return templates.TemplateResponse(
            "tutu.html",
            {
                "request": request,
                "style": f"{plugin_config.tutu_site_url}/static/style.css",
                "img_type": mode,
                "img_num": c,
                "img_api_url_num": img_api_url[: img_api_url.find("&c=")],
                "img_api_url": img_api_url,
                "img_list": img_list,
                "type_urls": type_urls,
                "img_api_url_fn": f"{plugin_config.tutu_site_url}/img_api?fn=?&c={c}",
                "img_api_url_random": f"{plugin_config.tutu_site_url}/img_api?mode=随机&c={c}",
            },
        )


@app.get("/soutu")
async def soutu(
    request: Request,
):
    return templates.TemplateResponse(
        "soutu.html",
        {
            "request": request,
            "style": f"{plugin_config.tutu_site_url}/static/style.css",
        },
    )


@app.get("/sr")
async def search_result(
    request: Request,
    s: int | None = None,
    r: int | None = None,
    query_type: str = "",
    word: str = "",
    mode: str = "",
    order: str = "",
    date: str = "",
    id: int = 0,
    page: int = 1,
):
    if (not s and not r) or (s and r):
        return templates.TemplateResponse(
            "show_info.html",
            {
                "request": request,
                "style": f"{plugin_config.tutu_site_url}/static/style.css",
                "msg": "？",
            },
        )
    elif not r and s not in var.soutu_data:
        return templates.TemplateResponse(
            "show_info.html",
            {
                "request": request,
                "style": f"{plugin_config.tutu_site_url}/static/style.css",
                "msg": "失效链接",
            },
        )

    # 第一次访问（直接拿数据
    if s:
        # 插画id：{title插画名称 uname画师名称 uid画师id url_list插画数据}
        out_text = ""
        query_type = var.soutu_data[s][0]["type"]
        page = var.soutu_data[s][0]["page"]
        params = {query_type: var.soutu_data[s][0]}
        result_list = var.soutu_data[s][1]
        for pid in result_list:
            data = result_list[pid]
            out_text += f"<span>插画 {data['title']}&emsp13;id {pid}</span><br/><span>画师 {data['uname']}&emsp13;id {data['uid']}</span><br/>"
            for img_url in data["url_list"]:
                out_text += f'<p><a href="{pixiv_reverse_proxy(img_url, resize=False)}">点击查看原图</a><br/><img alt="点我重新加载试试" src="{pixiv_reverse_proxy(img_url)}" onclick="this.src=this.src+\'?\'" loading="lazy"></p><br/>'
    # 翻页
    else:
        params = {
            "search": {
                "type": "search",
                "word": word,
                "mode": mode,
                "order": order,
                "page": page,
            },
            "rank": {
                "type": "rank",
                "mode": mode,
                "date": date,
                "page": page,
            },
            "member_illust": {
                "type": "member_illust",
                "id": id,
                "page": page,
            },
            "illust": {
                "type": "illust",
                "id": id,
                "page": page,
            },
            "related": {
                "type": "related",
                "id": id,
                "page": page,
            },
        }
        # http://nya.nikiss.top/sr?r=1&query_type=search&word=%E5%8E%9F%E7%A5%9E%20-R-18&mode=partial_match_for_tags&order=popular_desc&page=1
        out_text = ""
        result_list = await get_soutu_result("roll", in_params=params[query_type])
        if isinstance(result_list, dict):
            if result_list:
                for pid in result_list:
                    data = result_list[pid]
                    out_text += f"<span>插画 {data['title']}&emsp13;id {pid}</span><br/><span>画师 {data['uname']}&emsp13;id {data['uid']}</span><br/>"
                    for img_url in data["url_list"]:
                        out_text += f'<p><a href="{pixiv_reverse_proxy(img_url, resize=False)}">点击查看原图</a><br/><img alt="点我重新加载试试" src="{pixiv_reverse_proxy(img_url)}" onclick="this.src=this.src+\'?\'" loading="lazy"></p><br/>'
            else:
                out_text = "<h1>空空的</h1>"
        else:
            out_text = f"error!\n{result_list}"

    if query_type == "search":
        title = "搜索：" + params[query_type]["word"].replace(
            "-R-18", '<span style="text-decoration:line-through">R18</span>'
        )
    elif query_type == "rank":
        title = f"{soutu_options['_rank'][params[query_type]['mode']]} {params[query_type]['date'] if params[query_type]['date'] else ''}"
    elif query_type == "illust":
        title = f"作品id{params[query_type]['id']}详情"
    elif query_type == "member_illust":
        title = f"画师id{params[query_type]['id']}的作品"
    else:
        title = f"插画id{params[query_type]['id']}相关插画"

    new_url = f"{plugin_config.tutu_site_url}/sr?r=1"
    # 拼接参数
    for k, v in params[query_type].items():
        if k == "type":
            k = "query_type"
        if k != "page":
            new_url += f"&{k}={v}"

    if page > 1:
        last_page = f'<a href="{new_url}&page={page-1}">上一页</a>'
    else:
        last_page = "到头啦"

    next_page = f'<a href="{new_url}&page={page+1}">下一页</a>'

    if query_type == "illust":
        last_page = next_page = c_page = ""
    else:
        c_page = f"第{page}页"

    return templates.TemplateResponse(
        "soutu_result.html",
        {
            "request": request,
            "style": f"{plugin_config.tutu_site_url}/static/style.css",
            "title": title,
            "out_text": out_text,
            "last_page": last_page,
            "page": c_page,
            "next_page": next_page,
        },
    )
