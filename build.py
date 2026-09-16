# 스타 폭스 어드벤처 한글 패치 빌드 (일본판 GSAJ01 ISO 필요)
#
#   python build.py                         # 전체: 번역 JSON 생성 → 줄 수 검사 → 로고·배너 → ISO
#   python build.py --iso 원본.iso --out 결과.iso
#   python build.py --json-only             # 번역 JSON만 생성 (tools/pending.py 등에 사용)
#   python build.py --skip-logo             # 로고 재생성 생략 (build/override 재사용)
import argparse, glob, os, runpy, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sfa.config import BUILD, OVERRIDE_DIR, TRANSLATION_DIR, OUT_ISO_NAME, find_jp_iso, translation_jsons
from sfa.gcm import Disc
from sfa.isopatch import build_iso

DISC_NAME = 'Star Fox Adventures KOREAN'


def make_jsons():
    sys.path.insert(0, TRANSLATION_DIR)
    scripts = ['prologue.py'] + sorted(os.path.basename(p) for p in glob.glob(os.path.join(TRANSLATION_DIR, 'ch*.py')))
    for s in scripts:
        runpy.run_path(os.path.join(TRANSLATION_DIR, s), run_name='__main__')


def run(script, *args):
    subprocess.run([sys.executable, os.path.join(HERE, script), *args], check=True)


def main():
    ap = argparse.ArgumentParser(description='스타 폭스 어드벤처 한글 패치 ISO 빌드')
    ap.add_argument('--iso', help='일본판 ISO 경로 (기본: 자동 탐색)')
    ap.add_argument('--out', help='출력 ISO 경로 (기본: 원본 옆 "%s")' % OUT_ISO_NAME)
    ap.add_argument('--name', default=DISC_NAME, help='디스크 헤더 게임 이름')
    ap.add_argument('--json-only', action='store_true')
    ap.add_argument('--skip-logo', action='store_true')
    ap.add_argument('--atlas', action='store_true', help='build/atlas/에 파일별 글리프 아틀라스 PNG 저장')
    a = ap.parse_args()

    os.makedirs(BUILD, exist_ok=True)
    print('== 번역 JSON 생성'); make_jsons()
    if a.json_only:
        return
    iso = a.iso or find_jp_iso()
    out = a.out or os.path.join(os.path.dirname(iso), OUT_ISO_NAME)
    print('== 줄 수 검사'); run('tools/check_counts.py')
    if not a.skip_logo:
        print('== 로고·배너'); run('assets/make_logo.py', iso); run('assets/patch_assets.py', iso)
    print('== ISO 빌드')
    build_iso(iso, out, translation_jsons(), OVERRIDE_DIR, a.name,
              atlas_dir=os.path.join(BUILD, 'atlas') if a.atlas else None)
    print('== 검사'); run('tools/verify_iso.py', out)


if __name__ == '__main__':
    main()
