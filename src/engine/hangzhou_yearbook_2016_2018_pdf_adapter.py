"""Official Hangzhou Statistical Yearbook chapter PDFs, editions 2016–2018."""
import release_runtime
import requests
CHAPTERS = ['综合', '人口和就业人员', '农业', '工业、能源', '建筑业', '交通运输、邮电', '固定资产投资', '国内贸易', '对外经济、旅游', '财政、金融、保险', '城市建设、环境保护', '科技、教育、文化、卫生、体育', '人民生活、物价、民政']

def catalog(year, keyword=''):
    if isinstance(year, bool) or not isinstance(year, int) or year not in (2016, 2017, 2018):
        raise ValueError('available editions: 2016, 2017, 2018')
    return [{'edition': year, 'chapter': i, 'title': title, 'source': f'杭州市统计局《杭州统计年鉴{year}》', 'url': f'https://tjj.hangzhou.gov.cn/tjnj/nj{year}/{i}.pdf'} for i, title in enumerate(CHAPTERS, 1) if keyword in title]

def chapter(year, number):
    if isinstance(number, bool) or not isinstance(number, int) or (not 1 <= number <= 13):
        raise ValueError('chapter must be an integer between 1 and 13')
    item = catalog(year)[number - 1]
    response = requests.get(item['url'], timeout=60)
    response.raise_for_status()
    if not response.content.startswith(b'%PDF-'):
        raise ValueError('response is not a PDF')
    return {**item, 'content_type': 'application/pdf', 'content': response.content}
