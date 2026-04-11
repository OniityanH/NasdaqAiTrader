"""
数据采集器 - 本地新闻文件读取
从 newstrader 文件夹读取新闻 txt 文件
"""
import os
import glob
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LocalNewsCollector:
    """从本地txt文件读取新闻"""
    
    def __init__(self, news_dir: str = "/Users/zz/newstrader"):
        """
        初始化
        
        Args:
            news_dir: newstrader 文件夹路径
        """
        self.news_dir = news_dir
    
    def get_news_for_symbol(self, symbol: str) -> Optional[str]:
        """
        获取指定股票的新闻文件内容
        
        Args:
            symbol: 股票代码 (如 AAPL)
            
        Returns:
            格式化后的新闻字符串，如果文件不存在返回 None
        """
        # 获取今天的日期
        today = datetime.now().strftime("%Y%m%d")
        
        # 构造文件名
        filename = f"{today}_{symbol}.txt"
        filepath = os.path.join(self.news_dir, filename)
        
        if not os.path.exists(filepath):
            logger.info(f"新闻文件不存在: {filepath}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析文件内容，只保留新闻标题部分
            news_lines = self._parse_news_content(content)
            return news_lines
            
        except Exception as e:
            logger.error(f"读取新闻文件失败: {filepath}, error: {e}")
            return None
    
    def _parse_news_content(self, content: str) -> str:
        """
        解析新闻文件内容，提取新闻标题列表
        
        Args:
            content: 文件完整内容
            
        Returns:
            格式化后的新闻字符串
        """
        lines = content.strip().split('\n')
        
        result_lines = []
        news_count = 0
        
        for line in lines:
            line = line.strip()
            # 跳过标题行和分隔线
            if line.startswith('==') or line.startswith('Symbol:') or line.startswith('新闻数量:'):
                continue
            # 匹配新闻行 (以数字.开头)
            if line and line[0].isdigit() and '. ' in line:
                # 提取新闻标题（去掉编号和来源信息）
                parts = line.split(']', 1)
                if len(parts) > 1:
                    news_text = parts[1].strip()
                    news_count += 1
                    result_lines.append(f"{news_count}. {news_text}")
        
        if not result_lines:
            return "无新闻"
        
        # 返回前20条新闻
        return '\n'.join(result_lines[:20])
    
    def get_news_summary(self, symbol: str) -> str:
        """
        获取新闻摘要（供 DeepSeek prompt 使用）
        
        Args:
            symbol: 股票代码
            
        Returns:
            格式化后的新闻摘要，如果文件不存在返回 None
        """
        news_content = self.get_news_for_symbol(symbol)
        
        if news_content is None:
            return None
        
        # 统计新闻数量
        news_count = len([line for line in news_content.split('\n') if line.strip()])
        
        return f"共{news_count}条新闻:\n{news_content}"


# 便捷函数
def get_local_news(symbol: str, news_dir: str = "/Users/zz/newstrader") -> Optional[str]:
    """快速获取本地新闻"""
    collector = LocalNewsCollector(news_dir)
    return collector.get_news_for_symbol(symbol)


if __name__ == "__main__":
    # 测试
    collector = LocalNewsCollector()
    
    # 测试读取 AAPL 新闻
    news = collector.get_news_summary("AAPL")
    if news:
        print("=== AAPL 新闻 ===")
        print(news)
    else:
        print("AAPL 新闻文件不存在")
    
    # 测试读取不存在的股票
    news2 = collector.get_news_summary("TEST")
    if news2 is None:
        print("\nTEST 文件不存在，正确返回 None")
