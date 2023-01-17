<p align="center">
  <a href="https://v2.nonebot.dev/store">
  <img src="https://user-images.githubusercontent.com/44545625/209862575-acdc9feb-3c76-471d-ad89-cc78927e5875.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
</p>

<div align="center">

# nonebot_plugin_easy_translate

_✨ Nonebot2 简单易用谷歌翻译插件，免key！ ✨_

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
使用了sena-nana大佬给的接口，他的仓库
<a href="https://github.com/sena-nana/nonebot-plugin-novelai/blob/main/nonebot_plugin_novelai/extension/translation.py">sena-nana/nonebot-plugin-novelai</a>，不需要使用梯子和api key就能使用的翻译插件

<img width="500" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_easy_translate/readme_img/fanyi.jpg"/>

## 安装

使用nb-cli安装
```bash
nb plugin install nonebot_plugin_easy_translate
```

或者  
直接把插件clone下来放进去plugins文件夹

## 可选配置
在bot对应的.env文件修改

```bash
# 机器人的QQ号列表，如果有多个bot连接，会按照填写的list，左边的机器人QQ优先级最高 1234 > 5678 > 6666，会自动切换
# 如果不填该配置则由第一个连上的bot响应
easy_translate_bot_qqnum_list = [1234,5678,6666]
```

## 插件命令  
| 指令 | 说明 |
|:-----:|:----:|
| 翻译 | 你发一下就知道啦 |

## 更新日志
### 2023/1/16 \[v0.1.3]

* 最低python版本兼容至3.8

### 2023/1/15 \[v0.1.2]

* 发布插件