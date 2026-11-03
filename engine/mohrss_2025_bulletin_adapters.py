"""2025 年全国人力资源与社会保障主要统计快报，湖北省人社厅转载 PDF。"""
import release_runtime
import io, json, re, subprocess
SOURCE = 'https://rst.hubei.gov.cn/zfxxgk/fdzdgknr/tjxx/2025/202602/t20260204_5869835.shtml'
PDF = 'https://rst.hubei.gov.cn/zfxxgk/fdzdgknr/tjxx/2025/202602/P020260204416157035466.pdf'

def category(n):
    if n <= 5:
        return '就业和再就业'
    if n <= 8:
        return '城镇职工基本养老保险'
    if n <= 11:
        return '城乡居民基本养老保险'
    if n <= 14:
        return '失业保险'
    if n <= 17:
        return '工伤保险'
    if n <= 20:
        return '劳动人事争议仲裁'
    return '劳动保障监察'

def report(keyword=''):
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError('需要可选依赖 pdfplumber；参见 requirements-optional.txt') from exc
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', PDF], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('官方转载 PDF 请求失败（curl %s）' % p.returncode)
    with pdfplumber.open(io.BytesIO(p.stdout)) as pdf:
        if len(pdf.pages) != 3:
            raise RuntimeError('公报页数变化，停止解析')
        page = pdf.pages[0]
        text = page.extract_text() or ''
        if '2025年1-12月人力资源和社会保障主要统计快报数据' not in text:
            raise RuntimeError('未识别预期公报标题')
        words = page.extract_words()
        head = next((w for w in words if w['text'] == '数量'), None)
        if not head:
            raise RuntimeError('未识别数量表头')
        tables = page.extract_tables()
        candidates = [t for t in tables if len(t) >= 20 and any(('统计指标' in str(c) for row in t[:2] for c in row))]
        if len(candidates) != 1:
            raise RuntimeError('未唯一识别指标表格')
        raw = [r for r in candidates[0] if r and str(r[0] or '').isdigit()]
        if len(raw) != 23 or [int(r[0]) for r in raw] != list(range(1, 24)):
            raise RuntimeError('指标行数或顺序变化')
        indices = {int(w['text']): w for w in words if re.fullmatch('\\d{1,2}', w['text']) and 110 <= w['x0'] <= 150 and (int(w['text']) in range(1, 24))}
        if set(indices) != set(range(1, 24)):
            raise RuntimeError('未能匹配全部行号')
        rows = []
        for r in raw:
            n = int(r[0])
            y = indices[n]['top']
            values = [w['text'] for w in words if w['x0'] >= head['x0'] - 12 and abs(w['top'] - y) < 4 and re.fullmatch('[0-9,.]+', w['text'])]
            if len(values) != 1:
                raise RuntimeError('第 %d 行数量未唯一识别' % n)
            rows.append({'number': n, 'category': category(n), 'indicator': ' '.join((r[1] or '').split()).replace(' ', ''), 'unit': r[2], 'value': values[0]})
        notes = '\n'.join((page.extract_text() or '' for page in pdf.pages[1:]))
    return {'source': '人力资源和社会保障部 2025 年 1—12 月主要统计快报（湖北省人社厅转载）', 'source_page': SOURCE, 'pdf_url': PDF, 'period': '2025年1—12月', 'rows': [r for r in rows if not keyword or keyword in r['indicator'] or keyword in r['category']], 'notes': notes, 'note': '快报数据，累计与时点指标混合，单位与统计范围见原表附注；城镇调查失业率为 12 月份。转载来源不等于原部站 PDF。'}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(report(a.keyword), ensure_ascii=False, indent=2))
