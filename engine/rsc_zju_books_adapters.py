"""馆方公开的 RSC 电子书书单快照（2026-10-29）。"""
import release_runtime
import json
_DATA = 'Characterisation of Porous Solids VIII|9781847559418\nMultifunctional Conducting Molecular Materials|9781847557605\nChemical Vapour Deposition|9781847558794\nNanocasting|9781847559869\nChromic Phenomena|9781847550538\nNanoscopic Materials|9781847557636\nClean by Light Irradiation|9781849732031\nNanotechnologies in Food|9781847559883\nCompendium of Polymer Terminology and Nomenclature|9781847559425\nNanotubes and Nanowires|9781847552525\nCoordination Polymers|9781847558862\nPlant Biopolymer Science|9781847551672\nDendrimers in Medicine and Biotechnology|9781847552679\nPolymer Nanocomposites by Emulsion and Suspension|9781849732192\nDevelopment of a New Material|9781847550699\nPolymer Structure Characterization|9781847557896\nEmerging Themes in Polymer Science|9781847550736\nPolymer-based Nanostructures|9781847559968\nFire Retardancy of Polymers|9781847559210\nRaman Spectroscopy, Fullerenes and Nanotechnology|9781849731133\nFlat Panel Displays|9781847550828\nSilica-Based Materials for Advanced Chemical Applications|9781847557162\nGranular Materials|9781847550996\nThe Chemistry of Medical and Dental Materials|9781847552051\nIntelligent Materials|9781847558008\nThe Chemistry of Polymers|9781847552655\nInterpreting Organic Spectra|9781847551153\nThe Sulfur Problem|9781847552174\nIntroduction to Glass Science and Technology|9781847551160\nUnravelling Single Cell Genomics|9781849732284\nMicroporous Framework Solids|9781847557971'

def search(keyword=''):
    if not isinstance(keyword, str):
        raise TypeError('keyword 必须是字符串')
    rows = [line.split('|', 1) for line in _DATA.splitlines()]
    items = [{'title': title, 'doi': '10.1039/' + number, 'url': 'https://doi.org/10.1039/' + number} for title, number in rows if keyword.casefold() in title.casefold()]
    return {'source': '浙江大学图书馆 RSC 电子书书单', 'source_url': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1079', 'snapshot_date': '2026-10-29', 'keyword': keyword, 'total_listed': len(rows), 'matched': len(items), 'items': items, 'scope': '馆方列示的31种电子书书单快照；非 RSC 全库搜索，机构登录和全文权限未验证。'}
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('keyword', nargs='?', default='')
    print(json.dumps(search(parser.parse_args().keyword), ensure_ascii=False, indent=2))
