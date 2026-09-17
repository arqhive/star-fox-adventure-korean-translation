# 한글 타이틀 로고 생성: ISO의 일본어 로고(512x191)에서 가타카나를 지우고 「스타폭스 / 어드벤처」를 같은 스타일로 그림
# 출력: build/logo_kor.png (patch_assets.py가 CMPR로 변환해 넣음)
import os, sys, struct
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sfa.config import BUILD, find_jp_iso
from sfa.gcm import Disc
from sfa.gxtex import zlb_items, tex_info, dec_cmpr, HEADER

LOGO_TAB_INDEX = 455   # gamefront/TEX0.tab: 일본어 로고


def original_logo(iso):
    disc = Disc(iso)
    tab = disc.read('gamefront/TEX0.tab'); binf = disc.read('gamefront/TEX0.bin')
    off = (struct.unpack_from('>I', tab, LOGO_TAB_INDEX * 4)[0] & 0xFFFFFF) * 2
    raw = {o: r for o, c, r in zlb_items(binf)}[off]
    w, h, fmt = tex_info(raw); assert (w, h, fmt) == (512, 191, 14)
    return Image.fromarray(dec_cmpr(raw[HEADER:], w, h), 'RGBA')


iso = sys.argv[1] if len(sys.argv) > 1 else find_jp_iso()
os.makedirs(BUILD, exist_ok=True)
orig = np.array(original_logo(iso).convert('RGB')).astype(np.int32)
H, W = orig.shape[:2]
R, G, B = orig[..., 0], orig[..., 1], orig[..., 2]

# 1) 배경 복원: 로고와 둘레 광채까지 넓게 마스킹 → 먼 바탕색으로만 인페인트 (뿌연 판 방지)
bg_like = (R < 45) & (G < 75) & (B > 90) & (B < 200)
mask = (~bg_like).astype(np.uint8) * 255
mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
bgr = cv2.cvtColor(orig.astype(np.uint8), cv2.COLOR_RGB2BGR)
bg = cv2.inpaint(bgr, mask, 15, cv2.INPAINT_TELEA)
bg = cv2.GaussianBlur(bg, (0, 0), 6)
feather = cv2.GaussianBlur(mask, (0, 0), 4).astype(np.float32)[..., None] / 255.0
soft = (bg * feather + bgr * (1 - feather)).astype(np.uint8)
base = Image.fromarray(cv2.cvtColor(soft, cv2.COLOR_BGR2RGB)).convert('RGBA')

# 2) 원본에서 유지할 부분: 작은 영문 「STARFOX ADVENTURES」, 스우시(오른쪽 위 꼬리), ™
keep = Image.new('L', (W, H), 0); kd = ImageDraw.Draw(keep)
kd.polygon([(158, 28), (364, 28), (356, 54), (148, 54)], fill=255)   # 영문 「STARFOX ADVENTURES」 명판
keep = keep.filter(ImageFilter.GaussianBlur(0.6))

# 3) 한글 제목 렌더
font_path = 'C:/Windows/Fonts/NotoSansKR-VF.ttf'
def font(size):
    f = ImageFont.truetype(font_path, size)
    try: f.set_variation_by_axes([900])
    except Exception: pass
    return f

