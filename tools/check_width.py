# 번역 줄이 원본 창 너비를 넘는지 검사 (넘치면 게임이 자동 줄바꿈해 창 밖으로 밀림)
# 기준: 같은 window 값을 쓰는 원본 일본어 줄의 최대 너비
# 사용: python tools/check_width.py [여유픽셀]      ※ 먼저 python build.py --json-only
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sfa.config import find_jp_iso, translation_jsons
from sfa.gcm import Disc
from sfa.gametext import load, text_chars, area_path, split_prefix, render_glyph
from sfa.isopatch import load_translations

CACHE = {}


def advance(ch, metrics):
    if ord(ch) in metrics:
        return metrics[ord(ch)]
    if ch not in CACHE:
        img, l, r, top, bot = render_glyph(ch)
        CACHE[ch] = l + img.shape[1] + r
    return CACHE[ch]


def width(s, metrics):
    return sum(advance(ch, metrics) for ch in text_chars(s))


def jp_window_widths(disc):
    """window 값 → 원본 일본어 최대 줄 너비"""
    wmax = collections.defaultdict(int)
    for p in disc.entries:
        if not (p.startswith('gametext/') and p.endswith('Japanese.bin')):
            continue
        r = load(disc.read(p))
        m = {c[0]: c[3] + c[7] + c[4] for c in r['chars'] if c[9] == 0}
        for t in r['texts']:
            for s in r['strs'][t[6]:t[6] + t[1]]:
                wmax[t[2]] = max(wmax[t[2]], width(s, m))
    return wmax


def main(margin=0):
    disc = Disc(find_jp_iso())
    limits = jp_window_widths(disc)
    trans = load_translations(translation_jsons())
    rows = []
    for area, d in trans.items():
        if not d:
            continue
        r = load(disc.read(area_path(area)))
        metrics = {c[0]: c[3] + c[7] + c[4] for c in r['chars'] if c[9] == 0}
        T = {str(t[0]): t for t in r['texts']}
        for tid, v in d.items():
            t = T.get(tid)
            if not t:
                continue
            old = r['strs'][t[6]:t[6] + t[1]]
            lines = v.split('|') if isinstance(v, str) else v
            limit = limits[t[2]] - margin
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


if __name__ == '__main__':
    sys.exit(1 if main(int(sys.argv[1]) if len(sys.argv) > 1 else 0) else 0)
