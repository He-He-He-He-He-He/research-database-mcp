"""PubMed metadata and structured abstracts via official NCBI EFetch."""
import release_runtime
import re, xml.etree.ElementTree as ET, requests
URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'

def fetch(ids):
    if not isinstance(ids, list) or not 1 <= len(ids) <= 20 or any((not isinstance(i, str) or not re.fullmatch('[0-9]{1,12}', i) for i in ids)) or (len(set(ids)) != len(ids)):
        raise ValueError('provide 1–20 unique numeric PubMed IDs')
    params = {'db': 'pubmed', 'id': ','.join(ids), 'retmode': 'xml', 'tool': 'personal_research_cli'}
    with requests.get(URL, params=params, timeout=(10, 25), stream=True, allow_redirects=False) as r:
        r.raise_for_status()
        url = r.url
        data = bytearray()
        for part in r.iter_content(65536):
            data.extend(part)
            if len(data) > 10000000:
                raise ValueError('response exceeds 10 MB; request fewer articles')
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        raise RuntimeError('PubMed did not return valid XML') from None
    if root.tag != 'PubmedArticleSet':
        raise RuntimeError('unexpected PubMed XML root')

    def txt(x):
        return ' '.join(''.join(x.itertext()).split()) if x is not None else ''
    records = []
    seen = set()
    unsupported = []
    for item in root:
        if item.tag != 'PubmedArticle':
            unsupported.append(item.tag)
            continue
        citation = item.find('MedlineCitation')
        pmid = txt(citation.find('PMID')) if citation is not None else ''
        if pmid not in ids or pmid in seen:
            raise RuntimeError('unexpected or duplicate PubMed identifier')
        seen.add(pmid)
        article = citation.find('Article')
        article_ids = item.findall('./PubmedData/ArticleIdList/ArticleId')
        abstracts = []
        if article is not None:
            for a in article.findall('./Abstract/AbstractText'):
                abstracts.append({'label': a.get('Label'), 'category': a.get('NlmCategory'), 'text': txt(a)})
        others = []
        for group in citation.findall('OtherAbstract'):
            others.append({'type': group.get('Type'), 'language': group.get('Language'), 'sections': [{'label': a.get('Label'), 'category': a.get('NlmCategory'), 'text': txt(a)} for a in group.findall('AbstractText')]})
        authors = []
        for a in article.findall('./AuthorList/Author') if article is not None else []:
            authors.append({'last_name': txt(a.find('LastName')), 'fore_name': txt(a.find('ForeName')), 'collective_name': txt(a.find('CollectiveName'))})
        records.append({'pmid': pmid, 'title': txt(article.find('ArticleTitle')) if article is not None else '', 'journal': txt(article.find('./Journal/Title')) if article is not None else '', 'journal_publication_date': txt(article.find('./Journal/JournalIssue/PubDate')) if article is not None else '', 'abstract_sections': abstracts, 'other_abstracts': others, 'authors': authors, 'article_ids': [{'type': x.get('IdType'), 'value': txt(x)} for x in article_ids], 'publication_types': [txt(x) for x in article.findall('./PublicationTypeList/PublicationType')] if article is not None else []})
    return {'source_url': url, 'requested_ids': ids, 'records': records, 'missing_ids': [i for i in ids if i not in seen], 'unsupported_record_types': unsupported, 'note': 'PubMed 题录及作者提供摘要，不是全文；无摘要不等于无文章。期刊日期为源标签内容，电子/印刷日期可能不同；版权及再利用以文章/出版商许可为准。'}
