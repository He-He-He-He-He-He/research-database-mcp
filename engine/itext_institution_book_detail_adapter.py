"""爱教材学校 IP 会话图书题录详情；不读取正文。"""
import release_runtime
import re
from urllib.parse import urlsplit, parse_qs
import requests
from bs4 import BeautifulSoup
URL = 'https://www.itextbook.cn/f/book/bookDetail'

def _safe(value):
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if len(value) > 20000 or re.search('https?://|(?:token|cookie|session|authorization)\\s*[:=]|[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f]', value, re.I):
        return None
    return value

def detail(book_id, title, session=None):
    if not isinstance(book_id, str) or not re.fullmatch('[A-Za-z0-9]{32}', book_id):
        raise ValueError('书号须为检索结果的 32 位编号')
    if not isinstance(title, str) or not title.strip() or len(title) > 500 or re.search('[\\x00-\\x1f]', title):
        raise ValueError('须提供检索结果完整书名')
    try:
        r = (session or requests.Session()).get(URL, params={'bookId': book_id}, timeout=30, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('爱教材详情服务不可用')
        p = BeautifulSoup(r.content, 'html.parser')
        if not re.search('浙江大学\\s*IP\\s*(?:Reader|读者)', p.get_text(' ', strip=True), re.I):
            raise RuntimeError('未确认浙江大学 IP 读者')
        a = p.select_one('.book-title a.book_name')
        if not a:
            raise RuntimeError('未识别图书标题')
        u = urlsplit(a.get('href', ''))
        ids = parse_qs(u.query).get('bookId', [])
        if u.netloc not in ('', 'www.itextbook.cn') or u.path != '/f/cdf/goCdf' or ids != [book_id]:
            raise RuntimeError('详情书号未确认')
        actual = _safe(a.get_text(' ', strip=True))
        if actual != title.strip():
            raise RuntimeError('详情书名与检索结果不一致')

        def txt(selector):
            e = p.select_one(selector)
            return _safe(e.get_text(' ', strip=True)) if e else None
        fields = {}
        for e in p.select('.book-msg .msg-1 .text,.book-msg .msg-2'):
            label = e.select_one('.msg-label,.label-text')
            val = e.select_one('.msg-content,.label-ct')
            if label and val:
                key = label.get_text(' ', strip=True)
                if key in ('CLC', 'Language', 'PublishYear', 'publishCompany', 'EISBN', 'PISBN'):
                    if key in fields:
                        raise RuntimeError('详情字段重复')
                    fields[key] = _safe(val.get_text(' ', strip=True))
        status = txt('.status')
        if status not in ('nobuy', 'buy', 'buyed', None):
            status = None
        return {'source': '爱教材机构图书详情', 'institution': '浙江大学 IP Reader', 'book_id': book_id, 'title': actual, 'translated_title': txt('.book-hint'), 'author_raw': txt('.book-name'), 'classification_raw': fields.get('CLC'), 'language_raw': fields.get('Language'), 'publication_year_raw': fields.get('PublishYear'), 'publisher_raw': fields.get('publishCompany'), 'eisbn_raw': fields.get('EISBN'), 'pisbn_raw': fields.get('PISBN'), 'access_label_raw': status, 'description_raw': txt('.book-tabs .tabs-box'), 'note': '站方回显学校 IP 身份及书号、题名；检索范围未限定已购。原始访问标记仅反映本次页面，不能推断逐书全文权限；简介不等于正文，未读取正文或目录。'}
    except requests.RequestException:
        raise RuntimeError('爱教材详情连接失败') from None
