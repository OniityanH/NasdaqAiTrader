"""
运行记录器 - 记录每次交易的 Prompt 和输出
"""
import os
import json
from datetime import datetime
from typing import Dict, Any

class RunLogger:
    """运行记录器"""
    
    def __init__(self, runs_dir: str = "runs"):
        self.runs_dir = runs_dir
        os.makedirs(runs_dir, exist_ok=True)
    
    def save_run(self, symbol: str, prompt: str, decision: Dict[str, Any], market_data: Dict = None):
        """
        保存单次运行记录
        
        Args:
            symbol: 股票代码
            prompt: 发送给 AI 的 prompt
            decision: AI 决策结果
            market_data: 市场数据 (可选)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.runs_dir}/{timestamp}_{symbol}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "prompt": prompt,
            "decision": decision,
            "market_data": market_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def list_runs(self, symbol: str = None) -> list:
        """列出运行记录"""
        files = os.listdir(self.runs_dir)
        if symbol:
            files = [f for f in files if symbol in f]
        return sorted(files, reverse=True)
