# 本插件改造于改仓库 https://github.com/upbit/pixivpy
from datetime import datetime
from hashlib import md5
from typing import Any, Dict, List, Literal, Optional, Union
from urllib.parse import urlparse, parse_qs
from httpx import AsyncClient,ConnectTimeout
from typing_extensions import TypeAlias
from ujson import loads
from httpx_socks import AsyncProxyTransport

# 参数类型
_FILTER: TypeAlias = Literal["for_ios", ""]
_TYPE: TypeAlias = Literal["illust", "manga", ""]
_RESTRICT: TypeAlias = Literal["public", "private", ""]
_CONTENT_TYPE: TypeAlias = Literal["illust", "manga", ""]
_MODE: TypeAlias = Literal[
    "day",
    "week",
    "month",
    "day_male",
    "day_female",
    "week_original",
    "week_rookie",
    "day_manga",
    "day_r18",
    "day_male_r18",
    "day_female_r18",
    "week_r18",
    "week_r18g",
    "",
]
_SEARCH_TARGET: TypeAlias = Literal[
    "partial_match_for_tags", "exact_match_for_tags", "title_and_caption", "keyword", ""
]
_SORT: TypeAlias = Literal["date_desc", "date_asc", "popular_desc", ""]
_DURATION: TypeAlias = Literal[
    "within_last_day", "within_last_week", "within_last_month", "", None
]
_BOOL: TypeAlias = Literal["true", "false"]


