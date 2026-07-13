import re
from typing import Optional, List
from lxml import etree
from latex2mathml.converter import convert as latex_to_mathml

MATH_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/math'

ENTITIES = re.compile(r'&#x([0-9A-Fa-f]+);')


def _unentity(text: str) -> str:
    return ENTITIES.sub(lambda m: chr(int(m.group(1), 16)), text)


def _m_root(tag: str) -> etree.Element:
    return etree.Element('{%s}%s' % (MATH_NS, tag), nsmap={'m': MATH_NS})


def _m_elem(tag: str, parent=None, text: str = None) -> etree.Element:
    elem = etree.Element('{%s}%s' % (MATH_NS, tag))
    if text is not None:
        elem.text = text
    if parent is not None:
        parent.append(elem)
    return elem


def _m_attr(elem: etree.Element, name: str, value: str):
    elem.set('{%s}%s' % (MATH_NS, name), str(value))


def _m_run(text: str, italic: bool = False) -> etree.Element:
    r = _m_elem('r')
    rPr = _m_elem('rPr', r)
    if italic:
        sty = _m_elem('sty', rPr)
        _m_attr(sty, 'val', 'i')
    else:
        _m_elem('nor', rPr)
    _m_elem('t', r, text=text)
    return r


def _m_op(text: str) -> etree.Element:
    r = _m_elem('r')
    _m_elem('t', r, text=text)
    return r


def _strip_ns(tag: str) -> str:
    return tag.split('}', 1)[1] if '}' in tag else tag


_FENCE_PAIRS = {'(': ')', '[': ']', '{': '}', '|': '|', '\u2016': '\u2016'}


def _find_matching_close(children, start_idx):
    opener = children[start_idx].text.strip() if children[start_idx].text else ''
    expected_close = _FENCE_PAIRS.get(opener)
    depth = 0
    for i in range(start_idx, len(children)):
        c = children[i]
        if _strip_ns(c.tag) == 'mo' and c.text:
            t = c.text.strip()
            if expected_close and t == expected_close and depth > 0:
                depth -= 1
                if depth == 0:
                    return i
            elif t == opener:
                depth += 1
    return None


def _make_delimiter(beg_val, end_val, inner_children):
    d = _m_elem('d')
    dPr = _m_elem('dPr', d)
    _m_attr(_m_elem('begChr', dPr), 'val', _unentity(beg_val))
    _m_attr(_m_elem('endChr', dPr), 'val', _unentity(end_val))
    if inner_children:
        _m_attr(_m_elem('grow', dPr), 'val', '1')
        _m_attr(_m_elem('shp', dPr), 'val', 'match')
        e = _m_elem('e', d)
        for ic in inner_children:
            for cc in _convert(ic):
                e.append(cc)
    return d


def _group_fences(children):
    result = []
    i = 0
    n = len(children)
    while i < n:
        c = children[i]

        # Already an OMML element (from nested fence) — pass through
        if isinstance(c.tag, str) and c.tag.startswith('{%s}' % MATH_NS):
            result.append(c)
            i += 1
            continue

        tag_name = _strip_ns(c.tag)

        if tag_name == 'mo' and c.text and c.text.strip() in _FENCE_PAIRS:
            open_char = c.text.strip()
            close_idx = _find_matching_close(children, i)

            if close_idx is not None and close_idx > i:
                close_char = children[close_idx].text.strip()
                d = _make_delimiter(open_char, close_char, children[i + 1:close_idx])
                result.append(d)
                i = close_idx + 1
                continue
            elif close_idx is None and i + 1 < n:
                d = _make_delimiter(open_char, '', children[i + 1:])
                result.append(d)
                return result

        for cc in _convert(c):
            result.append(cc)
        i += 1
    return result


