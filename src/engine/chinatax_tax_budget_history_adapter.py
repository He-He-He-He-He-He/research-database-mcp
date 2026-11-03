"""国家税务总局 2023 年度报告表 14：税收收入和预算收入历史原表。"""
import release_runtime
import hashlib
import requests
SOURCE = 'https://guangdong.chinatax.gov.cn/gdsw/yhyshjzt2024_zcwj_ndbg/2024-05/28/0db75ca0a2fa4a2ba9a8237da71fcb82/files/2f7d83825ff5476795dc70b6b6350d2c.pdf'
SHA256 = '6f477554fd071e97d953d86615231d44b002ba84734f07cb6b8a63651b808d4a'
ROWS = [(2013, 95398, 129210, 73.8), (2014, 103766, 140370, 73.9), (2015, 110604, 152269, 72.6), (2016, 115880, 159605, 72.6), (2017, 126013, 172593, 73.0), (2018, 137968, 183360, 75.2), (2019, 140439, 190390, 73.8), (2020, 136780, 182914, 74.8), (2021, 154573, 202555, 76.3), (2022, 142065, 203649, 69.8), (2023, 159040, 216784, 73.4)]

def history(year=None):
    if year is not None and (isinstance(year, bool) or not isinstance(year, int) or year not in range(2013, 2024)):
        raise ValueError('year 应为 2013 至 2023 的整数或 None')
    return {'source': '国家税务总局《中国税务年度报告（2023）》表 14，广东省税务局官网提供原文件', 'source_url': SOURCE, 'pdf_sha256': SHA256, 'pdf_page': 54, 'printed_page': 48, 'unit': '亿元；比例为百分比', 'items': [{'year': y, 'tax_revenue': tax, 'general_public_budget_revenue': budget, 'tax_revenue_share_percent': share} for y, tax, budget, share in ROWS if year is None or year == y], 'note': '人工逐行抄录，数据为该报告的历史快照；税收收入不含海关代征进口税收、关税和船舶吨税，扣除出口退税。比例按原表保留，统计口径及修订应核原报告。'}

def verify_source():
    with requests.get(SOURCE, timeout=(15, 90), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('上游重定向')
        h = hashlib.sha256()
        size = 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > 25000000:
                raise ValueError('文件超过大小上限')
            h.update(chunk)
    digest = h.hexdigest()
    return {'source_url': SOURCE, 'bytes': size, 'sha256': digest, 'matches_transcribed_source': digest == SHA256, 'note': '仅比较原文件哈希，不自动校验人工抄录。'}
