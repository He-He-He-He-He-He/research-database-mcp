"""WHO diabetes country profiles 2016; fixed WHO path, original PDF text."""
import release_runtime
import io, re, requests
from pypdf import PdfReader
BASE = 'https://cdn.who.int/media/docs/default-source/country-profiles/diabetes/{}_en.pdf'
INFO = 'https://www.who.int/teams/noncommunicable-diseases/surveillance/data/diabetes-profiles'
METHOD = 'https://cdn.who.int/media/docs/default-source/ncds/ncd-surveillance/diabetes_profiles_explanatory_notes.pdf'

def report(code):
    if not isinstance(code, str) or not re.fullmatch('[A-Za-z]{3}', code):
        raise ValueError('需输入 3 位国家字母代码')
    code = code.lower()
    url = BASE.format(code)
    with requests.get(url, timeout=30, stream=True, allow_redirects=False) as r:
        if r.status_code == 404:
            raise ValueError('此代码对应路径未找到，不能推断该国无报告；请查看 WHO 目录')
        r.raise_for_status()
        body = b''
        for chunk in r.iter_content(65536):
            body += chunk
            if len(body) > 10000000:
                raise ValueError('PDF 超过大小限制')
        modified = r.headers.get('Last-Modified')
    pdf = PdfReader(io.BytesIO(body))
    return {'source_pdf': url, 'who_directory': INFO, 'methods_pdf': METHOD, 'code': code.upper(), 'server_last_modified': modified, 'pdf_metadata': {str(k): str(v) for k, v in (pdf.metadata or {}).items()}, 'pages': [{'page': i + 1, 'text': p.extract_text() or ''} for i, p in enumerate(pdf.pages)], 'caution': '已实测代码 EGY、CHN、FRA、USA；其余代码对应路径与国家身份未逐一验证。请核对 PDF 国名、年份和脚注。患病率与死亡率为估计，卫生系统能力部分采用 2015 年会员国调查；表中不同指标年份不同。文字抽取可能打乱表格/图形，图表可能未提取，须查看原图。服务器修改时间及 PDF 元数据不能证明当前文件与历史文件完全一致。'}
