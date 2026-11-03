"""国家网信办新闻服务中央审批名单：各类别原始 PDF 行。"""
import release_runtime
import hashlib, re
from io import BytesIO
from bs4 import BeautifulSoup
from pypdf import PdfReader
from cac_news_licenses_adapters import latest, _get, HOST
CENTRAL = ['互联网站', '应用程序', '论坛', '公众账号', '网络直播', '其他']
OTHER = ['互联网站', '应用程序', '论坛', '博客', '微博客', '公众账号', '网络直播', '其他']

def licensed_services(group, service_type, keyword=''):
    """按中央新闻单位/其他单位及服务类型查最新名单，保留原始文本。"""
    if group not in ('中央新闻单位', '其他单位'):
        raise ValueError('group 须为中央新闻单位或其他单位')
    expected_types = CENTRAL if group == '中央新闻单位' else OTHER
    if service_type not in expected_types:
        raise ValueError('该组不包含该服务类型')
    info = latest()
    links = [x for x in info['links'] if x['url'].startswith(HOST + '/')]
    if [x['label'] for x in links] != CENTRAL + OTHER:
        raise RuntimeError('公告分类结构已变化，需重新核验组别')
    selection = links[:len(CENTRAL)] if group == '中央新闻单位' else links[len(CENTRAL):]
    detail = next((x['url'] for x in selection if x['label'] == service_type))
    b = BeautifulSoup(_get(detail), 'html.parser').select_one('#BodyLabel')
    paths = list(dict.fromkeys(re.findall('(?:(?:https?:)?//www\\.cac\\.gov\\.cn)?(/rootimages/uploadimg/[^"\\s?]+?\\.pdf)', str(b))))
    if len(paths) != 1:
        raise RuntimeError('未识别唯一名单 PDF')
    url = HOST + paths[0]
    raw = _get(url)
    if not raw.startswith(b'%PDF'):
        raise RuntimeError('响应不是 PDF')
    pdf = PdfReader(BytesIO(raw))
    rows = []
    expected = None
    for i, p in enumerate(pdf.pages, 1):
        txt = p.extract_text() or ''
        if i == 1:
            m = re.search('（共(\\d+)个）', txt)
            if not m:
                raise RuntimeError('未识别官方名单数量')
            expected = int(m.group(1))
        for line in txt.splitlines():
            line = line.strip()
            if not line or re.match('^(?:属地\\s+)?序号\\s+服务名称', line):
                continue
            m = re.match('^([^\\d]*?)\\s*(\\d{1,5})\\s+(.+)$', line)
            if m and int(m.group(2)) == len(rows) + 1:
                rows.append({'number': int(m.group(2)), 'page': i, 'raw_text': ' '.join((x for x in (m.group(1).strip(), m.group(3)) if x))})
            elif rows:
                rows[-1]['raw_text'] += ' ' + line
    if len(rows) != expected:
        raise RuntimeError(f'名单序号 {len(rows)} 与官网总数 {expected} 不符，拒绝返回')
    matching = [x for x in rows if keyword in x['raw_text']]
    return {'group': group, 'service_type': service_type, 'announcement': info['source'], 'detail': detail, 'pdf': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'expected': expected, 'matching': len(matching), 'rows': matching}
