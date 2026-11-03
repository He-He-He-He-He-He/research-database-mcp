"""Bundled sample evidence, deliberately distinct from code accessibility."""
import json
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=1)
def evidence():
    path=Path(__file__).resolve().parent/'data/verified_capabilities.json'
    return json.loads(path.read_text(encoding='utf-8')).get('commands',{})

def status(command):
    entry=evidence().get(command)
    if not entry:return {'level':'not_tested','notice':'仅有代码入口；没有收录有效的实测样例，不当作已验证能力。'}
    return {'level':entry.get('level','not_tested'),'samples':entry.get('samples',[]),'scope_note':entry.get('scope_note'),'latest_observation':entry.get('latest_observation'),'notice':'样例证据仅对应所列参数、时间和环境；不是实时连通性或完整覆盖承诺。'}


def summarize(commands, samples):
    indexed={entry['command'] for entry in commands}
    included={name:entry for name,entry in samples.items() if name in indexed}
    return {'indexed_commands':len(indexed),'commands_with_sample_evidence':len(included),'sample_verified_commands':sum(entry.get('level')=='sample_verified' for entry in included.values()),'commands_without_sample_evidence':len(indexed-included.keys()),'unclassified_content_commands':sum(entry.get('content_level_hint','unclassified')=='unclassified' for entry in commands),'followup_templates':sum('followup_template' in entry for entry in commands),'basis':'bundled sample evidence and static contracts; not live availability or full-text access'}

@lru_cache(maxsize=1)
def coverage():
    path=Path(__file__).resolve().parent/'data/command_catalog.json'
    return summarize(json.loads(path.read_text(encoding='utf-8'))['commands'],evidence())
