#!/usr/bin/env python
"""
通知器模块 - 发送消息通知到不同平台（Telegram, Discord, 飞书）
"""

import os
import sys
import json
import logging
import requests
import datetime
import time
from typing import Dict, List, Optional, Any, Union

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 尝试导入语音播报器
try:
    from utils.voice_broadcaster import VoiceBroadcaster
except ImportError as e:
    print(f"警告: 无法导入语音播报器: {e}")

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/notifier.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OptionNotifier:
    """期权交易通知器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化通知器
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config_path = config_path or os.path.join("config", "warmachine_community_config.json")
        self.config = self._load_config()
        
        # 配置各平台的通知设置
        self.telegram_config = self.config.get("telegram", {})
        self.discord_config = self.config.get("discord", {})
        self.feishu_config = self.config.get("feishu", {})
        
        # 是否启用各平台
        self.telegram_enabled = self.telegram_config.get("enabled", False)
        self.discord_enabled = self.discord_config.get("enabled", False)
        self.feishu_enabled = self.feishu_config.get("enabled", False)
        
        # 初始化语音播报器
        try:
            self.voice_broadcaster = VoiceBroadcaster(self.config)
        except:
            self.voice_broadcaster = None
            logger.warning("无法初始化语音播报器")
        
        # 通知计数
        self.notification_count = 0
        
        logger.info("通知器初始化完成")
    
    def _load_config(self) -> Dict:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                logger.info(f"已加载配置文件: {self.config_path}")
                return config
            else:
                # 尝试加载标准配置
                standard_config_path = os.path.join("config", "warmachine_config.json")
                if os.path.exists(standard_config_path):
                    with open(standard_config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    logger.info(f"已加载标准配置文件: {standard_config_path}")
                    return config
                else:
                    logger.warning("找不到配置文件，使用默认配置")
                    return {}
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def send_message(self, message: str, image_path: str = None) -> Dict:
        """
        发送消息到所有启用的平台
        
        Args:
            message: 消息内容
            image_path: 图片路径(可选)
            
        Returns:
            发送结果
        """
        results = {}
        
        # 更新通知计数
        self.notification_count += 1
        
        # 如果启用了Telegram，发送到Telegram
        if self.telegram_enabled:
            telegram_result = self._send_to_telegram(message, image_path)
            results["telegram"] = telegram_result
        
        # 如果启用了Discord，发送到Discord
        if self.discord_enabled:
            discord_result = self._send_to_discord(message, image_path)
            results["discord"] = discord_result
        
        # 如果启用了飞书，发送到飞书
        if self.feishu_enabled:
            feishu_result = self._send_to_feishu(message, image_path)
            results["feishu"] = feishu_result
        
        logger.info(f"发送了第 {self.notification_count} 条通知消息")
        return results
    
    def broadcast(self, message: str, with_voice: bool = False) -> Dict:
        """
        广播消息，包括可选的语音播报
        
        Args:
            message: 消息内容
            with_voice: 是否以语音播报
        
        Returns:
            广播结果
        """
        results = {}
        
        # 先发送文本消息
        text_results = self.send_message(message)
        results["text"] = text_results
        
        # 如果启用语音并且语音播报器可用
        if with_voice and self.voice_broadcaster:
            try:
                voice_result = self.voice_broadcaster.broadcast_message(message)
                results["voice"] = voice_result
                logger.info("发送了语音广播")
            except Exception as e:
                logger.error(f"语音广播失败: {e}")
                results["voice"] = {"success": False, "error": str(e)}
        
        return results
    
    def _send_to_telegram(self, message: str, image_path: str = None) -> Dict:
        """
        发送消息到Telegram
        
        Args:
            message: 消息内容
            image_path: 图片路径(可选)
            
        Returns:
            发送结果
        """
        try:
            bot_token = self.telegram_config.get("token")
            chat_id = self.telegram_config.get("chat_id")
            
            if not bot_token or not chat_id:
                logger.warning("Telegram配置不完整，跳过发送")
                return {"success": False, "error": "配置不完整"}
            
            api_url = f"https://api.telegram.org/bot{bot_token}/"
            
            # 如果有图片，发送图片+文字
            if image_path and os.path.exists(image_path):
                endpoint = api_url + "sendPhoto"
                files = {"photo": open(image_path, "rb")}
                data = {"chat_id": chat_id, "caption": message, "parse_mode": "Markdown"}
                response = requests.post(endpoint, files=files, data=data)
                files["photo"].close()
            else:
                # 否则只发送文字
                endpoint = api_url + "sendMessage"
                data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
                response = requests.post(endpoint, json=data)
            
            # 检查响应
            if response.status_code == 200:
                logger.info(f"Telegram消息发送成功")
                return {"success": True}
            else:
                logger.warning(f"Telegram消息发送失败，状态码: {response.status_code}, 响应: {response.text}")
                return {"success": False, "error": f"状态码 {response.status_code}", "response": response.text}
                
        except Exception as e:
            logger.error(f"发送Telegram消息失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _send_to_discord(self, message: str, image_path: str = None) -> Dict:
        """
        发送消息到Discord
        
        Args:
            message: 消息内容
            image_path: 图片路径(可选)
            
        Returns:
            发送结果
        """
        try:
            webhook_url = self.discord_config.get("webhook_url")
            
            if not webhook_url:
                logger.warning("Discord配置不完整，跳过发送")
                return {"success": False, "error": "配置不完整"}
            
            payload = {"content": message}
            
            # 如果有图片，添加图片
            if image_path and os.path.exists(image_path):
                files = {"file": open(image_path, "rb")}
                response = requests.post(webhook_url, data=payload, files=files)
                files["file"].close()
            else:
                # 否则只发送文字
                response = requests.post(webhook_url, json=payload)
            
            # 检查响应
            if response.status_code == 204 or response.status_code == 200:
                logger.info(f"Discord消息发送成功")
                return {"success": True}
            else:
                logger.warning(f"Discord消息发送失败，状态码: {response.status_code}, 响应: {response.text}")
                return {"success": False, "error": f"状态码 {response.status_code}", "response": response.text}
                
        except Exception as e:
            logger.error(f"发送Discord消息失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _send_to_feishu(self, message: str, image_path: str = None) -> Dict:
        """
        发送消息到飞书
        
        Args:
            message: 消息内容
            image_path: 图片路径(可选)
            
        Returns:
            发送结果
        """
        try:
            webhook_url = self.feishu_config.get("webhook_url")
            
            if not webhook_url:
                logger.warning("飞书配置不完整，跳过发送")
                return {"success": False, "error": "配置不完整"}
            
            # 飞书消息格式
            payload = {
                "msg_type": "text",
                "content": {
                    "text": message
                }
            }
            
            # 如果有图片，切换为图片+文字模式
            if image_path and os.path.exists(image_path):
                # 图片处理需要飞书的额外API，这里简化处理
                # 实际项目中应该先上传图片，获取image_key后再构建消息
                logger.warning("飞书图片发送需要额外API，暂不支持")
            
            # 发送请求
            response = requests.post(webhook_url, json=payload)
            
            # 检查响应
            if response.status_code == 200:
                response_json = response.json()
                if response_json.get("code") == 0:
                    logger.info(f"飞书消息发送成功")
                    return {"success": True}
                else:
                    logger.warning(f"飞书消息发送失败，错误码: {response_json.get('code')}")
                    return {"success": False, "error": str(response_json)}
            else:
                logger.warning(f"飞书消息发送失败，状态码: {response.status_code}, 响应: {response.text}")
                return {"success": False, "error": f"状态码 {response.status_code}", "response": response.text}
                
        except Exception as e:
            logger.error(f"发送飞书消息失败: {e}")
            return {"success": False, "error": str(e)}
    
    def send_signal_notification(self, 
                               symbol: str, 
                               signal_type: str, 
                               price: float, 
                               strategy: str, 
                               confidence: float, 
                               with_voice: bool = False) -> Dict:
        """
        发送期权信号通知
        
        Args:
            symbol: 交易标的
            signal_type: 信号类型
            price: 价格
            strategy: 策略名称
            confidence: 置信度
            with_voice: 是否以语音播报
            
        Returns:
            通知结果
        """
        try:
            # 构建消息
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 信号类型映射
            action_map = {
                "buy_call": "买入看涨期权",
                "sell_call": "卖出看涨期权",
                "buy_put": "买入看跌期权",
                "sell_put": "卖出看跌期权"
            }
            action = action_map.get(signal_type, signal_type)
            
            # 构建通知消息
            message = f"""🔔 **期权交易信号** 

