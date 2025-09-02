# -*- coding: utf-8 -*-
# time: 2025/9/2 17:47
# file: wendao_test.py
# author: Jason
# email: 5515674@qq.com

import requests
import json
import os

RANK_URL = "https://wd.leiting.com/rank/getList"
LAST_CHAPTER_FILE = "last_chapter.json"

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

def save_chapter(chapter):
    """保存章节信息"""
    with open(LAST_CHAPTER_FILE, 'w', encoding='utf-8') as f:
        json.dump(chapter, f, ensure_ascii=False, indent=2)

def main():
    rank_list = get_rank_list()
    if not rank_list:
        print("无法获取当前排行榜信息")
        return False
    save_chapter(rank_list)
    return True

if __name__ == '__main__':
    rank_update = main()
    # 输出结果供GitHub Actions使用
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f'rank_update={str(rank_update).lower()}', file=fh)