# 일본어 원문을 번역용으로 출력: 줄마다 앞쪽 제어코드(prefix) » 본문
# 사용: python tools/extract_text.py SwapHol Seq1201 ...   (구역 이름 = gametext 폴더명, 컷신 = Seq + 번호)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sfa.config import find_jp_iso
from sfa.gcm import Disc
from sfa.gametext import load, area_path, split_prefix

if __name__ == '__main__':
    disc = Disc(find_jp_iso())
    for area in sys.argv[1:]:
        r = load(disc.read(area_path(area)))
        for t in r['texts']:
            print(f'## {area} {t[0]} win={t[2]}')
            for s in r['strs'][t[6]:t[6] + t[1]]:
                p, x = split_prefix(s)
                print(f'  {p} » {x}')
