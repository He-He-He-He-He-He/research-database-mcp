"""2021年卫生健康事业公报：昆明医科大学简报转载正文的页级检索。"""
import release_runtime
import hashlib, re
import requests
import fitz
URL = 'https://www.kmmu.edu.cn/upload/20230303/2023030309531206.pdf'
ORIGINAL = 'https://www.nhc.gov.cn/guihuaxxs/c100132/202207/0f04dbc604aa473b9c57b1c0f9308776.shtml'
MAX = 8000000

def search(keyword='', offset=0, limit=10):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须为不超过100字的字符串')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 30):
        raise ValueError('offset 须非负，limit 须为1至30')
    try:
        with requests.get(URL, timeout=(10, 25), stream=True, allow_redirects=False) as r:
            r.raise_for_status()
            if r.status_code != 200:
                raise RuntimeError('大学转载PDF发生重定向或状态异常')
            size = 0
            chunks = []
            for c in r.iter_content(65536):
                size += len(c)
                if size > MAX:
                    raise RuntimeError('PDF超过大小限制')
                chunks.append(c)
    except requests.RequestException as e:
        raise RuntimeError('大学转载PDF请求失败: ' + type(e).__name__) from None
    raw = b''.join(chunks)
    if not raw.startswith(b'%PDF-'):
        raise RuntimeError('大学转载文件不是PDF')
    results = []
    key = re.sub('\\s+', '', keyword).casefold()
    with fitz.open(stream=raw, filetype='pdf') as pdf:
        if len(pdf) != 51:
            raise RuntimeError('简报页数已改变，须重新核验范围')
        if '2021年我国卫生健康事业发展统计公报' not in re.sub('\\s+', '', pdf[35].get_text()):
            raise RuntimeError('未识别公报起始位置')
        if '国家卫生健康委网站' not in re.sub('\\s+', '', pdf[50].get_text()):
            raise RuntimeError('未识别转载来源说明')
        for i in range(35, 51):
            page = pdf[i]
            text = page.get_text()
            if i == 35:
                text = text[text.index('2021 年我国卫生健康事业发展统计公报'):]
            if i == 50:
                text = text.split('（来源：国家卫生健康委网站')[0]
            if not key or key in re.sub('\\s+', '', text).casefold():
                results.append({'pdf_page': i + 1, 'text': text, 'embedded_images': len(page.get_images())})
    return {'source': '昆明医科大学简报转载国家卫生健康委员会统计公报', 'url': URL, 'original_url': ORIGINAL, 'year': 2021, 'publication_date': '2022-07-12', 'snapshot_sha256': hashlib.sha256(raw).hexdigest(), 'scope_pdf_pages': [36, 51], 'keyword': keyword, 'matched_pages': len(results), 'offset': offset, 'limit': limit, 'items': results[offset:offset + limit], 'note': '大学简报转载文字，仅第36–51物理页；未包含原公报全部图表和脚注，不保证转载完整。原网页本机返回HTTP 412，转载日期及统计口径须回原文核对；分页文本保留原换行，不自动解释数字。无匹配不代表不存在。'}
