# astrbot plugin for ntfy
[![npm](https://img.shields.io/npm/v/@astrbot/plugin-ntfy?style=flat-square)](https://www.npmjs.com/package/@astrbot/plugin-ntfy)
[![npm](https://img.shields.io/npm/dt/@astrbot/plugin-ntfy?style=flat-square)](https://www.npmjs.com/package/@astrbot/plugin-ntfy)
[![GitHub license](https://img.shields.io/github/license/astrbot/plugin-ntfy?style=flat-square)]()  
AstrBot 连接 ntfy 插件, 可以发送或者订阅接收 ntfy 消息。

An [astrbot](https://astrbot.app) plugin for the [ntfy](https://ntfy.sh), which can be used to connect to ntfy and publish or receive ntfy messages.

## usage
1. Install the plugin in astrbot:  
在 astrbot 中安装插件:

2. Configure the plugin:
配置插件:
- `ntfyUrl`: The ntfy server URL, default is `https://ntfy.sh`.
- `ntfyTopic`: The ntfy topic to subscribe or publish messages, default is `astrbot`.
- `ntfyAuth`: The ntfy authentication token, if required.
- `ntfySubscribe`: Whether to subscribe to the ntfy topic, default is `false`.