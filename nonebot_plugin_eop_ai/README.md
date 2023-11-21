<p align="center">
  <a href="https://v2.nonebot.dev/store">
  <img src="https://user-images.githubusercontent.com/44545625/209862575-acdc9feb-3c76-471d-ad89-cc78927e5875.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
</p>

<div align="center">

# nonebot_plugin_eop_ai

_✨ Nonebot2 一款调用eop api的AI聊天插件 ✨_

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
- nikiss，个人QQ 1299577815，插件反馈QQ群 226462236，插件有问题到群里反馈响应更快哦
- <img width="100" src="https://avatars.githubusercontent.com/u/31379266"/>  

## 简介
本插件需要调用一个逆向poe前端写的后端，也是我负责开发维护的，[eop-next-api仓库](https://github.com/nikissXI/eop-next-api)，前端不是我开发的，目前尚未开源。  
> 后端可以自行部署，或者付费租用我的，目前价格10元/月，带前端，免梯直连，图省事且不差钱的可以加我QQ129957715了解。
> 目前插件功能尚不完善，建议配合付费租用后的前端使用。  

<img width="100%" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_eop_ai/readme_img/1.jpg"/>  

## 功能列表

> 以下未勾选功能仅表示未来可能开发的方向，不代表实际规划进度，具体开发事项可能随时变动
> 勾选: 已实现功能；未勾选: 正在开发 / 计划开发 / 待定设计

- [x] 基本的对话功能，支持文字或图片回复，如使用图片回复调用mozilla的剪切板查看回复的纯文字
- [x] 配合前端进行会话管理
- [x] 登陆失败时自动尝试重新登录
- [ ] 默认会话设置
- [ ] 预设管理
- [ ] 更完善的会话管理

## 安装

使用nb-cli安装
```bash
nb plugin install nonebot_plugin_eop_ai
```

或者  
直接把插件clone下来放进去plugins文件夹，依赖库自己补全  

可选安装ujson进行解析json数据  

## 配置
在bot对应的.env文件修改，文档中的均是默认值。  

#### 必填项
```bash
# eop后端url地址，如 https://api.eop.com
eop_ai_base_addr = 
# eop登录账号密码
eop_ai_user = username
eop_ai_passwd = password
```

#### 大概率用得上的选填项
```bash
# 代理地址，当前仅支持http代理
eop_ai_http_proxy_addr = http://127.0.0.1:7890
# AI回答默认输出类型，填1/2/3其中一个数字，1=文字，2=图片，3=图片+文字（文字在网页粘贴板）
eop_ai_reply_type = 3
# 图片输出时，图片的宽度
eop_ai_img_width = 400
# 处理消息时是否提示（不嫌烦或测试的时候可以打开）
eop_ai_reply_notice = false
# 群聊是否共享会话
eop_ai_group_share = true
# 是否默认允许所有群聊使用，否则需要使用命令启用（默认 /eopai）
eop_ai_all_group_enable = true
# 群聊中，机器人的回复是否艾特提问用户，如果eop_ai_group_share为false该选项强制为true
eop_ai_reply_at_user = true
```

#### 如果要修改触发命令就填
```bash
# 群聊艾特和发bot昵称是否响应（需要先启用该群的eop ai）
eop_ai_talk_tome = true
# 如果关闭所有群聊使用，启用该群的命令
eop_ai_group_enable_cmd = /eopai
# 触发对话的命令前缀，如果eop_ai_talk_tome为true直接艾特即可
eop_ai_talk_cmd = /talk
# 私聊沉浸式对话触发命令
eop_ai_talk_p_cmd = /hi
# 重置对话，就是清空聊天记录
eop_ai_reset_cmd = /reset
# AI回答输出类型切换，仅对使用命令的会话生效
eop_ai_reply_type_cmd = /reply
```

#### 大概率用不上的选填项
```bash
# 机器人的QQ号列表，选填
# 如果有多个bot连接，会按照填写的list，左边的机器人QQ优先级最高 1234 > 5678 > 6666，会自动切换
# 如果不填该配置则由第一个连上的bot响应，所以单bot连可以不填，写 ["all"]则所有机器人均响应
eop_ai_bot_qqnum_list = [1234, 5678, 6666]
# 插件数据文件名，默认./data/eop_ai.json
eop_ai_data = eop_ai.json
```

## 插件命令（均可修改！） 
| 指令 | 说明 |
|:-----:|:----:|
| /eopai | 如果eop_ai_group_enable_cmd为false，则用该命令启用 |
| /talk | 开始对话，默认群里@机器人也可以 |
| /hi | 沉浸式对话（仅限私聊） |
| /reset | 重置对话 |

## 会话管理
如果租了了开发者的后端，可以使用配套的前端进行会话管理。创建会话别名为{QQ号}或{群号}-share，插件会自动调用那个会话。  
<img width="400" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_eop_ai/readme_img/4.jpg"/>  

## 更新日志
### 2023/10/8 \[v0.1.5]

* 更新命令/reply用于切换输出模式

### 2023/10/7 \[v0.1.4]

* 优化转图片输出的速度

### 2023/10/6 \[v0.1.3]

* 优化md转图片的格式

### 2023/10/6 \[v0.1.2]

* 参考项目[nonebot-plugin-naturel-gpt](https://github.com/KroMiose/nonebot_plugin_naturel_gpt)，增加utils.py中的gen_chat_text函数
* 优化响应器逻辑

### 2023/10/5 \[v0.1.1]

* 发布插件
