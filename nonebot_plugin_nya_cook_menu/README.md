<p align="center">
  <a href="https://v2.nonebot.dev/store">
  <img src="https://user-images.githubusercontent.com/44545625/209862575-acdc9feb-3c76-471d-ad89-cc78927e5875.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
</p>

<div align="center">

# nonebot_plugin_nya_cook_menu

_✨ Nonebot2 喵喵自记菜谱 ✨_

</div>
<p align="center">
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="license">
  </a>
  <a href="https://v2.nonebot.dev/">
    <img src="https://img.shields.io/static/v1?label=nonebot&message=v2rc1%2B&color=green" alt="nonebot2">
  </a>
  <img src="https://img.shields.io/static/v1?label=python+&message=3.9%2B&color=blue" alt="python">
</p>

## 简介
我和老婆经常做菜忘记以前某个菜咋做，于是就整了这个插件记录一下我们的菜谱，顺便发到商店，嘿嘿~  
<img width="500" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_nya_cook_menu/readme_img/caipu.jpg"/>

## 安装

使用nb-cli安装
```bash
nb plugin install nonebot_plugin_nya_cook_menu
```

或者  
直接把插件clone下来放进去plugins文件夹

## 配置
在bot对应的.env文件修改

```bash
# 使用用户qq号，必填
nya_cook_user_list: list[int] = [1234, 5678]
# 机器人的QQ号列表，选填
# 如果有多个bot连接，会按照填写的list，左边的机器人QQ优先级最高 1234 > 5678 > 6666，会自动切换
# 如果不填该配置则由第一个连上的bot响应
nya_cook_bot_qqnum_list = ['1234','5678','6666']
```

## 插件命令  
| 指令 | 说明 |
|:-----:|:----:|
| 菜谱 | 你发一下就知道啦 |

## 更新日志
### 2023/1/16 \[v0.1.3]

* 最低python版本兼容至3.8
* 默认字体大小从16改到18

### 2023/1/16 \[v0.1.1]

* 发布插件