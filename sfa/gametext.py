# gametext/*.bin 포맷: 문자표 + 텍스트 + UTF-8 문자열 풀 + 파일별 글리프 텍스처
#
#  u32 문자 수, 문자표 16B×n (UCS4, xpos, ypos, left, right, top, bottom, w, h, font, texture)
#  u16 텍스트 수, u16 풀 크기, 텍스트 12B×n (id, 줄 수, window, alignH, alignV, lang, 첫 줄 인덱스)
#  u32 줄 수, u32 오프셋×n, 문자열 풀(4바이트 정렬)
#  u32, 텍스처들 (u16 fmt, u16 bpp, u16 w, u16 h, 데이터; fmt 2 = I4 8x8 블록), 0×8
import os, re, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 제어코드(사설 영역) 뒤에 붙는 바이너리 인자 길이
ARGS = {0xf8f4: 2, 0xf8f7: 2, 0xf8ff: 8, 0xe000: 2, 0xe018: 6, 0xe020: 2}
CODE = re.compile(r'\{[0-9A-F]{4}(?::[0-9a-f]*)?\}')
PREFIX = re.compile(r'^((?:\{(?:E0[0-9A-F]{2}|F8F4|F8FF)(?::[0-9a-f]*)?\})*)(.*)$', re.S)


def area_path(area):
    """'SwapHol' → gametext/SwapHol/Japanese.bin, 'Seq1201' → gametext/Sequences/1201_Japanese.bin"""
    return f'gametext/Sequences/{area[3:]}_Japanese.bin' if area.startswith('Seq') else f'gametext/{area}/Japanese.bin'


def split_prefix(s):
    """줄 앞쪽 타이밍/색 코드와 본문 분리"""
    m = PREFIX.match(s)
    return m.group(1), m.group(2)


def load(d):
    nc = struct.unpack_from('>I', d)[0]
    chars = [struct.unpack_from('>IHHbbbbBBBB', d, 4 + i * 16) for i in range(nc)]
    q = 4 + nc * 16
    nt, pool = struct.unpack_from('>HH', d, q); q += 4
    texts = [list(struct.unpack_from('>HHBBBBI', d, q + i * 12)) for i in range(nt)]; q += nt * 12
    nph = struct.unpack_from('>I', d, q)[0]; q += 4
    offs = struct.unpack_from('>%dI' % nph, d, q); q += 4 * nph
    pb = d[q:q + pool]; texofs = q + pool
    strs = []
    for o in offs:
        toks = []; p = o
        while pb[p]:
            b = pb[p]; n = 1 if b < 0x80 else 2 if b < 0xe0 else 3 if b < 0xf0 else 4
            ch = pb[p:p + n].decode('utf8'); p += n; cp = ord(ch)
            if 0xf8e0 <= cp <= 0xf8ff or 0xe000 <= cp <= 0xe0ff:
                a = ARGS.get(cp, 0)
                toks.append('{%04X%s}' % (cp, (':' + pb[p:p + a].hex()) if a else '')); p += a
            else:
                toks.append(ch)
        strs.append(''.join(toks))
    return dict(chars=chars, texts=texts, strs=strs, texofs=texofs, head=d[texofs:texofs + 4])


def encode(s):
    out = b''
    for m in re.finditer(r'\{([0-9A-F]{4})(?::([0-9a-f]*))?\}|.', s, re.S):
        if m.group(1):
            out += chr(int(m.group(1), 16)).encode('utf8') + bytes.fromhex(m.group(2) or '')
        else:
            out += m.group().encode('utf8')
    return out


def text_chars(s):
    return CODE.sub('', s)