class Pixiv:
    def __init__(
        self, http_proxy: Optional[str] = None, socks5_proxy: Optional[str] = None
    ) -> None:
        self.user_id: Union[int, str] = 0
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.hosts = "https://app-api.pixiv.net"
        self.http_proxy = http_proxy
        self.socks5_proxy = socks5_proxy
        self.client_id = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
        self.client_secret = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"

    def set_client(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret

    def require_auth(self) -> None:
        if self.access_token is None:
            raise PixivError("请先使用 set_auth() 方法设置token")

    async def auth(
        self,
        refresh_token: str,
    ):
        """使用refresh token获取新的token"""
        url = "https://oauth.secure.pixiv.net/auth/token"
        data = {
            "get_secure_url": 1,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        resp_json = await self.requests_call(
            method="POST", url=url, data=data, auth=True
        )
        self.user_id = resp_json["response"]["user"]["id"]
        self.access_token = resp_json["response"]["access_token"]
        self.refresh_token = resp_json["response"]["refresh_token"]

    async def requests_call(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        auth: bool = False,
    ) -> dict:
        """发起请求"""
        # 非refresh token
        if auth:
            local_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
            headers = {}
            headers["x-client-time"] = local_time
            headers["x-client-hash"] = md5(
                (
                    local_time
                    + "28c1fdd170a5204386cb1313c7077b34f83e4aaf4aa829ce78c231e05b0bae2c"
                ).encode("utf-8")
            ).hexdigest()
            headers["app-os"] = "ios"
            headers["app-os-version"] = "16.2"
            headers["app-version"] = "7.16.4"
            headers["accept-language"] = "zh-CN,zh-Hans;q=0.9"
            headers["user-agent"] = "PixivIOSApp/7.16.4 (iOS 16.2; iPhone14,4)"
        else:
            self.require_auth()
            headers = {
                "app-os": "ios",
                "app-os-version": "14.6",
                "app-version": "7.16.4",
                "accept-language": "zh-CN,zh-Hans;q=0.9",
                "user-agent": "PixivIOSApp/7.13.3 (iOS 14.6; iPhone13,2)",
                "host": "app-api.pixiv.net",
                "Authorization": f"Bearer {self.access_token}",
            }
        
        while True:
            ctc = 0
            try:
                if method not in {"GET", "POST", "DELETE"}:
                    raise PixivError(f"未知请求方法: {method}")
                else:
                    # socks5代理
                    if self.socks5_proxy:
                        socks5_proxy = AsyncProxyTransport.from_url(self.socks5_proxy)
                    else:
                        socks5_proxy = None

                    async with AsyncClient(
                        proxies=self.http_proxy,
                        transport=socks5_proxy,
                        verify=False,
                        headers=headers,
                        follow_redirects=True,
                        timeout=3,
                    ) as c:
                        resp = await c.request(
                            method,
                            url,
                            params=params,
                            data=data,
                        )
                        if resp.status_code not in {200, 301, 302}:
                            raise PixivError(
                                f"[错误] 请求失败! \n响应码{resp.status_code}: \n{resp.text}",
                                header=resp.headers,
                                body=resp.text,
                            )
                        else:
                            return loads(resp.text)
            except ConnectTimeout as e:
                if ctc > 2:
                    raise PixivError(f"请求方法：{method}\n链接：{url}\n错误信息：{repr(e)}")
                else:
                    ctc += 1
            except Exception as e:
                raise PixivError(f"请求方法：{method}\n链接：{url}\n错误信息：{repr(e)}")

    @classmethod
    def format_bool(cls, bool_value: Union[str, bool, None]) -> _BOOL:
        if isinstance(bool_value, bool):
            return "true" if bool_value else "false"
        if bool_value in {"true", "True"}:
            return "true"
        else:
            return "false"

    # 返回翻页用参数
    @classmethod
    def parse_next_url(cls, next_url: str) -> Dict[str, Any]:
        result_qs: Dict[str, Union[str, List[str]]] = {}
        query = urlparse(next_url).query
        for key, value in parse_qs(query).items():
            # merge seed_illust_ids[] liked PHP params to array
            if "[" in key and key.endswith("]"):
                # keep the origin sequence, just ignore array length
                result_qs[key.split("[")[0]] = value
            else:
                result_qs[key] = value[-1]

        return result_qs

    # 用户详情
    async def user_detail(
        self,
        user_id: Union[int, str],
        filter: _FILTER = "for_ios",
    ) -> dict:
        url = f"{self.hosts}/v1/user/detail"
        params = {
            "user_id": user_id,
            "filter": filter,
        }
        return await self.requests_call("GET", url, params=params)

    # 用户作品列表
    ## type: [illust, manga] # noqa
    async def user_illusts(
        self,
        user_id: Union[int, str],
        type: _TYPE = "illust",
        filter: _FILTER = "for_ios",
        offset: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/user/illusts"
        params = {
            "user_id": user_id,
            "filter": filter,
        }
        if type is not None:
            params["type"] = type
        if offset:
            params["offset"] = offset
        return await self.requests_call("GET", url, params=params)

    # 用户收藏作品列表
    # tag: 从 user_bookmark_tags_illust 获取的收藏标签
    async def user_bookmarks_illust(
        self,
        user_id: Union[int, str],
        restrict: _RESTRICT = "public",
        filter: _FILTER = "for_ios",
        max_bookmark_id: Union[int, str, None] = None,
        tag: Optional[str] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/user/bookmarks/illust"
        params = {
            "user_id": user_id,
            "restrict": restrict,
            "filter": filter,
        }
        if max_bookmark_id:
            params["max_bookmark_id"] = max_bookmark_id
        if tag:
            params["tag"] = tag
        return await self.requests_call("GET", url, params=params)

    # 用户相关
    async def user_related(
        self,
        seed_user_id: Union[int, str],
        filter: _FILTER = "for_ios",
        offset: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/user/related"
        params = {
            "filter": filter,
            # Pixiv warns to put seed_user_id at the end -> put offset here
            "offset": offset if offset else 0,
            "seed_user_id": seed_user_id,
        }
        return await self.requests_call("GET", url, params=params)

    # 关注用户的新作
    # restrict: [public, private]
    async def illust_follow(
        self,
        restrict: _RESTRICT = "public",
        offset: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v2/illust/follow"
        params: Dict[str, Union[str, int]] = {
            "restrict": restrict,
        }
        if offset:
            params["offset"] = offset
        return await self.requests_call("GET", url, params=params)

    # 作品详情 (类似PAPI.works()，iOS中未使用)
    async def illust_detail(self, illust_id: Union[int, str]) -> dict:
        url = f"{self.hosts}/v1/illust/detail"
        params = {
            "illust_id": illust_id,
        }
        return await self.requests_call("GET", url, params=params)

    # 作品评论
    async def illust_comments(
        self,
        illust_id: Union[int, str],
        offset: Union[int, str, None] = None,
        include_total_comments: Union[str, bool, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/illust/comments"
        params = {
            "illust_id": illust_id,
        }
        if offset:
            params["offset"] = offset
        if include_total_comments:
            params["include_total_comments"] = self.format_bool(include_total_comments)
        return await self.requests_call("GET", url, params=params)

    # 相关作品列表
    async def illust_related(
        self,
        illust_id: Union[int, str],
        filter: _FILTER = "for_ios",
        seed_illust_ids: Union[int, str, List[str], None] = None,
        offset: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v2/illust/related"
        params: Dict[str, Any] = {
            "illust_id": illust_id,
            "filter": filter,
            "offset": offset,
        }
        if isinstance(seed_illust_ids, str):
            params["seed_illust_ids[]"] = [seed_illust_ids]
        elif isinstance(seed_illust_ids, list):
            params["seed_illust_ids[]"] = seed_illust_ids
        return await self.requests_call("GET", url, params=params)

    # 插画推荐 (Home - Main)
    # content_type: [illust, manga]
    async def illust_recommended(
        self,
        content_type: _CONTENT_TYPE = "illust",
        include_ranking_label: Union[bool, str] = True,
        filter: _FILTER = "for_ios",
        max_bookmark_id_for_recommend: Union[int, str, None] = None,
        min_bookmark_id_for_recent_illust: Union[int, str, None] = None,
        offset: Union[int, str, None] = None,
        include_ranking_illusts: Union[str, bool, None] = None,
        bookmark_illust_ids: Union[str, List[Union[int, str]], None] = None,
        include_privacy_policy: Union[str, List[Union[int, str]], None] = None,
    ) -> dict:
        url = "https://app-api.pixiv.net/v1/illust/recommended"
        params: Dict[str, Any] = {
            "content_type": content_type,
            "include_ranking_label": self.format_bool(include_ranking_label),
            "filter": filter,
        }
        if max_bookmark_id_for_recommend:
            params["max_bookmark_id_for_recommend"] = max_bookmark_id_for_recommend
        if min_bookmark_id_for_recent_illust:
            params[
                "min_bookmark_id_for_recent_illust"
            ] = min_bookmark_id_for_recent_illust
        if offset:
            params["offset"] = offset
        if include_ranking_illusts:
            params["include_ranking_illusts"] = self.format_bool(
                include_ranking_illusts
            )

        if include_privacy_policy:
            params["include_privacy_policy"] = include_privacy_policy

        return await self.requests_call("GET", url, params=params)

    # 小说推荐
    async def novel_recommended(
        self,
        include_ranking_label: Union[bool, str] = True,
        filter: _FILTER = "for_ios",
        offset: Union[int, str, None] = None,
        include_ranking_novels: Union[str, bool, None] = None,
        already_recommended: Union[str, List[str], None] = None,
        max_bookmark_id_for_recommend: Union[int, str, None] = None,
        include_privacy_policy: Union[str, List[Union[int, str]], None] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/novel/recommended"
        params: Dict[str, Any] = {
            "include_ranking_label": self.format_bool(include_ranking_label),
            "filter": filter,
        }
        if offset:
            params["offset"] = offset
        if include_ranking_novels:
            params["include_ranking_novels"] = self.format_bool(include_ranking_novels)
        if max_bookmark_id_for_recommend:
            params["max_bookmark_id_for_recommend"] = max_bookmark_id_for_recommend
        if already_recommended:
            if isinstance(already_recommended, str):
                params["already_recommended"] = already_recommended
            elif isinstance(already_recommended, list):
                params["already_recommended"] = ",".join(
                    str(iid) for iid in already_recommended
                )
        if include_privacy_policy:
            params["include_privacy_policy"] = include_privacy_policy

        return await self.requests_call("GET", url, params=params)

    # 作品排行
    # mode: [day, week, month, day_male, day_female, week_original, week_rookie, day_manga]
    # date: '2016-08-01'
    # mode (Past): [day, week, month, day_male, day_female, week_original, week_rookie,
    #               day_r18, day_male_r18, day_female_r18, week_r18, week_r18g]
    async def illust_ranking(
        self,
        mode: _MODE = "day",
        filter: _FILTER = "for_ios",
        date: Optional[str] = None,
        offset: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/illust/ranking"
        params: Dict[str, Any] = {
            "mode": mode,
            "filter": filter,
        }
        if date:
            params["date"] = date
        if offset:
            params["offset"] = offset
        return await self.requests_call("GET", url, params=params)

    # 趋势标签 (Search - tags)
    async def trending_tags_illust(self, filter: _FILTER = "for_ios") -> dict:
        url = f"{self.hosts}/v1/trending-tags/illust"
        params = {
            "filter": filter,
        }
        return await self.requests_call("GET", url, params=params)

    # 搜索 (Search)
    # search_target - 搜索类型
    #   partial_match_for_tags  - 标签部分一致
    #   exact_match_for_tags    - 标签完全一致
    #   title_and_caption       - 标题说明文
    # sort: [date_desc, date_asc, popular_desc] - popular_desc为会员的热门排序
    # duration: [within_last_day, within_last_week, within_last_month]
    # start_date, end_date: '2020-07-01'
    async def search_illust(
        self,
        word: str,
        search_target: _SEARCH_TARGET = "partial_match_for_tags",
        sort: _SORT = "date_desc",
        bookmark_num_min: Optional[int] = None,
        bookmark_num_max: Optional[int] = None,
        merge_plain_keyword_results: _BOOL = "true",
        duration: _DURATION = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filter: _FILTER = "for_ios",
        offset: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/search/illust"
        params: Dict[str, Any] = {
            "word": word,
            "search_target": search_target,
            "merge_plain_keyword_results": merge_plain_keyword_results,
            "include_translated_tag_results": True,
            "sort": sort,
            "filter": filter,
        }
        if bookmark_num_min:
            params["bookmark_num_min"] = bookmark_num_min
        if bookmark_num_max:
            params["bookmark_num_max"] = bookmark_num_max
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if duration:
            params["duration"] = duration
        if offset:
            params["offset"] = offset
        return await self.requests_call("GET", url, params=params)

    # 搜索小说 (Search Novel)
    # search_target - 搜索类型
    #   partial_match_for_tags  - 标签部分一致
    #   exact_match_for_tags    - 标签完全一致
    #   text                    - 正文
    #   keyword                 - 关键词
    # sort: [date_desc, date_asc]
    # start_date/end_date: 2020-06-01
    async def search_novel(
        self,
        word: str,
        search_target: _SEARCH_TARGET = "partial_match_for_tags",
        sort: _SORT = "date_desc",
        merge_plain_keyword_results: _BOOL = "true",
        include_translated_tag_results: _BOOL = "true",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filter: Optional[str] = None,
        offset: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/search/novel"
        params: Dict[str, Any] = {
            "word": word,
            "search_target": search_target,
            "merge_plain_keyword_results": merge_plain_keyword_results,
            "include_translated_tag_results": include_translated_tag_results,
            "sort": sort,
            "filter": filter,
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if offset:
            params["offset"] = offset
        return await self.requests_call("GET", url, params=params)

    async def search_user(
        self,
        word: str,
        sort: _SORT = "date_desc",
        duration: _DURATION = None,
        filter: _FILTER = "for_ios",
        offset: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/search/user"
        params: Dict[str, Any] = {
            "word": word,
            "sort": sort,
            "filter": filter,
        }
        if duration:
            params["duration"] = duration
        if offset:
            params["offset"] = offset
        return await self.requests_call("GET", url, params=params)

    # 作品收藏详情
    async def illust_bookmark_detail(self, illust_id: Union[int, str]) -> dict:
        url = f"{self.hosts}/v2/illust/bookmark/detail"
        params = {
            "illust_id": illust_id,
        }
        return await self.requests_call("GET", url, params=params)

    # 新增收藏
    async def illust_bookmark_add(
        self,
        illust_id: Union[int, str],
        restrict: _RESTRICT = "public",
        tags: Union[str, List[str], None] = None,
    ) -> dict:
        url = f"{self.hosts}/v2/illust/bookmark/add"
        data = {
            "illust_id": illust_id,
            "restrict": restrict,
        }
        if isinstance(tags, list):
            tags = " ".join(str(tag) for tag in tags)
        if tags is not None:
            data["tags[]"] = tags

        return await self.requests_call("POST", url, data=data)

    # 删除收藏
    async def illust_bookmark_delete(self, illust_id: Union[int, str]) -> dict:
        url = f"{self.hosts}/v1/illust/bookmark/delete"
        data = {
            "illust_id": illust_id,
        }
        return await self.requests_call("POST", url, data=data)

    # 关注用户
    async def user_follow_add(
        self,
        user_id: Union[int, str],
        restrict: _RESTRICT = "public",
    ) -> dict:
        url = f"{self.hosts}/v1/user/follow/add"
        data = {"user_id": user_id, "restrict": restrict}
        return await self.requests_call("POST", url, data=data)

    # 取消关注用户
    async def user_follow_delete(self, user_id: Union[int, str]) -> dict:
        url = f"{self.hosts}/v1/user/follow/delete"
        data = {"user_id": user_id}
        return await self.requests_call("POST", url, data=data)

    # 用户收藏标签列表
    async def user_bookmark_tags_illust(
        self,
        restrict: _RESTRICT = "public",
        offset: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/user/bookmark-tags/illust"
        params: Dict[str, Any] = {
            "restrict": restrict,
        }
        if offset:
            params["offset"] = offset
        return await self.requests_call("GET", url, params=params)

    # Following用户列表
    async def user_following(
        self,
        user_id: Union[int, str],
        restrict: _RESTRICT = "public",
        offset: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/user/following"
        params = {
            "user_id": user_id,
            "restrict": restrict,
        }
        if offset:
            params["offset"] = offset

        return await self.requests_call("GET", url, params=params)

    # Followers用户列表
    async def user_follower(
        self,
        user_id: Union[int, str],
        filter: _FILTER = "for_ios",
        offset: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/user/follower"
        params = {
            "user_id": user_id,
            "filter": filter,
        }
        if offset:
            params["offset"] = offset

        return await self.requests_call("GET", url, params=params)

    # 好P友
    async def user_mypixiv(
        self,
        user_id: Union[int, str],
        offset: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/user/mypixiv"
        params = {
            "user_id": user_id,
        }
        if offset:
            params["offset"] = offset

        return await self.requests_call("GET", url, params=params)

    # 黑名单用户
    async def user_list(
        self,
        user_id: Union[int, str],
        filter: _FILTER = "for_ios",
        offset: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v2/user/list"
        params = {
            "user_id": user_id,
            "filter": filter,
        }
        if offset:
            params["offset"] = offset

        return await self.requests_call("GET", url, params=params)

    # 获取ugoira信息
    async def ugoira_metadata(self, illust_id: Union[int, str]) -> dict:
        url = f"{self.hosts}/v1/ugoira/metadata"
        params = {
            "illust_id": illust_id,
        }

        return await self.requests_call("GET", url, params=params)

    # 用户小说列表
    async def user_novels(
        self,
        user_id: Union[int, str],
        filter: _FILTER = "for_ios",
        offset: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/user/novels"
        params = {
            "user_id": user_id,
            "filter": filter,
        }
        if offset:
            params["offset"] = offset
        return await self.requests_call("GET", url, params=params)

    # 小说系列详情
    async def novel_series(
        self,
        series_id: Union[int, str],
        filter: _FILTER = "for_ios",
        last_order: Optional[str] = None,
    ) -> dict:
        url = f"{self.hosts}/v2/novel/series"
        params = {
            "series_id": series_id,
            "filter": filter,
        }
        if last_order:
            params["last_order"] = last_order
        return await self.requests_call("GET", url, params=params)

    # 小说详情
    async def novel_detail(self, novel_id: Union[int, str]) -> dict:
        url = f"{self.hosts}/v2/novel/detail"
        params = {
            "novel_id": novel_id,
        }

        return await self.requests_call("GET", url, params=params)

    # 小说正文
    async def novel_text(self, novel_id: Union[int, str]) -> dict:
        url = f"{self.hosts}/v1/novel/text"
        params = {
            "novel_id": novel_id,
        }

        return await self.requests_call("GET", url, params=params)

    # 大家的新作
    # content_type: [illust, manga]
    async def illust_new(
        self,
        content_type: _CONTENT_TYPE = "illust",
        filter: _FILTER = "for_ios",
        max_illust_id: Union[int, str, None] = None,
    ) -> dict:
        url = f"{self.hosts}/v1/illust/new"
        params: Dict[str, Any] = {
            "content_type": content_type,
            "filter": filter,
        }
        if max_illust_id:
            params["max_illust_id"] = max_illust_id
        return await self.requests_call("GET", url, params=params)

    # # 特辑详情 (无需登录，调用Web API)
    # def showcase_article(self, showcase_id: Union[int , str]) -> dict:
    #     url = "https://www.pixiv.net/ajax/showcase/article"
    #     # Web API，伪造Chrome的User-Agent
    #     headers = {
    #         "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
    #         + "(KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
    #         "Referer": "https://www.pixiv.net",
    #     }
    #     params = {
    #         "article_id": showcase_id,
    #     }

    #     return await self.requests_call("GET", url, params=params)


class PixivError(Exception):
    def __init__(
        self,
        reason: str,
        header: Optional[Any] = None,
        body: Optional[str] = None,
    ):
        self.reason = str(reason)
        self.header = header
        self.body = body
        super(Exception, self).__init__(self, reason)

    def __str__(self) -> str:
        return self.reason
