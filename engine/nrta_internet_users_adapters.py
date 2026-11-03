"""国家广电总局网络视听年度付费及短视频上传用户数据。"""
import release_runtime
import json, re, subprocess
from nrta_broadcast_statistics_adapters import _Paragraphs, SOURCES
PATTERNS = {'互联网视频年度付费用户': '互联网视频年度付费用户(\\d+(?:\\.\\d+)?)亿户', '互联网音频年度付费用户': '互联网音频年度付费用户(\\d+(?:\\.\\d+)?)亿户', '短视频上传用户': '短视频上传用户(超过|达到)?(\\d+(?:\\.\\d+)?)亿户'}

def report(year, keyword=''):
    if int(year) not in (2023, 2024, 2025):
        raise ValueError('仅支持 2023—2025 年')
    url = SOURCES[int(year)]
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('广电总局公报读取失败（curl %s）' % p.returncode)
    parser = _Paragraphs()
    parser.feed(p.stdout.decode('utf-8'))
    pars = parser.paragraphs
    rows = []
    for label, pattern in PATTERNS.items():
        results = [(p, m) for p in pars for m in re.finditer(pattern, p)]
        if len(results) != 1:
            raise RuntimeError('无法唯一识别“%s”' % label)
        paragraph, match = results[0]
        qualifier = match.group(1) or '' if label == '短视频上传用户' else ''
        value = match.group(2) if label == '短视频上传用户' else match.group(1)
        rows.append({'indicator': label, 'value': value, 'unit': '亿户', 'qualifier': qualifier, 'source_excerpt': match.group(0), 'source_paragraph': paragraph})
    notes = [x for x in pars if re.match('^\\[\\d+\\]', x)]
    return {'source': '国家广播电视总局全国广播电视行业统计公报', 'year': int(year), 'url': url, 'items': [r for r in rows if not keyword or keyword in r['indicator']], 'footnotes': notes, 'note': '视频和音频为年度付费用户，短视频为上传用户；计量单位为户，不能直接当成人口数或去重人数，超过表示下限而非精确数。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=[2023, 2024, 2025])
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(report(a.year, a.keyword), ensure_ascii=False, indent=2))
