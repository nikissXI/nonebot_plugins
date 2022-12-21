<!-- [![tests](https://github.com/ffreemt/nonebot-plugin-guess-game/actions/workflows/routine-tests.yml/badge.svg)](https://github.com/ffreemt/nonebot-plugin-guess-game/actions/workflows/routine-tests.yml) -->
# nonebot-plugin-mc-status
[![nonebot2](https://img.shields.io/static/v1?label=nonebot&message=v2rc1%2B&color=green)](https://v2.nonebot.dev/)[![python](https://img.shields.io/static/v1?label=python+&message=3.9%2B&color=blue)](https://img.shields.io/static/v1?label=python+&message=3.7%2B&color=blue)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Nonebot2查询JAVA MC服务器在线信息插件

### 安装

```bash
pip install nonebot-plugin-guess
# pip install nonebot-plugin-guess -U  # 升级到最新版
```
or
```bash
poetry add nonebot-plugin-guess
# poetry add nonebot-plugin-guess@latest   # 升级到最新版
```
or
```
poetry add git+https://github.com/ffreemt/nonebot-plugin-guess-game.git
```
or
```
pip install git+https://github.com/ffreemt/nonebot-plugin-guess-game.git
```


### 使用
```python
# bot.py
...
nonebot.load_plugin("nonebot_plugin_guess")
...
```
添加了服务器信息后，会在bot根目录下的data目录创建一个mc_status_data.json文件，用于存储插件信息

### 默认命令  
**信息** - 所有人都能使用，查看当前群添加的服务器状态  
**添加服务器** - 字面意思，bot超级管理员用  
**删除服务器** - 字面意思，bot超级管理员用  
**信息数据** - 查看已添加的群和服务器信息，bot超级管理员用  

### 定制

自己看代码改啦！