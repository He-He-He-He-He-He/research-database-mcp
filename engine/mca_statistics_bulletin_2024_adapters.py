"""民政部 2024 年全国民政事业发展统计公报 PDF 文本页检索。"""
import release_runtime
import argparse
import json
import requests
import fitz
URL = 'https://www.mca.gov.cn/gdnps/n2445/n2451/n2458/n2681/c1662004999980006189/attr/400985.pdf'

def search_bulletin(keyword, timeout=15):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('请输入 1–100 字关键词')
    keyword = keyword.strip()
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    if not r.content.startswith(b'%PDF-'):
        raise ValueError('官方响应不是 PDF')
    doc = fitz.open(stream=r.content, filetype='pdf')
    if len(doc) != 14:
        raise ValueError('公报页数已变化，请重新核验')
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text().replace('\n', '')
        if keyword in text:
            pages.append({'page': i + 1, 'text': text})
    doc.close()
    return {'source': '中华人民共和国民政部', 'source_url': URL, 'year': 2024, 'keyword': keyword, 'pages': pages, 'note': '按 PDF 页检索文字层，保留整页上下文；图表和图片文字可能不被提取，需查看原 PDF，非完整结构化统计库。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword')
    a = p.parse_args()
    print(json.dumps(search_bulletin(a.keyword), ensure_ascii=False, indent=2))
