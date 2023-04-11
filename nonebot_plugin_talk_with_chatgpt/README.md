<p align="center">
  <a href="https://v2.nonebot.dev/store">
  <img src="https://user-images.githubusercontent.com/44545625/209862575-acdc9feb-3c76-471d-ad89-cc78927e5875.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
</p>

<div align="center">

# nonebot_plugin_talk_with_chatgpt

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
直接把插件clone下来放进去plugins文件夹，如果没有装httpx需要装一下

## 配置
在bot对应的.env文件修改

#### 必填项
```bash
# 填上面获取到的accessToken
talk_with_chatgpt_accesstoken = xxxxxxxxxxx
# http代理，不支持socks代理，默认空值
talk_with_chatgpt_http_proxy = http://127.0.0.1:7890
```

#### 大概率用得上的选填项
```bash
# 触发对话的命令前缀，群聊直接艾特也可以触发
talk_with_chatgpt_start_cmd = talk
# 重置对话的命令，就是清空聊天记录
talk_with_chatgpt_clear_cmd = clear
# 设置预设的命令前缀
talk_with_chatgpt_prompt_cmd = prompt
# 处理消息时是否提示，默认开
talk_with_chatgpt_reply_notice = true
# 群聊是否共享会话，默认关
talk_with_chatgpt_group_share = false
```

#### 可能用得上的选填项
```bash
# 请求超时时间，回答生成的时间也要算在这里面的，所以不能太短，默认60秒
talk_with_chatgpt_timeout = 60
# chatgpt反代地址，默认 https://bypass.churchless.tech/api/conversation
talk_with_chatgpt_api_addr = https://bypass.churchless.tech/api/conversation
# chatgpt模型，默认 text-davinci-002-render-sha，更多模型请参考 https://platform.openai.com/docs/models
talk_with_chatgpt_api_model = text-davinci-002-render-sha
```

#### 基本用不上的选填项
```bash
# 机器人的QQ号列表，选填
# 如果有多个bot连接，会按照填写的list，左边的机器人QQ优先级最高 1234 > 5678 > 6666，会自动切换
# 如果不填该配置则由第一个连上的bot响应，所以单bot连可以不填
talk_with_chatgpt_bot_qqnum_list = [1234, 5678, 6666]
# 插件数据文件名，默认./data/talk_with_chatgpt.json
talk_with_chatgpt_data = talk_with_chatgpt.json
```

## 插件命令（均可修改！） 
| 指令 | 说明 |
|:-----:|:----:|
| talk | 开始对话，群里@机器人也可以 |
| clear | 重置对话（不会重置预设） |
| prompt | 设置预设（人格），设置后会重置对话 |

## 更新日志
### 2023/4/11 \[v0.1.0]

* 发布第一版较简陋的插件
