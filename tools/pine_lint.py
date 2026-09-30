#!/usr/bin/env python3
"""
Offline sanity checks for the Pine v6 sources in this repo.

TradingView's compiler is the only authority, but a few of its rules can be checked before pasting a script
into the editor. Every check here exists because one of them has already bitten this project:

  1. indentation       - 4-space indents, no tabs, no jaw-dropping indent jumps (Pine is whitespace sensitive)
  2. value vs void     - an if/else where one branch ends with a value and the other with a void call is
                         rejected with CE10235 ("Return type of one of the if or switch blocks ...")
  3. forward refs      - a user function may not read a global or call a user function declared later
  4. UDT fields        - every `obj.field` on a typed global must exist on that type. `settings.foo` once
                         matched `htfSettings.foo` with a naive regex and produced a false alarm, so the
                         matcher is anchored properly here.
  5. trailing junk     - trailing whitespace and paren imbalance on a single logical line
  6. in-place fields   - CE10137: a field of an object returned by a call cannot be assigned directly
                         (`array.get(a, i).field := x` must go through a variable)
  7. stateful calls    - CW10003: a function that keeps ta.* / timeframe.change state must not be called from a
                         local scope (a branch), or its series go inconsistent between runs
  8. global writes     - CE10088: a function cannot reassign a global variable (`currentAlerts := alerts.new()`).
                         Fields of a global object are fine (`currentAlerts.equalLows := true`), the variable
                         itself is not

Usage:  python3 tools/pine_lint.py 9os.XLR8.pine
Exit code 0 = clean, 1 = something to look at.
"""
import re
import sys

BUILTIN_NAMESPACES = (
    'array', 'box', 'line', 'label', 'math', 'str', 'ta', 'time', 'time_close', 'request', 'input',
    'color', 'table', 'chart', 'indicator', 'plot', 'plotcandle', 'plotshape', 'plotchar', 'alert',
    'alertcondition', 'syminfo', 'barstate', 'timeframe', 'dayofweek', 'year', 'month', 'dayofmonth',
    'hour', 'minute', 'second', 'timestamp', 'min', 'max', 'na', 'nz', 'int', 'float', 'bool', 'string',
    'size', 'extend', 'xloc', 'yloc', 'text', 'line_style', 'label_style', 'barmerge', 'strategy', 'log',
    'runtime', 'session', 'display', 'shape', 'format', 'position', 'font', 'map', 'matrix', 'polyline',
)


def load(path):
    return [l.rstrip('\n') for l in open(path, encoding='utf-8')]


def indent(l):
    return len(l) - len(l.lstrip(' '))


def is_code(lines, i):
    l = lines[i]
    return bool(l.strip()) and not l.strip().startswith('//')


def block_end(lines, i):
    """Index of the last significant line of the block introduced by line i (one level deeper)."""
    base = indent(lines[i])
    j, last = i + 1, None
    while j < len(lines):
        if not is_code(lines, j):
            j += 1
            continue
        if indent(lines[j]) <= base:
            break
        last = j
        j += 1
    return last


def stmt_kind(lines, i):
    s = lines[i].split('//')[0].strip()
    if re.match(r'^(else\b|if\b|if\(|for\b|while\b|switch\b)', s):
        return 'ctrl'
    if ':=' in s:
        return 'assign'
    if re.match(r'^[A-Za-z_][\w.]*\s*\(.*\)$', s):
        return 'call'
    return 'expr'


def check_indent(lines):
    out, prev = [], 0
    for i, l in enumerate(lines, 1):
        if not l.strip() or l.strip().startswith('//'):
            continue
        ind = indent(l)
        if '\t' in l:
            out.append((i, 'tab character'))
        if ind % 4:
            out.append((i, 'indent %d is not a multiple of 4' % ind))
        if ind > prev + 4:
            out.append((i, 'indent jumps from %d to %d' % (prev, ind)))
        prev = ind
    return out


