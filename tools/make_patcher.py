"""게임큐브용 파일 단위 패처 생성기 (disc-file-patcher 스킬의 게임큐브판).

원본 일본판 ISO와 한글 빌드 ISO를 FST 기준으로 비교해, 바뀐 파일마다 xdelta 차분을 만든다.
차분은 빌드가 파일을 쓴 순서(새 오프셋 순)로 manifest 에 적으므로, 정본 ISO에 패처를 적용하면
빌드 결과와 바이트까지 같은 ISO가 나온다. 사용자용 패처(패치하기.bat + patch.ps1)와 wit·xdelta3 를
한 폴더/zip 으로 묶는다. wit 은 CISO·WIA 등을 ISO로 바꿀 때만 쓴다(게임큐브는 다시 묶을 필요가 없음).

사용:
  python tools/make_patcher.py --orig "원본.iso" --build "한글.iso" --out ../release/v1.2f/sfa-korean-v1.2f \
      --version 1.2f --wit <wit-cygwin64 폴더> --xdelta <xdelta3.exe> [--readme README.txt]
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from sfa.gcm import Disc  # noqa: E402

WIT_FILES = ('bin/wit.exe', 'bin/cygwin1.dll', 'bin/cygz.dll', 'bin/cygcrypto-1.1.dll', 'bin/cygncursesw-10.dll')


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    for k in ('orig', 'build', 'out', 'version', 'wit', 'xdelta'):
        ap.add_argument('--' + k, required=True)
    ap.add_argument('--title', default='스타폭스 어드벤처')
    ap.add_argument('--result', default='Star Fox Adventures (Korean)')
    ap.add_argument('--readme')
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    orig, build = Disc(a.orig), Disc(a.build)
    out = Path(a.out)
    xdelta = str(Path(a.xdelta).resolve())   # 상대경로 그대로면 Windows에서 실행 파일을 못 찾음

    # 헤더는 게임 이름(0x20~0x60)만 달라야 한다. 실행 파일·애플로더는 같아야 한다.
    ho, hb = open(a.orig, 'rb').read(0x2440), open(a.build, 'rb').read(0x2440)
    diff = [i for i in range(len(ho)) if ho[i] != hb[i]]
    assert all(0x20 <= i < 0x60 for i in diff), f'게임 이름 밖의 헤더가 다름: {[hex(i) for i in diff[:8]]}'
    assert set(orig.entries) == set(build.entries), '파일 목록이 다름(추가·삭제 파일은 지원 안 함)'
    discname = hb[0x20:0x60].split(b'\0')[0].decode('ascii')

    changed = [p for p in build.entries if orig.read(p) != build.read(p)]
    changed.sort(key=lambda p: build.entries[p][0])   # 빌드가 쓴 순서 = 새 오프셋 순
    end = max(o + s for _, o, s in orig.files)
    pos = (end + 0x7fff) // 0x8000 * 0x8000
    for p in changed:   # 패처와 같은 배치 규칙인지 확인
        assert build.entries[p][0] == pos, f'배치 규칙이 다름: {p}'
        pos = (pos + build.entries[p][1] + 3) // 4 * 4

    if out.exists():
        shutil.rmtree(out)
    (out / 'data').mkdir(parents=True)
    tmp = Path(tempfile.mkdtemp())
    lines = []
    for i, p in enumerate(changed):
        A, B = orig.read(p), build.read(p)
        (tmp / 'a').write_bytes(A); (tmp / 'b').write_bytes(B)
        patch = f'{i:03d}.xdelta'
        # -A= : 헤더에 파일 경로(PC 사용자 이름 포함)를 적지 않음
        subprocess.run([xdelta, '-e', '-f', '-9', '-S', 'djw', '-A=', '-s', str(tmp / 'a'), str(tmp / 'b'),
                        str(out / 'data' / patch)], check=True)
        lines.append('\t'.join(('raw', patch, p, md5(A), md5(B))))
    shutil.rmtree(tmp)
    (out / 'data' / 'manifest.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (out / 'data' / 'config.txt').write_text(
        f'id={orig.gid}\nrev={ho[7]}\ntitle={a.title}\nversion={a.version}\nresult={a.result}\ndiscname={discname}\n',
        encoding='utf-8')

    tpl = HERE.parent / 'patcher'
    shutil.copy2(tpl / 'patch.ps1', out / 'patch.ps1')
    shutil.copy2(tpl / '패치하기.bat', out / '패치하기.bat')
    if a.readme:
        shutil.copy2(a.readme, out / Path(a.readme).name)
    (out / 'bin').mkdir()
    for f in WIT_FILES:
        shutil.copy2(Path(a.wit) / f, out / 'bin' / Path(f).name)
    shutil.copy2(Path(a.wit) / 'gpl-2.0.txt', out / 'bin' / 'wit-gpl-2.0.txt')
    shutil.copy2(xdelta, out / 'bin' / 'xdelta3.exe')

    zpath = out.parent / (out.name + '.zip')   # with_suffix 는 'v1.2f' 의 '.2f' 를 확장자로 봄
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for dp, _, fs in os.walk(out):
            for f in sorted(fs):
                q = Path(dp) / f
                z.write(q, Path(out.name) / q.relative_to(out))
    size = sum(f.stat().st_size for f in (out / 'data').iterdir())
    print(f'파일 {len(lines)}개, 차분 합계 {size / 1e6:.2f} MB, zip {zpath.stat().st_size / 1e6:.2f} MB')
    print(f'게임 이름: {discname}')
    print(f'패처: {out}')


if __name__ == '__main__':
    main()
