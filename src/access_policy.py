"""Mode permissions. Public sample coverage is separate from access requirements."""
MODES = ('general', 'zju', 'login')
ALIASES = {'partial':'general', 'full':'login'}
LABELS = {'general':'一般模式', 'zju':'浙大内网模式', 'login':'登录模式'}


def normalize(mode):
    value = ALIASES.get(mode, mode)
    if value not in (None, *MODES):
        raise ValueError('mode 须为 general、zju 或 login（旧 partial/full 仍兼容）')
    return value


def required(entry):
    # Compatibility for older third-party catalog consumers.
    if entry.get('access') in MODES: return entry['access']
    if entry.get('credential'): return 'login'
    if entry.get('institution'): return 'zju'
    return 'general'


def allowed(mode, entry):
    mode = normalize(mode)
    level = required(entry)
    return mode is not None and (level == 'general' or mode == 'login' or mode == level)


def describe(mode, entry):
    level = required(entry)
    return {'required_mode':level, 'allowed_in_mode':allowed(mode, entry),
            'note':{'general':'公开查询或本地文件功能；仍需网络、依赖和实际文件。',
                    'zju':'依靠机构网络或 IP 身份；选择模式不等于已处于校园网或已获源站访问。',
                    'login':'按需使用接收者自己的登录、API 凭据；可能还需机构网络。'}[level]}