def check_value_vs_void(lines):
    """An if/else whose branches end with different kinds, where one of them is a void call, is CE10235."""
    out = []
    for i, l in enumerate(lines):
        if not re.match(r'^else\b', l.strip()):
            continue
        mi = None
        for k in range(i - 1, -1, -1):
            if not is_code(lines, k):
                continue
            if indent(lines[k]) < indent(l):
                break
            if indent(lines[k]) == indent(l) and re.match(r'^(if|switch)\b', lines[k].strip()):
                mi = k
                break
        if mi is None:
            continue
        eb, ib = block_end(lines, i), block_end(lines, mi)
        if eb is None or ib is None:
            continue
        k1, k2 = stmt_kind(lines, ib), stmt_kind(lines, eb)
        if 'call' in (k1, k2) and k1 != k2:
            out.append((mi + 1, 'if block ends with %s (%s)' % (k1, lines[ib].strip()[:48]),
                        i + 1, 'else block ends with %s (%s)' % (k2, lines[eb].strip()[:48])))
    return out


def scan_declarations(lines):
    """Global declarations, function definitions, and the bodies of those functions."""
    globals_, funcs = {}, []
    for i, l in enumerate(lines, 1):
        if l.startswith(' ') or not l.strip() or l.strip().startswith('//'):
            m = re.match(r'^type\s+(\w+)', l)
            if m:
                globals_.setdefault(m.group(1), i)
            continue
        m = re.match(r'^(?:var\s+|varip\s+)?(?:array<[\w<>]+>|matrix<[\w<>]+>|map<[\w,]+>|[A-Za-z_]\w*)\s+(\w+)\s*:?=', l)
        if m:
            globals_.setdefault(m.group(1), i)
        m = re.match(r'^([A-Z][A-Za-z_]*)\s*=', l)
        if m:
            globals_.setdefault(m.group(1), i)
        m = re.match(r'^type\s+(\w+)', l)
        if m:
            globals_.setdefault(m.group(1), i)

        m = re.match(r'^(\w+)\((.*)\)\s*=>', l)
        if m:
            body, j = [], i
            while j < len(lines):
                cur = lines[j]
                if not cur.strip() or cur.strip().startswith('//'):
                    j += 1
                    continue
                if not cur.startswith(' '):
                    break
                body.append((j + 1, cur))
                j += 1
            funcs.append((i, m.group(1), set(re.findall(r'(\w+)\s*(?:=|,|\))', m.group(2))), body))
    return globals_, funcs


def check_forward_refs(lines):
    globals_, funcs = scan_declarations(lines)
    defs = {name: line for line, name, _, _ in funcs}
    out = []
    for line, name, params, body in funcs:
        for bl, code in body:
            code = code.split('//')[0]
            for ident in set(re.findall(r'(?<![\w.])([A-Za-z_]\w*)', code)):
                if ident in params or ident == name:
                    continue
                if ident in globals_ and globals_[ident] > line:
                    out.append((name, line, 'declares later: ' + ident, globals_[ident]))
                if ident in defs and defs[ident] > bl:
                    out.append((name, line, 'calls later: %s()' % ident, defs[ident]))
    return sorted(set(out))


def check_udt_fields(lines):
    """Collect UDT field names, then verify obj.field for every global whose declared type is a UDT."""
    types, cur = {}, None
    for l in lines:
        m = re.match(r'^type\s+(\w+)', l)
        if m:
            cur = m.group(1)
            types[cur] = []
            continue
        if cur is not None:
            if re.match(r'^\s{4}\S', l):
                fm = re.match(r'^\s+[\w<>\.\[\]]+\s+(\w+)', l)
                if fm:
                    types[cur].append(fm.group(1))
            elif l.strip():
                cur = None

    udt_vars = {}
    for l in lines:
        m = re.match(r'^(?:var\s+|varip\s+)?(\w+)\s+(\w+)\s*=', l)
        if m and m.group(1) in types:
            udt_vars[m.group(2)] = m.group(1)

    out = []
    for line, l in enumerate(lines, 1):
        s = l.split('//')[0]
        for var, typ in udt_vars.items():
            for f in re.findall(r'(?<![\w.])%s\.(\w+)' % re.escape(var), s):
                if f not in types[typ]:
                    out.append((line, '%s.%s is not a field of type %s' % (var, f, typ)))
    return out


