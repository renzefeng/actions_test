#!/usr/bin/env python3
"""
排行榜数据处理脚本 - 适配你的数据结构
"""

import json
import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class LeaderboardProcessor:
    def __init__(self, cache_dir: str = "./leaderboard_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # ⚠️ 重要：修改为你的游戏角色名！
        self.my_character_name = "゛青霖"  # 例如："中州帝仙つ"

        # 获取今日日期
        self.today = self.get_beijing_time().strftime("%Y-%m-%d")

    def get_beijing_time(self):
        """获取北京时间（UTC+8）"""
        utc_now = datetime.utcnow()
        beijing_time = utc_now + timedelta(hours=8)
        return beijing_time

    def parse_time_string(self, time_str: str) -> int:
        """
        解析时间字符串如 "24575年175天" 为总天数
        返回：总天数（年*365 + 天）
        """
        try:
            # 使用正则表达式提取年份和天数
            match = re.match(r"(\d+)年(\d+)天", time_str)
            if match:
                years = int(match.group(1))
                days = int(match.group(2))
                return years * 365 + days
            else:
                # 尝试其他格式
                print(f"⚠️  无法解析时间格式: {time_str}")
                return 0
        except Exception as e:
            print(f"⚠️  解析时间错误 {time_str}: {e}")
            return 0

    def load_today_data(self, rank_data_json: str) -> Dict[str, Any]:
        """加载今日排行榜数据"""
        try:
            # 处理可能的转义字符
            if rank_data_json.startswith('"') and rank_data_json.endswith('"'):
                rank_data_json = rank_data_json[1:-1]

            # 替换可能的转义字符
            rank_data_json = rank_data_json.replace('\\"', '"')

            today_data = json.loads(rank_data_json)

            print(f"✅ 成功加载今日数据")
            print(f"   状态码: {today_data.get('status', '未知')}")
            print(f"   记录数量: {len(today_data.get('list', []))}")

            return today_data
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {e}")
            print(f"数据前100字符: {rank_data_json[:100]}...")
            sys.exit(1)

    def find_my_data(self, player_list: List[Dict]) -> Optional[Dict]:
        """在玩家列表中查找我的数据"""
        for idx, player in enumerate(player_list, 1):
            if player.get('name') == self.my_character_name:
                # 添加排名信息
                player['rank'] = idx
                return player
        return None

    def calculate_gaps(self, my_total_days: int, player_list: List[Dict]) -> List[Dict]:
        """计算我与所有其他玩家的时间差距（天数）"""
        gaps = []

        for idx, player in enumerate(player_list, 1):
            player_name = player.get('name', f"玩家{idx}")

            # 跳过自己
            if player_name == self.my_character_name:
                continue

            # 解析玩家的时间
            player_time_str = player.get('col2', '0年0天')
            player_total_days = self.parse_time_string(player_time_str)

            # 计算差距（我 - 对手）
            gap_days = my_total_days - player_total_days

            gaps.append({
                'player': player_name,
                'zone': player.get('zone', '未知'),
                'element': player.get('col3', '未知'),
                'player_time': player_time_str,
                'player_total_days': player_total_days,
                'gap_days': gap_days,  # 正数表示我领先，负数表示我落后
                'player_rank': idx
            })

        # 按差距排序（最接近的对手在前）
        gaps.sort(key=lambda x: abs(x['gap_days']))
        return gaps

    def save_today_analysis(self, today_data: Dict,
                            my_data: Dict,
                            gaps: List[Dict]) -> str:
        """保存今日分析结果"""
        # 解析我的总天数
        my_time_str = my_data.get('col2', '0年0天')
        my_total_days = self.parse_time_string(my_time_str)

        analysis = {
            'date': self.today,
            'my_data': {
                'name': my_data.get('name'),
                'zone': my_data.get('zone'),
                'element': my_data.get('col3'),
                'time_string': my_time_str,
                'total_days': my_total_days,
                'rank': my_data.get('rank', 0),
                'timestamp': datetime.now().isoformat()
            },
            'player_gaps': gaps,
            'total_players': len(today_data.get('list', [])),
            'status': today_data.get('status', 0)
        }

        # 保存原始数据
        raw_file = self.cache_dir / f"rank_{self.today}.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(today_data, f, ensure_ascii=False, indent=2)
        print(f"📁 原始数据保存至: {raw_file}")

        # 保存分析结果
        analysis_file = self.cache_dir / f"analysis_{self.today}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        print(f"📊 分析结果保存至: {analysis_file}")

        return str(analysis_file)

    def load_historical_data(self, days: int = 7) -> List[Dict]:
        """加载最近N天的历史分析数据"""
        historical_data = []

        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            analysis_file = self.cache_dir / f"analysis_{date}.json"

            if analysis_file.exists():
                try:
                    with open(analysis_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        historical_data.append(data)
                except Exception as e:
                    print(f"⚠️  读取历史文件 {analysis_file} 失败: {e}")

        print(f"📅 加载了 {len(historical_data)} 天的历史数据")
        return historical_data

    def analyze_7day_trend(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """分析7天趋势"""
        if not historical_data:
            return {
                "analysis_date": self.today,
                "error": "无历史数据",
                "days_analyzed": 0
            }

        # 按日期排序
        historical_data.sort(key=lambda x: x.get('date', ''))

        # 收集我的数据趋势
        my_trend = []
        for data in historical_data:
            my_data = data.get('my_data', {})
            my_trend.append({
                'date': data.get('date'),
                'total_days': my_data.get('total_days', 0),
                'rank': my_data.get('rank', 0),
                'time_string': my_data.get('time_string', ''),
                'zone': my_data.get('zone', '')
            })

        # 收集玩家差距趋势
        player_gap_trends = {}
        for data in historical_data:
            date = data.get('date')
            for gap_info in data.get('player_gaps', []):
                player = gap_info.get('player')
                if player not in player_gap_trends:
                    player_gap_trends[player] = []

                player_gap_trends[player].append({
                    'date': date,
                    'gap_days': gap_info.get('gap_days'),
                    'player_total_days': gap_info.get('player_total_days'),
                    'player_rank': gap_info.get('player_rank')
                })

        # 计算显著变化（天数差距变化超过100天）
        significant_changes = []
        for player, trends in player_gap_trends.items():
            if len(trends) >= 2:
                first_gap = trends[0]['gap_days']
                last_gap = trends[-1]['gap_days']
                change = last_gap - first_gap  # 正数表示差距扩大（我相对落后更多）

                # 只记录变化超过100天的玩家
                if abs(change) > 100:
                    # 判断变化方向
                    if change > 0:
                        if first_gap > 0 and last_gap > 0:
                            direction = "领先优势缩小"
                        elif first_gap < 0 and last_gap < 0:
                            direction = "落后差距扩大"
                        else:
                            direction = "差距变化"
                    else:
                        if first_gap > 0 and last_gap > 0:
                            direction = "领先优势扩大"
                        elif first_gap < 0 and last_gap < 0:
                            direction = "落后差距缩小"
                        else:
                            direction = "差距变化"

                    significant_changes.append({
                        'player': player,
                        'change_days': change,
                        'direction': direction,
                        'first_gap': first_gap,
                        'last_gap': last_gap,
                        'first_date': trends[0]['date'],
                        'last_date': trends[-1]['date'],
                        'current_status': "领先" if last_gap > 0 else "落后"
                    })

        # 按变化幅度排序
        significant_changes.sort(key=lambda x: abs(x['change_days']), reverse=True)

        # 计算我的进步
        my_progress = []
        if len(my_trend) >= 2:
            for i in range(1, len(my_trend)):
                prev = my_trend[i - 1]
                curr = my_trend[i]
                days_gained = curr['total_days'] - prev['total_days']
                rank_change = prev['rank'] - curr['rank']  # 正数表示排名上升

                my_progress.append({
                    'from_date': prev['date'],
                    'to_date': curr['date'],
                    'days_gained': days_gained,
                    'rank_change': rank_change,
                    'daily_rate': days_gained / ((datetime.strptime(curr['date'], "%Y-%m-%d") -
                                                  datetime.strptime(prev['date'], "%Y-%m-%d")).days or 1)
                })

        trend_result = {
            'analysis_date': self.today,
            'days_analyzed': len(historical_data),
            'my_trend': my_trend,
            'my_progress': my_progress,
            'significant_gap_changes': significant_changes[:15],  # 前15个显著变化
            'total_players_tracked': len(player_gap_trends)
        }

        return trend_result

    def save_trend_result(self, trend_result: Dict[str, Any]) -> str:
        """保存趋势分析结果"""
        trend_file = self.cache_dir / f"trend_{self.today}.json"
        with open(trend_file, 'w', encoding='utf-8') as f:
            json.dump(trend_result, f, ensure_ascii=False, indent=2)

        print(f"📈 趋势分析保存至: {trend_file}")

        # 控制台输出
        self.print_trend_summary(trend_result)

        return str(trend_file)

    def print_trend_summary(self, trend_result: Dict[str, Any]):
        """打印趋势摘要到控制台"""
        print("\n" + "=" * 60)
        print("📊 问道排行榜7天趋势分析报告")
        print("=" * 60)

        # 我的修炼趋势
        my_trend = trend_result.get('my_trend', [])
        if my_trend:
            print(f"\n🧘 我的修炼进度 ({len(my_trend)}天记录):")
            for record in my_trend:
                days = record['total_days']
                years = days // 365
                remaining_days = days % 365
                print(f"  📅 {record['date']}: {years}年{remaining_days}天 (排名: {record['rank']})")

            if len(my_trend) >= 2:
                first = my_trend[0]
                last = my_trend[-1]
                total_change = last['total_days'] - first['total_days']
                rank_change = first['rank'] - last['rank']  # 正数表示排名上升

                print(f"\n  📈 总体变化:")
                print(f"     修炼时间: {total_change:+d} 天")
                print(f"     排名变化: {rank_change:+d} 位")

                # 显示每日平均进度
                my_progress = trend_result.get('my_progress', [])
                if my_progress:
                    avg_daily = sum(p['days_gained'] for p in my_progress) / len(my_progress)
                    print(f"     日均修炼: {avg_daily:.1f} 天")

        # 与其他道友的差距变化
        gap_changes = trend_result.get('significant_gap_changes', [])
        if gap_changes:
            print(f"\n⚔️  与其他道友的差距变化 (显著变化前{len(gap_changes)}名):")
            for i, change in enumerate(gap_changes, 1):
                status_symbol = "▲" if change['current_status'] == "领先" else "▼"
                gap_desc = f"{abs(change['last_gap'])}天" if change['last_gap'] != 0 else "持平"

                print(f"\n  {i}. {change['player']} {status_symbol}")
                print(f"     {change['direction']} {abs(change['change_days'])}天")
                print(f"     目前{change['current_status']} {gap_desc}")
                print(f"     📅 {change['first_date']}: {change['first_gap']:+d}天")
                print(f"     📅 {change['last_date']}: {change['last_gap']:+d}天")
        else:
            print(f"\n⚔️  无显著差距变化（变化均小于100天）")

        print(f"\n📊 统计: 追踪了 {trend_result.get('total_players_tracked', 0)} 名道友")
        print("=" * 60)


    def generate_email_html(self, trend_result: Dict[str, Any],
                            today_data: Dict,
                            my_data: Dict) -> str:
        """生成HTML格式的邮件内容"""
        # 我的基本信息
        my_time_str = my_data.get('col2', '0年0天')
        my_total_days = self.parse_time_string(my_time_str)
        years = my_total_days // 365
        days = my_total_days % 365

        # 创建HTML邮件内容
        html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
            .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #667eea; background-color: #f9f9f9; }}
            .badge {{ display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin: 0 5px; }}
            .badge-ahead {{ background-color: #4CAF50; color: white; }}
            .badge-behind {{ background-color: #f44336; color: white; }}
            .badge-neutral {{ background-color: #2196F3; color: white; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
            .positive {{ color: #4CAF50; font-weight: bold; }}
            .negative {{ color: #f44336; font-weight: bold; }}
            .player-row:hover {{ background-color: #f5f5f5; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            .timestamp {{ color: #999; font-size: 11px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏆 修仙排行榜分析报告</h1>
                <p>分析日期: {trend_result.get('analysis_date', self.today)}</p>
            </div>
    
            <!-- 我的修炼概况 -->
            <div class="section">
                <h2>🧘 我的修炼概况</h2>
                <table>
                    <tr>
                        <td><strong>角色名</strong></td>
                        <td>{my_data.get('name')}</td>
                        <td><strong>区服</strong></td>
                        <td>{my_data.get('zone')}</td>
                    </tr>
                    <tr>
                        <td><strong>当前境界</strong></td>
                        <td>{years}年{days}天</td>
                        <td><strong>灵根属性</strong></td>
                        <td>{my_data.get('col3')}</td>
                    </tr>
                    <tr>
                        <td><strong>今日排名</strong></td>
                        <td>第{my_data.get('rank')}名</td>
                        <td><strong>总修炼天数</strong></td>
                        <td>{my_total_days}天</td>
                    </tr>
                </table>
            </div>
    
            <!-- 7天趋势 -->
            <div class="section">
                <h2>📈 7天修炼趋势</h2>
                <p>基于 {trend_result.get('days_analyzed', 0)} 天的历史数据</p>
        '''

        # 添加我的趋势表格
        my_trend = trend_result.get('my_trend', [])
        if my_trend and len(my_trend) >= 2:
            first = my_trend[0]
            last = my_trend[-1]
            total_change = last['total_days'] - first['total_days']
            rank_change = first['rank'] - last['rank']

            html_content += f'''
                <table>
                    <tr>
                        <th>日期</th>
                        <th>修炼天数</th>
                        <th>排名</th>
                        <th>变化</th>
                    </tr>
            '''

            for i, record in enumerate(my_trend):
                if i > 0:
                    prev = my_trend[i - 1]
                    days_change = record['total_days'] - prev['total_days']
                    rank_change_row = prev['rank'] - record['rank']
                    days_class = "positive" if days_change > 0 else "negative" if days_change < 0 else ""
                    rank_class = "positive" if rank_change_row > 0 else "negative" if rank_change_row < 0 else ""

                    html_content += f'''
                    <tr>
                        <td>{record['date']}</td>
                        <td>{record['total_days']}天</td>
                        <td>第{record['rank']}名</td>
                        <td>
                            <span class="{days_class}">{days_change:+.0f}天</span> / 
                            <span class="{rank_class}">{rank_change_row:+d}名</span>
                        </td>
                    </tr>
                    '''

            html_content += f'''
                </table>
                <p><strong>总体变化:</strong> 
                    <span class="{'positive' if total_change > 0 else 'negative' if total_change < 0 else ''}">
                        {total_change:+.0f}天
                    </span>，
                    <span class="{'positive' if rank_change > 0 else 'negative' if rank_change < 0 else ''}">
                        排名{rank_change:+d}位
                    </span>
                </p>
            '''
        else:
            html_content += "<p>暂无足够的历史数据进行分析</p>"

        html_content += '''
            </div>
        '''

        # 添加显著差距变化
        gap_changes = trend_result.get('significant_gap_changes', [])
        if gap_changes:
            html_content += f'''
            <div class="section">
                <h2>⚔️ 显著差距变化（前{min(10, len(gap_changes))}名）</h2>
                <table>
                    <tr>
                        <th>修仙者</th>
                        <th>变化趋势</th>
                        <th>当前状态</th>
                        <th>差距变化</th>
                        <th>时间范围</th>
                    </tr>
            '''

            for i, change in enumerate(gap_changes[:10], 1):
                status_class = "badge-ahead" if change['current_status'] == "领先" else "badge-behind"
                change_class = "positive" if change['change_days'] < 0 else "negative"  # 负数表示对我有利

                html_content += f'''
                    <tr class="player-row">
                        <td><strong>#{i}</strong> {change['player']}</td>
                        <td>{change['direction']}</td>
                        <td><span class="badge {status_class}">{change['current_status']}</span></td>
                        <td class="{change_class}">{change['change_days']:+.0f}天</td>
                        <td>{change['first_date']} → {change['last_date']}</td>
                    </tr>
                '''

            html_content += '''
                </table>
            </div>
            '''

        # 邮件结尾
        beijing_now = self.get_beijing_time()
        html_content += f"""
            <div class="footer">
                <p>此报告由 GitHub Actions 自动生成</p>
                <p class="timestamp">生成时间: {beijing_now.strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p class="timestamp">数据来源: 修仙排行榜API | 分析周期: 7天</p>
            </div>
        </div>
    </body>
    </html>
        """

        return html_content

def main():
    """主函数"""
    # 获取排行榜数据
    if len(sys.argv) > 1:
        rank_data_json = sys.argv[1]
    else:
        rank_data_json = os.environ.get('RANK_DATA_JSON', '{}')

    if not rank_data_json or rank_data_json == '{}':
        print("❌ 错误：未提供排行榜数据")
        print("请提供JSON数据或设置 RANK_DATA_JSON 环境变量")
        sys.exit(1)

    # 初始化处理器
    processor = LeaderboardProcessor()
    print(rank_data_json)
    # 1. 加载今日数据
    today_data = processor.load_today_data(rank_data_json)

    # 检查状态码
    if today_data.get('status') != 1:
        print(f"⚠️  警告：API返回状态码 {today_data.get('status')}，可能数据不完整")

    # 2. 查找我的数据
    player_list = today_data.get('list', [])
    my_data = processor.find_my_data(player_list)

    if not my_data:
        print(f"❌ 错误：未找到角色 '{processor.my_character_name}'")
        print("前5名玩家：")
        for i, player in enumerate(player_list[:5], 1):
            print(f"  {i}. {player.get('name')} - {player.get('col2')}")
        sys.exit(1)

    # 解析我的修炼时间
    my_time_str = my_data.get('col2', '0年0天')
    my_total_days = processor.parse_time_string(my_time_str)
    years = my_total_days // 365
    days = my_total_days % 365

    print(f"✅ 找到我的数据:")
    print(f"   角色: {my_data.get('name')}")
    print(f"   道行: {years}年{days}天")
    print(f"   区服: {my_data.get('zone')}")
    print(f"   系别: {my_data.get('col3')}")
    print(f"   排名: 第{my_data.get('rank', 0)}名")

    # 3. 计算与其他玩家的差距
    gaps = processor.calculate_gaps(my_total_days, player_list)
    print(f"📊 计算了与 {len(gaps)} 名道友的差距")

    # 显示最接近的5名对手
    if gaps:
        print("\n👥 最接近的10名对手:")
        for i, gap in enumerate(gaps[:10], 1):
            status = "领先" if gap['gap_days'] > 0 else "落后"
            print(f"  {i}. {gap['player']}: {status} {int(abs(gap['gap_days'])/365)}年")

    # 4. 保存今日分析
    analysis_file = processor.save_today_analysis(today_data, my_data, gaps)

    # 5. 加载历史数据并分析7天趋势
    historical_data = processor.load_historical_data(days=7)
    trend_result = processor.analyze_7day_trend(historical_data)

    # 6. 保存趋势分析结果
    trend_file = processor.save_trend_result(trend_result)

    # 7. 生成邮件内容
    email_html = processor.generate_email_html(trend_result, today_data, my_data)

    # 设置输出变量（用于GitHub Actions）
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as fh:
            print(f'analysis_file={analysis_file}', file=fh)
            print(f'trend_file={trend_file}', file=fh)
            print(f'processed=true', file=fh)
            print(f'my_rank={my_data.get("rank", 0)}', file=fh)
            print(f'my_days={my_total_days}', file=fh)
            print(f'has_update=true', file=fh)

            # 对HTML进行base64编码，避免特殊字符问题
            import base64
            email_html_encoded = base64.b64encode(email_html.encode('utf-8')).decode('utf-8')
            print(f'email_html={email_html_encoded}', file=fh)

    print(f"\n🎉 修仙排行榜分析完成！")
    print(f"📧 邮件内容已生成，共 {len(email_html)} 字符")

    # # 设置输出变量（用于GitHub Actions）
    # if 'GITHUB_OUTPUT' in os.environ:
    #     with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as fh:
    #         print(f'analysis_file={analysis_file}', file=fh)
    #         print(f'trend_file={trend_file}', file=fh)
    #         print(f'processed=true', file=fh)
    #         print(f'my_rank={my_data.get("rank", 0)}', file=fh)
    #         print(f'my_days={my_total_days}', file=fh)
    #
    # print(f"\n🎉 问道排行榜分析完成！")


if __name__ == "__main__":
    main()