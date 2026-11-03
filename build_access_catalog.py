"""Rebuild static access hints from reachable command functions, not whole imports.

These hints describe code requirements, not live entitlements or connectivity.
No modules are executed and no credentials or network are accessed.
"""
import ast
import ipaddress
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
UNKNOWN = object()


def known(node, command):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == 'a' and node.attr == 'cmd':
        return command
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        values = [known(x, command) for x in node.elts]
        return values if all(x is not UNKNOWN for x in values) else UNKNOWN
    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        left, right = known(node.left, command), known(node.comparators[0], command)
        if left is UNKNOWN or right is UNKNOWN:
            return UNKNOWN
        op = node.ops[0]
        try:
            if isinstance(op, ast.Eq): return left == right
            if isinstance(op, ast.NotEq): return left != right
            if isinstance(op, ast.In): return left in right
            if isinstance(op, ast.NotIn): return left not in right
        except TypeError:
            return UNKNOWN
    if isinstance(node, ast.BoolOp):
        values = [known(x, command) for x in node.values]
        if isinstance(node.op, ast.And) and False in values: return False
        if isinstance(node.op, ast.Or) and True in values: return True
        if all(x is not UNKNOWN for x in values): return all(values) if isinstance(node.op, ast.And) else any(values)
    if isinstance(node, ast.IfExp):
        value = known(node.test, command)
        if value is not UNKNOWN: return known(node.body if value else node.orelse, command)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        value = known(node.func.value, command)
        args = [known(x, command) for x in node.args]
        if isinstance(value, str) and all(x is not UNKNOWN for x in args) and node.func.attr in ('startswith', 'endswith'):
            return getattr(value, node.func.attr)(*args)
    return UNKNOWN


def selected(node, command):
    """Prune only branches known from the command name; retain input branches."""
    if isinstance(node, ast.If):
        value = known(node.test, command)
        if value is not UNKNOWN:
            for child in node.body if value else node.orelse:
                yield from selected(child, command)
            return
    if isinstance(node, ast.IfExp):
        value = known(node.test, command)
        if value is not UNKNOWN:
            yield from selected(node.body if value else node.orelse, command)
            return
    yield node
    for child in ast.iter_child_nodes(node):
        yield from selected(child, command)


