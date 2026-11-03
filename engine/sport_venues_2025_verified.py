"""Manually transcribed, image-verified 2025 sport venue table (fixed snapshot)."""
import release_runtime
import hashlib
import requests
URL = 'https://www.sport.gov.cn/jjs/n5043/c29462896/part/29462992.jpg'
SHA256 = 'c765016e69d2fa07eed34faeb462e64f0aba47bd364b5c17423cf09214404e52'
ROWS = [('人均体育场地面积', '3.11', '平方米'), ('体育场地数量', '500.37', '万个'), ('田径场地', '21.11', '万个'), ('游泳场地', '4.07', '万个'), ('足球场地', '16.58', '万个'), ('篮球场地', '125.27', '万个'), ('排球场地', '12.10', '万个'), ('乒乓球场地', '114.07', '万个'), ('羽毛球场地', '31.64', '万个'), ('滑冰场地', '1723', '个'), ('滑雪场地', '903', '个'), ('全民健身路径', '113.29', '万个'), ('健身房', '15.63', '万个'), ('健身步道数量', '18.20', '万个'), ('健身步道长度', '43.03', '万公里'), ('体育场地总面积', '43.72', '亿平方米')]

def query(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须不超过100字')
    with requests.get(URL, timeout=30, stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        if r.status_code != 200:
            raise RuntimeError('官方图片状态异常')
        parts = []
        size = 0
        for chunk in r.iter_content(65536):
            size += len(chunk)
            if size > 8000000:
                raise RuntimeError('图片超过8MB限制')
            parts.append(chunk)
    digest = hashlib.sha256(b''.join(parts)).hexdigest()
    if digest != SHA256:
        raise RuntimeError('官方图片已变化，人工转录须重新核验')
    items = [{'indicator': n, 'value': v, 'unit': u} for n, v, u in ROWS if keyword in n]
    return {'source': '国家体育总局2025年全国体育场地统计调查', 'source_url': URL, 'as_of': '2025-12-31', 'source_image_sha256': digest, 'method': '人工根据官方图像主要数据表和正文核对转录，非机器OCR或自动全表解析', 'matched': len(items), 'items': items, 'note': '固定快照；总面积来自正文，其余为图末主要数据表；步道数量和长度拆为两条。各子类与总计可能重叠，勿相加。图表分类、统计口径及图中未列项目请核原图；空结果不证明无数据。'}
