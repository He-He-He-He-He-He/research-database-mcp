"""上海市人大法规规章规范性文件数据库公开搜索及 PDF 详情。"""
import release_runtime
import base64, io, re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
BASE = 'https://fgk.shrd.gov.cn'

def shanghai_law_search(query, page=1, page_size=10, timeout=25):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('标题关键词须为 1–200 字')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (page, page_size))) or not 1 <= page <= 100 or (not 1 <= page_size <= 50):
        raise ValueError('页码须为 1–100、每页 1–50 条')
    p = {'pageNo': page, 'pageSize': page_size, 'isLike': 1, 'wjbt': query.strip()}
    r = requests.get(BASE + '/fgk/newData', params=p, timeout=timeout)
    r.raise_for_status()
    d = r.json()
    if d.get('code') != 0 or not isinstance(d.get('count'), int) or (not isinstance(d.get('data'), list)):
        raise ValueError('上海法规数据库返回结构异常')
    if d['count'] < 0 or len(d['data']) > page_size or ((page - 1) * page_size < d['count'] and (not d['data'])):
        raise ValueError('上海法规目录页数与总数不一致')
    rows = []
    for x in d['data']:
        id = x.get('dataId', '')
        if not re.fullmatch('[A-Za-z0-9]+', id) or not x.get('wjbt'):
            raise ValueError('文档标识或标题异常')
        rows.append({'id': id, 'title': x['wjbt'], 'publication_date': x.get('gbrq'), 'effective_date': x.get('sxrq'), 'agency': x.get('tgjg'), 'detail_url': BASE + '/fgk/newDataShow?id=' + id + '&type=newData', 'source_record': x})
    return {'source': '上海市人大法规规章规范性文件数据库', 'source_url': r.url, 'query': query.strip(), 'page': page, 'page_size': page_size, 'upstream_total': d['count'], 'returned': len(rows), 'next_page': page + 1 if page * page_size < d['count'] and page < 100 else None, 'truncated': page * page_size < d['count'], 'items': rows, 'note': '站方标题模糊检索；数据涵盖多类地方文件，效力及现行状态需在详情和后续变更中核对；源数据更新可能改变跨页顺序。'}

def shanghai_law_detail(document_id, include_text=False, timeout=35):
    if not isinstance(document_id, str) or not re.fullmatch('[A-Za-z0-9]{1,80}', document_id):
        raise ValueError('文档 ID 无效')
    if not isinstance(include_text, bool):
        raise ValueError('include_text 须为布尔值')
    r = requests.get(BASE + '/fgk/newDataShow', params={'id': document_id, 'type': 'newData'}, timeout=timeout)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    title = s.select_one('.detail-tit')
    a = s.select_one('.detail-right a[href*="fgkZskDownload"]')
    source = urlparse(r.url)
    if source.scheme != 'https' or source.netloc != 'fgk.shrd.gov.cn':
        raise ValueError('详情跳转至非授权域名')
    embedded = re.search(b"\\bvar\\s+pdfbase64\\s*=\\s*'([A-Za-z0-9+/=]+)'", r.content)
    if title is None or (a is None and embedded is None):
        raise ValueError('详情或 PDF 未识别')
    pdf = urljoin(BASE, a['href']) if a else None
    if pdf:
        u = urlparse(pdf)
        if u.scheme != 'https' or u.netloc != 'fgk.shrd.gov.cn' or u.path != '/fileUpload/fgkZskDownload':
            raise ValueError('PDF 链接异常')
    fields = {}
    for div in s.select('.detail-left > div'):
        label = div.select_one('span')
        if label:
            fields[label.get_text(strip=True).rstrip('：:')] = div.get_text(' ', strip=True).replace(label.get_text(strip=True), '', 1).strip()
    out = {'source': '上海市人大法规规章规范性文件数据库', 'source_url': r.url, 'title': title.get_text(' ', strip=True), 'fields': fields, 'pdf_url': pdf, 'pdf_format': 'external' if pdf else 'embedded', 'note': '状态以数据库详情为准，须结合后续修改和正式公布核对；内嵌 PDF 无独立下载链接。PDF 文本提取可能遗漏图表、图片及排版，图片未 OCR。'}
    if include_text:
        if embedded is not None and pdf is None:
            encoded = embedded.group(1)
            if len(encoded) > 28 * 1024 * 1024:
                raise ValueError('内嵌 PDF 超过 20 MiB')
            try:
                content = base64.b64decode(encoded, validate=True)
            except ValueError as exc:
                raise ValueError('内嵌 PDF 编码异常') from exc
            if len(content) > 20 * 1024 * 1024 or not content.startswith(b'%PDF-'):
                raise ValueError('内嵌内容不是有效大小的 PDF')
        else:
            target = pdf
            for _ in range(4):
                rr = requests.get(target, timeout=timeout, stream=True, allow_redirects=False)
                if rr.status_code not in (301, 302, 303, 307, 308):
                    break
                location = rr.headers.get('Location')
                rr.close()
                if not location:
                    raise ValueError('PDF 重定向缺少地址')
                target = urljoin(target, location)
                next_url = urlparse(target)
                if next_url.scheme != 'https' or next_url.netloc != 'fgk.shrd.gov.cn':
                    raise ValueError('PDF 重定向到非授权域名')
            rr.raise_for_status()
            if rr.status_code != 200:
                raise ValueError('PDF 返回重定向或异常状态')
            content = bytearray()
            for chunk in rr.iter_content(65536):
                content.extend(chunk)
                if len(content) > 20 * 1024 * 1024:
                    raise ValueError('PDF 超过 20 MiB')
            if not content.startswith(b'%PDF-'):
                raise ValueError('下载内容不是 PDF')
        reader = PdfReader(io.BytesIO(content))
        out['pages'] = [{'page': i + 1, 'text': p.extract_text() or ''} for i, p in enumerate(reader.pages)]
    return out
