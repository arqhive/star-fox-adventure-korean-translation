# 경로 설정: 원본 ISO 위치, 빌드 산출물 폴더
import os, glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(REPO, 'build')
JSON_DIR = os.path.join(BUILD, 'json')
OVERRIDE_DIR = os.path.join(BUILD, 'override')
TRANSLATION_DIR = os.path.join(REPO, 'translation')
JP_ISO_NAME = 'Star Fox Adventures (Japan) (Rev 1).iso'
OUT_ISO_NAME = 'Star Fox Adventures (Korean).iso'
GAME_ID = 'GSAJ01'


def is_jp_iso(path):
    try:
        with open(path, 'rb') as f:
            return f.read(6) == GAME_ID.encode()
    except OSError:
        return False


def find_jp_iso():
    """환경변수 SFA_JP_ISO → 저장소 폴더 → 상위 폴더 순서로 일본판 ISO 탐색"""
    env = os.environ.get('SFA_JP_ISO')
    if env:
        return env
    for d in (REPO, os.path.dirname(REPO)):
        named = os.path.join(d, JP_ISO_NAME)
        if os.path.exists(named):
            return named
        for p in sorted(glob.glob(os.path.join(glob.escape(d), '*.iso'))):
            if is_jp_iso(p) and 'Korean' not in os.path.basename(p):
                return p
    raise SystemExit('일본판 ISO(GSAJ01)를 찾지 못했습니다. --iso 옵션이나 SFA_JP_ISO 환경변수로 지정하세요.')


def translation_jsons():
    """빌드에 쓰는 번역 JSON 목록 (순서 = 우선순위)"""
    fixed = [os.path.join(TRANSLATION_DIR, 'menu.json'), os.path.join(JSON_DIR, 'kor_prologue.json')]
    chapters = sorted(glob.glob(os.path.join(glob.escape(JSON_DIR), 'kor_ch*.json')))
    return [p for p in fixed + chapters if os.path.exists(p)]