def _convert(elem) -> List[etree.Element]:
    """Convert MathML element to list of OMML elements.
    Returns a list to allow flattening of groups like <mrow>."""

    if not isinstance(getattr(elem, 'tag', None), str):
        text = (elem.text or '').strip()
        if text:
            return [_m_op(_unentity(text))]
        return []

    tag = _strip_ns(elem.tag)
    children = [c for c in elem if isinstance(getattr(c, 'tag', None), str)]

    if tag == 'mrow':
        return _group_fences(children)

    if tag == 'mi':
        return [_m_run(_unentity(elem.text or ''), italic=True)]

    if tag == 'mn':
        return [_m_run(_unentity(elem.text or ''), italic=False)]

    if tag == 'mo':
        return [_m_op(_unentity(elem.text or ''))]

    if tag == 'mtext':
        return [_m_run(_unentity(elem.text or ''), italic=False)]

    if tag == 'mspace':
        return []

    if tag == 'mfrac':
        f = _m_elem('f')
        fPr = _m_elem('fPr', f)
        _m_attr(_m_elem('type', fPr), 'val', 'bar')
        num = _m_elem('num', f)
        den = _m_elem('den', f)
        for i, c in enumerate(children):
            if i == 0:
                for cc in _convert(c):
                    num.append(cc)
            elif i == 1:
                for cc in _convert(c):
                    den.append(cc)
        return [f]

    if tag == 'msup':
        ss = _m_elem('sSup')
        e = _m_elem('e', ss)
        sup_e = _m_elem('sup', ss)
        for i, c in enumerate(children):
            if i == 0:
                for cc in _convert(c):
                    e.append(cc)
            elif i == 1:
                for cc in _convert(c):
                    sup_e.append(cc)
        return [ss]

    if tag == 'msub':
        ss = _m_elem('sSub')
        e = _m_elem('e', ss)
        sub_e = _m_elem('sub', ss)
        for i, c in enumerate(children):
            if i == 0:
                for cc in _convert(c):
                    e.append(cc)
            elif i == 1:
                for cc in _convert(c):
                    sub_e.append(cc)
        return [ss]

    if tag == 'msubsup':
        ss = _m_elem('sSubSup')
        e = _m_elem('e', ss)
        sub_e = _m_elem('sub', ss)
        sup_e = _m_elem('sup', ss)
        for i, c in enumerate(children):
            if i == 0:
                for cc in _convert(c):
                    e.append(cc)
            elif i == 1:
                for cc in _convert(c):
                    sup_e.append(cc)
            elif i == 2:
                for cc in _convert(c):
                    sub_e.append(cc)
        return [ss]

    if tag == 'msqrt':
        rad = _m_elem('rad')
        radPr = _m_elem('radPr', rad)
        _m_attr(_m_elem('degHide', radPr), 'val', '1')
        e = _m_elem('e', rad)
        for c in children:
            for cc in _convert(c):
                e.append(cc)
        return [rad]

    if tag == 'mroot':
        rad = _m_elem('rad')
        deg_e = _m_elem('deg', rad)
        e = _m_elem('e', rad)
        for i, c in enumerate(children):
            if i == 0:
                for cc in _convert(c):
                    deg_e.append(cc)
            elif i == 1:
                for cc in _convert(c):
                    e.append(cc)
        return [rad]

    if tag == 'mfenced':
        op = elem.get('open', '(')
        cl = elem.get('close', ')')
        d = _m_elem('d')
        dPr = _m_elem('dPr', d)
        _m_attr(_m_elem('begChr', dPr), 'val', op)
        _m_attr(_m_elem('endChr', dPr), 'val', cl)
        _m_attr(_m_elem('grow', dPr), 'val', '1')
        _m_attr(_m_elem('shp', dPr), 'val', 'match')
        for c in children:
            ce = _m_elem('e', d)
            for cc in _convert(c):
                ce.append(cc)
        return [d]

    if tag == 'munder':
        lim = _m_elem('limLow')
        e = _m_elem('e', lim)
        lim_e = _m_elem('lim', lim)
        for i, c in enumerate(children):
            if i == 0:
                for cc in _convert(c):
                    e.append(cc)
            elif i == 1:
                for cc in _convert(c):
                    lim_e.append(cc)
        return [lim]

    if tag == 'mover':
        upp = _m_elem('limUpp')
        e = _m_elem('e', upp)
        lim_e = _m_elem('lim', upp)
        for i, c in enumerate(children):
            if i == 0:
                for cc in _convert(c):
                    e.append(cc)
            elif i == 1:
                for cc in _convert(c):
                    lim_e.append(cc)
        return [upp]

    if tag == 'munderover':
        # Nest limUpp inside limLow: limLow(limUpp(base, upper), lower)
        lim_upp = _m_elem('limUpp')
        e_upp = _m_elem('e', lim_upp)
        lim_upp_lim = _m_elem('lim', lim_upp)
        lim_low = _m_elem('limLow')
        e_low = _m_elem('e', lim_low)
        lim_low_lim = _m_elem('lim', lim_low)
        for i, c in enumerate(children):
            if i == 0:
                for cc in _convert(c):
                    e_upp.append(cc)
            elif i == 1:
                for cc in _convert(c):
                    lim_low_lim.append(cc)
            elif i == 2:
                for cc in _convert(c):
                    lim_upp_lim.append(cc)
        e_low.append(lim_upp)
        return [lim_low]

    if tag == 'mtable':
        m = _m_elem('m')
        mPr = _m_elem('mPr', m)
        _m_attr(_m_elem('baseJc', mPr), 'val', 'center')
        mcs = _m_elem('mcs', mPr)

        # Count columns from first row
        first_tr = None
        for child in elem:
            if isinstance(getattr(child, 'tag', None), str) and _strip_ns(child.tag) == 'mtr':
                first_tr = child
                break
        col_count = 0
        if first_tr is not None:
            col_count = sum(1 for td in first_tr if isinstance(getattr(td, 'tag', None), str) and _strip_ns(td.tag) == 'mtd')

        for _ in range(col_count):
            mc = _m_elem('mc', mcs)
            mcPr = _m_elem('mcPr', mc)
            _m_attr(_m_elem('mcJc', mcPr), 'val', 'center')

        for tr in elem:
            if not isinstance(getattr(tr, 'tag', None), str) or _strip_ns(tr.tag) != 'mtr':
                continue
            mr = _m_elem('mr', m)
            for td in tr:
                if not isinstance(getattr(td, 'tag', None), str) or _strip_ns(td.tag) != 'mtd':
                    continue
                me = _m_elem('e', mr)
                for cc in _convert(td):
                    me.append(cc)
        return [m]

    if tag in ('mpadded', 'mstyle', 'mphantom', 'mtd', 'mtr'):
        return _group_fences(children)

    if tag == 'menclose':
        box = _m_elem('borderBox')
        e = _m_elem('e', box)
        for c in children:
            for cc in _convert(c):
                e.append(cc)
        return [box]

    if tag == 'merror':
        return [_m_run(_unentity(elem.text or '?'), italic=False)]

    # Default: treat unknown element text as operator
    text = _unentity(elem.text or '')
    if text.strip():
        return [_m_op(text)]
    return []


def mathml_to_omml(mathml: str) -> Optional[etree.Element]:
    try:
        root = etree.fromstring(mathml.encode('utf-8'))
    except Exception:
        return None

    display = root.get('display', 'inline') == 'block'

    top_children = [c for c in root if isinstance(getattr(c, 'tag', None), str)]
    content = _group_fences(top_children)

    if not content:
        return None

    if display:
        omath_para = _m_root('oMathPara')
        omath = _m_elem('oMath', omath_para)
        for c in content:
            omath.append(c)
        return omath_para

    omath = _m_root('oMath')
    for c in content:
        omath.append(c)
    return omath


def latex_to_omml(latex: str, display: bool = False) -> Optional[etree.Element]:
    try:
        disp = 'block' if display else 'inline'
        mathml = latex_to_mathml(latex, display=disp)
        return mathml_to_omml(mathml)
    except Exception as e:
        print(f"OMML conversion error for '{latex}': {e}")
        return None
