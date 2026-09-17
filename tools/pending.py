# 아직 번역되지 않은 텍스트 출력 (같은 ID+같은 원문은 한 번만). 인자 없으면 전체 구역·컷신 검사
# 사용: python tools/pending.py [구역 ...]      ※ 먼저 python build.py --json-only 로 번역 JSON 생성
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sfa.config import find_jp_iso, translation_jsons
from sfa.gcm import Disc
from sfa.gametext import load, area_path, split_prefix
from sfa.isopatch import load_translations

JP = re.compile('[぀-ヺー-ヿ一-鿿]')   # 가운뎃점 ・(U+30FB)은 한국어 표기에도 쓰므로 제외


def all_areas(disc):
    out = []
    for p in disc.entries:
        m = re.fullmatch(r'gametext/(?:Sequences/(\d+)_Japanese|([^/]+)/Japanese)\.bin', p)
        if m:
            out.append('Seq' + m.group(1) if m.group(1) else m.group(2))
    return out


if __name__ == '__main__':
    disc = Disc(find_jp_iso())
    areas = sys.argv[1:] or all_areas(disc)
    tr = load_translations(translation_jsons()); done = set()
    for area, d in tr.items():
        r = load(disc.read(area_path(area)))
        for t in r['texts']:
            if str(t[0]) in d:
                done.add((t[0], '|'.join(r['strs'][t[6]:t[6] + t[1]])))
    seen = {}
    for area in areas:
        r = load(disc.read(area_path(area)))
        for t in r['texts']:
            ss = r['strs'][t[6]:t[6] + t[1]]; key = (t[0], '|'.join(ss))
            if key in done or not any(JP.search(s) for s in ss):
                continue
            seen.setdefault(key, []).append(area)
    n = 0
    for (tid, joined), al in seen.items():
        n += len(joined)
        print(f'## {tid} [{",".join(al)}]')
        for s in joined.split('|'):
            p, x = split_prefix(s)
            print(f'  {p} » {x}')
    print('미번역 글자', n, '텍스트', len(seen), file=sys.stderr)
