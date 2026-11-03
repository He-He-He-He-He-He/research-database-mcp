"""ITF Transport Outlook 2023, PDF page text search."""
import release_runtime
import io, requests, fitz
URL = 'https://www.oecd.org/content/dam/oecd/en/publications/reports/2023/05/itf-transport-outlook-2023_4466cd78/b6cc9ad5-en.pdf'
LANDING = 'https://www.oecd.org/en/publications/itf-transport-outlook-2023_b6cc9ad5-en.html'

def search(keyword, limit=10, version='2023'):
    versions = {'2023': (URL, LANDING, '2023-05-24'), '2021': ('https://www.oecd.org/content/dam/oecd/en/publications/reports/2021/05/itf-transport-outlook-2021_fff2ec9f/16826a30-en.pdf', 'https://www.oecd.org/en/publications/itf-transport-outlook-2021_16826a30-en.html', '2021-05-17'), '2017': ('https://www.oecd.org/content/dam/oecd/en/publications/reports/2017/01/itf-transport-outlook-2017_g1g72df1/9789282108000-en.pdf', 'https://www.oecd.org/en/publications/itf-transport-outlook-2017_9789282108000-en.html', '2017-01-30')}
    if version not in versions:
        raise ValueError('版本须为 2017、2021 或 2023')
    url, landing, release = versions[version]
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('请输入 1 至 100 字符关键词')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('结果上限应为 1 至 50')
    with requests.get(url, timeout=50, stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        data = bytearray()
        for b in r.iter_content(65536):
            data.extend(b)
            if len(data) > 15000000:
                raise ValueError('PDF 超过大小限制')
        modified = r.headers.get('Last-Modified')
    doc = fitz.open(stream=bytes(data), filetype='pdf')
    try:
        found = []
        total = 0
        for n, page in enumerate(doc):
            text = page.get_text()
            if keyword.casefold() in text.casefold():
                total += 1
                if len(found) < limit:
                    found.append({'pdf_page': n + 1, 'text': text})
        return {'source_pdf': url, 'publication_page': landing, 'report_year': int(version), 'report_release': release, 'revision': '文件标注 2021 年 10 月修订版，非 5 月首版' if version == '2021' else '未确认首版不可变', 'server_last_modified': modified, 'pdf_metadata': doc.metadata, 'page_count': len(doc), 'keyword': keyword, 'matched_pages': total, 'returned_pages': found, 'caution': 'PDF 物理页码；报告发布日期与当前文件服务器/PDF 修改时间不同；2021 版标明 2021 年 10 月修订，其他版本首版不可变未证。2050 结果为模型政策情景而非已观测现实，须结合两种情景、单位及基期；文字提取不保证图形、颜色或表格的完整和顺序，请核对原页。上限只影响返回页数，匹配页数不代表资料或图表完整覆盖。'}
    finally:
        doc.close()
