from asyncio import gather
from pathlib import Path
from random import choice
from typing import Optional, Union
from nonebot import get_asgi
from nonebot.log import logger
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from .config import pc, soutu_options, var
from .data_handle import (
    fn_cache_sent_img,
    get_img_url,
    pixiv_reverse_proxy,
    url_diy_replace,
)
from .pixivapi import Pixiv

app = get_asgi()
app.mount("/tutu", StaticFiles(directory=f"{Path(__file__).parent}/html"), name="tutu")
templates = Jinja2Templates(directory=f"{Path(__file__).parent}/html")


@app.get("/img_api")
async def img_api(
    request: Request,
    fn: Optional[str] = None,
    mode: str = "随机",
    fw: int = 0,
    c: int = 1,
    api: Optional[str] = None,
):
    img_url_list = []
    api_url_list = []
    task_list = []
    if fw:
        c = 1

    if not fn and c > 10:
        return

    if fn:
        file_name = fn
        if file_name not in var.api_list_local:
            msg = "可用fn参数，点击可直接跳转<br />"
            if var.api_list_local:
                for ff in var.api_list_local:
                    msg += f'<a href="img_api?c={c}&fn={ff}">{ff} 数量: {len(var.api_list_local[ff])}</a><br />'
            else:
                msg += "无可用"
            return templates.TemplateResponse(
                "show_info.html",
                {
                    "request": request,
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
                    "msg": "没有加入任何API哦，无图图",
                },
            )
        elif mode == "随机":
            for i in range(c):
                img_type = choice(
                    [
                        img_type_i
                        for img_type_i in var.api_list_online
                        if img_type_i != pc.tutu_r18_name
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
            img_api_url = f"img_api?c={c}&fn={fn}"
            img_3 = f"img_api?c=3&fn={fn}"
            img_10 = f"img_api?c=10&fn={fn}"
        elif api:
            img_api_url = f"img_api?c={c}&api={api}"
            img_3 = f"img_api?c=3&api={api}"
            img_10 = f"img_api?c=10&api={api}"
        else:
            img_api_url = f"img_api?c={c}&mode={mode}"
            img_3 = f"img_api?c=3&mode={mode}"
            img_10 = f"img_api?c=10&mode={mode}"
        type_urls = ""
        img_list = ""
        for m in var.api_list_online:
            type_urls += f'<a href="img_api?c={c}&mode={m}">{"." if m == pc.tutu_r18_name else m}</a> &emsp13;'
        for success, img_url, img_num in img_url_list:
            if success:
                img_list += f'<span>No.{img_num}</span><br /><p><a href="{img_url}">点击查看原图</a><br/><img alt="点我重新加载试试" src="{url_diy_replace(img_url)}" onclick="this.src=this.src+\'?\'" loading="lazy"></p><br />'
            else:
                img_list += (
                    f"<span>No.{img_num}</span><br /><span>{img_url}</span><br />"
                )
        return templates.TemplateResponse(
            "tutu.html",
            {
                "request": request,
                "img_3": img_3,
                "img_10": img_10,
                "img_type": mode,
                "type_urls": type_urls,
                "img_api_url_fn": f"img_api?c={c}&fn=.",
                "img_api_url_random": f"img_api?c={c}&mode=随机",
                "img_num": c,
                "img_list": img_list,
                "next_group": img_api_url,
            },
        )


@app.get("/soutu")
async def soutu(
    request: Request,
    sk: int = 0,
    query_type: str = "",
    word: str = "",
    search_target: str = "",
    sort: str = "",
    bookmark_num_min: Union[str, int] = "",
    bookmark_num_max: Union[str, int] = "",
    mode: str = "",
    date: str = "",
    user_id: int = 0,
    illust_id: int = 0,
    page: int = 1,
):
    """
    pixiv搜图
    """
    if not pc.pixiv_refresh_token:
        return templates.TemplateResponse(
            "show_info.html",
            {
                "request": request,
                "msg": "refresh token未配置",
            },
        )

    if sk not in var.soutu_key_live:
        return templates.TemplateResponse(
            "show_info.html",
            {
                "request": request,
                "msg": "链接失效，请私聊机器人发“搜图”获取新链接",
            },
        )
    else:
        var.soutu_key_live[sk] = pc.pixiv_sk_time

    if not query_type:
        return templates.TemplateResponse(
            "soutu.html",
            {
                "request": request,
                "sk": sk,
            },
        )

    offset = (page - 1) * 30
    params = {
        "search_illust": {
            "word": word,
            "search_target": search_target,
            "sort": sort,
            "offset": offset,
        },
        "illust_ranking": {
            "mode": mode,
            "date": date,
            "offset": offset,
        },
        "illust_recommended": {
            "offset": offset,
        },
        "user_illusts": {
            "user_id": user_id,
            "offset": offset,
        },
        "illust_detail": {
            "illust_id": illust_id,
        },
        "illust_related": {
            "illust_id": illust_id,
            "offset": offset,
        },
    }
    if query_type == "search_illust":
        if not bookmark_num_min:
            bookmark_num_min = 0
        if not bookmark_num_max:
            bookmark_num_max = 0
        bookmark_num_min, bookmark_num_max = int(bookmark_num_min), int(
            bookmark_num_max
        )
        if bookmark_num_min > 0:
            params[query_type]["bookmark_num_min"] = bookmark_num_min
        if bookmark_num_max > 0:
            params[query_type]["bookmark_num_max"] = bookmark_num_max

    try:
        api = Pixiv(http_proxy=pc.tutu_http_proxy, socks5_proxy=pc.tutu_socks5_proxy)
        await api.auth(refresh_token=pc.pixiv_refresh_token)
        resp_json = await getattr(api, query_type)(**params[query_type])
    except Exception as e:
        msg = f"搜图请求出错：{e}"
        logger.error(msg)
        return msg

    if query_type == "illust_detail":
        result_keyword = "illust"

    else:
        result_keyword = "illusts"

    if result_keyword not in resp_json:
        return templates.TemplateResponse(
            "show_info.html",
            {
                "request": request,
                "msg": "无结果",
            },
        )
    else:
        # 遍历数据
        out_text = ""
        result_list = []
        if result_keyword == "illust":
            result_list.append(resp_json[result_keyword])
        else:
            result_list = resp_json[result_keyword]

    more_num = 1
    for d in result_list:
        # 分割线
        out_text += '<br /><div style="background-color: rgb(255, 93, 155);height:10px;width:100%;margin-top:20px;"></div>'
        # 插画简介
        out_text += f"<span><strong>插画</strong> {d['title']}&emsp13;id {d['id']}</span><br/><span><strong>画师</strong> {d['user']['name']}&emsp13;id {d['user']['id']}</span><br/>"

        # tags，查询插画详情时显示
        if result_keyword == "illust":
            out_text += "<strong>标签 </strong>"
            if d["illust_ai_type"] != 0:
                out_text += "<strong>AI生成</strong>&emsp13;"
            for t in d["tags"]:
                out_text += t["name"]
                if t["translated_name"]:
                    out_text += f"({t['translated_name']})"
                out_text += "&emsp13;"
            out_text += "<br/>"

        # 获取图片链接, 输出图片
        if d["meta_single_page"]:
            img_url = d["meta_single_page"]["original_image_url"]
            if img_url.find("ugoira") == -1:
                out_text += f'<p><a href="{pixiv_reverse_proxy(img_url, resize=False)}">点击查看原图</a><br/><img alt="点我重新加载试试" src="{pixiv_reverse_proxy(img_url)}" onclick="this.src=this.src+\'?\'" loading="lazy"></p>'
            else:
                out_text += f'<p>动图无法预览<br/><img alt="点我重新加载试试" src="{pixiv_reverse_proxy(img_url,resize=False)}" onclick="this.src=this.src+\'?\'" loading="lazy"></p>'
        else:
            first_pic = True
            for mp in d["meta_pages"]:
                img_url = mp["image_urls"]["original"]
                if first_pic:
                    first_pic = False
                    out_text += f'<p><a href="{pixiv_reverse_proxy(img_url, resize=False)}">点击查看原图</a><br/><img alt="点我重新加载试试" src="{pixiv_reverse_proxy(img_url)}" onclick="this.src=this.src+\'?\'" loading="lazy"></p><button id="button{more_num}" onclick="show({more_num})">点击查看/隐藏余下{len(d["meta_pages"])-1}张</button><div id="more{more_num}" style="display:none;">'
                else:
                    out_text += f'<p><a href="{pixiv_reverse_proxy(img_url, resize=False)}">点击查看原图</a><br/><img alt="点我重新加载试试" src="{pixiv_reverse_proxy(img_url)}" onclick="this.src=this.src+\'?\'" loading="lazy"></p>'
            out_text += "</div>"
            more_num += 1

    # 根据不同的
    if query_type == "search_illust":
        title = "搜索：" + params[query_type]["word"]
    elif query_type == "illust_ranking":
        title = f"{soutu_options['rank_name'][params[query_type]['mode']]} {params[query_type]['date'] if params[query_type]['date'] else ''}"
    elif query_type == "user_illusts":
        title = f"画师id{params[query_type]['user_id']}的作品"
    elif query_type == "illust_detail":
        title = f"作品id{params[query_type]['illust_id']}详情"
    elif query_type == "illust_recommended":
        title = f"随机推荐"
    else:
        title = f"插画id{params[query_type]['illust_id']}相关插画"

    # 拼接翻页链接
    page_params = f"soutu?sk={sk}&query_type={query_type}"
    for k, v in params[query_type].items():
        if k != "offset":
            page_params += f"&{k}={v}"

    if query_type == "illust_detail":
        last_page = ""
        next_page = ""
        c_page = ""
    else:
        if page != 1:
            last_page = f'<a href="{page_params}&page={page-1}">上一页</a>'
        else:
            last_page = "到头啦"

        if resp_json["next_url"]:
            next_page = f'<a href="{page_params}&page={page+1}">下一页</a>'
        else:
            next_page = "到底啦"

        c_page = f"第{page}页"

    return templates.TemplateResponse(
        "soutu_result.html",
        {
            "request": request,
            "title": title,
            "out_text": out_text,
            "last_page": last_page,
            "c_page": c_page,
            "next_page": next_page,
            "sk": sk,
        },
    )
