# 스타폭스 어드벤처 (GC) 한글 패치

*Star Fox Adventures* (게임큐브, 일본판 Rev 1 `GSAJ01`) 비공식 한국어 팬 패치입니다.
대사는 일본어판 원문을 기준으로 번역했습니다.

**제작: arqhive** · **최신 버전: [v1.1](https://github.com/arqhive/star-fox-adventure-korean-translation/releases/tag/v1.1)**

- 대사, 메뉴, 컷신 자막, 슬리피 힌트, 커뮤니케이터, 월드맵 등 게임 내 텍스트 전체를 한글화했습니다.
- 파일마다 필요한 한글 글리프를 그려 넣는 방식이라 실행 파일(DOL)은 수정하지 않습니다.
- 타이틀 로고를 「스타폭스 / 어드벤처」로 한글화했습니다.
- 게임 안 글자 폰트는 맑은 고딕 Bold판과 Pretendard Bold판 중에서 고를 수 있습니다. 번역 내용은 같습니다.
- 용어는 스타폭스 64 3D 한국 정발판 표기를 우선하고, 나머지는 일본어 발음을 따랐습니다([`docs/용어집.md`](docs/용어집.md)).

> 이 저장소에는 **게임 데이터(롬·디스크 이미지, 추출한 원문 대사, 그래픽, 스크린샷)가 들어 있지 않습니다.**
> 패치를 만들거나 적용하려면 본인이 소유한 게임에서 직접 덤프한 원본이 필요합니다.

## 사용자용: 패치 적용

### 준비물

- 일본판 Rev 1(`GSAJ01`) ISO. 북미판·유럽판이나 RVZ·NKit·CISO로 변환한 이미지에는 적용할 수 없습니다. 변환한 이미지는 Dolphin에서 ISO로 되돌린 뒤 적용하세요.
- xdelta 패치 도구. Windows에서는 Delta Patcher를, 명령줄에서는 xdelta3를 쓰면 됩니다.

### 적용 방법

1. [배포 페이지](https://github.com/arqhive/star-fox-adventure-korean-translation/releases/tag/v1.1)에서 원하는 폰트의 ZIP 하나를 받습니다.

   | 폰트 | 배포 파일 |
   |---|---|
   | 맑은 고딕 Bold | `sfa-korean-v1.1-malgun.zip` |
   | Pretendard Bold | `sfa-korean-v1.1-pretendard.zip` |

2. ZIP을 풀고 원본 ISO에 `.xdelta` 패치를 적용합니다. 명령줄에서는 다음처럼 적용합니다.

   ```bash
   xdelta3 -d -s "Star Fox Adventures (Japan) (Rev 1).iso" sfa-korean-pretendard.xdelta "Star Fox Adventures (Korean).iso"
   ```

3. 결과 ISO의 확인값을 아래 표와 비교합니다.

자세한 방법은 ZIP에 들어 있는 `README.txt`를 참고하세요.

일본판 기준 패치라 세이브 데이터는 일본판 세이브와 호환됩니다. Dolphin 세이브(`.gci`)를 Nintendont로 옮길 때는 메모리 카드 이미지를 일본어(Shift-JIS) 인코딩으로 만들어야 세이브 설명문이 깨지지 않습니다.

### 파일 확인값

| 항목 | 원본 일본판 Rev 1 | 패치 적용 결과 (v1.1, 맑은 고딕) | 패치 적용 결과 (v1.1, Pretendard) |
|---|---|---|---|
| 크기 | 1,459,978,240 바이트 | 1,459,978,240 바이트 | 1,459,978,240 바이트 |
| CRC32 | `9781203A` | `A0A7125C` | `9EED902D` |
| MD5 | `ebff34930b3e8846167047bf71d25fbc` | `c9b1f3a673e96e8a79e6c17cda5d4aef` | `9365e36151888c3013547d6c9fa3c634` |
| SHA-1 | `979e8f24000cb9a8b332228a6b0fbf8a59aa0cab` | `42e812a029e218d386e64354fe1cc3ca49194bef` | `078e71644e6c02998d890fb76d97cacb1feb39b2` |

원본 파일명 예: `Star Fox Adventures (Japan) (Rev 1).iso`

### 실행 환경

- **확인함**: Dolphin, Wii U vWii + Nintendont.

### 알려진 문제

- 배너(게임 목록·메모리 카드 화면) 설명은 Shift-JIS만 지원해 한글을 넣을 수 없으므로 영문으로 표기했습니다.
- 실행 파일에 들어 있는 디스크 오류 메시지 일부는 일본어로 남아 있습니다. 디스크를 읽을 수 없을 때만 나옵니다.

## 개발자용: 직접 빌드

### 요구 사항

- Python 3.10 이상과 `pip install -r requirements.txt`(numpy, Pillow, opencv-python).
- 일본판 ISO `Star Fox Adventures (Japan) (Rev 1).iso`(위 확인값과 일치하는 파일).
- 게임 안 글리프 폰트. 기본값은 맑은 고딕 Bold(`C:/Windows/Fonts/malgunbd.ttf`)이며 `--font` 옵션이나 환경 변수 `SFA_GLYPH_FONT`로 바꿀 수 있습니다. Pretendard판은 [Pretendard](https://github.com/orioncactus/pretendard) v1.3.9의 `Pretendard-Bold.otf`를 씁니다.
- 로고 폰트 Noto Sans KR 가변 폰트(`C:/Windows/Fonts/NotoSansKR-VF.ttf`).

### 빌드

```bash
python build.py --iso "Star Fox Adventures (Japan) (Rev 1).iso"
```

Pretendard판은 다음처럼 빌드합니다.

```bash
python build.py --skip-logo --font Pretendard-Bold.otf --out "Star Fox Adventures (Korean, Pretendard).iso" --name "Star Fox Adventures KOR PRETENDARD"
```

`--iso`를 생략하면 환경 변수 `SFA_JP_ISO`, 저장소 폴더, 상위 폴더 순서로 GSAJ01 ISO를 찾습니다.
결과는 원본 옆에 `Star Fox Adventures (Korean).iso`로 만들어지며, `--out`으로 바꿀 수 있습니다.

`build.py`는 다음 순서로 진행합니다.

1. `translation/*.py`를 `build/json/*.json`으로 변환합니다.
2. `tools/check_counts.py`로 번역 줄 수가 원문과 맞는지 검사합니다.
3. `assets/make_logo.py`와 `assets/patch_assets.py`로 한글 로고를 만들고 배너 텍스트를 바꿉니다.
4. ISO 복사본에 수정 파일을 추가합니다. 원본 데이터 뒤에 이어 쓰고 FST만 고칩니다.
5. `tools/verify_iso.py`로 일본어 문장 잔존과 텍스처 크기를 검사합니다.

배포용 패치는 xdelta 3.1.0으로 만듭니다. 구버전 패처와 호환되도록 djw 2차 압축을 씁니다.

```bash
xdelta3 -e -9 -S djw -A= -s "Star Fox Adventures (Japan) (Rev 1).iso" "Star Fox Adventures (Korean).iso" sfa-korean.xdelta
```

#### 기존 한글 ISO의 로고만 교체

v1.1 배포본은 v1.0.2의 각 폰트판에 다음 도구로 로고만 바꿔 만들었습니다. 번역, 폰트, DOL, 배너는 다시 만들지 않습니다. 출력에는 아직 없는 파일 경로를 지정하세요.

```bash
python assets/make_logo.py "원본 일본판.iso"
python tools/replace_logo.py "기존 한글판.iso" "로고 수정 한글판.iso"
```

`--logo`로 512×191 PNG를 따로 지정할 수도 있습니다. 배포용 xdelta는 로고 수정 한글판과 **원본 일본판 ISO**를 비교해 만듭니다.

### 번역 수정

번역 원고는 `translation/` 아래의 파이썬 파일입니다. 구역(gametext 폴더명)이나 컷신(`Seq` + 번호)별로 텍스트 ID와 줄 목록을 적습니다.

```python
'20107': [_, _, '나는 스케일 장군, 이 별의 지배자다.', ...],
```

- 리스트 길이는 원문 줄 수와 같아야 합니다. `_`(None)은 원문 유지, 마지막 `'...'`은 나머지 줄 원문 유지입니다.
- 줄 앞의 타이밍·색 코드는 자동으로 유지되므로 본문만 적습니다.
- 버튼 아이콘 약어는 `{A}` `{B}` `{C}` `{J}`(스틱) `{L}` `{R}` `{S}` `{X}` `{Y}` `{Z}`, 통역 아이콘은 `{N}` `{TT}` `{I:x}`입니다.
- 한 번 번역한 텍스트는 다른 구역에 같은 ID와 같은 원문이 있으면 자동으로 적용됩니다.

도움 도구는 다음과 같습니다.

```bash
python tools/extract_text.py SwapHol Seq20107     # 원문 보기
python build.py --json-only                       # 번역 JSON만 생성
python tools/pending.py                           # 미번역 텍스트 목록
python tools/check_counts.py                      # 줄 수 검사
python tools/check_width.py                       # 줄 너비 검사
python tools/verify_iso.py "Star Fox Adventures (Korean).iso"
```

### 폴더 구조

```
build.py       전체 빌드
sfa/           라이브러리: 디스크 FST(gcm), gametext 포맷·글리프(gametext), GX 텍스처(gxtex), ISO 패치(isopatch)
translation/   번역 원고: menu.json(메뉴·시스템), prologue.py, ch1.py에서 ch6.py까지, 공용 common.py
assets/        타이틀 로고 생성, 배너 교체
tools/         원문 추출, 미번역 목록, 줄 수·줄 너비 검사, 결과 ISO 검사, 로고 교체
docs/          용어집·말투표, 파일 포맷 메모, 릴리즈 노트 사본(docs/releases/)
```

### 기술 문서

디스크 구조와 gametext·텍스처 포맷은 [`docs/format.md`](docs/format.md)에 정리했습니다.
용어와 캐릭터별 말투는 [`docs/용어집.md`](docs/용어집.md)에 있습니다.

## 변경 내역

전체 내역은 [`CHANGELOG.md`](CHANGELOG.md)에 있습니다.

## 크레딧·라이선스

- 제작: arqhive.
- Pretendard판 글리프: [Pretendard](https://github.com/orioncactus/pretendard), SIL Open Font License 1.1.
- 맑은 고딕판 글리프: Microsoft 맑은 고딕 Bold로 그렸습니다.
- 타이틀 로고: Noto Sans KR로 그렸습니다.

## 면책

비공식 팬 번역이며 Nintendo, Rare와 관련이 없습니다. 「스타폭스 어드벤처」 관련 상표·저작권은 Nintendo와 Rare에 있습니다.
패치를 적용한 게임 파일의 배포를 금지합니다.
