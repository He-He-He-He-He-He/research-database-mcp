"""瑞丽市司法局公开的 2025 年法律服务统计报表。"""
import release_runtime
import subprocess
from moe_education_statistics_adapters import _LeafTables
SOURCES = {'aid': ('法律援助案件及各类受援人统计表', 'https://www.rl.gov.cn/sfj/Web/_F0_0_6GTGPBMS9B1D909CC029449CA6.htm'), 'lawyer': ('律师公益法律服务统计表', 'https://www.rl.gov.cn/sfj/Web/_F0_0_6HEZA6Q223279F3F8D24449B95.htm')}

def ruili_legal_services_tables():
    return [{'key': k, 'year': 2025, 'title': v[0], 'url': v[1]} for k, v in SOURCES.items()]

def ruili_legal_services_table(key):
    if key not in SOURCES:
        raise ValueError('key 须为 aid 或 lawyer')
    title, url = SOURCES[key]
    data = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')
    parser = _LeafTables()
    parser.feed(data)
    if len(parser.tables) != 1 or not parser.tables[0] or '2025-01-01' not in str(parser.tables[0][:3]):
        raise ValueError('网页结构或统计时段发生变化，未返回猜测结果')
    return {'year': 2025, 'region': '云南省瑞丽市', 'title': title, 'source_url': url, 'rows': parser.tables[0], 'note': '原表单元格与 rowspan/colspan 按原文保留；统计单位及口径以表头、注释为准。'}
