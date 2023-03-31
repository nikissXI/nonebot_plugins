from asyncio import gather
from pathlib import Path
from random import choice
from typing import Optional
from nonebot import get_asgi
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from .config import pc, var
from .data_handle import (
    fn_cache_sent_img,
    get_img_url,
    url_diy_replace,
)

app = get_asgi()
app.mount("/tutu_static", StaticFiles(directory=f"{Path(__file__).parent}/html"), name="tutu_static")
templates = Jinja2Templates(directory=f"{Path(__file__).parent}/html")


@app.get("/tutu")
async def tutu(
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
                    msg += f'<a href="tutu?c={c}&fn={ff}">{ff} 数量: {len(var.api_list_local[ff])}</a><br />'
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
            img_api_url = f"tutu?c={c}&fn={fn}"
            img_1 = f"tutu?c=1&mode={mode}"
            img_3 = f"tutu?c=3&fn={fn}"
            img_6 = f"tutu?c=6&fn={fn}"
        elif api:
            img_api_url = f"tutu?c={c}&api={api}"
            img_1 = f"tutu?c=1&mode={mode}"
            img_3 = f"tutu?c=3&api={api}"
            img_6 = f"tutu?c=6&api={api}"
        else:
            img_api_url = f"tutu?c={c}&mode={mode}"
            img_1 = f"tutu?c=1&mode={mode}"
            img_3 = f"tutu?c=3&mode={mode}"
            img_6 = f"tutu?c=6&mode={mode}"
        type_urls = ""
        img_list = ""
        for m in var.api_list_online:
            type_urls += f'<a href="tutu?c={c}&mode={m}">{"." if m == pc.tutu_r18_name else m}</a> &emsp13;'
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
                "img_1": img_1,
                "img_3": img_3,
                "img_6": img_6,
                "img_type": mode,
                "type_urls": type_urls,
                "img_api_url_fn": f"tutu?c={c}&fn=.",
                "img_api_url_random": f"tutu?c={c}&mode=随机",
                "img_num": c,
                "img_list": img_list,
                "next_group": img_api_url,
            },
        )
