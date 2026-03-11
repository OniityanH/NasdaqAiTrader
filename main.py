"""
Nasdaq AI Trader - 主入口
"""
import argparse
import logging
import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scheduler.trading_loop import TradingScheduler


def setup_logging(level: str = "INFO"):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/trading.log', encoding='utf-8')
        ]
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Nasdaq AI Trader")
    parser.add_argument("--config", default="config/api_keys.yaml", help="配置文件路径")
    parser.add_argument("--once", action="store_true", help="只运行一次")
    parser.add_argument("--iterations", type=int, default=None, help="运行次数")
    parser.add_argument("--log-level", default="INFO", help="日志级别")
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # 加载环境变量
    load_dotenv()
    
    logger.info("=" * 50)
    logger.info("Nasdaq AI Trader 启动")
    logger.info("=" * 50)
    
    # 检查配置文件
    if not os.path.exists(args.config):
        logger.error(f"配置文件不存在: {args.config}")
        print(f"请创建配置文件: {args.config}")
        print("\n配置文件示例:")
        print("-" * 40)
        with open("config/api_keys.yaml", "r") as f:
            print(f.read()[:500])
        return
    
    # 创建调度器
    try:
        scheduler = TradingScheduler(args.config)
        
        if args.once:
            # 运行一次
            logger.info("运行一次交易循环...")
            results = scheduler.run_once()
            print("\n" + "=" * 50)
            print("交易结果:")
            print("=" * 50)
            for r in results:
                print(f"\n{r.get('symbol')}:")
                print(f"  决策: {r.get('decision', {}).get('decision', 'N/A')}")
                print(f"  原因: {r.get('decision', {}).get('reason', 'N/A')}")
                print(f"  执行: {'成功' if r.get('trade', {}).get('executed') else '无'}")
        else:
            # 持续运行
            logger.info(f"持续运行模式 (间隔: {scheduler.interval}秒)")
            scheduler.run(max_iterations=args.iterations)
            
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        print(f"\n错误: {e}")
        print("\n请检查配置文件是否正确填写 API Keys")


if __name__ == "__main__":
    main()
