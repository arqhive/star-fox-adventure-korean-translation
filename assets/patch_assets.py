# 로고·배너 교체 파일 생성 → build/override/ (isopatch가 ISO에 함께 넣음)
import os, sys, struct
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sfa.config import BUILD, OVERRIDE_DIR, find_jp_iso
from sfa.gcm import Disc
from sfa.gxtex import zlb_items, zlb_pack, tex_info, enc_cmpr, dec_cmpr, HEADER

LOGO_TAB_INDEX = 455   # gamefront/TEX0: 일본어 로고 512x191 CMPR (영문 로고는 454, 456)


def write(path, data):
    p = os.path.join(OVERRIDE_DIR, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(data)


def patch_logo(disc, logo_path=None):
    binf = bytearray(disc.read('gamefront/TEX0.bin')); tab = bytearray(disc.read('gamefront/TEX0.tab'))
    ent = struct.unpack_from('>I', tab, LOGO_TAB_INDEX * 4)[0]; off = (ent & 0xFFFFFF) * 2
    raw = bytearray({o: r for o, c, r in zlb_items(bytes(binf))}[off])
    w, h, fmt = tex_info(raw); assert (w, h, fmt) == (512, 191, 14)
    logo = np.array(Image.open(logo_path or os.path.join(BUILD, 'logo_kor.png')).convert('RGB'))
    if logo.shape != (h, w, 3):
        raise ValueError(f'로고 크기는 {w}x{h}여야 합니다: {logo.shape}')
    data = enc_cmpr(logo)
    raw[HEADER:HEADER + len(data)] = data          # 뒤쪽 절반은 게임이 쓰지 않는 버퍼 여유분 → 원본 유지
    Image.fromarray(dec_cmpr(data, w, h)).save(os.path.join(BUILD, 'logo_kor_cmpr_preview.png'))
    new = zlb_pack(raw)
    pos = (len(binf) + 31) // 32 * 32               # TEX0.bin 끝에 새 텍스처 추가, tab 오프셋만 변경
    binf += b'\0' * (pos - len(binf)) + new
    binf += b'\0' * ((-len(binf)) % 32)
    struct.pack_into('>I', tab, LOGO_TAB_INDEX * 4, (ent & 0xFF000000) | (pos // 2))
    write('gamefront/TEX0.bin', bytes(binf)); write('gamefront/TEX0.tab', bytes(tab))
    print('로고 교체:', hex(off), '->', hex(pos), len(new) - 16, 'bytes')
    return {'gamefront/TEX0.bin': bytes(binf), 'gamefront/TEX0.tab': bytes(tab)}


def patch_banner(disc):
    bnr = bytearray(disc.read('opening.bnr')); assert bnr[:4] == b'BNR1'
    # 배너 이미지는 글자 없는 엠블럼 → 유지. 텍스트는 Shift-JIS만 가능해 한글 불가 → 영문
    def put(o, n, s):
        e = s.encode('shift_jis'); assert len(e) < n
        bnr[o:o + n] = e + b'\0' * (n - len(e))
    put(0x1820, 0x20, 'STARFOX ADVENTURES')
    put(0x1840, 0x20, '2002 Nintendo')
    put(0x1860, 0x40, 'STARFOX ADVENTURES (KOREAN)')
    put(0x18A0, 0x40, '2002 Nintendo. Game by Rare.')
    put(0x18E0, 0x80, 'Korean translation patch.\nSave Dinosaur Planet from General Scales!')
    write('opening.bnr', bytes(bnr)); print('배너 텍스트 교체')


if __name__ == '__main__':
    disc = Disc(sys.argv[1] if len(sys.argv) > 1 else find_jp_iso())
    patch_logo(disc); patch_banner(disc)
