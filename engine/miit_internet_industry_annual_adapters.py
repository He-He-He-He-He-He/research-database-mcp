"""工信部互联网行业运行报告：2022—2025 年原文及核心数字快照。"""
import release_runtime
from pathlib import Path
from urllib.parse import quote
ROOT = Path(__file__).resolve().parent / '数据' / '工信部互联网运行报告'
META = {2022: {'pdf_id': '20230207093131219', 'suffix': '运行情况', 'primary': 'https://www.miit.gov.cn/gxsj/tjfx/hlw/art/2023/art_40202ca145fe4d34a5ca4cf2f5dfc91e.html', '收入': 14590, '收入同比': -1.1, '利润': 1415, '利润同比': 3.3, '研发': 771.8, '研发同比': 7.7}, 2023: {'pdf_id': '20240206142118896', 'suffix': '运行情况', 'primary': 'https://www.miit.gov.cn/jgsj/yxj/xxfb/art/2024/art_3aa3fa8990d64171a1fd5682dd365ea8.html', '收入': 17483, '收入同比': 6.8, '利润': 1295, '利润同比': 0.5, '研发': 943.2, '研发同比': -3.7}, 2024: {'pdf_id': '20250211090459669', 'suffix': '运行平稳', 'primary': 'https://www.miit.gov.cn/gxsj/tjfx/hlw/art/2025/art_e745b288fa3a4cb6b40cf05dee1ebe76.html', '收入': 18049, '收入同比': -0.1, '利润': 1508, '利润同比': -6.4, '研发': 995.7, '研发同比': 2.8}, 2025: {'pdf_id': '20260209100839635', 'suffix': '运行情况', 'primary': 'https://www.miit.gov.cn/jgsj/yxj/xxfb/art/2026/art_658e7a98637e462f9df431cfe99ffbdc.html', '收入': 20473, '收入同比': 1.5, '利润': 1540, '利润同比': -8.3, '研发': 1126, '研发同比': 6.5}}

def internet_industry_annual(year=None, keyword=''):
    if year is not None:
        year = int(year)
        if year not in META:
            raise ValueError('当前快照仅覆盖 2022—2025 年')
    needle = ''.join(keyword.split()).casefold()
    results = []
    for y, m in META.items():
        if year is not None and y != year:
            continue
        content = (ROOT / f'{y}.txt').read_text(encoding='utf8')
        if needle and needle not in ''.join(content.split()).casefold():
            continue
        filename = f"{y}年互联网和相关服务业{m['suffix']}.pdf"
        url = 'https://cif.mofcom.gov.cn/cif/html/upload/' + m['pdf_id'] + '_' + quote(filename)
        results.append({'year': y, 'scope': '上年互联网和相关服务收入2000万元及以上的规模以上企业；同比按可比口径', 'source_url': m['primary'], 'reprint_pdf': url, 'local_pdf': str(ROOT / f'{y}.pdf'), 'metrics': {k: {'value': m[k], 'unit': '%' if k.endswith('同比') else '亿元'} for k in ['收入', '收入同比', '利润', '利润同比', '研发', '研发同比']}, 'text': content})
    return {'source': '工信部运行监测协调局年度运行报告；本地原文来自商务部中国投资指南转载', 'coverage': '2022—2025', 'note': '各年同比按官方可比口径，不应直接以相邻年份发布的绝对值计算或验证。', 'total': len(results), 'results': results}
