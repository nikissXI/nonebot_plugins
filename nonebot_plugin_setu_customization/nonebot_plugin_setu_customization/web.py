from asyncio import gather
from pathlib import Path
from random import choice
from nonebot import get_asgi
from nonebot.log import logger
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates
from .config import plugin_config, var
from .data_handle import get_img_url, cache_sent_img

app = get_asgi()


@app.get("/img_api")
async def img_api(
    request: Request,
    fn: str | None = None,
    mode: str = "all",
    fw: int = 0,
    c: int = 1,
    api: str | None = None,
):
    templates = Jinja2Templates(directory=f"{Path(__file__).parent}/html")
    img_url_list = []
    api_url_list = []
    task_list = []
    if fw:
        c = 1

    if fn:
        file_name = fn
        if file_name not in var.api_list_local:
            urls = ""
            for ff in var.api_list_local:
                urls += f'<a href="{plugin_config.tutu_site_url}/img_api?fn={ff}&c={c}">{ff} 数量: {len(var.api_list_local[ff])}</a><br />'
            return templates.TemplateResponse(
                "img_showfn.html",
                {
                    "request": request,
                    "urls": urls,
                },
            )
        else:
            # if not fw and file_name.find("wx_") != -1:
            #     return "不支持该类型，因为微信的图有防盗链，可以用重定向浏览，加参数fw=1"
            # else:
            for i in range(c):
                img_url = choice(var.api_list_local[file_name])
                # img_num = cache_sent_img(
                #     f"{plugin_config.tutu_site_url}/img_api?fw=1&fn={file_name}", img_url
                # )
                img_url_list.append((True, img_url, "X"))

    else:
        if api:
            for i in range(c):
                api_url_list.append(api)
        elif not var.api_list_online:
            return "no image"
        elif mode == "all":
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
            return "该类别不存在"

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
        urls = ""
        img_list = ""
        for mode in var.api_list_online:
            urls += f'<a href="{plugin_config.tutu_site_url}/img_api?mode={mode}&c={c}">{"." if mode == plugin_config.tutu_r18_name else mode}</a> &emsp13;'
        for success, img_url, img_num in img_url_list:
            if success:
                img_list += f'<span>No.{img_num}</span><br /><img alt="img" src="{img_url}"><br />'
            else:
                img_list += f"<span>No.{img_num}</span><br /><span>{img_url}</span><br />"
        return templates.TemplateResponse(
            "img.html",
            {
                "request": request,
                "img_api_url_num": img_api_url[: img_api_url.find("&c=")],
                "img_api_url": img_api_url,
                "img_list": img_list,
                "urls": urls,
                "img_api_url_fn": f"{plugin_config.tutu_site_url}/img_api?fn=?&c={c}",
                "img_api_url_all": f"{plugin_config.tutu_site_url}/img_api?mode=all&c={c}",
            },
        )
