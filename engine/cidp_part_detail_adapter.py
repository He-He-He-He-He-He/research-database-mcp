"""CIDP 公开三维模型产品的网页规格表；不下载模型。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from cidp_search_adapters import BASE

def detail(part_id, expected_title, session=None):
    if not isinstance(part_id, str) or not re.fullmatch('[0-9a-fA-F]{32}', part_id):
        raise ValueError('产品编号须为 32 位十六进制')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 300 or re.search('[\\x00-\\x1f]', expected_title):
        raise ValueError('须提供完整产品名称')
    s = session or requests.Session()
    try:
        r = s.get(BASE + '/web/Part/' + part_id, timeout=25, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('模型详情服务不可用')
        p = BeautifulSoup(r.content, 'html.parser')
        title = p.title.get_text(' ', strip=True) if p.title else ''
        if title != '海枣数字-' + expected_title.strip():
            raise RuntimeError('网页标题与检索结果不一致')
        table = p.select_one('table#resultTab')
        if not table:
            raise RuntimeError('未找到具体规格表')
        trs = table.select('tr')
        if not trs or len(trs) > 10001:
            raise RuntimeError('规格表行数异常')

        def cells(tr):
            return [v.get_text(' ', strip=True) for v in tr.find_all(['td', 'th'], recursive=False)]
        rows = [cells(tr) for tr in trs]
        if not rows[0] or any((len(row) != len(rows[0]) for row in rows[1:])):
            raise RuntimeError('规格表列数不一致')
        meta = []
        for t in p.select('table.dzs-wenzi'):
            for tr in t.select('tr'):
                vals = cells(tr)
                if any(vals):
                    meta.append(vals)
        return {'source': 'CIDP 制造业资源平台公开产品详情', 'part_id': part_id, 'title': expected_title.strip(), 'metadata_rows_raw': meta, 'headers_raw': rows[0], 'rows_raw': rows[1:], 'note': '网页表头、单元格与空列按显示文本保留；列名可能省略单位，不能自行推断。学校机构身份、模型下载与逐项使用权限未验证；不输出下载链接。'}
    except requests.RequestException:
        raise RuntimeError('CIDP 详情连接失败') from None
