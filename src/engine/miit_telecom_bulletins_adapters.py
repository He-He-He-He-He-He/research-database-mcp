"""工信部 2019—2025 年通信业统计公报，快照和关键指标。"""
import release_runtime
from pathlib import Path
ROOT = Path(__file__).resolve().parent / '数据' / '工信部通信业公报'
SOURCES = {2024: {'primary': 'https://www.miit.gov.cn/jgsj/yxj/xxfb/art/2025/art_1ba37f13e02149d4b1cdffc41c78cc68.html', 'reprint': 'https://finance.sina.com.cn/jjxw/2025-01-26/doc-inehhqye0000524.shtml', 'metrics': {'固定宽带用户': (6.7, '亿户', '年末，三家基础电信企业'), '5G移动电话用户': (10.14, '亿户', '年末，2024年2月起纳入中国广电'), '移动互联网接入流量': (3376, '亿GB', '全年'), '移动互联网月户均流量': (18.18, 'GB/户·月', '全年月均'), '固定宽带业务收入': (2763, '亿元', '全年'), '新兴业务收入': (4348, '亿元', '全年，云计算、大数据、移动物联网、数据中心等')}}, 2025: {'primary': 'https://www.miit.gov.cn/jgsj/yxj/xxfb/art/2026/art_bea806f4dd20457cb0158795cc210aa7.html', 'reprint': 'https://jx.al.gov.cn/info/1762/31761.htm', 'metrics': {'固定宽带用户': (6.91, '亿户', '年末，三家基础电信企业'), '5G移动电话用户': (12.04, '亿户', '年末，含中国广电'), '移动互联网接入流量': (3958, '亿GB', '全年'), '移动互联网月户均流量': (20.74, 'GB/户·月', '全年月均'), '固定宽带业务收入': (2896, '亿元', '全年'), '新兴业务收入': (4508, '亿元', '全年，云计算、大数据、移动物联网、数据中心等')}}}
SOURCES.update({2021: {'primary': 'https://www.miit.gov.cn/gxsj/tjfx/txy/art/2022/art_e8b64ba8f29d4ce18a1003c4f4d88234.html', 'reprint': 'https://finance.sina.cn/tech/2022-02-03/detail-ikyakumy4095482.d.html?vt=4', 'metrics': {'固定宽带用户': (5.36, '亿户', '年末，三家基础电信企业'), '5G移动电话用户': (3.55, '亿户', '年末，依2021年公报调整后定义'), '移动互联网接入流量': (2216, '亿GB', '全年'), '移动互联网月户均流量': (13.36, 'GB/户·月', '全年月均'), '新兴业务收入': (2225, '亿元', '全年，云计算、大数据等，具体范围以当年原文为准')}}, 2022: {'primary': 'https://www.miit.gov.cn/gxsj/tjfx/txy/art/2023/art_77b586a554e64763ab2c2888dcf0b9e3.html', 'reprint': 'https://finance.sina.com.cn/tech/roll/2023-02-10/doc-imyfctke6249985.shtml', 'metrics': {'固定宽带用户': (5.9, '亿户', '年末，三家基础电信企业'), '5G移动电话用户': (5.61, '亿户', '年末'), '移动互联网接入流量': (2618, '亿GB', '全年'), '移动互联网月户均流量': (15.2, 'GB/户·月', '全年月均'), '固定宽带业务收入': (2402, '亿元', '全年'), '新兴业务收入': (3072, '亿元', '全年，数据中心、云计算、大数据、物联网等')}}, 2023: {'primary': 'https://www.miit.gov.cn/jgsj/yxj/xxfb/art/2024/art_7f101ab7d4b54297b4a18710ae16ff83.html', 'reprint': 'https://finance.sina.com.cn/jjxw/2024-01-24/doc-inaerexh6818495.shtml', 'metrics': {'固定宽带用户': (6.36, '亿户', '年末，三家基础电信企业'), '5G移动电话用户': (8.05, '亿户', '年末'), '移动互联网接入流量': (3015, '亿GB', '全年'), '移动互联网月户均流量': (16.85, 'GB/户·月', '全年月均'), '固定宽带业务收入': (2626, '亿元', '全年'), '新兴业务收入': (3564, '亿元', '全年，数据中心、云计算、大数据、物联网等')}}})
SOURCES.update({2019: {'primary': 'https://www.miit.gov.cn/gxsj/tjfx/txy/art/2020/art_2d61a3d279ba4d53aa944359d20b8d7f.html', 'reprint': 'https://epaper.cena.com.cn/oldpaper/content/2020-03/03/content_740229.htm', 'metrics': {'固定宽带用户': (4.49, '亿户', '年末，三家基础电信企业'), '移动互联网接入流量': (1220, '亿GB', '全年'), '移动互联网月户均流量': (7.82, 'GB/户·月', '全年月均')}}, 2020: {'primary': 'https://www.miit.gov.cn/gxsj/tjfx/txy/art/2021/art_057a331667154aaaa6767018dfd79a4f.html', 'reprint': 'https://finance.sina.com.cn/tech/2021-01-22/doc-ikftssan9611078.shtml', 'metrics': {'固定宽带用户': (4.84, '亿户', '年末，三家基础电信企业'), '移动互联网接入流量': (1656, '亿GB', '全年'), '移动互联网月户均流量': (10.35, 'GB/户·月', '全年月均')}}})

def telecom_bulletins(year=None, keyword=''):
    if year is not None:
        year = int(year)
        if year not in SOURCES:
            raise ValueError('当前快照仅覆盖 2019—2025 年')
    needle = ''.join(keyword.split()).casefold()
    results = []
    for y, s in sorted(SOURCES.items()):
        if year is not None and y != year:
            continue
        txt = (ROOT / f'{y}.txt').read_text(encoding='utf8')
        if needle and needle not in ''.join(txt.split()).casefold():
            continue
        results.append({'year': y, 'primary': s['primary'], 'reprint': s['reprint'], 'version': '该年公报所列值；2019数值版本未明确' if y == 2019 else '该年报告的当年数据为初步数', 'metrics': {k: {'value': v, 'unit': u, 'scope': scope} for k, (v, u, scope) in s['metrics'].items()}, 'reprint_text': txt})
    return {'coverage': '2019—2025 年通信业统计公报摘录', 'total': len(results), 'results': results}
