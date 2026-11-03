"""2018年人力资源和社会保障统计公报：社会保障学会转载PDF页级检索。"""
import release_runtime
import hashlib, re
import requests
import fitz
URL = 'https://caoss.org.cn/UploadFile/news/file/20190612/20190612093987298729.pdf'
ORIGINAL = 'https://www.mohrss.gov.cn/'
MAX = 8000000

def search(keyword='', offset=0, limit=10):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须不超过100字')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 20):
        raise ValueError('分页无效')
    try:
        with requests.get(URL, timeout=(10, 25), stream=True, allow_redirects=False) as r:
            r.raise_for_status()
            if r.status_code != 200:
                raise RuntimeError('转载PDF状态异常或重定向')
            chunks = []
            size = 0
            for c in r.iter_content(65536):
                size += len(c)
                if size > MAX:
                    raise RuntimeError('PDF超过8MB限制')
                chunks.append(c)
    except requests.RequestException as e:
        raise RuntimeError('转载PDF请求失败: ' + type(e).__name__) from None
    raw = b''.join(chunks)
    if not raw.startswith(b'%PDF-'):
        raise RuntimeError('响应不是PDF')
    key = re.sub('\\s+', '', keyword).casefold()
    items = []
    with fitz.open(stream=raw, filetype='pdf') as pdf:
        if len(pdf) != 11 or '2018年度人力资源和社会保障事业发展统计公报' not in re.sub('\\s+', '', pdf[0].get_text()):
            raise RuntimeError('PDF页数或报告标题不符')
        for i, page in enumerate(pdf):
            text = page.get_text()
            if not key or key in re.sub('\\s+', '', text).casefold():
                items.append({'pdf_page': i + 1, 'text': text, 'embedded_images': len(page.get_images())})
    return {'source': '人力资源和社会保障部，中国社会保障学会转载', 'url': URL, 'original_source': ORIGINAL, 'year': 2018, 'sha256': hashlib.sha256(raw).hexdigest(), 'total_pages': 11, 'keyword': keyword, 'matched_pages': len(items), 'offset': offset, 'limit': limit, 'items': items[offset:offset + limit], 'note': '历史报告PDF页级文本；来源为中国社会保障学会转载，页码为PDF物理页序，图表及嵌入图片未识别，表格顺序、脚注、单位和跨年口径须核原件，未命中不能证明无数据。'}
