# 스타 폭스 어드벤처 한글화 (GameCube)

게임큐브 **스타 폭스 어드벤처 일본판(GSAJ01, Rev 1)** ISO에 한국어 번역을 적용하는 빌드 도구입니다.

- 대사·메뉴·컷신 자막·힌트·커뮤니케이터 등 게임 내 텍스트 전체 (일본어 원문 기준 번역)
- 파일마다 필요한 한글 글리프를 그려 넣는 방식이라 실행 파일(DOL) 수정 없음
- 타이틀 로고 한글화 (「스타폭스 / 어드벤처」)
- 용어는 스타폭스 64 3D 한국 정발판 표기를 우선, 나머지는 일본어 발음 기준 ([docs/용어집.md](docs/용어집.md))

> 이 저장소에는 게임 데이터가 들어 있지 않습니다. 직접 소유한 일본판 디스크에서 만든 ISO가 필요합니다.

## 패치만 적용하기

빌드 없이 쓰려면 [최신 릴리스](https://github.com/arqhive/star-fox-adventure-korean-translation/releases/latest)에서 원하는 폰트의 패치를 받아 일본판 ISO에 적용하세요 (Delta Patcher 또는 `xdelta3 -d -s 원본.iso 패치.xdelta 결과.iso`). 번역 내용은 같고 게임 안 글자 폰트만 다릅니다.

| 파일 (v0.9.1) | 폰트 | 결과 ISO MD5 |
|---|---|---|
| `sfa-korean-v0.9.1-malgun.zip` | 맑은 고딕 Bold | `2576141100f54707748aebfb47bba31d` |
| `sfa-korean-v0.9.1-pretendard.zip` | Pretendard Bold | `47f8d029251f5944946d99c3493e44a8` |

원본: 일본판 Rev 1 (GSAJ01), MD5 `ebff34930b3e8846167047bf71d25fbc`

버전별 변경 내용은 각 [릴리스](https://github.com/arqhive/star-fox-adventure-korean-translation/releases)의 업데이트 기록을 참고하세요.

패치 만들기 (xdelta 3.1.0, 구버전 패처 호환을 위해 djw 2차 압축):

```bash
xdelta3 -e -9 -S djw -A= -s "Star Fox Adventures (Japan) (Rev 1).iso" "Star Fox Adventures (Korean).iso" sfa-korean.xdelta
```

## 준비

- Python 3.10 이상
- `pip install -r requirements.txt`
- 한글 글리프·로고용 폰트
  - 게임 내 글리프: 기본 맑은 고딕 Bold (`C:/Windows/Fonts/malgunbd.ttf`). `--font` 옵션이나 환경변수 `SFA_GLYPH_FONT`로 변경
    - Pretendard판: [Pretendard](https://github.com/orioncactus/pretendard) v1.3.9의 `Pretendard-Bold.otf` (OFL)
  - 로고: Noto Sans KR 가변 폰트 (`C:/Windows/Fonts/NotoSansKR-VF.ttf`)
- 일본판 ISO: `Star Fox Adventures (Japan) (Rev 1).iso`, MD5 `ebff34930b3e8846167047bf71d25fbc`

## 빌드

```bash
python build.py --iso "Star Fox Adventures (Japan) (Rev 1).iso"
```

Pretendard판:

```bash
python build.py --skip-logo --font Pretendard-Bold.otf --out "Star Fox Adventures (Korean, Pretendard).iso" --name "Star Fox Adventures KOR PRETENDARD"
```

`--iso`를 생략하면 환경변수 `SFA_JP_ISO` → 저장소 폴더 → 상위 폴더 순서로 GSAJ01 ISO를 찾습니다.
결과는 원본 옆에 `Star Fox Adventures (Korean).iso`로 만들어집니다 (`--out`으로 변경).

빌드 순서:
1. `translation/*.py` → `build/json/*.json` (번역 원고를 JSON으로 변환)
2. `tools/check_counts.py` — 번역 줄 수가 원문과 맞는지 검사
3. `assets/make_logo.py`, `assets/patch_assets.py` — 한글 로고 생성, 배너 텍스트 교체
4. ISO 복사본에 수정 파일 추가 (원본 데이터 뒤에 이어 쓰고 FST만 수정)
5. `tools/verify_iso.py` — 일본어 문장 잔존·텍스처 크기 검사

## 폴더 구성

| 경로 | 내용 |
|---|---|
| `build.py` | 전체 빌드 |
| `sfa/` | 라이브러리: 디스크 FST(`gcm`), gametext 포맷·글리프(`gametext`), GX 텍스처(`gxtex`), ISO 패치(`isopatch`) |
| `translation/` | 번역 원고. `menu.json`(메뉴·시스템), `prologue.py`, `ch1.py`~`ch6.py`, 공용 `common.py` |
| `assets/` | 타이틀 로고 생성·배너 교체 |
| `tools/` | 원문 추출, 미번역 목록, 줄 수 검사, 결과 ISO 검사 |
| `docs/` | 용어집·말투표, 파일 포맷 메모 |

## 번역 수정하기

번역 원고는 `translation/` 아래 파이썬 파일입니다. 구역(gametext 폴더명)이나 컷신(`Seq` + 번호)별로 텍스트 ID → 줄 목록을 적습니다.

```python
'20107': [_, _, '나는 스케일 장군, 이 별의 지배자다.', ...],
```

- 리스트 길이는 원문 줄 수와 같아야 합니다. `_`(None)은 원문 유지, 마지막 `'...'`은 나머지 줄 원문 유지
- 줄 앞의 타이밍·색 코드는 자동으로 유지되므로 본문만 적습니다
- 버튼 아이콘 약어: `{A}` `{B}` `{C}` `{J}`(스틱) `{L}` `{R}` `{S}` `{X}` `{Y}` `{Z}`, 통역 아이콘 `{N}` `{TT}` `{I:x}`
- 한 번 번역한 텍스트는 다른 구역에 같은 ID·같은 원문이 있으면 자동 적용됩니다

도움 도구:

```bash
python tools/extract_text.py SwapHol Seq20107     # 원문 보기
python build.py --json-only                       # 번역 JSON만 생성
python tools/pending.py                           # 미번역 텍스트 목록
python tools/check_counts.py                      # 줄 수 검사
python tools/verify_iso.py "Star Fox Adventures (Korean).iso"
```

## 알려진 한계

- 배너(opening.bnr) 텍스트는 Shift-JIS만 지원해 한글 불가 → 영문 표기
- 실행 파일에 내장된 디스크 오류 메시지(디스크를 읽을 수 없을 때만 표시)는 일본어 그대로
- Dolphin에서 확인. 실기(게임큐브) 동작은 미검증

## 면책 조항

- 이 프로젝트는 개인이 만든 **비공식 팬 번역**이며, Nintendo, Rare 및 그 계열사와 아무런 관련이 없고 승인이나 지원을 받지 않았습니다.
- 「Star Fox」, 「스타폭스」, 「Star Fox Adventures」 등 게임 이름·캐릭터·로고와 관련 상표 및 저작권은 각 권리자에게 있습니다.
- 이 저장소와 릴리스에는 게임 데이터(ISO, 실행 파일, 원본 텍스트·이미지)가 포함되어 있지 않습니다. 패치는 직접 정품을 소유한 사람이 자신의 디스크로 만든 이미지에 적용하는 용도로만 제공합니다.
- 패치를 적용한 ISO를 배포하거나 판매하지 마세요. 이 프로젝트의 결과물을 상업적으로 이용하지 마세요.
- 이 소프트웨어와 패치는 있는 그대로 제공되며, 사용으로 인해 발생하는 데이터 손상, 세이브 손실, 기기 문제 등 어떤 결과에도 제작자는 책임지지 않습니다. 원본 이미지는 반드시 백업한 뒤 사용하세요.
- 권리자의 요청이 있으면 저장소와 릴리스를 내리겠습니다.
