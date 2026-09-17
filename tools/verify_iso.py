# 빌드된 ISO 검사: 모든 일본어 gametext 파일에 일본어 문장이 남았는지, 글리프 텍스처 최대 높이
# 사용: python tools/verify_iso.py "Star Fox Adventures (Korean).iso"
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sfa.gcm import Disc
from sfa.gametext import load, textures

JP = re.compile('[぀-ヺー-ヿ一-鿿]')   # 가운뎃점 ・(U+30FB)은 한국어 표기에도 쓰므로 제외

if __name__ == '__main__':
    disc = Disc(sys.argv[1])
    files = left = maxh = 0
    for p in disc.entries:
        if not (p.startswith('gametext/') and 'Japanese' in p and p.endswith('.bin')):
            continue
        d = disc.read(p); r = load(d); files += 1
        maxh = max([maxh] + [h for _, _, _, h, _ in textures(d, r['texofs'])[0]])
        for t in r['texts']:
            ss = r['strs'][t[6]:t[6] + t[1]]
            if any(JP.search(s) for s in ss):
                left += 1; print('일본어 남음:', p, t[0], '|'.join(ss)[:60])
    end = max(a + b for _, a, b in disc.files)
    print(f'검사 파일 {files}, 일본어 남은 텍스트 {left}, 최대 텍스처 높이 {maxh}, 디스크 사용 {end / 2**20:.0f}MB')
    sys.exit(1 if left else 0)
