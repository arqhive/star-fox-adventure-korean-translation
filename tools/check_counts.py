# 번역 JSON의 줄 수가 원문과 맞는지 검사 (문제 있으면 출력하고 종료 코드 1)
# 사용: python tools/check_counts.py [json ...]   (인자 없으면 빌드에 쓰는 전체 JSON)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sfa.config import find_jp_iso, translation_jsons
from sfa.gcm import Disc
from sfa.gametext import load, area_path
from sfa.isopatch import load_translations


def check(disc, jsons):
    problems = 0
    for jf in jsons:
        for area, d in load_translations([jf]).items():
            if not d:
                continue
            r = load(disc.read(area_path(area))); T = {str(t[0]): t for t in r['texts']}
            for k, v in d.items():
                if k not in T:
                    print(os.path.basename(jf), area, k, '원문에 없는 ID'); problems += 1; continue
                if isinstance(v, str):
                    continue
                n = T[k][1]
                ok = len(v) - 1 <= n if v and v[-1] == '...' else len(v) == n
                if not ok:
                    print(os.path.basename(jf), area, k, f'줄 수 {len(v)} != 원문 {n}', r['strs'][T[k][6]:T[k][6] + n])
                    problems += 1
    return problems


if __name__ == '__main__':
    n = check(Disc(find_jp_iso()), sys.argv[1:] or translation_jsons())
    print('문제', n, '건')
    sys.exit(1 if n else 0)
