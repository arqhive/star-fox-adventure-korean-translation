# GameCube GX 텍스처 디코드/인코드 + SFA 텍스처 컨테이너(ZLB 압축, 0x60 헤더)
import struct, zlib
import numpy as np

HEADER = 0x60  # SFA 텍스처 헤더 크기 (w @0x0A, h @0x0C, format @0x16)


def c565(v):
    r = (v >> 11) & 31; g = (v >> 5) & 63; b = v & 31
    return np.array([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2), 255], np.int32)


def dec_cmpr(data, w, h):
    bw = (w + 7) // 8 * 8; bh = (h + 7) // 8 * 8
    out = np.zeros((bh, bw, 4), np.uint8); p = 0
    for y in range(0, bh, 8):
        for x in range(0, bw, 8):
            for sy in (0, 4):
                for sx in (0, 4):
                    c0, c1, bits = struct.unpack_from('>HHI', data, p); p += 8
                    a, b = c565(c0), c565(c1)
                    if c0 > c1: pal = [a, b, (2 * a + b) // 3, (a + 2 * b) // 3]
                    else: pal = [a, b, (a + b) // 2, np.array([0, 0, 0, 0])]
                    for i in range(16):
                        idx = (bits >> (30 - 2 * i)) & 3
                        out[y + sy + i // 4, x + sx + i % 4] = pal[idx]
    return out[:h, :w]


def dec_rgb5a3(data, w, h):  # 4x4 블록 순서
    bw = (w + 3) // 4 * 4; bh = (h + 3) // 4 * 4
    flat = np.frombuffer(data[:bw * bh * 2], '>u2'); a = np.zeros((bh, bw), np.int32); k = 0
    for y in range(0, bh, 4):
        for x in range(0, bw, 4):
            a[y:y + 4, x:x + 4] = flat[k:k + 16].reshape(4, 4); k += 16
    out = np.zeros((bh, bw, 4), np.uint8); hi = (a & 0x8000) != 0
    out[..., 0] = np.where(hi, ((a >> 10) & 31) * 255 // 31, ((a >> 8) & 15) * 17)
    out[..., 1] = np.where(hi, ((a >> 5) & 31) * 255 // 31, ((a >> 4) & 15) * 17)
    out[..., 2] = np.where(hi, (a & 31) * 255 // 31, (a & 15) * 17)
    out[..., 3] = np.where(hi, 255, ((a >> 12) & 7) * 255 // 7)
    return out[:h, :w]


def dec_rgba8(data, w, h):  # 4x4 블록 순서
    bw = (w + 3) // 4 * 4; bh = (h + 3) // 4 * 4
    out = np.zeros((bh, bw, 4), np.uint8); p = 0
    for y in range(0, bh, 4):
        for x in range(0, bw, 4):
            out[y:y + 4, x:x + 4] = np.frombuffer(data[p:p + 64], np.uint8).reshape(4, 4, 4); p += 64
    return out[:h, :w]


def dec_ia8(data, w, h):
    a = np.frombuffer(data[:w * h * 2], np.uint8).reshape(h, w, 2)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., 0] = out[..., 1] = out[..., 2] = a[..., 1]; out[..., 3] = a[..., 0]
    return out


DEC = {14: dec_cmpr, 5: dec_rgb5a3, 6: dec_rgba8, 3: dec_ia8}


def zlb_items(d):
    """[(오프셋, 압축 크기, 해제된 텍스처), ...]"""
    p = 0; res = []
    while True:
        i = d.find(b'ZLB\0', p)
        if i < 0:
            return res
        ver, dsz, csz = struct.unpack_from('>III', d, i + 4)
        try:
            raw = zlib.decompress(d[i + 16:i + 16 + csz])
        except Exception:
            p = i + 4; continue
        res.append((i, csz, raw)); p = i + 16 + csz


def zlb_pack(raw):
    comp = zlib.compress(bytes(raw), 9)
    return b'ZLB\0' + struct.pack('>III', 1, len(raw), len(comp)) + comp


def tex_info(raw):
    w, h = struct.unpack_from('>HH', raw, 0x0A)
    return w, h, raw[0x16]


def _to565(c):
    c = np.clip(c, 0, 255).astype(np.int32)
    return ((c[..., 0] * 31 + 127) // 255 << 11) | ((c[..., 1] * 63 + 127) // 255 << 5) | ((c[..., 2] * 31 + 127) // 255)


def _expand565(v):
    r = (v >> 11) & 31; g = (v >> 5) & 63; b = v & 31
    return np.stack([(r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)], -1).astype(np.int32)


def enc_cmpr(rgb):
    """불투명 RGB → GX CMPR (8x8 안에 4x4 서브블록 순서). 주성분 축 끝점 후보 중 오차 최소 선택"""
    h, w = rgb.shape[:2]; bw = (w + 7) // 8 * 8; bh = (h + 7) // 8 * 8
    img = np.zeros((bh, bw, 3), np.int32); img[:h, :w] = rgb[..., :3]
    img[h:, :] = img[h - 1:h, :]; img[:, w:] = img[:, w - 1:w]
    out = bytearray()
    for y in range(0, bh, 8):
        for x in range(0, bw, 8):
            for sy in (0, 4):
                for sx in (0, 4):
                    blk = img[y + sy:y + sy + 4, x + sx:x + sx + 4].reshape(16, 3).astype(np.float64)
                    mean = blk.mean(0); cen = blk - mean; cov = cen.T @ cen
                    axis = np.array([1.0, 1.0, 1.0]) if np.allclose(cov, 0) else np.linalg.eigh(cov)[1][:, -1]
                    proj = cen @ axis; best = None
                    for lo_q, hi_q in ((0, 100), (5, 95), (12, 88)):
                        c_hi = mean + axis * np.percentile(proj, hi_q); c_lo = mean + axis * np.percentile(proj, lo_q)
                        v0 = int(_to565(c_hi[None])[0]); v1 = int(_to565(c_lo[None])[0])
                        if v0 < v1: v0, v1 = v1, v0
                        if v0 == v1:
                            if v0 < 0xFFFF: v0 += 1
                            else: v1 -= 1
                        e0 = _expand565(np.array(v0)); e1 = _expand565(np.array(v1))
                        pal = np.stack([e0, e1, (2 * e0 + e1) // 3, (e0 + 2 * e1) // 3])
                        d = ((blk[:, None, :] - pal[None]) ** 2).sum(-1)
                        idx = d.argmin(1); err = d.min(1).sum()
                        if best is None or err < best[0]: best = (err, v0, v1, idx)
                    _, v0, v1, idx = best; bits = 0
                    for i in range(16): bits = (bits << 2) | int(idx[i])
                    out += struct.pack('>HHI', v0, v1, bits)
    return bytes(out)
