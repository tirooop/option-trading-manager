#!/usr/bin/env python
"""
多标的期权监控器 - 同时监控多个交易标的的期权市场
"""

import os
import sys
import json
import logging
import argparse
import datetime
import time
import threading
import queue
from typing import Dict, List, Any, Optional, Union, Tuple

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 尝试导入工具模块
try:
    from utils.ai_router import AIRouterSync
except ImportError as e:
    print(f"警告: 无法导入AI路由器: {e}")

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/multi_symbol_watcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SymbolWatcher:
    """单个标的的监控类"""
    
    def __init__(self, symbol_config: Dict, config_path: str = None, notifier = None):
        """
        初始化标的监控器
        
        Args:
            symbol_config: 标的配置信息
            config_path: 全局配置文件路径
            notifier: 通知器实例
        """
        self.symbol = symbol_config.get("symbol")
        self.config = symbol_config
        self.notifier = notifier
        self.config_path = config_path
        
        # 市场信息
        self.market = symbol_config.get("market", "US")
        self.type = symbol_config.get("type", "equity")
        
        # 期权配置
        self.options_enabled = symbol_config.get("options_enabled", True)
        self.options_config = symbol_config.get("options_config", {})
        
        # 交易时间
        self.trading_hours = symbol_config.get("trading_hours", {
            "market_open": "09:30",
            "market_close": "16:00"
        })
        
        # 最后更新时间
        self.last_update = None
        
        # 当前价格和期权数据
        self.current_price = None
        self.current_options = {}
        
        # 加载的策略
        self.strategies = []
        
        # 信号队列
        self.signal_queue = queue.Queue()
        
        logger.info(f"初始化 {self.symbol} 监控器")
    
    def load_strategies(self) -> bool:
        """
        加载该标的的策略
        
        Returns:
            加载成功与否
        """
        try:
            # 查找策略目录
            production_dir = "production_strategies"
            strategy_files = []
            
            if os.path.exists(production_dir):
                for file in os.listdir(production_dir):
                    if file.endswith(".py") and self.symbol.upper() in file.upper():
                        strategy_files.append(os.path.join(production_dir, file))
            
            if not strategy_files:
                logger.warning(f"未找到 {self.symbol} 的策略文件")
                return False
                
            logger.info(f"为 {self.symbol} 找到 {len(strategy_files)} 个策略")
            self.strategies = strategy_files
            return True
            
        except Exception as e:
            logger.error(f"加载 {self.symbol} 策略失败: {e}")
            return False
    
    def update_market_data(self) -> bool:
        """
        更新市场数据
        
        Returns:
            是否成功更新
        """
        try:
            # 这里应该连接到实际的数据源获取数据
            # 模拟实现 - 生成随机数据
            import random
            
            # 模拟价格波动
            if self.current_price is None:
                self.current_price = 100 + random.random() * 100
            else:
                change_pct = (random.random() - 0.5) * 0.01  # -0.5% 到 +0.5% 的波动
                self.current_price *= (1 + change_pct)
            
            # 模拟当前时间
            self.last_update = datetime.datetime.now()
            
            # 如果启用了期权，模拟期权数据
            if self.options_enabled:
                # 获取期权配置
                preferred_strikes = self.options_config.get("preferred_strikes", "").split(", ")
                preferred_expiries = self.options_config.get("preferred_expiries", "").split(", ")
                
                # 根据当前价格生成行权价
                strikes = []
                for strike_desc in preferred_strikes:
                    if strike_desc == "ATM":
                        # 接近当前价格的整数
                        strikes.append(round(self.current_price))
                    elif "ATM+" in strike_desc:
                        # 高于当前价格
                        offset = int(strike_desc.replace("ATM+", ""))
                        strikes.append(round(self.current_price) + offset)
                    elif "ATM-" in strike_desc:
                        # 低于当前价格
                        offset = int(strike_desc.replace("ATM-", ""))
                        strikes.append(round(self.current_price) - offset)
                
                # 生成到期日
                expiries = []
                today = datetime.date.today()
                
                if "weekly" in preferred_expiries:
                    # 下周五
                    days_to_friday = (4 - today.weekday()) % 7 + 7
                    expiries.append(today + datetime.timedelta(days=days_to_friday))
                    
                if "monthly" in preferred_expiries:
                    # 当月第三个周五(简化实现)
                    this_month_days = (datetime.date(today.year, today.month, 1).weekday() + 18) % 7
                    monthly_exp = datetime.date(today.year, today.month, this_month_days)
                    if monthly_exp < today:
                        next_month = today.month + 1 if today.month < 12 else 1
                        next_year = today.year if today.month < 12 else today.year + 1
                        this_month_days = (datetime.date(next_year, next_month, 1).weekday() + 18) % 7
                        monthly_exp = datetime.date(next_year, next_month, this_month_days)
                    expiries.append(monthly_exp)
                
                # 生成期权数据
                options_data = {}
                
                for expiry in expiries:
                    days_to_expiry = (expiry - today).days
                    expiry_str = expiry.strftime("%Y-%m-%d")
                    options_data[expiry_str] = {}
                    
                    for strike in strikes:
                        # 计算模拟的期权价格
                        call_price = self._simulate_option_price(
                            "call", self.current_price, strike, days_to_expiry
                        )
                        put_price = self._simulate_option_price(
                            "put", self.current_price, strike, days_to_expiry
                        )
                        
                        options_data[expiry_str][strike] = {
                            "call": call_price,
                            "put": put_price,
                            "call_bid": call_price * 0.95,
                            "call_ask": call_price * 1.05,
                            "put_bid": put_price * 0.95,
                            "put_ask": put_price * 1.05,
                            "iv_call": 0.3 + (random.random() - 0.5) * 0.1,
                            "iv_put": 0.3 + (random.random() - 0.5) * 0.1
                        }
                
                self.current_options = options_data
            
            logger.info(f"更新 {self.symbol} 数据: 价格 {self.current_price:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"更新 {self.symbol} 市场数据失败: {e}")
            return False
    
    def _simulate_option_price(self, option_type: str, spot: float, strike: float, days_to_expiry: int) -> float:
        """
        模拟期权价格（简化实现）
        
        Args:
            option_type: 期权类型 ('call' 或 'put')
            spot: 当前价格
            strike: 行权价
            days_to_expiry: 到期天数
            
        Returns:
            期权价格
        """
        import random
        import math
        
        # 简化期权定价模型
        t = days_to_expiry / 365.0
        vol = 0.3  # 假设波动率为30%
        
        intrinsic = max(0, spot - strike) if option_type == "call" else max(0, strike - spot)
        time_value = spot * vol * math.sqrt(t) * 0.4  # 简化的时间价值
        
        # 添加一些随机性
        random_factor = 1.0 + (random.random() - 0.5) * 0.1  # +/-5%
        
        return (intrinsic + time_value) * random_factor
    
    def check_trading_hours(self) -> bool:
        """
        检查当前是否在交易时间内
        
        Returns:
            是否在交易时间内
        """
        # 加密货币市场是24/7的
        if self.market == "CRYPTO":
            return True
            
        # 获取当前时间
        now = datetime.datetime.now()
        current_time = now.time()
        
        # 解析交易时间
        market_open = self.trading_hours.get("market_open", "09:30")
        market_close = self.trading_hours.get("market_close", "16:00")
        
        open_hour, open_minute = map(int, market_open.split(":"))
        close_hour, close_minute = map(int, market_close.split(":"))
        
        open_time = datetime.time(open_hour, open_minute)
        close_time = datetime.time(close_hour, close_minute)
        
        # 检查是否为交易日 (周一至周五)
        is_weekday = 0 <= now.weekday() <= 4
        
        # 检查是否在交易时间内
        is_during_market = open_time <= current_time <= close_time
        
        return is_weekday and is_during_market
    
    def run_strategies(self) -> List[Dict]:
        """
        运行所有加载的策略
        
        Returns:
            生成的信号列表
        """
        signals = []
        
        if not self.strategies:
            logger.warning(f"{self.symbol} 没有策略可运行")
            return signals
            
        # 检查是否有市场数据
        if self.current_price is None:
            logger.warning(f"{self.symbol} 没有市场数据，无法运行策略")
            return signals
        
        # 这里应该实现策略调用逻辑
        # 简单模拟策略执行并生成随机信号
        import random
        
        for strategy_file in self.strategies:
            strategy_name = os.path.basename(strategy_file).replace(".py", "")
            
            # 随机确定是否产生信号
            if random.random() < 0.1:  # 10%的概率产生信号
                # 随机确定信号类型
                signal_types = ["buy_call", "sell_call", "buy_put", "sell_put"]
                signal_type = random.choice(signal_types)
                
                # 从可用的期权中选择一个
                if self.current_options:
                    expiry = random.choice(list(self.current_options.keys()))
                    strike = random.choice(list(self.current_options[expiry].keys()))
                    
                    option_data = self.current_options[expiry][strike]
                    option_price = option_data["call"] if "call" in signal_type else option_data["put"]
                    
                    # 创建信号
                    signal = {
                        "symbol": self.symbol,
                        "strategy": strategy_name,
                        "type": signal_type,
                        "expiry": expiry,
                        "strike": strike,
                        "price": option_price,
                        "spot_price": self.current_price,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "confidence": round(random.random() * 0.5 + 0.5, 2)  # 50-100%的置信度
                    }
                    
                    signals.append(signal)
                    logger.info(f"策略 {strategy_name} 为 {self.symbol} 生成信号: {signal_type} @{strike} (到期: {expiry})")
        
        # 将信号放入队列
        for signal in signals:
            self.signal_queue.put(signal)
        
        return signals
    
    def get_market_state(self) -> str:
        """
        获取当前市场状态
        
        Returns:
            市场状态描述
        """
        if not self.check_trading_hours():
            return "CLOSED"
            
        now = datetime.datetime.now()
        current_time = now.time()
        
        # 解析交易时间
        market_open = self.trading_hours.get("market_open", "09:30")
        market_close = self.trading_hours.get("market_close", "16:00")
        pre_market_start = self.trading_hours.get("pre_market_start", "04:00")
        after_hours_end = self.trading_hours.get("after_hours_end", "20:00")
        
        open_hour, open_minute = map(int, market_open.split(":"))
        close_hour, close_minute = map(int, market_close.split(":"))
        pre_hour, pre_minute = map(int, pre_market_start.split(":"))
        after_hour, after_minute = map(int, after_hours_end.split(":"))
        
        open_time = datetime.time(open_hour, open_minute)
        close_time = datetime.time(close_hour, close_minute)
        pre_time = datetime.time(pre_hour, pre_minute)
        after_time = datetime.time(after_hour, after_minute)
        
        if self.market == "CRYPTO":
            return "OPEN"
        elif current_time < pre_time or current_time > after_time:
            return "CLOSED"
        elif current_time < open_time:
            return "PRE_MARKET"
        elif current_time > close_time:
            return "AFTER_HOURS"
        else:
            return "REGULAR_HOURS"
    
    def process_signals(self) -> List[Dict]:
        """
        处理队列中的信号
        
        Returns:
            处理的信号列表
        """
        processed = []
        
        # 处理队列中的所有信号
        while not self.signal_queue.empty():
            try:
                signal = self.signal_queue.get(block=False)
                
                # 在这里可以添加信号过滤、验证等逻辑
                
                # 记录处理的信号
                processed.append(signal)
                
                # 如果有通知器，发送通知
                if self.notifier:
                    self._send_signal_notification(signal)
                
                # 标记任务完成
                self.signal_queue.task_done()
                
            except queue.Empty:
                break
        
        return processed
    
    def _send_signal_notification(self, signal: Dict):
        """
        发送信号通知
        
        Args:
            signal: 信号数据
        """
        try:
            if not self.notifier:
                return
                
            # 构建消息
            signal_type = signal.get("type", "unknown")
            strike = signal.get("strike", "N/A")
            expiry = signal.get("expiry", "N/A")
            confidence = signal.get("confidence", 0)
            strategy = signal.get("strategy", "unknown")
            
            action_map = {
                "buy_call": "买入看涨期权",
                "sell_call": "卖出看涨期权",
                "buy_put": "买入看跌期权",
                "sell_put": "卖出看跌期权"
            }
            
            action = action_map.get(signal_type, signal_type)
            
            message = f"""🔔 **期权交易信号** 

📊 标的: **{self.symbol}** (当前价格: ${signal.get('spot_price', 0):.2f})
📈 信号: **{action}**
💰 行权价: ${strike}
📅 到期日: {expiry}
💎 策略: {strategy}
🔍 置信度: {confidence:.0%}

⏰ 信号生成时间: {signal.get('timestamp', 'N/A')}
"""
            
            # 发送通知
            self.notifier.send_message(message)
            
        except Exception as e:
            logger.error(f"发送信号通知失败: {e}")
    
    def run_one_cycle(self) -> Dict:
        """
        运行一个完整的监控周期
        
        Returns:
            周期结果
        """
        try:
            # 更新市场数据
            data_updated = self.update_market_data()
            
            # 检查交易时间
            is_trading_hours = self.check_trading_hours()
            market_state = self.get_market_state()
            
            results = {
                "symbol": self.symbol,
                "data_updated": data_updated,
                "market_state": market_state,
                "signals": [],
                "current_price": self.current_price,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # 如果在交易时间内并且数据已更新，运行策略
            if is_trading_hours and data_updated:
                signals = self.run_strategies()
                results["signals"] = signals
            
            # 处理信号队列
            processed_signals = self.process_signals()
            results["processed_signals"] = processed_signals
            
            return results
            
        except Exception as e:
            logger.error(f"运行 {self.symbol} 监控周期失败: {e}")
            return {
                "symbol": self.symbol,
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }

class MultiSymbolWatcher:
    """多标的期权监控器"""
    
    def __init__(self, symbols_file: str = None, config_path: str = None, notifier = None):
        """
        初始化多标的监控器
        
        Args:
            symbols_file: 标的配置文件路径
            config_path: 全局配置文件路径
            notifier: 通知器实例
        """
        # 标的配置文件
        self.symbols_file = symbols_file or os.path.join("option_manager", "symbols.json")
        self.config_path = config_path or os.path.join("config", "warmachine_community_config.json")
        
        # 通知器
        self.notifier = notifier
        
        # 加载标的配置
        self.symbols_config = self._load_symbols_config()
        
        # 全局设置
        self.settings = self.symbols_config.get("settings", {})
        
        # 更新间隔(秒)
        self.update_interval = self.settings.get("update_interval_seconds", 60)
        
        # 标的监控器
        self.watchers = {}
        
        # 初始化 AI 路由器
        try:
            self.ai_router = AIRouterSync({})
        except:
            self.ai_router = None
            logger.warning("无法初始化AI路由器")
        
        # 初始化标的监控器
        self._init_watchers()
        
        logger.info(f"多标的期权监控器初始化完成，监控 {len(self.watchers)} 个标的")
    
    def _load_symbols_config(self) -> Dict:
        """
        加载标的配置文件
        
        Returns:
            配置字典
        """
        try:
            if os.path.exists(self.symbols_file):
                with open(self.symbols_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                logger.info(f"已加载标的配置文件: {self.symbols_file}")
                return config
            else:
                logger.error(f"标的配置文件不存在: {self.symbols_file}")
                return {"symbols": [], "settings": {}}
        except Exception as e:
            logger.error(f"加载标的配置文件失败: {e}")
            return {"symbols": [], "settings": {}}
    
    def _init_watchers(self):
        """初始化所有标的的监控器"""
        try:
            symbols = self.symbols_config.get("symbols", [])
            
            for symbol_config in symbols:
                if not symbol_config.get("enabled", True):
                    continue
                    
                symbol = symbol_config.get("symbol")
                if not symbol:
                    continue
                
                # 创建标的监控器
                watcher = SymbolWatcher(symbol_config, self.config_path, self.notifier)
                
                # 加载策略
                watcher.load_strategies()
                
                # 添加到监控列表
                self.watchers[symbol] = watcher
                
            logger.info(f"已初始化 {len(self.watchers)} 个标的监控器")
            
        except Exception as e:
            logger.error(f"初始化标的监控器失败: {e}")
    
    def _generate_market_summary(self, results: Dict[str, Dict]) -> str:
        """
        生成市场摘要，使用AI解读
        
        Args:
            results: 各标的运行结果
            
        Returns:
            市场摘要文本
        """
        try:
            if not self.ai_router:
                return self._generate_simple_summary(results)
                
            # 构建市场数据摘要
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            market_data = []
            signals = []
            
            for symbol, result in results.items():
                if "error" in result:
                    continue
                    
                market_state = result.get("market_state", "UNKNOWN")
                current_price = result.get("current_price")
                
                if current_price:
                    market_data.append(f"{symbol}: ${current_price:.2f} ({market_state})")
                
                # 收集信号
                for signal in result.get("signals", []):
                    signal_type = signal.get("type")
                    strike = signal.get("strike")
                    expiry = signal.get("expiry")
                    
                    signals.append(f"{symbol} - {signal_type} @{strike} (到期:{expiry})")
            
            # 如果没有数据，返回简单摘要
            if not market_data:
                return self._generate_simple_summary(results)
                
            # 构建 AI 提示
            prompt = f"""
作为专业的期权市场分析师，请根据以下数据提供一份简短市场摘要（100字以内）:

时间: {timestamp}
市场数据:
{', '.join(market_data)}

{'有以下交易信号:\n' + '\n'.join(signals) if signals else '无交易信号'}

请分析当前市场状况和这些资产的表现，给出简洁的市场总结，适合发送到交易群组。
注意使用专业但通俗的语言。
"""
            
            # 调用 AI 生成摘要
            summary = self.ai_router.ask(prompt)
            
            # 添加标题和时间戳
            return f"📊 **市场摘要** ({timestamp})\n\n{summary}"
            
        except Exception as e:
            logger.error(f"生成AI市场摘要失败: {e}")
            return self._generate_simple_summary(results)
    
    def _generate_simple_summary(self, results: Dict[str, Dict]) -> str:
        """
        生成简单的市场摘要
        
        Args:
            results: 各标的运行结果
            
        Returns:
            简单摘要文本
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        summary = f"📊 **市场状况更新** ({timestamp})\n\n"
        
        # 添加各标的状态
        for symbol, result in results.items():
            if "error" in result:
                summary += f"❌ {symbol}: 监控错误\n"
                continue
                
            price = result.get("current_price", 0)
            market_state = result.get("market_state", "UNKNOWN")
            
            state_emoji = {
                "REGULAR_HOURS": "🟢",
                "PRE_MARKET": "🟡",
                "AFTER_HOURS": "🟠",
                "CLOSED": "🔴",
                "OPEN": "🟢",
                "UNKNOWN": "❓"
            }.get(market_state, "❓")
            
            summary += f"{state_emoji} {symbol}: ${price:.2f}\n"
        
        # 添加信号汇总
        total_signals = 0
        for result in results.values():
            total_signals += len(result.get("signals", []))
        
        if total_signals > 0:
            summary += f"\n🔔 本周期共产生 {total_signals} 个交易信号"
        else:
            summary += "\n📭 本周期无交易信号"
            
        return summary
    
    def run_once(self) -> Dict:
        """
        运行一次所有标的的监控
        
        Returns:
            运行结果
        """
        results = {}
        has_signals = False
        
        # 运行每个标的的监控
        for symbol, watcher in self.watchers.items():
            result = watcher.run_one_cycle()
            results[symbol] = result
            
            # 检查是否有信号
            if result.get("signals") and len(result.get("signals", [])) > 0:
                has_signals = True
        
        # 如果有信号或者每小时发送一次摘要
        current_hour = datetime.datetime.now().hour
        hourly_update = hasattr(self, 'last_summary_hour') and self.last_summary_hour != current_hour
        
        if has_signals or hourly_update:
            # 生成并发送市场摘要
            summary = self._generate_market_summary(results)
            
            if self.notifier:
                self.notifier.send_message(summary)
            
            # 记录最后发送小时
            self.last_summary_hour = current_hour
        
        return results
    
    def run_continuous(self, max_iterations: int = None):
        """
        持续运行监控
        
        Args:
            max_iterations: 最大迭代次数，如果不指定则一直运行
        """
        iteration = 0
        
        try:
            while max_iterations is None or iteration < max_iterations:
                start_time = time.time()
                
                # 运行一次监控
                self.run_once()
                
                # 计算应该休眠的时间
                elapsed = time.time() - start_time
                sleep_time = max(1, self.update_interval - elapsed)
                
                # 输出下次更新时间
                next_update = datetime.datetime.now() + datetime.timedelta(seconds=sleep_time)
                logger.info(f"下次更新时间: {next_update.strftime('%H:%M:%S')}, {sleep_time:.1f}秒后")
                
                # 休眠
                time.sleep(sleep_time)
                
                iteration += 1
                
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止监控")
        except Exception as e:
            logger.error(f"运行监控时发生错误: {e}")

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="多标的期权监控器")
    parser.add_argument("--symbols-file", "-s", type=str, help="标的配置文件路径")
    parser.add_argument("--config", "-c", type=str, help="全局配置文件路径")
    parser.add_argument("--iterations", "-i", type=int, help="最大迭代次数，不指定则一直运行")
    args = parser.parse_args()
    
    try:
        # 创建模拟通知器
        class MockNotifier:
            def send_message(self, message, image_path=None):
                print("\n==== MOCK NOTIFICATION ====")
                print(message)
                if image_path:
                    print(f"附图: {image_path}")
                print("========================\n")
        
        # 创建多标的监控器
        watcher = MultiSymbolWatcher(args.symbols_file, args.config, MockNotifier())
        
        # 启动持续监控
        watcher.run_continuous(args.iterations)
        
    except Exception as e:
        print(f"运行多标的期权监控器出错: {e}")

if __name__ == "__main__":
    main() 