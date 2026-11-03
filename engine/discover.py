"""在本机离线查找工具包的来源说明和调用示例。"""
import release_runtime
import argparse
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def discover(keyword, limit=20):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('请输入 1–200 个字符的关键词')
    if not 1 <= limit <= 100:
        raise ValueError('结果数量须在 1–100 之间')
    needle = keyword.strip().casefold()
    hits = []
    for path in ROOT.glob('*.md'):
        lines = path.read_text(encoding='utf-8').splitlines()
        matches = [(i + 1, line.strip()) for i, line in enumerate(lines) if needle in line.casefold()]
        name_match = needle in path.name.casefold()
        if not matches and (not name_match):
            continue
        commands = []
        for _, line in matches:
            commands.extend(re.findall('`((?:python3 |curl |await api\\.)[^`]+)`', line))
            if line.lstrip().startswith(('python3 ', 'curl ', 'await api.')):
                commands.append(line.strip())
        if not commands:
            commands = [line.strip() for line in lines if line.lstrip().startswith(('python3 ', 'curl ', 'await api.'))]
        commands = list(dict.fromkeys(commands))[:5]
        hits.append({'file': path.name, 'title': next((x.lstrip('# ').strip() for x in lines if x.startswith('# ')), path.stem), 'matches': [{'line': i, 'text': text[:400]} for i, text in matches[:3]], 'examples': commands, 'filename_match': name_match})
    hits.sort(key=lambda x: (not x['filename_match'], x['file'].casefold()))
    return {'query': keyword, 'total_matching_documents': len(hits), 'items': hits[:limit], 'note': '仅查本地说明，不查询上游或证明当前权限；示例须核对各文件中的适用范围。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(discover(a.keyword, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
