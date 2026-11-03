"""Selected official Taizhou Statistical Yearbook 2023 chapter PDFs."""
import release_runtime
import io
from pypdf import PdfReader
import requests
BASE = 'https://zjjcmspublic.oss-cn-hangzhou-zwynet-d01-a.internet.cloud.zj.gov.cn/jcms_files/jcms1/web3456/site/attach/0/'
CHAPTERS = {1: ('综合', '2b347955f0b744fdb7e7b603f7810a35.pdf'), 2: ('人口和从业人员', 'e017a72e58df43a6af45459646de888c.pdf'), 3: ('农业', '5864934536164d989ae82c35ed324cd5.pdf'), 4: ('工业', '73f1e398645c444b8a5c450385dbfd01.pdf'), 9: ('对外经济贸易和旅游', '36aec455b15440aa988a870279ff05b0.pdf'), 18: ('乡镇经济社会基本情况', '0d26064bac874cb88853c909a4a854ef.pdf'), 21: ('统计公报', '2ab9c28840194eb9a963103e8dafc617.pdf')}

def catalog():
    return [{'chapter': n, 'title': title, 'url': BASE + name} for n, (title, name) in CHAPTERS.items()]

def chapter(number):
    if isinstance(number, bool) or number not in CHAPTERS:
        raise ValueError('chapter is not in the selected catalog')
    title, name = CHAPTERS[number]
    url = BASE + name
    response = requests.get(url, timeout=45)
    response.raise_for_status()
    if not response.content.startswith(b'%PDF'):
        raise ValueError('upstream did not return a PDF')
    pdf = PdfReader(io.BytesIO(response.content))
    pages = [page.extract_text() or '' for page in pdf.pages]
    if not any((p.strip() for p in pages)):
        raise ValueError('PDF has no extractable text')
    return {'source': '台州市统计局《台州统计年鉴2023》', 'chapter': number, 'title': title, 'source_url': url, 'pages': pages}
