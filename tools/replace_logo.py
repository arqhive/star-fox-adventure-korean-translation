"""기존 한글 ISO의 로고만 교체. 번역·폰트·DOL·배너는 그대로 복사한다."""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from assets.patch_assets import patch_logo
from sfa.config import GAME_ID
from sfa.gcm import Disc
from sfa.isopatch import write_iso


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--logo', type=Path, help='512x191 PNG; 기본값 build/logo_kor.png')
    args = parser.parse_args()
    if args.output.exists() or args.source.resolve() == args.output.resolve():
        parser.error('기존 ISO를 덮어쓰지 않습니다. 새 출력 경로를 지정하세요.')
    disc = Disc(str(args.source))
    if disc.gid != GAME_ID:
        parser.error(f'{GAME_ID} 디스크가 아닙니다: {disc.gid}')
    newfiles = patch_logo(disc, args.logo)
    write_iso(str(args.source), str(args.output), newfiles, disc.name)


if __name__ == '__main__':
    main()
