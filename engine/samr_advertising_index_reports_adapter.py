"""中国广告业发展指数报告：湖南省政府官网转载的官方报告原文查询。"""
import release_runtime
import hashlib, subprocess
import fitz
SOURCES = {2025: {'url': 'https://www.hunan.gov.cn/zqt/zcsd/202506/33712921/files/b9de07218055469788c9ac300c9cbcfe.pdf', 'data_year': 2024}, 2026: {'url': 'https://www.hunan.gov.cn/zqt/zcsd/202606/34010646/files/6a8fcb5dc7934c838054421e1b874be9.pdf', 'data_year': 2025}}

def catalog():
    return {'source': '市场监管总局与中国经济信息社中国广告业发展指数报告，湖南省政府官网转载', 'items': [{'report_year': y, 'data_year': v['data_year'], 'pdf_url': v['url']} for y, v in sorted(SOURCES.items(), reverse=True)], 'note': '仅固定验证的 2025、2026 两份报告，不是完整历史目录；报告年份与主要统计年份不同。'}

def search(report_year, keyword, limit=10):
    if isinstance(report_year, bool) or not isinstance(report_year, int) or report_year not in SOURCES:
        raise ValueError('报告年份目前支持 2025、2026')
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('关键词须为 1–100 字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit 须为 1–50')
    item = SOURCES[report_year]
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '90', '--max-filesize', '40000000', item['url']], capture_output=True, timeout=95)
    if p.returncode:
        raise RuntimeError('官方报告下载失败（curl 状态 %s）' % p.returncode)
    raw = p.stdout
    if len(raw) > 40000000 or not raw.startswith(b'%PDF-'):
        raise ValueError('来源文件非预期 PDF 或过大')
    d = fitz.open(stream=raw, filetype='pdf')
    if len(d) > 300:
        raise ValueError('页数超限')
    hits = []
    count = 0
    for page in d:
        text = page.get_text()
        if keyword in text:
            count += 1
            if len(hits) < limit:
                hits.append({'page': page.number + 1, 'text': text})
    return {'source': '市场监管总局与中国经济信息社中国广告业发展指数报告，湖南省政府官网转载', 'report_year': report_year, 'main_data_year': item['data_year'], 'pdf_url': item['url'], 'pdf_sha256': hashlib.sha256(raw).hexdigest(), 'pdf_pages': len(d), 'keyword': keyword, 'matched_pages': count, 'hits': hits, 'note': '返回物理页可提取文字；图形、图片和扫描页未 OCR，表格阅读顺序可能错乱，需核原图表和注释。报告年份不同于主要数据年份；省际指数和收入比较应核指标范围、方法和修订。'}
