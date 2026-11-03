"""Offline evidence index for library-gaps; exact names and explicit catalogue-number contexts only."""
import release_runtime
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
EXCLUDE = {'馆藏缺口离线索引说明.md'}

def build_index():
    raw = subprocess.check_output([sys.executable, str(ROOT / 'research.py'), 'library-gaps', '--limit', '1000'], cwd=ROOT, text=True)
    gaps = json.loads(raw)
    lines = []
    for path in sorted(ROOT.glob('*.md')):
        if path.name in EXCLUDE:
            continue
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            line = line.strip()
            if line:
                lines.append((path.name, number, line))
    results = []
    for item in gaps['items']:
        ident, name = (item['id'], item['name'])
        id_pat = re.compile('(?:馆藏(?:目录)?|目录|条目|资源编号|馆藏编号|目录编号|ID)\\s*(?:ID\\s*)?[：:#（(]?\\s*' + re.escape(ident) + '(?!\\d)', re.I)
        name_lower = name.casefold()
        prefix = name_lower[:4]
        paren_id = re.compile('[（(]' + re.escape(ident) + '[）)]')
        evidence = []
        for filename, number, line in lines:
            match_type = '完整名称' if name_lower in line.casefold() else '明确编号' if id_pat.search(line) else '名称前缀及括号编号' if len(prefix) == 4 and prefix in line.casefold() and paren_id.search(line) else None
            if not match_type:
                continue
            evidence.append({'file': filename, 'line': number, 'matched_by': match_type, 'excerpt': line[:280] + ('…' if len(line) > 280 else '')})
        results.append({'id': ident, 'name': name, 'status': '找到匹配记录' if evidence else '未找到记录', 'evidence': evidence})
    return {'snapshot_date': gaps.get('snapshot_date'), 'scope': '仅检索工具包根目录 Markdown 中的完整名称或明确标注的馆藏编号；未匹配不等于未尝试，匹配也不自动证明业务接入。', 'count': len(results), 'matched': sum((bool(x['evidence']) for x in results)), 'items': results}

def main():
    parser = argparse.ArgumentParser(description='离线索引馆藏缺口与核查说明')
    parser.add_argument('--id', help='仅显示指定馆藏编号')
    parser.add_argument('--output', help='将 JSON 写入指定本地路径')
    args = parser.parse_args()
    data = build_index()
    if args.id:
        data['items'] = [x for x in data['items'] if x['id'] == args.id]
        data['count'] = len(data['items'])
        data['matched'] = sum((bool(x['evidence']) for x in data['items']))
    output = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
    else:
        print(output, end='')
if __name__ == '__main__':
    main()
