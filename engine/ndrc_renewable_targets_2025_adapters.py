"""发改委 2025 年各省可再生能源电力消纳责任权重（政策目标）。"""
import release_runtime
import argparse
import json
import re
import requests
import fitz
URL = 'https://www.ndrc.gov.cn/xwdt/tzgg/202507/P020250711615437918932.pdf'
POLICY_URL = 'https://www.ndrc.gov.cn/xwdt/tzgg/202507/t20250711_1399143.html'

def renewable_targets(region=None, timeout=15):
    if region is not None and (not isinstance(region, str) or len(region) > 20):
        raise ValueError('地区无效')
    response = requests.get(URL, timeout=timeout)
    response.raise_for_status()
    if not response.content.startswith(b'%PDF-'):
        raise ValueError('官方附件非 PDF')
    doc = fitz.open(stream=response.content, filetype='pdf')
    if len(doc) != 1:
        raise ValueError('官方附件页数已变化')
    text = doc[0].get_text()
    doc.close()
    if '2025 年总量消纳责任权重' not in text or '备注：' not in text:
        raise ValueError('官方表头或注释已变化')
    body = text.split('2025 年非水电消纳责任权重', 1)[1].split('备注：', 1)[0]
    parts = [line.strip() for line in body.splitlines() if line.strip()]
    if len(parts) != 90:
        raise ValueError('表格结构或地区数量已变化')
    items = []
    for i in range(0, len(parts), 3):
        name, total, nonhydro = parts[i:i + 3]
        if not re.fullmatch('\\d+\\.\\d+%', total) or not re.fullmatch('\\d+\\.\\d+%', nonhydro):
            raise ValueError('权重格式异常')
        items.append({'region': name, 'total_target': total, 'nonhydro_target': nonhydro})
    if region is not None:
        items = [x for x in items if x['region'] == region]
    return {'source': '国家发展改革委、国家能源局', 'source_url': URL, 'policy_url': POLICY_URL, 'year': 2025, 'items': items, 'notes': '备注：' + text.split('备注：', 1)[1].strip(), 'note': '本表为下达的责任权重，不是实际完成率；西藏不考核，新疆只监测。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--region')
    a = p.parse_args()
    print(json.dumps(renewable_targets(a.region), ensure_ascii=False, indent=2))
