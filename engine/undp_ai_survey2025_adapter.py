"""UNDP 2025 AI and Human Development survey: country-level answer distributions."""
import release_runtime
import argparse, io, json
import pandas as pd
import requests
DATA = 'https://hdr.undp.org/sites/default/files/2025/AIHDS/2025_AI_Survey_Data.dta'
METHOD = 'https://hdr.undp.org/sites/default/files/2025/AIHDS/2025_AI_Survey_Methodology.pdf'
QUESTIONS = {'Q8': 'How much do you know about artificial intelligence?', 'Q10': 'How often have you used artificial intelligence tools? See official questionnaire for full wording.'}
QUESTIONNAIRE = 'https://hdr.undp.org/sites/default/files/2025/AIHDS/2025_AI_Survey_Questionnaire.pdf'

def query(country, question='Q8', local_file=None):
    if question not in QUESTIONS:
        raise ValueError('question must be Q8 or Q10')
    if not isinstance(country, str) or not country.strip():
        raise ValueError('country is required')
    if local_file:
        data = pd.read_stata(local_file, columns=['Country', question, 'Weight_none_resp1'])
    else:
        with requests.get(DATA, timeout=90, stream=True) as r:
            r.raise_for_status()
            content = bytearray()
            for chunk in r.iter_content(131072):
                content.extend(chunk)
                if len(content) > 35000000:
                    raise ValueError('unexpected data size')
        data = pd.read_stata(io.BytesIO(content), columns=['Country', question, 'Weight_none_resp1'])
    countries = list(data.Country.cat.categories)
    matches = [c for c in countries if c.casefold() == country.strip().casefold()]
    if not matches:
        raise ValueError('unknown country; choices: ' + ', '.join(countries))
    subset = data.loc[data.Country == matches[0], [question, 'Weight_none_resp1']].dropna()
    subset = subset[subset.Weight_none_resp1 > 0]
    total = float(subset.Weight_none_resp1.sum())
    if total <= 0:
        raise ValueError('no weighted responses')
    counts = subset.groupby(question, observed=True).agg(n=(question, 'size'), weight=('Weight_none_resp1', 'sum'))
    records = [{'answer': str(k), 'weighted_percent': round(float(row.weight) / total * 100, 2), 'unweighted_n': int(row.n)} for k, row in counts.iterrows()]
    return {'provider': None if local_file else 'UNDP Human Development Report Office', 'source': local_file if local_file else DATA, 'methodology': None if local_file else METHOD, 'questionnaire': None if local_file else QUESTIONNAIRE, 'collection_period': None if local_file else '2024-11 to 2025-01', 'country': matches[0], 'question_code': question, 'question': None if local_file else QUESTIONS[question], 'valid_unweighted_n': int(len(subset)), 'records': records, 'note': ('Local microdata provenance, question wording, weight meaning and survey period unverified; calculations assume the expected schema. ' if local_file else '') + "Computed using Weight_none_resp1; percentages use all nonmissing responses including don't know and refusal. Independent calculations, not verified against official published estimates. Country-level only; no microdata returned." + ('' if local_file else ' Survey covers 21 countries, not the entire world.')}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('--question', choices=QUESTIONS, default='Q8')
    p.add_argument('--local-file')
    a = p.parse_args()
    print(json.dumps(query(a.country, a.question, a.local_file), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