def textures(d, ofs):
    p = ofs + 4; res = []
    while p + 8 <= len(d):
        fmt, bpp, w, h = struct.unpack_from('>HHHH', d, p)
        if w == 0:
            break
        p += 8
        n = ((w + 7) // 8 * 8) * ((h + 7) // 8 * 8) * bpp // 8 if fmt == 2 else w * h * bpp // 8
        res.append((fmt, bpp, w, h, d[p:p + n])); p += n
    return res, p


def i4_decode(raw, w, h):
    a = np.frombuffer(raw, np.uint8); nib = np.stack([a >> 4, a & 15], 1).reshape(-1)
    bw = (w + 7) // 8; bh = (h + 7) // 8; out = np.zeros((bh * 8, bw * 8), np.uint8); k = 0
    for by in range(bh):
        for bx in range(bw):
            out[by * 8:by * 8 + 8, bx * 8:bx * 8 + 8] = nib[k:k + 64].reshape(8, 8) * 17; k += 64
    return out[:h, :w]


def i4_encode(img):
    h, w = img.shape; bw = (w + 7) // 8; bh = (h + 7) // 8
    pad = np.zeros((bh * 8, bw * 8), np.uint8); pad[:h, :w] = (img.astype(int) + 8) // 17
    nib = np.concatenate([pad[by * 8:by * 8 + 8, bx * 8:bx * 8 + 8].reshape(-1) for by in range(bh) for bx in range(bw)])
    return bytes(((nib[0::2] << 4) | nib[1::2]).astype(np.uint8))


# ---- 한글 글리프 렌더 (셀 높이 21, 전각 폭 21: 원본 일본어 폰트 메트릭과 동일) ----
CELL = 21
_FONT = None


def glyph_font():
    global _FONT
    if _FONT is None:
        path = os.environ.get('SFA_GLYPH_FONT', 'C:/Windows/Fonts/malgunbd.ttf')
        _FONT = ImageFont.truetype(path, 20)
    return _FONT


def render_glyph(ch):
    """→ (이미지, left, right, top, bottom)"""
    font = glyph_font()
    cell = Image.new('L', (CELL + 8, CELL), 0)
    ImageDraw.Draw(cell).text((4, CELL / 2), ch, font=font, fill=255, anchor='lm')
    a = (np.array(cell).astype(int) + 8) // 17 * 17
    adv = CELL if ord(ch) >= 0x1100 else max(4, round(font.getlength(ch)) + 1)
    ys, xs = np.nonzero(a)
    if len(xs) == 0:
        return np.zeros((0, 0), np.uint8), adv, 0, CELL, 0
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    left = max(0, x0 - 4); w = x1 - x0
    return a[y0:y1, x0:x1].astype(np.uint8), left, max(0, adv - left - w), y0, CELL - y1


def kana_kanji(cp):
    return 0x3040 <= cp <= 0x30ff or 0x4e00 <= cp <= 0x9fff


def build_file(data, trans, common):
    """일본어 gametext 파일에 번역을 적용해 새 바이너리 생성.
    trans: {텍스트ID: 번역}, common: {(ID, 원문): 번역}
    번역 값: 'a|b' 문자열(코드 포함 전체 교체) 또는 리스트(줄마다 앞쪽 코드 유지, None=원문, 끝 '...'=나머지 원문)"""
    r = load(data)
    chars = [list(c) for c in r['chars']]
    texts = r['texts']; strs = r['strs']
    new_strs = []
    for t in texts:
        old = strs[t[6]:t[6] + t[1]]
        v = trans.get(str(t[0]))
        if v is None:
            v = common.get((t[0], '|'.join(old)))
        if v is None:
            lines = old
        elif isinstance(v, str):
            lines = v.split('|')
        else:
            if v and v[-1] == '...':
                v = v[:-1] + [None] * (len(old) - len(v) + 1)
            assert len(v) == len(old), f'{t[0]}: 줄 수 {len(v)} != 원문 {len(old)}'
            lines = [o if n is None else split_prefix(o)[0] + n for o, n in zip(old, v)]
        t[6] = len(new_strs); t[1] = len(lines); new_strs.extend(lines)

    texs, _ = textures(data, r['texofs'])
    used = {ord(ch) for s in new_strs for ch in text_chars(s)}
    # 안 쓰는 가나/한자 글리프 제거 (숫자·기호·라틴은 동적 표시 대비 유지)
    chars = [c for c in chars if not (c[9] == 0 and kana_kanji(c[0]) and c[0] not in used)]
    f0 = [c for c in chars if c[9] == 0]
    tidx = f0[0][10] if f0 else [c for c in r['chars'] if c[9] == 0][0][10]
    fmt, bpp, tw, th, raw = texs[tidx]
    atlas = i4_decode(raw, tw, th)
    glyphs = [(c, atlas[c[2]:c[2] + c[8], c[1]:c[1] + c[7]].copy()) for c in f0]
    have = {c[0] for c in f0}; added = []
    for s in new_strs:
        for ch in text_chars(s):
            if ord(ch) not in have:
                img, l, rr, top, bot = render_glyph(ch)
                c = [ord(ch), 0, 0, l, rr, top, bot, img.shape[1], img.shape[0], 0, tidx]
                chars.append(c); glyphs.append((c, img)); have.add(ord(ch)); added.append(ch)

    # 아틀라스 재배치 (원래 폭, 1px 간격)
    x, y, rowh = 1, 1, 0
    for c, img in glyphs:
        w, h = c[7], c[8]
        if x + w + 1 > tw:
            x = 1; y += rowh + 1; rowh = 0
        c[1], c[2] = x, y; x += w + 1; rowh = max(rowh, h)
    nh = (y + rowh + 1 + 7) // 8 * 8
    assert nh <= 1024, f'텍스처 높이 {nh} > 1024'
    new_atlas = np.zeros((nh, tw), np.uint8)
    for c, img in glyphs:
        if c[7] and c[8]:
            new_atlas[c[2]:c[2] + c[8], c[1]:c[1] + c[7]] = img
    texs[tidx] = (fmt, bpp, tw, nh, i4_encode(new_atlas))

    pool = b''; offs = []
    for s in new_strs:
        offs.append(len(pool)); pool += encode(s) + b'\0'
    pool += b'\0' * (-len(pool) % 4)
    o = struct.pack('>I', len(chars)) + b''.join(struct.pack('>IHHbbbbBBBB', *c) for c in chars)
    o += struct.pack('>HH', len(texts), len(pool)) + b''.join(struct.pack('>HHBBBBI', *t) for t in texts)
    o += struct.pack('>I', len(offs)) + struct.pack('>%dI' % len(offs), *offs) + pool
    o += r['head'] + b''.join(struct.pack('>HHHH', a, b, w, h) + d for a, b, w, h, d in texs) + b'\0' * 8
    return o, added, new_atlas, (th, nh)
