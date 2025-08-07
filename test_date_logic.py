#!/usr/bin/env python3
"""
测试日期逻辑脚本
演示访问统计在不同日期的行为
"""

from datetime import datetime, timezone, timedelta
import json

def get_current_date():
    """获取当前日期（UTC+8，中国时区）"""
    china_tz = timezone(timedelta(hours=8))
    return datetime.now(china_tz).strftime('%Y-%m-%d')

def simulate_visit_data():
    """模拟访问数据"""
    china_tz = timezone(timedelta(hours=8))
    
    # 模拟过去几天的访问数据
    visits = [
        # 今天
        "2024-01-15 09:30:00 | 192.168.1.100 | Chrome",
        "2024-01-15 14:20:00 | 203.45.67.89 | Safari", 
        "2024-01-15 18:45:00 | 192.168.1.100 | Chrome",
        
        # 昨天
        "2024-01-14 10:15:00 | 192.168.1.100 | Chrome",
        "2024-01-14 16:30:00 | 203.45.67.89 | Firefox",
        
        # 前天
        "2024-01-13 11:00:00 | 192.168.1.100 | Chrome",
        "2024-01-13 15:45:00 | 203.45.67.89 | Safari",
        "2024-01-13 20:20:00 | 192.168.1.100 | Chrome",
    ]
    
    return visits

def calculate_stats(visits, target_date):
    """计算指定日期的访问统计"""
    today_visits = 0
    yesterday_visits = 0
    total_visits = len(visits)
    
    china_tz = timezone(timedelta(hours=8))
    yesterday = (datetime.now(china_tz) - timedelta(days=1)).strftime('%Y-%m-%d')
    
    for visit in visits:
        timestamp = visit.split(' | ')[0]
        if timestamp.startswith(target_date):
            today_visits += 1
        elif timestamp.startswith(yesterday):
            yesterday_visits += 1
    
    return {
        'total': total_visits,
        'today': today_visits,
        'yesterday': yesterday_visits,
        'current_date': target_date
    }

def main():
    print("📊 访问统计日期逻辑演示")
    print("=" * 50)
    
    # 获取当前日期
    current_date = get_current_date()
    print(f"当前日期: {current_date}")
    
    # 模拟访问数据
    visits = simulate_visit_data()
    print(f"总访问记录数: {len(visits)}")
    
    print("\n📅 不同日期的统计结果:")
    print("-" * 30)
    
    # 模拟不同日期的统计
    test_dates = [
        "2024-01-15",  # 今天
        "2024-01-16",  # 明天
        "2024-01-17",  # 后天
    ]
    
    for date in test_dates:
        stats = calculate_stats(visits, date)
        print(f"\n日期: {date}")
        print(f"  总访问量: {stats['total']}")
        print(f"  今日访问: {stats['today']}")
        print(f"  昨日访问: {stats['yesterday']}")
    
    print("\n🔍 关键观察:")
    print("1. 总访问量: 保持不变（历史累计）")
    print("2. 今日访问: 根据当前日期动态计算")
    print("3. 昨日访问: 自动计算前一天的数据")
    print("4. 时区处理: 使用中国时区（UTC+8）")
    
    print("\n📝 明天访问时会发生什么:")
    print("- 今日访问量会重置为0")
    print("- 昨天的数据会变成'昨日访问'")
    print("- 总访问量继续累加")
    print("- 所有历史数据都保留在Google Sheets中")

if __name__ == "__main__":
    main()
