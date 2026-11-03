"""2023年公民科技信息获取渠道：论文正文检索与可核对摘录。"""
import release_runtime
import argparse
import json
from pathlib import Path
SOURCE = 'https://castjournals.cast.org.cn/joweb/kpyj/CN/1240340680552272222'
FILE = Path(__file__).parent / '数据/中国公民科学素质调查/2023科技信息渠道.html'

def search(keyword):
    if not keyword.strip():
        raise ValueError('关键词不能为空')
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise RuntimeError('正文检索需要 Beautiful Soup 4') from exc
    soup = BeautifulSoup(FILE.read_text(encoding='utf-8'), 'html.parser')
    nodes = soup.select('.mag_main_zhengwen_left_div_p')
    if not nodes:
        raise ValueError('网页正文结构不可识别')
    items = []
    for node in nodes:
        text = node.get_text(' ', strip=True)
        if ''.join(keyword.split()) in ''.join(text.split()):
            items.append({'paragraph_id': node.get('id'), 'text': text})
    return {'year': 2023, 'source': SOURCE, 'keyword': keyword, 'items': items}

def channels():
    general = [('电视', 85.5), ('互联网及移动互联网', 79.2), ('面对面交流', 34.3), ('广播', 31.9), ('报纸', 26.8), ('图书', 22.3), ('期刊杂志', 20.0)]
    internet = [('社交平台', 75.8), ('短视频平台', 68.3), ('搜索引擎', 54.5)]
    return {'year': 2023, 'source': SOURCE, 'unit': '%', 'indicator': '在首选、其次或第三中选择该渠道的比例', 'general': {'denominator': '受访公民', 'rows': [{'channel': k, 'value': v} for k, v in general]}, 'internet': {'denominator': '首选、其次或第三选择互联网获取科技信息的受访者', 'rows': [{'channel': k, 'value': v} for k, v in internet]}, 'note': '多重响应比例不可相加；不同分母不可直接比较。仅摘录正文明确数值。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    s.add_parser('channels')
    q = s.add_parser('search')
    q.add_argument('keyword')
    a = p.parse_args()
    print(json.dumps(channels() if a.command == 'channels' else search(a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
