import time
from datetime import datetime
from python_ntfy import NtfyClient
from threading import th

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.api.message_components import *
import aiohttp


@register("astrbot_plugin_ntfy_client", "Wanxp", "一个连接ntfy的客户端，可以收发消息", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.message_received = False
        self.timer = None
        self.config = config
        self._running = False
        self._conn_lock = asyncio.Lock()
        self._is_connected = False
        self._current_time_messaged = datetime.now().timestamp()

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        if not self._check_config():
            logger.error("ntfy 配置不完整，请检查配置文件")
            return False
        if self._running:
            logger.warning("插件已经在运行中，无法重复初始化")
            return False
        self.init_listener()
        self._running = True

    def init_listener(self):
        """初始化监听器"""
        if not self._check_config():
            logger.error("ntfy 配置不完整，无法接收消息")
            return
        host = self.config["ntfy"].get("host")
        subscribe_topic = self.config["ntfy"].get("subscribe_topic")
        token = self.config["ntfy"].get("token")
        os.environ["NTFY_TOKEN"] = token
        self._client = NtfyClient(server=host, topic=subscribe_topic)
        self.timer = th.Timer(10.0, self.receive_messages)
        self.timer.start()

    async def receive_messages(self):
        """接收消息的异步方法"""
        if self._running is False:
            logger.warning("插件未运行，无法接收消息")
            return
        if self.message_received:
            logger.info("正在等待新消息...")
            return
        self.message_received = True
        messages = self._client.get_cached_messages(since=self._current_time_messaged, scheduled=False)
        if not messages:
            self.message_received = False
            logger.info("没有新消息")
            return
        last_message = ''
        for message in messages:
            self._current_time_messaged = message["time"]
            sender_id = message.get("sender", "unknown")
            sender_name = message.get("title", "未知发送者")
            message_str = message.get("message", "")
            if last_message == message_str:
                logger.info(f"重复消息，跳过处理: {message_str}")
                continue

            last_message = message_str
            # 防止过份频繁发送消息
            time.sleep(0.5)
            yield self.context.get_event_queue().plain_result(f"发送者:{sender_id}\nmessage:{message_str}")
        self.message_received = False

    def _check_config(self):
        """检查配置是否完整"""
        ntfy_config = self.config.get("ntfy", {})
        required_keys = ["host", "token", "publish_topic", "sender", "subscribe_topic", "receiver"]
        for key in required_keys:
            if key not in ntfy_config or not ntfy_config[key]:
                logger.error(f"ntfy 配置缺少必要的键: {key}")
                return False
        return True

    async def _send_to_ntfy(self, sender_id: str, sender_name: str, message_str: str, event: AstrMessageEvent):
        host = self.config["ntfy"].get(
            "host"
        )  # 从配置中获取 ntfy 的 host
        sender = self.config["ntfy"].get(
            "sender"
        )  # 从配置中获取 ntfy 的sender ID 列表
        sender_ids = (
            sender.split(",") if sender else []
        )  # 如果配置中有 sender ，则将其分割成列表
        isSender = False
        print(f"当前用户 {sender_name} ({sender_id}) 尝试调用 ntfy 插件")
        for sender_id in sender_ids:
            if str(sender_id).__contains__(sender_id.strip()):
                isAdmin = True
                break
        if isSender is False:
            logger.warning(
                f"用户 {sender_name} ({sender_id}) 没有权限调用 ntfy 插件"
            )
            return
        token = self.config["ntfy"].get("token")  # 从配置中获取 n8n 的 webhook URL
        public_topic = self.config["ntfy"].get("publish_topic")  # 从配置中获取 发布地址,逗号分割的

        # 移除掉第一个'n8n'
        message_str = message_str.replace(
            "ntfy", "", 1
        ).strip()  # 去掉指令名，保留用户输入的内容
        topic = public_topic.strip()
        if not topic:
            return
        try:
            await self._ensure_connection()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        url=f'{host}/{topic}/publish?token={token}&message={message_str}'
                ) as response:
                    if response.status != 200:
                        logger.error(f"调用 ntfy 发布消息 失败: {await response.text()}")
                        yield event.plain_result(
                            f"调用 ntfy :{topic} 失败，请检查配置或网络连接。"
                        )
                        return

                    logger.info(f"调用 ntfy  :{topic} 成功: {await response.text()}")
                    yield event.plain_result(f"调用 ntfy  :{topic} 成功")

        except aiohttp.ClientError as e:
            logger.error(f"aiohttp 请求错误: {e}")
            yield event.plain_result(
                f"调用 ntfy :{topic} 时发生错误，请检查网络连接。错误详情: {str(e)}"
            )

        except Exception as e:
            logger.error(f"未捕获的异常: {e}")
            yield event.plain_result(
                f"调用 ntfy :{topic} 时发生未捕获的异常。错误详情: {str(e)}"
            )

    # 注册指令的装饰器。指令名为 ntfy_test 。注册成功后，发送 `/ntfy_test` 就会触发这个指令，并回复 `已发送消息到 ntfy_test`。
    @filter.command("ntfy_test")
    async def test_gotify(self, event: AstrMessageEvent):
        """测试 ntfy 连接的指令"""
        if not self._check_config():
            yield event.plain_result("❌ ntfy 配置不完整，请检查配置")
            return

        # 构建测试消息
        test_message = {
            "title": "AstrBot ntfy 插件测试",
            "message": f"测试消息发送成功！\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n发送者：{event.get_sender_name()}",
            "priority": 5
        }

        success = await self._send_to_ntfy(event.session_id, event.get_sender_name, test_message, event)

        if success:
            yield event.plain_result("✅ ntfy 测试消息发送成功！")
        else:
            yield event.plain_result("❌ ntfy 测试消息发送失败，请检查配置和网络连接")

    # 注册指令的装饰器。指令名为 ntfy 。注册成功后，发送 `/ntfy` 就会触发这个指令，并回复 `已发送消息到 ntfy`。
    @filter.command("ntfy")
    async def call_ntfy(self, event: AstrMessageEvent):
        """这是一个 发送消息到ntfy 的指令"""  # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        sender_name = event.get_sender_name()
        message_str = event.message_str  # 用户发的纯文本消息字符串

    async def _ensure_connection(self):
        async with self._conn_lock:
            if not self._is_connected:
                self._is_connected = True
                logger.info("HfCtrl连接已建立")  # 网页6的日志监控特性

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        self._running = False
