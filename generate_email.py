# -*- coding: utf-8 -*-
# time: 2025/9/2 17:47
# file: wendao_test.py
# author: Jason
# email: 5515674@qq.com

import requests
import json
import os
from datetime import datetime, timedelta
import jinja2

RANK_URL = "https://wd.leiting.com/rank/getList"
LAST_CHAPTER_FILE = "last_chapter.json"

def load_template(template_path):
    """加载HTML模板"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return jinja2.Template(f.read())

def get_rank_list():
    """获取排行榜信息"""
    try:
        headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        }
        data = {
            "type":"108",
            "level":"120-129",
            "zone":"1462"
        }
        response = requests.post(RANK_URL,data=data, headers=headers)
        return response.json().get("list")
    except Exception as e:
        print(f"获取排行榜信息时出错: {e}")
    return None


def process_rank_data(rank_data):
    """处理排行榜数据"""
    processed_data = []
    new_books_count = len(rank_data)

    for item in rank_data:
        # 确定变化类型
        # change = item.get('change', 'same')
        # change_text = item.get('change_text', '→')

        # if change == 'new':
        #     new_books_count += 1

        processed_data.append({
            'name': item['name'],
            'zone': item['zone'],
            'col2': item['col2'],
            'col3': item['col3'],
        })

    return processed_data, new_books_count


def generate_html_email(rank_data, template_path):
    """生成HTML邮件内容"""
    # 处理数据
    processed_data, new_books_count = process_rank_data(rank_data)

    # 准备模板数据
    template_data = {
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'next_update_time': (datetime.now() + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M'),
        'rank_data': processed_data,
        'rank_count': len(processed_data),
        'new_books_count': new_books_count,
    }
    # 渲染模板
    template = load_template(template_path)
    html_content = template.render(template_data)

    return html_content

def save_chapter(chapter):
    """保存章节信息"""
    with open(LAST_CHAPTER_FILE, 'w', encoding='utf-8') as f:
        json.dump(chapter, f, ensure_ascii=False, indent=2)

def main():
    rank_data_json = os.environ.get('RANK_DATA', '[]')
    rank_data = json.loads(rank_data_json)
    if not rank_data:
        print("无法获取当前排行榜信息")
        return False
    # 生成HTML内容
    template_path = 'templates/rank_email.html'
    html_content = generate_html_email(rank_data, template_path)
    # 输出到文件（用于调试）
    # with open('generated_email.html', 'w', encoding='utf-8') as f:
    #     f.write(html_content)
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as fh:
        print(f'email_html={html_content}', file=fh)

if __name__ == '__main__':
    main()