"""广电总局全国广播电视和网络视听行业部分收入数据。"""
import release_runtime
import json, re, subprocess
from nrta_broadcast_statistics_adapters import _Paragraphs, SOURCES
PATTERNS = {'短视频及网络直播': '短视频、网络直播等收入', '网络视听用户付费和节目版权': '网络视听用户付费、节目版权等服务收入', '广告': '广告收入', '有线电视网络': '有线电视网络收入', '节目制作与销售': '节目制作、销售等节目相关收入'}

def report(year, keyword=''):
    if int(year) not in (2024, 2025):
        raise ValueError('当前仅支持 2024 和 2025 年')
    url = SOURCES[int(year)]
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('广电总局公报读取失败（curl %s）' % p.returncode)
    parser = _Paragraphs()
    parser.feed(p.stdout.decode('utf-8'))
    paragraphs = parser.paragraphs
    matches = [x for x in paragraphs if '实际创收收入中' in x]
    if len(matches) != 1:
        raise RuntimeError('未唯一识别实际创收收入段落')
    paragraph = matches[0]
    rows = []
    for label, prefix in PATTERNS.items():
        pattern = re.escape(prefix) + '(\\d+(?:\\.\\d+)?)亿元，同比(增长|下降)(\\d+(?:\\.\\d+)?)%'
        found = list(re.finditer(pattern, paragraph))
        if len(found) != 1:
            raise RuntimeError('无法唯一识别 %s 的金额和增速' % label)
        m = found[0]
        rows.append({'category': label, 'original_label': prefix, 'revenue_100m_yuan': m.group(1), 'growth_direction': m.group(2), 'growth_pct': m.group(3), 'source_excerpt': m.group(0)})
    notes = [x for x in paragraphs if re.match('^\\[\\d+\\]', x)]
    return {'source': '国家广播电视总局全国广播电视行业统计公报', 'year': int(year), 'url': url, 'items': [x for x in rows if not keyword or keyword in x['category'] or keyword in x['original_label']], 'source_paragraph': paragraph, 'footnotes': notes, 'note': '按公报实际创收收入分项提取，单位亿元；增速方向与数值分开保留，口径和平台构成须核对原公报。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=[2024, 2025])
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(report(a.year, a.keyword), ensure_ascii=False, indent=2))
