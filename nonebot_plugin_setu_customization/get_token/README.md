python get_pixiv_refresh_token.py  
运行脚本，然后会打开浏览器让你填账号密码登录，登陆前先按F12  
登陆后，在网络日志那搜索callback，找到如下图的链接，右键复制    
<img width="300" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_setu_customization/get_token/callback.jpg"/>  
回去框框里粘贴链接，就能获取到refresh token了  
<img width="300" src="https://raw.githubusercontent.com/nikissXI/nonebot_plugins/main/nonebot_plugin_setu_customization/get_token/zhantie.jpg"/>  
插件里面用的client id和client secret是这个脚本里的，所以不用管，如果是其他方式获取的自己去改  
搜图的按热度排序是需要高级会员的