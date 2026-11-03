"""IDMC national annual internal displacement estimates distributed via UN OCHA HDX."""
import release_runtime
import argparse, csv, io, json, re, requests
URL = 'https://data.humdata.org/dataset/459fc96c-f196-44c1-a0a5-1b5a7b3592dd/resource/0fb4e415-abdb-481a-a3c6-8821e79919be/download/internal-displacements-new-displacements-idps.csv'
META = 'https://data.humdata.org/dataset/idmc-internal-displacements-new-displacements-idps'
HEAD = ('iso3', 'country_name', 'year', 'new_displacement', 'new_displacement_rounded', 'total_displacement', 'total_displacement_rounded')

def query(country, start, end):
    if not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be uppercase ISO3')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start, end))) or not 2009 <= start <= end <= 2025:
        raise ValueError('year must be 2009–2025')
    with requests.get(URL, stream=True, timeout=30) as r:
        r.raise_for_status()
        b = bytearray()
        for chunk in r.iter_content(65536):
            b.extend(chunk)
            if len(b) > 2000000:
                raise ValueError('unexpected file size')
    reader = csv.DictReader(io.StringIO(bytes(b).decode('utf-8-sig')))
    if tuple(reader.fieldnames or ()) != HEAD:
        raise ValueError('unexpected file schema')
    out = []
    for row in reader:
        if row['iso3'] != country or not row['year'].isdigit() or (not start <= int(row['year']) <= end):
            continue
        for k in HEAD[2:]:
            row[k] = int(row[k]) if row[k].isdigit() else None
        out.append(row)
    return {'provider': 'Internal Displacement Monitoring Centre (IDMC, non-governmental)', 'distributor': 'UN OCHA Humanitarian Data Exchange', 'source': URL, 'metadata': META, 'license': 'CC BY 3.0 IGO as stated in HDX metadata', 'country': country, 'records': out, 'note': 'New displacements count movements and can include repeat displacement of one person; total displacement is estimated people living in internal displacement at year end. Most values are estimates. Cause scope and historical revisions require checking underlying IDMC metadata; empty values remain null and zero is not evidence of complete coverage.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(query(a.country, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
