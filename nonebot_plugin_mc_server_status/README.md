<p align="center">
  <a href="https://v2.nonebot.dev/store">
  <img src="https://user-images.githubusercontent.com/44545625/209862575-acdc9feb-3c76-471d-ad89-cc78927e5875.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
</p>

<div align="center">

# nonebot_plugin_mc_server_status

_✨ Nonebot2查询MC服务器在线信息插件 ✨_

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
使用mcstatus库，支持Java和Bedrock服务器的服务器查询。   

<img width="300" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_mc_server_status/readme_img/xinxi.jpg"/>

## 安装

使用nb-cli安装
```bash
nb plugin install nonebot_plugin_mc_server_status
```

或者  
直接把插件clone下来放进去plugins文件夹，记得把依赖装上 pip install mcstatus  

## 使用

添加了服务器信息后，会在bot根目录下的data目录创建一个mc_status_data.json文件，用于存储插件信息  
在bot对应的.env文件修改

```bash
# 管理员的QQ号（别问我为什么要另外写）
mc_status_admin_qqnum = 114514

# 可选配置
# 机器人的QQ号列表，如果有多个bot连接，会按照填写的list，左边的机器人QQ优先级最高 1234 > 5678 > 6666，会自动切换
# 如果不填该配置则由第一个连上的bot响应
tutu_bot_qqnum_list = [1234, 5678, 6666]
```

## 插件命令  
| 指令 | 说明 |
|:-----:|:----:|
| 信息|所有人都能使用，查看当前群添加的服务器状态，需要加命令前缀，默认/|
| 信息数据|查看已添加的群和服务器信息，bot超级管理员用，需要加命令前缀，默认/|
| 添加服务器|字面意思，bot超级管理员用，一个群可以添加多个服务器|
| 删除服务器|字面意思，bot超级管理员用|

## 更新日志
### 2023/2/11 \[v0.2.9]

* 信息和信息数据的增加命令前缀

### 2023/1/24 \[v0.2.8]

* 修复多bot处理bug

### 2023/1/20 \[v0.2.7]

* gocq插件版不支持base64图片发送，改为BytesIO发送服务器图标

### 2023/1/17 \[v0.2.4]

* 又忘记删东西导致无法运行，已修复

### 2023/1/16 \[v0.2.3]

* 最低python版本兼容至3.8

### 2023/1/15 \[v0.2.2]

* 优化多bot逻辑，机器人qq号配置改为可选

### 2023/1/15 \[v0.2.1]

* 插件重构