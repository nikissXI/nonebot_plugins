<p align="center">
  <a href="https://v2.nonebot.dev/store">
  <img src="https://user-images.githubusercontent.com/44545625/209862575-acdc9feb-3c76-471d-ad89-cc78927e5875.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
</p>

<div align="center">

# nonebot_plugin_talk_with_chatgpt
# 开发者的chatgpt账号被封了后就没用过了，所以不清楚该插件还能不能使用

_✨ Nonebot2 一个简单易用的chatgpt插件 ✨_

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

# 注意！
使用本插件需要自建反代服务器来绕过403盾，推荐使用[潘多拉next](https://github.com/pandora-next/deploy)搭建反代，免梯直连访问稳定，很方便，使用代理模式启动，接口路径为/backend-api/conversation   

## 简介
发现商店里没有基于accessToken登录的chatgpt插件，也没看到喜欢的插件，就花一天时间自己写了一个。参考了[chatgpt web](https://github.com/Chanzhaoyu/chatgpt-web)这个开源项目，使用了社区上的反代，如果要使用其他反代可以参考这个项目里的。  
<img width="100%" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_talk_with_chatgpt/readme_img/1.jpg"/>  

插件功能相对其他的来说比较简单，因此也比较易用，获取accessToken并配置代理即可使用，[accessToken获取方式](https://chat.openai.com/api/auth/session)，accessToken字段的值就是了。如果有其他想法或建议欢迎提出，欢迎pr。

## 安装

使用nb-cli安装
```bash
nb plugin install nonebot_plugin_talk_with_chatgpt
```

或者  
直接把插件clone下来放进去plugins文件夹，如果没有装httpx和ujson需要装一下

## 配置
在bot对应的.env文件修改，文档中的均是默认值

#### 必填项
```bash
# 填上面获取到的accessToken
talk_with_chatgpt_accesstoken = xxxxxxxxxxx
# chatgpt反代地址，默认 
talk_with_chatgpt_api_addr = 
```

#### 大概率用得上的选填项
```bash
# 默认无代理，视api情况看是否需要梯子。这个内置的反代我测过是不需要梯子的。
talk_with_chatgpt_http_proxy = null

# 处理消息时是否提示
talk_with_chatgpt_reply_notice = true
# 群聊是否共享会话
talk_with_chatgpt_group_share = false
# 只允许超级管理员修改预设
talk_with_chatgpt_prompt_admin_only = true
# 是否默认允许所有群聊使用，否则需要使用命令启用
talk_with_chatgpt_all_group_enable = true
# 机器人的回复是否使用图片发送
talk_with_chatgpt_send_with_img = false
```

#### 如果要修改触发命令就填
```bash
# 群聊艾特是否响应
talk_with_chatgpt_talk_at = true
# 触发对话的命令前缀，默认群聊直接艾特也可以触发
talk_with_chatgpt_talk_cmd = /talk
# 私聊沉浸式对话触发命令
talk_with_chatgpt_talk_p_cmd = /hi
# 重置对话的命令，就是清空聊天记录
talk_with_chatgpt_reset_cmd = /reset
# 设置预设的命令前缀
talk_with_chatgpt_prompt_cmd = /prompt
# 如果关闭所有群聊使用，启用该群的命令
talk_with_chatgpt_group_enable_cmd = /chatgpt
```

#### 大概率用不上的选填项
```bash
# 敏感词屏蔽，默认不屏蔽任何词
talk_with_chatgpt_ban_word = ["示例词1", "示例词2"]
# 请求超时时间，回答生成的时间也要算在这里面的，所以不能太短，默认60秒
talk_with_chatgpt_timeout = 60
# chatgpt模型，默认 text-davinci-002-render-sha，更多模型请参考 https://platform.openai.com/docs/models
talk_with_chatgpt_api_model = text-davinci-002-render-sha

# 机器人的QQ号列表，选填
# 如果有多个bot连接，会按照填写的list，左边的机器人QQ优先级最高 1234 > 5678 > 6666，会自动切换
# 如果不填该配置则由第一个连上的bot响应，所以单bot连可以不填，写 ["all"]则所有机器人均响应
talk_with_chatgpt_bot_qqnum_list = [1234, 5678, 6666]
# 插件数据文件名，默认./data/talk_with_chatgpt.json
talk_with_chatgpt_data = talk_with_chatgpt.json
# 如果使用图片回复，字体大小
talk_with_chatgpt_font_size = 18
```

## 插件命令（均可修改！） 
| 指令 | 说明 |
|:-----:|:----:|
| /talk | 开始对话，默认群里@机器人也可以 |
| /hi | 沉浸式对话（仅限私聊） |
| /reset | 重置对话（不会重置预设） |
| /prompt | 设置预设（人格），设置后会重置对话 |
| /chatgpt | 如果talk_with_chatgpt_all_group_enable为false，则用该命令启用 |

## 更新日志
### 2023/11/23 \[v0.6.4]

* 更新readme，推荐使用潘多拉next的反代

### 2023/11/22 \[v0.6.3]

* 移除内置的社区反代，因为失效了，更新readme，提醒自建反代

### 2023/7/21 \[v0.6.2]

* [修复无法响应的问题](https://github.com/nikissXI/nonebot_plugins/issues/29)

### 2023/6/28 \[v0.6.1]

* 新增配置项 talk_with_chatgpt_send_with_img 和 talk_with_chatgpt_ban_word

### 2023/5/30 \[v0.5.0]

* 更换了自带预设“猫娘”的内容，新增配置项 talk_with_chatgpt_all_group_enable 和 talk_with_chatgpt_group_enable_cmd ，新增命令/chatgpt

### 2023/5/29 \[v0.4.3]

* [支持所有机器人响应命令](https://github.com/nikissXI/nonebot_plugins/issues/22)

### 2023/5/18 \[v0.4.2]

* [修复会话丢失不重置的问题](https://github.com/nikissXI/nonebot_plugins/issues/21)

### 2023/4/22 \[v0.4.1]

* [增加群聊at触发开关](https://github.com/nikissXI/nonebot_plugins/issues/21)

### 2023/4/21 \[v0.4.0]

* 更换了默认API，暂时能用，建议还是自己搭建API
* 新增多预设功能，内置三个预设：猫娘、魅魔、开发者模式
* 增加私聊沉浸式对话
* 优化大量细节

### 2023/4/11 \[v0.2.3]

* 发布第一版较简陋的插件，并修复了些小问题，细节很重要
