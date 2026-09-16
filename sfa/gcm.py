# GameCube 디스크 이미지(GCM/ISO) 파일 시스템(FST) 읽기
import struct


def fst(path):
    """(게임 ID, 내부 이름, DOL 오프셋, [(경로, 오프셋, 크기), ...])"""
    with open(path, 'rb') as f:
        h = f.read(0x440)
        gid = h[:6].decode(); name = h[0x20:0x60].split(b'\0')[0].decode('latin1')
        dol, fo, fs = struct.unpack('>III', h[0x420:0x42c])
        f.seek(fo); d = f.read(fs)
    n = struct.unpack('>I', d[8:12])[0]; st = n * 12; out = []

    def nm(o):
        e = d.index(b'\0', st + o); return d[st + o:e].decode('shift_jis', 'replace')

    def walk(i, end, pre):
        while i < end:
            fl = d[i * 12]; no = struct.unpack('>I', b'\0' + d[i * 12 + 1:i * 12 + 4])[0]
            a, b = struct.unpack('>II', d[i * 12 + 4:i * 12 + 12])
            if fl: walk(i + 1, b, pre + nm(no) + '/'); i = b
            else: out.append((pre + nm(no), a, b)); i += 1
    walk(1, n, '')
    return gid, name, dol, out


class Disc:
    """ISO에서 경로로 파일을 읽는 도우미"""
    def __init__(self, path):
        self.path = path
        self.gid, self.name, self.dol, self.files = fst(path)
        self.entries = {p: (a, b) for p, a, b in self.files}
        self._f = open(path, 'rb')

    def read(self, path):
        a, b = self.entries[path]; self._f.seek(a); return self._f.read(b)