class Analyzer:
    def __init__(self):
        self.modules = {}

    def module(self, name):
        if name in self.modules: return self.modules[name]
        path = ROOT / 'engine' / (name + '.py')
        if not path.is_file(): return None
        tree = ast.parse(path.read_text(encoding='utf-8'))
        symbols, imports = {}, {}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                symbols[node.name] = node
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name): symbols[target.id] = node
            elif isinstance(node, ast.Import):
                for alias in node.names: imports[alias.asname or alias.name.split('.')[0]] = (alias.name, None)
            elif isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names: imports[alias.asname or alias.name] = (node.module, alias.name)
        result = (symbols, imports)
        self.modules[name] = result
        return result

    def analyze(self, entry, dispatch):
        command = entry['command']
        todo = [('research', dispatch, {})]
        if command.startswith('cas-common-'):
            todo = [('cas_common_chemistry_adapter', ast.Name(id='search' if command.endswith('search') else 'detail', ctx=ast.Load()), {})]
        seen, modules, envs, services, hosts, evidence = set(), set(), set(), set(), set(), set()
        credential = institution = False
        while todo:
            module, node, overrides = todo.pop()
            info = self.module(module)
            if not info: continue
            symbols, imports = info
            imports = {**imports, **overrides}
            nodes = list(selected(node, command))
            # Function-local imports must be resolved without pulling in unused functions.
            for item in nodes:
                if isinstance(item, ast.Import):
                    for alias in item.names: imports[alias.asname or alias.name.split('.')[0]] = (alias.name, None)
                elif isinstance(item, ast.ImportFrom) and item.module:
                    for alias in item.names: imports[alias.asname or alias.name] = (item.module, alias.name)
            for item in nodes:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    value = item.value
                    if value == 'find-generic-password': credential = True; evidence.add('credential-store-read')
                    if re.fullmatch(r'(?:research-toolkit[-.].+|zju-research-un-population-api|zju-research-toolkit)', value): services.add(value)
                    for url in re.findall(r'https?://[^\s\x00-\x20\x7f<>"\'{}]+', value):
                        try:
                            host = urlsplit(url).hostname
                            if host and '.' in host and re.fullmatch(r'[A-Za-z0-9.-]+', host):
                                hosts.add(host.lower())
                                try:
                                    address=ipaddress.ip_address(host)
                                    if address.is_private and not address.is_loopback and not address.is_unspecified: institution = True; evidence.add('private-network-address')
                                except ValueError: pass
                        except ValueError: pass
                    if re.fullmatch(r'[A-Z][A-Z0-9_]*(?:API_KEY|APIKEY|TOKEN|SECRET|PASSWORD|COOKIE)', value): envs.add(value)
                # Inspect actual guards rather than school names in docstrings/notes.
                if isinstance(item, ast.If):
                    test = ast.unparse(item.test)
                    errors = [ast.unparse(x) for x in item.body if isinstance(x, ast.Raise)]
                    if errors and re.search(r'浙江大学|Zhejiang University|(?:机构|学校|校园).{0,12}(?:认证|授权|登录|权限|访问|IP)|\bIP\b.{0,30}(?:Reader|读者)', test + ' '.join(errors), re.I):
                        institution = True; evidence.add('institution-response-guard')
                    if errors and re.search(r'key|token|secret|password|cookie|credential', test, re.I) and not re.search(r'keyword|monkey|page.?token|resumption.?token|cursor', test, re.I):
                        text = ' '.join(errors)
                        if re.search(r'需要|缺少|未配置|请.*设置|not configured|not found|requires?|missing|must', text, re.I) and re.search(r'密钥|凭据|[A-Z_]+(?:KEY|TOKEN)|credential|API.?key|token|password|cookie', text, re.I):
                            credential = True; evidence.add('required-credential-guard')
                if isinstance(item, ast.Call) and ast.unparse(item.func) == 'release_runtime.credential':
                    credential = True; evidence.add('credential-reader')
                refs = []
                if isinstance(item, ast.Attribute) and isinstance(item.value, ast.Name) and item.value.id in imports:
                    target, symbol = imports[item.value.id]
                    if symbol is None: refs.append((target, item.attr))
                if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load):
                    if item.id in imports:
                        target, symbol = imports[item.id]
                        if symbol is not None: refs.append((target, symbol))
                    elif item.id in symbols: refs.append((module, item.id))
                for target, symbol in refs:
                    key = (target, symbol)
                    if key in seen: continue
                    seen.add(key)
                    target_info = self.module(target)
                    if target_info and symbol in target_info[0]:
                        if target != 'research': modules.add(target)
                        todo.append((target, target_info[0][symbol], {}))
        # Explicit institution commands are intentionally tied to institution identity.
        if re.search(r'(?:-institution-|-ip-)', command):
            institution = True; evidence.add('explicit-institution-command')
        # Keep the legacy public starter set as regression fixtures, not an access gate.
        if entry.get('starter') and not credential and not institution:
            evidence.add('public-regression-fixture')
        access = 'login' if credential else 'zju' if institution else 'general'
        return {'access':access,'credential':credential,'institution':institution,
                'credential_environment_hints':sorted(envs) if credential else [],
                'credential_services':sorted(services) if credential else [],
                'network_hosts':sorted(hosts),
                'access_evidence':sorted(evidence) or ['no-required-credential-or-institution-guard-in-reachable-code'],
                'classification':'static-code-requirements; live response remains authoritative'}


def rebuild():
    sys.setrecursionlimit(50000)
    analyzer = Analyzer()
    main = analyzer.module('research')[0]['main']
    # Parser construction is irrelevant to query access, and includes all commands.
    start = next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='a' for t in n.targets))+1
    # Ignore parser-local constants not used by a given handler (e.g. NBS base).
    body = main.body[start:]
    dispatch = ast.Module(body=[node for node in body if isinstance(node,ast.If)], type_ignores=[])
    path = ROOT/'command_catalog.json'
    document = json.loads(path.read_text(encoding='utf-8'))
    counts = {'general':0,'zju':0,'login':0}
    for entry in document['commands']:
        entry.pop('required_environments',None)
        entry.update(analyzer.analyze(entry, dispatch))
        entry['readiness'] = {'general':'public-or-resource-validation-required','zju':'institution-network-required','login':'personal-credential-required'}[entry['access']]
        counts[entry['access']] += 1
    document['note'] = '按命令实际可达函数静态分类，不以起步样例限制公开功能。分类不证明联网、数据完整性、机构订阅或登录有效。'
    path.write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(counts))


if __name__ == '__main__': rebuild()
