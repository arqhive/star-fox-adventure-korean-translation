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

# 1) 배경 복원: 파란 배경이 아닌 픽셀(로고)을 마스크 → 인페인트
bg_like = (R < 45) & (G < 75) & (B > 90) & (B < 200)
mask = (~bg_like).astype(np.uint8) * 255
mask = cv2.dilate(mask, np.ones((7, 7), np.uint8))
bgr = cv2.cvtColor(orig.astype(np.uint8), cv2.COLOR_RGB2BGR)
bg = cv2.inpaint(bgr, mask, 9, cv2.INPAINT_TELEA)
bg = cv2.GaussianBlur(bg, (0, 0), 2)
# 인페인트 영역만 부드러운 배경으로 교체
soft = np.where(mask[..., None] > 0, bg, bgr)
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

def stylize(glyph):
    """노란→주황 그라데이션 채움 + 남색 테두리 + 밝은 파랑 외곽 광채"""
    g = np.array(glyph)
    def grow(a, r):
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)); return cv2.dilate(a, k)
    glow = cv2.GaussianBlur(grow(g, 7), (0, 0), 0.6)   # 흐린 광채 대신 선명한 외곽선
    light = grow(g, 5); dark = grow(g, 3)
    h, w = g.shape
    out = np.zeros((h, w, 4), np.float32)
    def over(color, alpha):
        a = (alpha.astype(np.float32) / 255.0)[..., None]
        c = np.broadcast_to(np.array(color, np.float32), out[..., :3].shape) if np.ndim(color) == 1 else color
        out[..., :3] = c * a + out[..., :3] * (1 - a); out[..., 3:] = np.maximum(out[..., 3:], a * 255)
    over(np.array([10, 25, 95]), glow)   # 가장 바깥 남색 선 (배경과 경계 선명하게)
    over(np.array([120, 210, 255]), light)
    over(np.array([8, 18, 80]), dark)
    ys = np.linspace(0, 1, h)[:, None, None]
    top = np.array([255, 250, 120], np.float32); mid = np.array([255, 205, 40], np.float32); bot = np.array([240, 120, 10], np.float32)
    grad = np.where(ys < 0.5, top + (mid - top) * (ys / 0.5), mid + (bot - mid) * ((ys - 0.5) / 0.5))
    grad = np.broadcast_to(grad, (h, w, 3))
    over(grad, g)
    # 윗부분 하이라이트
    hl = g.copy(); hl[int(h * 0.55):] = 0; hl = (cv2.erode(hl, np.ones((5, 5), np.uint8)) * 0.35).astype(np.uint8)
    over(np.array([255, 255, 230]), hl)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA')

line1 = italic(stretch(text_layer('스타폭스', 58, 0), 1.3))
line2 = italic(stretch(text_layer('어드벤처', 58, 0), 1.3))

canvas = base.copy()
def place(layer, cx, top, maxw):
    if layer.size[0] - 40 > maxw:
        s = maxw / (layer.size[0] - 40); layer = layer.resize((int(layer.size[0] * s), int(layer.size[1] * s)), Image.LANCZOS)
    st = stylize(layer)
    canvas.alpha_composite(st, (int(cx - st.size[0] / 2), int(top - 20)))

place(line1, 236, 58, 370)
place(line2, 270, 112, 330)

# 원본 유지 부분 다시 얹기
orig_img = Image.fromarray(orig.astype(np.uint8)).convert('RGBA')
canvas = Image.composite(orig_img, canvas, keep)
# ™을 둘째 줄 오른쪽 끝 옆으로 옮겨 붙임
tm_box = (406, 147, 428, 159)
tm = orig_img.crop(tm_box); ta = np.array(tm.convert('RGB')).astype(int)
tm_mask = Image.fromarray(((ta.min(-1) > 110) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.5))
canvas.paste(tm, (448, 150), tm_mask)
canvas.convert('RGB').save(os.path.join(BUILD, 'logo_kor.png'))
print('saved logo_kor.png')
