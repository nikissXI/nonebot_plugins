# nonebot_plugin_setu_customization
[![nonebot2](https://img.shields.io/static/v1?label=nonebot&message=v2rc1%2B&color=green)](https://v2.nonebot.dev/)[![python](https://img.shields.io/static/v1?label=python+&message=3.9%2B&color=blue)](https://img.shields.io/static/v1?label=python+&message=3.7%2B&color=blue)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Nonebot2 可动态管理API并带网页浏览的setu插件

### 安装

使用nb-cli安装
```bash
nb plugin install nonebot_plugin_setu_customization
```

或者  
直接把插件clone下来放进去plugins文件夹

### 配置
在bot对应的.env文件修改

```bash
# 必填项
# 机器人的QQ号（由于开发者多gocq连接，所以有这个设置）
tutu_bot_qqnum = 114514
# 管理员的QQ号（别问我为什么要另外写）
tutu_admin_qqnum = 114514

# 非必填项
# R18类别的名称
tutu_r18_name = R18
# 本地图片库的路径
tutu_local_api_path = data/tutu_local_img_lib/
# 本地库二次元文件名称
tutu_self_anime_lib =  self_anime
# 本地库三次元文件名称
tutu_self_cosplay_lib = self_cosplay
# 插件数据文件名
tutu_data_filename = tutu_data.json
# 网页访问地址，就是nonebot的监听地址和端口号，如 http://127.0.0.1:8080
tutu_site_url = http://127.0.0.1:8080
# socks5代理地址，如 socks5://127.0.0.1:1234
tutu_socks5_proxy = socks5://127.0.0.1:1234
# http代理地址，如 http://127.0.0.1:1234
tutu_http_proxy = http://127.0.0.1:1234
# 使用网页访问时，微信图片反代地址，不用网页浏览可不填，如 http://img.example.top:114
tutu_wx_img_proxy = http://img.example.top:114
# 使用网页访问时，B站图片反代地址，不用网页浏览可不填，如 http://img.example.top:514
tutu_bili_img_proxy = http://img.example.top:514
# 爬取文章图片时，图片的宽或高小于多少忽略爬取
tutu_crawler_min_width =  500
tutu_crawler_min_height =  500
# 自动爬取功能，文章url文件放置路径
tutu_crawler_file_path = tutu_crawler/
# 自动爬取功能，检测文章标题，含有其中关键字则忽略爬取
tutu_crawler_keyword = ["删", "薪", "敏感", "暂停", "停更", "图包"]
```

### 目录
data/tutu_data.json 存储群白名单信息，api接口信息，合并发送开关  
data/tutu_local_img_lib/ 存储用户自己上传的图片url文件，如下图  
<img width="600" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_setu_customization/src/local_img_lib.jpg"/>

如果要自己爬图入库的看最下方  
tutu_crawler/ 自动爬取文章图片用的，里面放待爬取的文章url文件，还是看最下方

### 命令  
| 指令 | 说明 |
|:-----:|:----:|
| 图图 | 机器人出图（好友私聊，群聊要添加白名单） |
| 图图帮助 | 查看图图命令的更多使用姿势 |
| （下面都是管理员命令） | （发送命令有使用格式） |
| 图图插件群管理 | 增删群白名单 |
| 图图插件接口测试 | 测试接口连接情况和返回的数据 |
| 图片测试 | 测试某张图能否正常发出来 |
| 文章爬取 | 爬取微信文章或B站专栏的图片 |
| 爬取合并 | 是否将爬取结果合并发送，默认合并 |
| 图片序号 | 每张发出来的图片都有一个序号，可查看之前发送的图片url |
| 图片删除 | 删除本地库的某张图片 |
| 开爬 | 上传指定格式的文件让nb爬（详情看readme最下方） |

### 自定义图片url关键字替换
在data_handle.py文件里面的 url_diy_replace 函数，如果有其他更好的反代地址或其他需求可以自行调整
<img width="600" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_setu_customization/src/url_diy_replace.jpg"/>

### 使用示例、导入api和图片库
**二次元图片api**  
https://api.lolicon.app/setu/v2  
http://api.tangdouz.com/sjdmbz.php  
https://api.dujin.org/pic/yuanshen/  
https://api.mtyqx.cn/tapi/random.php  
https://www.dmoe.cc/random.php  
https://setu.yuban10703.xyz/setu  
https://api.ixiaowai.cn/api/api.php  
https://tuapi.eees.cc/api.php?category=dongman&type=302  
https://api.yimian.xyz/img/  
https://tenapi.cn/acg/  
https://api.jiecs.top/lolicon/  
https://api.vvhan.com/api/acgimg  
http://api.iw233.cn/api.php?sort=random  
https://image.anosu.top/pixiv/direct  

**R18图片api**  
https://api.lolicon.app/setu/v2?r18=1  
https://setu.yuban10703.xyz/setu?r18=1  
https://api.jiecs.top/lolicon/?r18=1  
https://image.anosu.top/pixiv/direct?r18=1  

**三次元图片api**  
没收集到好的，但是我爬了很多，在仓库的tutu_local_img_lib文件夹，下载放进去data/tutu_local_img_lib/里面

**本地图片库**  
即data/tutu_local_img_lib/中的图片，放入图片url文件后，使用命令“图图插件接口管理 刷新本地”进行导入  
访问接口url如果没有在.env配置tutu_site_url，就是nonebot的地址和端口号，如绑定的host=127.0.0.1，port=8080，就是http://127.0.0.1:8080/img_api?fw=1&fn=\<filename\>
| 参数 | 说明 |
|:-----:|:----:|
| fw | 是否重定向，0返回网页，1重定向到图片url |
| fn | 本地图片库文件名 |
| mode | 图片类型，没有fn参数时有效 |
| c | 返回的图片数量，没有fw参数时有效 |

```bash
# 添加一个接口到二次元类型接口
图图插件接口管理 二次元 + https://api.lolicon.app/setu/v2
# 添加一个本地图片库接口到三次元类型接口
图图插件接口管理 三次元 + http://127.0.0.1:8080/img_api?fw=1&fn=self_cosplay
# 爬取一篇微信文章的图片到本地图片库self_anime
https://mp.weixin.qq.com/s/IHeYqZTu8xYLv7nDkRwxUQ self_anime
# 该命令等效于上面的命令 默认2指self_anime，3指self_cosplay
https://mp.weixin.qq.com/s/IHeYqZTu8xYLv7nDkRwxUQ 2
```

### 文章图片爬取 
下载mitmproxy_script文件夹中的两个脚本 
```bash
# 安装mitmproxy
pip install mitmproxy
# 运行papa.py，8080的监听端口，可以自己改
python papa.py -p8080
# 手机或电脑设置好代理后，用浏览器访问以下网站，如果看到证书选择那就是代理对了，然后看说明安装证书
mitm.it
# 然后根据下面的方法爬取，结果输出在result文件夹中
```

**爬取微信公众号文章url 方法一**  
PS：建议电脑端或iOS微信使用  
微信连上代理后，大部分微信公众号的对话框有个查看历史文章（有的没有），点进去后浏览，一直往下刷到底就行，如果没有历史文章接口看方法二
<img width="600" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_setu_customization/src/weixin1.jpg"/>

**爬取微信公众号文章url 方法二**  
PS：容易被限制，如果翻页不回显数据就是被限制了，被限制就等几个小时再来（具体时间自己摸索），否则限制时间会大幅度延长
注册一个微信公众平台账号  
https://mp.weixin.qq.com/  
依次点草稿箱、新的创作、写新图文，会有个新页面，在最上面有个超链接，点选择公众号，搜索公众号，然后选择就可以看到历史文章了，一页页往下翻，一次翻二三十页就好，不然容易被限制
<img width="600" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_setu_customization/src/weixin2.jpg"/>

**爬取B站专栏图片**  
用网页打开某个UP的账号空间，点TA的专栏，就会打开 https://space.bilibili.com/XXXXXXX/article  
<img width="600" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_setu_customization/src/bili.jpg"/>
然后就会自动翻页爬取所有文章url了，可以在结果文件夹里看到进度，爬取完会有个DONE文件

**提取文章url**  
爬取到新数据会生成“new_data_XXX”文件在结果文件夹中，里面的格式是“标题 *** 文章url”，可以通过标题进行筛选，不要的文章整行剪切丢到“history_data_XXX”  
“history_data_XXX”是历史数据，每次运行爬取脚本会读取历史数据，爬过的就不会再爬
最后就是筛选好的“new_data_XXX”文件
```bash
# 运行split_url.py
python 运行split_url.py
```
split_url.py会遍历result里面的文件，把里面命名含有“new_data_”的文件里的url提取出来输出到“wait_for_upload”文件夹  
在nonebot根目录的“tutu_crawler”里新建一个文件夹，文件夹名字是爬取的图片加入的本地图片库，如“self_anime”，也可以直接新建一个名字“2”的文件夹，默认2指self_anime，3指self_cosplay  
把wait_for_upload里面的文件根据类型上传到 tutu_crawler/<本地图片库>/里面  
然后给机器人私聊发送“开爬”就会自动爬取