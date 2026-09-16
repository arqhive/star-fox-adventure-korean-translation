# 번역 원고 공용: 아이콘 약어 변환(ic), JSON 저장(save)
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sfa.config import JSON_DIR
import re
def ic(s):
    """번역 원고 약어 → 제어코드.
    {A}{B}{C}{J}{L}{R}{S}{X}{Y}{Z}=버튼 아이콘, {N}=아소카족 통역, {TT}=손테일족 통역, {I:x}=통역 아이콘 x(폰트5)"""
    if s is None or s == '...': return s
    s = s.replace('{TT}', '{F8F7:0005}y{F8F7:0000}').replace('{N}', '{F8F7:0005}n{F8F7:0000}')
    s = re.sub(r'\{I:(.)\}', r'{F8F7:0005}\1{F8F7:0000}', s)
    return re.sub(r'\{([ABCJLRSXYZ])\}', r'{F8F7:0002}\1{F8F7:0000}', s)


def save(out, name):
    os.makedirs(JSON_DIR, exist_ok=True)
    json.dump(out, open(os.path.join(JSON_DIR, name), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
