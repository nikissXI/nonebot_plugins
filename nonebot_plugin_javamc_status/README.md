<!-- [![tests](https://github.com/ffreemt/nonebot-plugin-guess-game/actions/workflows/routine-tests.yml/badge.svg)](https://github.com/ffreemt/nonebot-plugin-guess-game/actions/workflows/routine-tests.yml) -->
# nonebot_plugin_javamc_status
[![nonebot2](https://img.shields.io/static/v1?label=nonebot&message=v2rc1%2B&color=green)](https://v2.nonebot.dev/)[![python](https://img.shields.io/static/v1?label=python+&message=3.9%2B&color=blue)](https://img.shields.io/static/v1?label=python+&message=3.7%2B&color=blue)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Nonebot2查询JAVA MC服务器在线信息插件

### 安装

使用nb-cli安装
```bash
nb plugin install nonebot_plugin_javamc_status
```

或者  
直接把插件clone下来放进去plugins文件夹

### 使用

添加了服务器信息后，会在bot根目录下的data目录创建一个mc_status_data.json文件，用于存储插件信息

### 默认命令  
**信息** - 所有人都能使用，查看当前群添加的服务器状态  
**添加服务器** - 字面意思，bot超级管理员用  
**删除服务器** - 字面意思，bot超级管理员用  
**信息数据** - 查看已添加的群和服务器信息，bot超级管理员用  

### 定制

自己看代码改啦！