📊 标的: **{symbol}**
📈 信号: **{action}**
💰 价格: ${price:.2f}
💎 策略: {strategy}
🔍 置信度: {confidence:.0%}

⏰ 信号生成时间: {timestamp}
"""
            
            # 构建语音消息（简化版）
            voice_message = f"{symbol}期权信号：{action}，价格{price:.2f}美元，置信度{int(confidence*100)}%。"
            
            # 发送通知
            if with_voice:
                return self.broadcast(message, True)
            else:
                return self.send_message(message)
                
        except Exception as e:
            logger.error(f"发送信号通知失败: {e}")
            return {"success": False, "error": str(e)}
    
    def send_summary_notification(self, symbols: List[str], prices: Dict[str, float]) -> Dict:
        """
        发送市场摘要通知
        
        Args:
            symbols: 标的列表
            prices: 价格字典
            
        Returns:
            通知结果
        """
        try:
            # 构建消息
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"📊 **市场摘要** ({timestamp})\n\n"
            
            # 添加各标的价格
            for symbol in symbols:
                price = prices.get(symbol, 0)
                message += f"• {symbol}: ${price:.2f}\n"
            
            # 发送通知
            return self.send_message(message)
                
        except Exception as e:
            logger.error(f"发送摘要通知失败: {e}")
            return {"success": False, "error": str(e)}

# 直接运行时的示例用法
if __name__ == "__main__":
    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)
    
    # 创建通知器
    notifier = OptionNotifier()
    
    # 测试发送消息
    notifier.send_message("测试消息通知 - 这是一个来自OptionNotifier的测试消息")
    
    # 测试发送信号通知
    notifier.send_signal_notification(
        symbol="SPY",
        signal_type="buy_call",
        price=450.75,
        strategy="价值回归策略",
        confidence=0.85
    )
    
    # 测试市场摘要
    notifier.send_summary_notification(
        symbols=["SPY", "QQQ", "TSLA", "ETH-USD"],
        prices={"SPY": 450.75, "QQQ": 380.25, "TSLA": 275.50, "ETH-USD": 2450.00}
    ) 