def check_inplace_field_assign(lines):
    """CE10137: `array.get(...).field := x` and friends cannot be compiled."""
    pattern = re.compile(r'\b(?:array\.(?:get|first|last|shift)|map\.get|matrix\.get|box\.copy)\([^)]*\)\.\w+\s*:=')
    out = []
    for i, l in enumerate(lines, 1):
        code = '' if l.strip().startswith('//') else l.split('//')[0]
        if pattern.search(code):
            out.append((i, 'field assigned on a call result - put it in a variable first'))
    return out


STATE_CALL = re.compile(r'(?<![\w.])(?:ta\.[a-z_]+|timeframe\.change)\s*\(')


def check_stateful_calls(lines):
    """CW10003: calls to functions carrying ta.* state must not sit inside a branch."""
    globals_, funcs = scan_declarations(lines)
    body_lines, info = {}, {}
    for line, name, params, body in funcs:
        calls = set()
        uses_state = False
        for bl, code in body:
            body_lines[bl] = name
            code = code.split('//')[0]
            if STATE_CALL.search(code):
                uses_state = True
            for ident in re.findall(r'(?<![\w.])([A-Za-z_]\w*)\s*\(', code):
                calls.add(ident)
        info[name] = {'line': line, 'uses_state': uses_state, 'calls': calls}

    # propagate "uses ta.* state" through the call graph
    changed = True
    while changed:
        changed = False
        for name, d in info.items():
            if d['uses_state']:
                continue
            for callee in d['calls']:
                if callee in info and info[callee]['uses_state']:
                    d['uses_state'] = True
                    changed = True
                    break

    out = []
    for i, l in enumerate(lines, 1):
        if i in body_lines or not l.strip() or l.strip().startswith('//'):
            continue                       # inside a function body: the caller is checked instead
        if indent(l) == 0:
            continue                       # global scope, always calculated
        code = l.split('//')[0]
        for callee in set(re.findall(r'(?<![\w.])([A-Za-z_]\w*)\s*\(', code)):
            if callee in info and info[callee]['uses_state']:
                out.append((i, '%s() keeps ta.* state but is called from a branch' % callee))
    return sorted(set(out))


def check_global_writes(lines):
    """CE10088: `global := ...` inside a function body is not allowed."""
    globals_, funcs = scan_declarations(lines)
    out = []
    for line, name, params, body in funcs:
        locals_ = set(params)
        for bl, code in body:
            code = code.split('//')[0]
            # local declarations: `Type x = ...`, `var Type x = ...`, `x = ...`
            for m in re.finditer(r'(?:var\s+|varip\s+)?(?:[\w<>]+\s+|)(\w+)\s*=[^=]', code):
                locals_.add(m.group(1))
            m = re.match(r'\s*([A-Za-z_]\w*)\s*:=', code)
            if not m:
                continue
            target = m.group(1)
            if target in locals_:
                continue
            if target in globals_:
                out.append((bl, 'function %s() reassigns the global %s' % (name, target)))
    return sorted(set(out))


def check_noise(lines):
    out = []
    for i, l in enumerate(lines, 1):
        if l != l.rstrip():
            out.append((i, 'trailing whitespace'))
        code = '' if l.strip().startswith('//') else l.split('//')[0]
        if code.count('(') != code.count(')') and 'http' not in l:
            out.append((i, 'unbalanced parentheses'))
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else '9os.XLR8.pine'
    lines = load(path)
    total = 0

    def report(title, rows, fmt=lambda r: '    line %-6s %s' % (r[0], ' | '.join(str(x) for x in r[1:]))):
        nonlocal total
        print('%s: %d' % (title, len(rows)))
        for r in rows[:40]:
            print(fmt(r))
        total += len(rows)

    report('indentation', check_indent(lines))
    report('value-vs-void if/else blocks (CE10235)', check_value_vs_void(lines))
    report('forward references', check_forward_refs(lines),
           fmt=lambda r: '    %s() at line %s %s (declared at %s)' % (r[0], r[1], r[2], r[3]))
    report('unknown UDT fields', check_udt_fields(lines))
    report('in-place field assignment (CE10137)', check_inplace_field_assign(lines))
    report('stateful calls from a branch (CW10003)', check_stateful_calls(lines))
    report('global writes inside a function (CE10088)', check_global_writes(lines))
    report('noise', check_noise(lines))
    print('\n%s: %d lines, %d findings' % (path, len(lines), total))
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
