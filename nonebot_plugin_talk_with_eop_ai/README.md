<p align="center">
  <a href="https://v2.nonebot.dev/store">
  <img src="https://user-images.githubusercontent.com/44545625/209862575-acdc9feb-3c76-471d-ad89-cc78927e5875.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
</p>

<div align="center">

# nonebot_plugin_talk_with_eop_ai

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

## 简介
本插件需要调用一个逆向poe前端写的后端，也是我负责开发维护的，[eop-next-api仓库](https://github.com/nikissXI/eop-next-api)。  
后端可以自行部署，或者付费租用我的，目前价格15元/月，带前端，免梯直连，图省事且不差钱的可以加我QQ129957715了解。  
<img width="100%" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_talk_with_poe_ai/readme_img/1.jpg"/>  


## 安装

使用nb-cli安装
```bash
nb plugin install nonebot_plugin_talk_with_eop_ai
```

或者  
直接把插件clone下来放进去plugins文件夹，依赖库自己补全

## 配置
在bot对应的.env文件修改，文档中的均是默认值。  
poe登录凭证需要两个值，获取方法如下：  

注意：需要先手动create bot试试能不能创建。不同浏览器可能会有点不同，自己变通一下啦！两个值在安装好插件后，使用命令“/poeai auth”进行登录  

#### 大概率用得上的选填项
```bash
# 代理地址，支持http和socks代理，国内的话不用代理无法连接poe
talk_with_eop_ai_proxy = http://127.0.0.1:7890
# 处理消息时是否提示
talk_with_eop_ai_reply_notice = true
# 群聊是否共享会话
talk_with_eop_ai_group_share = false
# 只允许超级管理员修改预设
talk_with_eop_ai_prompt_admin_only = true
# 是否默认允许所有群聊使用，否则需要使用命令启用
talk_with_eop_ai_all_group_enable = true
# 机器人的回复是否使用图片发送
talk_with_eop_ai_send_with_img = false
```

#### 如果要修改触发命令就填
```bash
# 群聊艾特是否响应
talk_with_eop_ai_talk_at = true
# 触发对话的命令前缀，默认群聊直接艾特也可以触发
talk_with_eop_ai_talk_cmd = /talk
# 私聊沉浸式对话触发命令
talk_with_eop_ai_talk_p_cmd = /hi
# 重置对话的命令，就是清空聊天记录
talk_with_eop_ai_reset_cmd = /reset
# 设置预设的命令前缀
talk_with_eop_ai_prompt_cmd = /prompt
# 如果关闭所有群聊使用，启用该群的命令
talk_with_eop_ai_group_enable_cmd = /poeai
# 重连
talk_with_eop_ai_reconnect_cmd = /poeai re
# 录入登录凭证
talk_with_eop_ai_auth_cmd = /poeai auth
```

#### 大概率用不上的选填项
```bash
# 敏感词屏蔽，默认不屏蔽任何词
talk_with_eop_ai_ban_word = ["示例词1", "示例词2"]
# AI模型  chinchilla（ChatGPT），a2（Claude），beaver（ChatGPT4），a2_2（Claude-2-100k）
talk_with_eop_ai_api_model = chinchilla

# 机器人的QQ号列表，选填
# 如果有多个bot连接，会按照填写的list，左边的机器人QQ优先级最高 1234 > 5678 > 6666，会自动切换
# 如果不填该配置则由第一个连上的bot响应，所以单bot连可以不填，写 ["all"]则所有机器人均响应
talk_with_eop_ai_bot_qqnum_list = [1234, 5678, 6666]
# 插件数据文件名，默认./data/talk_with_eop_ai.json
talk_with_eop_ai_data = talk_with_eop_ai.json
# 如果使用图片回复，字体大小
talk_with_eop_ai_font_size = 18
```

## 插件命令（均可修改！） 
| 指令 | 说明 |
|:-----:|:----:|
| /talk | 开始对话，默认群里@机器人也可以 |
| /hi | 沉浸式对话（仅限私聊） |
| /reset | 重置对话（不会重置预设） |
| /prompt | 设置预设（人格），设置后会重置对话 |
| /poeai | 如果talk_with_eop_ai_all_group_enable为false，则用该命令启用 |
| /poeai re | eop ai 重连，有时候可能各种因素导致登陆失败 |
| /poeai auth | 修改登录凭证并重新登录 |

## 更新日志

### 2023/9/25 \[v0.1.0]

* 发布插件
