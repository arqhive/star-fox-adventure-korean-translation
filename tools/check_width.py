# 번역 줄이 원본 창 너비를 넘는지 검사 (넘치면 게임이 자동 줄바꿈해 창 밖으로 밀림)
# 기준: 같은 window 값·같은 종류(슬리피 힌트/그 외)를 쓰는 원본 일본어 줄의 최대 너비 (일본어 없는 디버그 줄 제외)
# 사용: python tools/check_width.py [여유픽셀]      ※ 먼저 python build.py --json-only
#       python tools/check_width.py --windows       창별 한도·쓰임새 요약
import os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sfa.config import find_jp_iso, translation_jsons
from sfa.gcm import Disc
from sfa.gametext import load, text_chars, area_path, split_prefix, render_glyph
from sfa.isopatch import load_translations

CACHE = {}
TOKEN = re.compile(r'\{([0-9A-F]{4})(?::([0-9a-f]*))?\}|(.)', re.S)


def file_metrics(r):
    """(코드포인트, font) → 진행폭.  font 0 = 본문, 2 = 버튼 아이콘, 5 = 통역 아이콘 등"""
    return {(c[0], c[9]): c[3] + c[7] + c[4] for c in r['chars']}


def advance(ch, font, metrics):
    cp = ord(ch)
    if (cp, font) in metrics:
        return metrics[(cp, font)]
    if (cp, 0) in metrics:
        return metrics[(cp, 0)]
    if ch not in CACHE:
        img, l, r, top, bot = render_glyph(ch)
        CACHE[ch] = l + img.shape[1] + r
    return CACHE[ch]


def width(s, metrics):
    """{F8F7:000N} 폰트 전환까지 따라가며 잰 줄 너비.
    버튼 아이콘({A}{Y} 등)은 아이콘 글리프 폭(22~24px)으로 잰다 — 영문자 폭(12px)으로 재면 넘치는 줄을 놓친다."""
    font, w = 0, 0
    for code, arg, ch in TOKEN.findall(s):
        if code:
            if code == 'F8F7' and arg:
                font = int(arg, 16)
            continue
        w += advance(ch, font, metrics)
    return w


JP_CHAR = re.compile('[ぁ-んァ-ヶ一-龥]')


def text_kind(lines):
    """같은 window 를 써도 화면이 다른 글이 있다 — 슬리피 힌트(첫 줄이 ※)는 다른 글과 따로 잰다"""
    for s in lines:
        tx = text_chars(s).strip()
        if tx:
            return 'hint' if tx.startswith('※') else 'normal'
    return 'normal'


def jp_window_widths(disc, detail=None):
    """(window, 종류) → 원본 일본어 최대 줄 너비.
    일본어가 한 글자도 없는 줄(디버그 알파벳·저작권 표기)은 한도를 부풀리므로 빼고,
    그런 줄밖에 없는 창(크레디트 등)만 포함해서 잰다.  detail(dict)을 주면 창별 사용 현황도 채운다"""
    wjp = collections.defaultdict(int)
    wall = collections.defaultdict(int)
    for p in disc.entries:
        if not (p.startswith('gametext/') and p.endswith('Japanese.bin')):
            continue
        r = load(disc.read(p))
        m = file_metrics(r)
        area = p.split('/')[1] if '/Sequences/' not in p else 'Seq' + p.split('/')[-1].split('_')[0]
        for t in r['texts']:
            lines = r['strs'][t[6]:t[6] + t[1]]
            key = (t[2], text_kind(lines))
            for s in lines:
                w = width(s, m)
                tx = text_chars(s)
                wall[key] = max(wall[key], w)
                if JP_CHAR.search(tx) and w > wjp[key]:
                    wjp[key] = w
                    if detail is not None:
                        detail.setdefault(key, {})['widest'] = (area, t[0], tx)
            if detail is not None:
                d = detail.setdefault(key, {})
                d.setdefault('areas', collections.Counter())[area if not area.startswith('Seq') else '(컷신)'] += 1
    limits = {}
    for key, w in wall.items():
        limits[key] = wjp[key] if wjp.get(key) else w
    return limits


def main(margin=0):
    disc = Disc(find_jp_iso())
    limits = jp_window_widths(disc)
    trans = load_translations(translation_jsons())
    rows = []
    for area, d in trans.items():
        if not d:
            continue
        r = load(disc.read(area_path(area)))
        metrics = file_metrics(r)
        T = {str(t[0]): t for t in r['texts']}
        for tid, v in d.items():
            t = T.get(tid)
            if not t:
                continue
            old = r['strs'][t[6]:t[6] + t[1]]
            lines = v.split('|') if isinstance(v, str) else v
            limit = limits[(t[2], text_kind(old))] - margin
            for i, line in enumerate(lines):
                if line is None or line == '...':
                    continue
                s = line if isinstance(v, str) else split_prefix(old[i])[0] + line
                w = width(s, metrics)
                if w > limit:
                    rows.append((w - limit, w, limit, area, tid, i, t[2], text_chars(s)))
    rows.sort(reverse=True)
    for over, w, limit, area, tid, i, win, s in rows:
        print(f'+{over:4d}px  {w}/{limit}  win={win}  {area} {tid} 줄{i}: {s}')
    print(f'넘치는 줄 {len(rows)}개 (여유 {margin}px 기준)', file=sys.stderr)
    return len(rows)


def windows():
    """창(window)·종류별 한도와 쓰임새 요약"""
    disc = Disc(find_jp_iso())
    detail = {}
    limits = jp_window_widths(disc, detail)
    for key in sorted(limits, key=lambda k: -sum(detail.get(k, {}).get('areas', {}).values())):
        d = detail.get(key, {})
        n = sum(d.get('areas', {}).values())
        top = ', '.join('%s %d' % kv for kv in d.get('areas', collections.Counter()).most_common(4))
        win, kind = key
        print(f'win={win:<4} {kind:<6} 한도 {limits[key]:4d}px  텍스트 {n:5d}개  [{top}]')
        if 'widest' in d:
            area, tid, text = d['widest']
            print(f'                가장 긴 원문: {area} #{tid} {text}')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--windows':
        windows()
        sys.exit(0)
    sys.exit(1 if main(int(sys.argv[1]) if len(sys.argv) > 1 else 0) else 0)
