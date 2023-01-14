# nonebot_plugin_mc_server_status
[![nonebot2](https://img.shields.io/static/v1?label=nonebot&message=v2rc1%2B&color=green)](https://v2.nonebot.dev/)[![python](https://img.shields.io/static/v1?label=python+&message=3.9%2B&color=blue)](https://img.shields.io/static/v1?label=python+&message=3.7%2B&color=blue)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Nonebot2查询MC服务器在线信息插件  
支持Java和Bedrock服务器  

### 安装

使用nb-cli安装
```bash
nb plugin install nonebot_plugin_mc_server_status
```

或者  
直接把插件clone下来放进去plugins文件夹，记得把依赖装上 pip install mcstatus  

### 使用

添加了服务器信息后，会在bot根目录下的data目录创建一个mc_status_data.json文件，用于存储插件信息  
在bot对应的.env文件修改

```bash
# 机器人的QQ号（由于开发者多gocq连接，所以有这个设置）
mc_status_bot_qqnum = 114514
# 管理员的QQ号（别问我为什么要另外写）
mc_status_admin_qqnum = 114514
```

### 插件命令  
| 指令 | 说明 |
|:-----:|:----:|
| 信息|所有人都能使用，查看当前群添加的服务器状态|
| 添加服务器|字面意思，bot超级管理员用|
| 删除服务器|字面意思，bot超级管理员用|
| 信息数据|查看已添加的群和服务器信息，bot超级管理员用|

### 使用截图
<img width="600" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_mc_server_status/readme_img/xinxi.jpg"/>

### 定制

自己看代码改啦！