def text_layer(text, size, spacing):
    f = font(size)
    widths = [f.getbbox(ch)[2] - f.getbbox(ch)[0] for ch in text]
    tw = sum(widths) + spacing * (len(text) - 1)
    img = Image.new('L', (tw + 40, size + 40), 0); d = ImageDraw.Draw(img); x = 20
    for ch, w in zip(text, widths):
        bb = f.getbbox(ch); d.text((x - bb[0], 20 - bb[1] + (size - (bb[3] - bb[1])) // 2), ch, font=f, fill=255); x += w + spacing
    return img

def stretch(img, sx):
    return img.resize((int(img.size[0] * sx), img.size[1]), Image.LANCZOS)

def italic(img, shear=0.22):
    w, h = img.size; nw = w + int(h * shear)
    return img.transform((nw, h), Image.AFFINE, (1, shear, -h * shear, 0, 1, 0), Image.BICUBIC)

def smooth_band(d, a, b):
    """거리 d가 [a, b] 구간이면 1 (경계 1px 부드럽게)"""
    return np.clip(d - a + 0.5, 0, 1) * np.clip(b - d + 0.5, 0, 1)

def stylize(g):
    """원본 일본어 로고와 같은 구조로 채색. g: 캔버스 크기 글자 마스크(0~255)"""
    h, w = g.shape
    inside = (g >= 128).astype(np.uint8)
    d = cv2.distanceTransform(1 - inside, cv2.DIST_L2, 5)          # 글자 바깥쪽 거리
    out = np.zeros((h, w, 4), np.float32)
    def over(color, alpha):
        a = np.clip(alpha, 0, 1).astype(np.float32)[..., None]
        c = np.broadcast_to(np.array(color, np.float32), out[..., :3].shape) if np.ndim(color) == 1 else color
        out[..., :3] = c * a + out[..., :3] * (1 - a); out[..., 3:] = np.maximum(out[..., 3:], a * 255)
    glow = np.clip(1 - (d - 7) / 13, 0, 1) ** 1.6 * 0.9
    over(np.array([35, 150, 245]), glow)                              # 바깥 파란 광채
    over(np.array([150, 240, 250]), smooth_band(d, 6.0, 7.0))        # 청록 테두리
    over(np.array([215, 238, 248]), smooth_band(d, 4.0, 6.0))        # 은백색 베벨
    over(np.array([0, 0, 49]), smooth_band(d, 0.0, 4.0))             # 굵은 남색 선
    ys = np.linspace(0, 1, h)[:, None, None]
    ys = np.clip((ys - 0.25) / 0.6, 0, 1)
    top = np.array([255, 250, 120], np.float32); mid = np.array([255, 205, 40], np.float32); bot = np.array([240, 120, 10], np.float32)
    grad = np.where(ys < 0.5, top + (mid - top) * (ys / 0.5), mid + (bot - mid) * ((ys - 0.5) / 0.5))
    over(np.broadcast_to(grad, (h, w, 3)), g.astype(np.float32) / 255)  # 노랑→주황 채움
    hl = cv2.erode(g, np.ones((5, 5), np.uint8)).astype(np.float32) / 255 * 0.3
    hl[int(h * 0.5):] = 0
    over(np.array([255, 255, 230]), hl)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA')

# 게임은 원본 일본어 로고 모양 바깥을 흐리게 표시 → 한글을 원본 글자 영역(실루엣) 안에 자동 배치
def silhouette():
    solid = ((R > 120) | (B < 110)).astype(np.uint8)                   # 원본 글자 본체+테두리
    solid = cv2.morphologyEx(solid, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    cnts, _ = cv2.findContours(solid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    fill = np.zeros_like(solid); cv2.drawContours(fill, cnts, -1, 1, -1)
    fill = cv2.erode(fill, np.ones((3, 3), np.uint8))                  # 가장자리 여유
    plate = np.zeros_like(fill); cv2.fillPoly(plate, [np.array([(154, 24), (370, 24), (362, 58), (144, 58)])], 1)
    return fill * (1 - plate)

STROKE = 5      # 영역 검사에 쓰는 테두리 두께 (남색 선+베벨)
TOLERANCE = 40  # 영역 밖으로 나가도 되는 픽셀 수 (바깥 광채 끝부분)

def fit_line(text, allowed, y0, y1, x1, sizes, stretches, shears, prefer_cx):
    """allowed 영역 안에 (테두리 포함) 들어가는 배치 중 글자 면적이 가장 큰 것 → (캔버스 크기 마스크, 정보)"""
    band = np.zeros_like(allowed); band[y0:y1, :x1] = 1
    outside = (1 - allowed * band).astype(np.float32)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * STROKE + 1, 2 * STROKE + 1))
    best = None
    for size in sizes:
        base_layer = text_layer(text, size, 0)
        for shear in shears:
            for sx in stretches:
                lay = np.array(italic(stretch(base_layer, sx), shear))
                ys, xs = np.nonzero(lay > 60)
                lay = lay[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
                area = int((lay > 60).sum())
                if best and area <= best[0]: continue
                pad = np.pad(lay, STROKE + 2)
                tmpl = cv2.dilate((pad > 60).astype(np.uint8), k).astype(np.float32)
                th, tw = tmpl.shape
                if th > H or tw > W: continue
                cost = cv2.matchTemplate(outside, tmpl, cv2.TM_CCORR)
                ok = np.argwhere(cost <= TOLERANCE)
                if not len(ok): continue
                cy = (y0 + y1) / 2 - th / 2
                y, x = min(ok, key=lambda q: (q[0] - cy) ** 2 + (q[1] + tw / 2 - prefer_cx) ** 2)
                m = np.zeros((H, W), np.uint8); m[y:y + th, x:x + tw] = pad
                best = (area, m, dict(text=text, size=size, stretch=sx, shear=shear, x=int(x), y=int(y), w=tw, h=th))
    if not best:
        raise SystemExit(f'{text}: 원본 영역 안에 맞는 크기를 찾지 못함')
    return best[1], best[2]

allowed = silhouette()
SIZES = range(66, 34, -2); STRETCHES = [round(1.0 + 0.1 * i, 1) for i in range(13)]; SHEARS = (0.22, 0.32, 0.42)
m1, i1 = fit_line('스타폭스', allowed, 44, 118, 420, SIZES, STRETCHES, SHEARS, 220)
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
allowed2 = allowed * (1 - cv2.dilate((m1 > 60).astype(np.uint8), k))  # 윗줄 글자 본체와 겹치지 않게
m2, i2 = fit_line('어드벤처', allowed2, 96, 166, 512, SIZES, STRETCHES, SHEARS, 300)
print('배치:', i1, i2)
glyph_mask = Image.fromarray(np.maximum(m1, m2))

canvas = base.copy()
canvas.alpha_composite(stylize(np.array(glyph_mask)))

# 원본 유지 부분 다시 얹기
orig_img = Image.fromarray(orig.astype(np.uint8)).convert('RGBA')
canvas = Image.composite(orig_img, canvas, keep)
# ™을 둘째 줄 오른쪽 끝 옆으로 옮겨 붙임
tm_box = (406, 147, 428, 159)
tm = orig_img.crop(tm_box); ta = np.array(tm.convert('RGB')).astype(int)
tm_mask = Image.fromarray(((ta.min(-1) > 110) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.5))
canvas.paste(tm, (tm_box[0], tm_box[1]), tm_mask)   # 원본 위치
canvas.convert('RGB').save(os.path.join(BUILD, 'logo_kor.png'))
print('saved logo_kor.png')
