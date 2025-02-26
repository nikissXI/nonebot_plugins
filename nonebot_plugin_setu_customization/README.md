<p align="center">
  <a href="https://v2.nonebot.dev/store">
  <img src="https://user-images.githubusercontent.com/44545625/209862575-acdc9feb-3c76-471d-ad89-cc78927e5875.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
</p>

<div align="center">

# nonebot_plugin_setu_customization

_✨ Nonebot2 可动态管理 API 的 setu 插件 ✨_

</div>

<p align="center">
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="license">
  </a>
  <a href="https://v2.nonebot.dev/">
    <img src="https://img.shields.io/static/v1?label=nonebot&message=v2rc1%2B&color=green" alt="nonebot2">
  </a>
  <img src="https://img.shields.io/static/v1?label=python+&message=3.8%2B&color=blue" alt="python">
</p>

## 开发者信息

- 网名昵称 nikiss，插件反馈 QQ 群 226462236，插件有问题到群里反馈响应更快哦
- <img width="100" src="https://avatars.githubusercontent.com/u/31379266"/>

## 简介

可以动态增删网络上的图片 API 接口，也可以载入本地图库链接对外提供图片 API 接口，支持接口分类管理，不再受限于单个 API 出图。

<img width="300" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_setu_customization/readme_img/tutu_test.jpg"/>

## 安装

使用 nb-cli 安装

```bash
# 如果没找到这个插件，使用nb plugin list 刷新缓存
nb plugin install nonebot_plugin_setu_customization
```

或者  
直接把插件 clone 下来，把 nonebot_plugin_setu_customization 文件夹放进去 plugins 目录

## 配置

在 bot 对应的.env 文件修改

```bash
# 均为选填项，自己按需求填，不需要的就不要写进配置！

# 机器人的QQ号列表，如果有多个bot连接，会按照填写的list，左边的机器人QQ优先级最高 1234 > 5678 > 6666，会自动切换
# 如果不填该配置则由第一个连上的bot响应
tutu_bot_qqnum_list = [1234, 5678, 6666]
# 图图命令CD时间（秒）
tutu_cooldown = 3
# 本地图片库的路径
tutu_local_api_path = data/tutu_local_img_lib/
# 插件数据文件名
tutu_data_filename = tutu_data.json
# pixiv图片反代地址，自己可以看看哪个快用哪个 如果默认返回的地址够快就不用 https://i.pixiv.re/ 、 https://i.pixiv.cat/ 、 https://i.loli.best/
tutu_pixiv_proxy = https://i.pixiv.re/
# http代理地址，如 http://127.0.0.1:1234
tutu_http_proxy = http://127.0.0.1:1234
```

## 目录

data/tutu_data.json 存储插件信息
data/tutu_local_img_lib/ 存储用户自己上传的图片地址文件

## 命令

|          指令          |                                        说明                                        |
| :--------------------: | :--------------------------------------------------------------------------------: |
|      图图插件帮助      |                                      帮助菜单                                      |
|          图图          | 出图，如果后面接类型可以指定图库类型，如“图图二次元”（好友私聊，群聊要添加白名单） |
| （下面都是管理员命令） |                               （发送命令有使用格式）                               |
|     图图插件群管理     |                                    增删群白名单                                    |
|  图图插件刷新本地图库  |                                    刷新本地图库                                    |
|    图图插件接口管理    |                                   增删 API 接口                                    |
|    图图插件接口测试    |                            测试接口连接情况和返回的数据                            |
|      插件图片测试      |                              测试某张图能否正常发出来                              |

## 使用示例、导入 api 和图片库

<img width="600" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_setu_customization/readme_img/api_mg.jpg"/>

接口不一定能用或稳定使用，这些只是以前找的接口，如果访问不了可以试试挂梯子  
**二次元图片 api**  
https://image.anosu.top/pixiv/direct
https://api.lolicon.app/setu/v2
https://api.anosu.top/img/?sort=setu
https://api.anosu.top/img/?sort=pixiv&size=original

**R18 图片 api**  
https://setu.yuban10703.xyz/setu?r18=1
https://image.anosu.top/pixiv/direct?r18=1
https://api.lolicon.app/setu/v2?r18=1
https://api.anosu.top/img/?sort=r18&size=original

**三次元图片 api**  
没收集到好的，但是我爬了很多，在仓库的 tutu_local_img_lib 文件夹，下载放进去 data/tutu_local_img_lib/里面，没事来看看有没有更新，里面也有二次元的

**本地图片库**  
即 data/tutu_local_img_lib/中的图片，放入图片地址文件后，使用命令“图图刷新本地图库”进行载入
<img width="600" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_setu_customization/readme_img/local_img_lib.jpg"/>

```bash
# 添加一个接口到二次元类型接口
图图插件接口管理 二次元 + https://api.lolicon.app/setu/v2
# 添加一个本地图片库接口到三次元类型接口
图图插件接口管理 三次元 + 本地图库self_cosplay
```

## 更新日志

### 2025/02/26 \[v2.0.0]

- httpx 更换为 aiohttp
- 精简大量代码，移除 socks 代理、网页访问、批量增加 api、合并发图、自动爬图等（反正以现在的文档介绍为准）

### 2024/6/25 \[v1.8.0]

- 优化 readme
- 修改插件元数据

### 2023/3/31 \[v1.7.0]

- 优化 readme
- 有个 bug 忘记修了
- 图片下载超时时间从 30 秒改为 10 秒
- 修复了一个导致图片发送慢的究极傻逼逻辑，

### 2023/3/21 \[v1.6.2]

- 修复 readme 里的错误
- 更换默认 pixiv 反代，之前的挂了（咋没人告诉我

### 2023/1/24 \[v1.6.0]

- 修复多 bot 处理 bug
- 移除搜图功能

### 2023/1/23 \[v1.5.1]

- 恢复搜图功能，使用 pixivpy 调用 P 站的接口完成搜图功能 https://github.com/upbit/pixivpy
- 优化搜图前端界面

### 2023/1/16 \[v1.4.9]

- 最低 python 版本兼容至 3.8
- 默认字体大小从 16 改到 18

### 2023/1/16 \[v1.4.8]

- 换个好看的字体

### 2023/1/15 \[v1.4.7]

- 依赖错误修复
- 增加单次图片发送数量设置
- 优化多 bot 逻辑，机器人 qq 号配置改为可选

### 2023/1/14 \[v1.4.5]

- 依赖错误修复，优化逻辑

### 2023/1/9 \[v1.4.3]

- 页面细节优化

### 2023/1/8 \[v1.4.2]

- 增加 P 站搜图功能（需要公网服务器网页访问结果），优化图片下载状态判断
- P 站搜图功能基础上增加网页预览 http://127.0.0.1:8080/soutu （具体域名和端口看你 nb 绑定的地址）

### 2023/1/4 \[v1.3.1]

- 增加本地下图和远端下图配置，优化 api 请求逻辑

### 2023/1/4 \[v1.2.2]

- 出图改为 nb 下载好再发送，优化大量细节，修 bug

### 2023/1/3 \[v1.1.1]

- 优化接口管理功能

### 2023/1/3 \[v1.1.0]

- 增加批量导入 api

### 2023/1/3 \[v1.0.0]

- 发布插件
