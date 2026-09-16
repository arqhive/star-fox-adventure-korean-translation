# 번역 적용 + 이미지 교체 파일을 일본판 ISO 복사본에 넣기
# 새 파일은 원본 데이터 끝 뒤에 이어 쓰고 FST의 오프셋·크기만 수정 (디스크 용량 1.46GB 안)
import os, re, json, struct, shutil
from PIL import Image
from .gcm import Disc
from .gametext import load, build_file, area_path
from .config import GAME_ID

DISC_SIZE = 1459978240


def load_translations(jsons):
    trans = {}
    for jf in jsons:
        for area, d in json.load(open(jf, encoding='utf8')).items():
            trans.setdefault(area, {}).update(d)
    return trans


def build_gametext(disc, trans, atlas_dir=None, log=print):
    """→ {디스크 경로: 새 바이너리}"""
    # 공통 문구: 번역된 텍스트를 다른 구역의 같은 ID·같은 원문에도 적용
    common = {}
    for area, d in trans.items():
        if not d:
            continue
        r = load(disc.read(area_path(area)))
        for t in r['texts']:
            if str(t[0]) in d:
                common.setdefault((t[0], '|'.join(r['strs'][t[6]:t[6] + t[1]])), d[str(t[0])])
    # 번역 JSON에 없는 파일도 전부 검사: 공통 번역이 하나라도 걸리면 재빌드
    areas = list(trans)
    for p in disc.entries:
        m = re.fullmatch(r'gametext/(?:Sequences/(\d+)_Japanese|([^/]+)/Japanese)\.bin', p)
        if m:
            ar = 'Seq' + m.group(1) if m.group(1) else m.group(2)
            if ar not in trans:
                areas.append(ar)
    out = {}
    for area in areas:
        path = area_path(area); data = disc.read(path)
        if area not in trans:
            r0 = load(data)
            if not any((t[0], '|'.join(r0['strs'][t[6]:t[6] + t[1]])) in common for t in r0['texts']):
                continue
        new, added, atlas, (oh, nh) = build_file(data, trans.get(area, {}), common)
        out[path] = new
        if atlas_dir:
            os.makedirs(atlas_dir, exist_ok=True)
            Image.fromarray(atlas).save(os.path.join(atlas_dir, f'atlas_{area}.png'))
        log(f'{path}: {len(data)} -> {len(new)} bytes, 글리프 +{len(added)}, 텍스처 높이 {oh} -> {nh}')
    return out


def collect_overrides(disc, override_dir, log=print):
    out = {}
    if not override_dir or not os.path.isdir(override_dir):
        return out
    for root, _, fs in os.walk(override_dir):
        for fn in fs:
            full = os.path.join(root, fn); rel = os.path.relpath(full, override_dir).replace(os.sep, '/')
            assert rel in disc.entries, rel
            out[rel] = open(full, 'rb').read()
            log(f'{rel}: override {len(out[rel])} bytes')
    return out


def write_iso(src_iso, out_iso, newfiles, disc_name, log=print):
    disc = Disc(src_iso)
    log('ISO 복사 중...')
    shutil.copyfile(src_iso, out_iso)
    with open(out_iso, 'r+b') as f:
        h = f.read(0x440); fo, fs = struct.unpack('>II', h[0x424:0x42c])
        f.seek(fo); fstd = bytearray(f.read(fs))
        end = max(a + b for _, a, b in disc.files)
        pos = (end + 0x7fff) // 0x8000 * 0x8000
        n = struct.unpack('>I', fstd[8:12])[0]; st = n * 12

        def nm(o):
            e = fstd.index(0, st + o); return bytes(fstd[st + o:e]).decode('shift_jis')
        idx = {}

        def walk(i, stop, pre):
            while i < stop:
                fl = fstd[i * 12]; no = int.from_bytes(fstd[i * 12 + 1:i * 12 + 4], 'big')
                nxt = struct.unpack('>I', fstd[i * 12 + 8:i * 12 + 12])[0]
                if fl: walk(i + 1, nxt, pre + nm(no) + '/'); i = nxt
                else: idx[pre + nm(no)] = i; i += 1
        walk(1, n, '')
        for path, data in newfiles.items():
            f.seek(pos); f.write(data)
            struct.pack_into('>II', fstd, idx[path] * 12 + 4, pos, len(data))
            pos = (pos + len(data) + 3) // 4 * 4
        assert pos <= DISC_SIZE, '디스크 용량 초과'
        f.seek(fo); f.write(fstd)
        f.seek(0x20); f.write(disc_name.encode('ascii').ljust(0x40, b'\0')[:0x40])
    log(f'완료: {out_iso}')


def build_iso(src_iso, out_iso, jsons, override_dir, disc_name, atlas_dir=None, log=print):
    disc = Disc(src_iso)
    assert disc.gid == GAME_ID, f'일본판 ISO가 아닙니다: {disc.gid}'
    newfiles = build_gametext(disc, load_translations(jsons), atlas_dir, log)
    newfiles.update(collect_overrides(disc, override_dir, log))
    write_iso(src_iso, out_iso, newfiles, disc_name, log)
