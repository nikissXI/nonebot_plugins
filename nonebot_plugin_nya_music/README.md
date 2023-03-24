<p align="center">
  <a href="https://v2.nonebot.dev/store">
  <img src="https://user-images.githubusercontent.com/44545625/209862575-acdc9feb-3c76-471d-ad89-cc78927e5875.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
</p>

<div align="center">

# nonebot_plugin_nya_music

_✨ Nonebot2 喵喵点歌 ✨_

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

## 简介
闲的没事（bushi）整个点歌插件玩玩，做的比较粗糙，但能用  
可以搜索和下载歌曲  
<img width="500" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_nya_music/readme_img/pic1.jpg"/>

## 安装

使用nb-cli安装
```bash
nb plugin install nonebot_plugin_nya_music
```

或者  
直接把插件clone下来放进去plugins文件夹，但要记得装Pillow和httpx库

## 配置
在bot对应的.env文件修改

```bash
# 每页返回的结果数量，选填
nya_music_page_items = 10

# 机器人的QQ号列表，选填
# 如果有多个bot连接，会按照填写的list，左边的机器人QQ优先级最高 1234 > 5678 > 6666，会自动切换
# 如果不填该配置则由第一个连上的bot响应
nya_music_bot_qqnum_list = [1234, 5678, 6666]
```

## 插件命令  
| 指令 | 说明 |
|:-----:|:----:|
| 点歌 | 你发一下就知道啦 |

## 更新日志
### 2023/3/25 \[v0.1.3]

* 修复小bug

### 2023/3/24 \[v0.1.0]

* 发布插件