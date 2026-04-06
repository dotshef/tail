"""
prompts.json의 장면 정보를 기반으로 컷별 러프 스케치를 생성하는 PoC 스크립트.

Pillow로 기본 도형(원, 타원, 선, 사각형)을 배치하여
캐릭터 위치·소품·구도를 잡는 러프 스케치를 만든다.

사용법:
    python scripts/gen_sketch.py --story "여우와 두루미" --cut 2
"""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 캔버스 크기 (4:3)
W, H = 1024, 768
BG_COLOR = (255, 255, 255)
LINE_COLOR = (60, 60, 60)
LIGHT_GRAY = (200, 200, 200)
LINE_W = 3


def draw_fox(draw: ImageDraw.Draw, cx: int, cy: int, scale: float = 1.0, flip: bool = False):
    """여우 실루엣 (간단한 도형 조합)"""
    s = scale
    d = -1 if flip else 1

    # 몸통 (타원)
    draw.ellipse([cx - 30*s, cy - 20*s, cx + 30*s, cy + 40*s], outline=LINE_COLOR, width=LINE_W)
    # 머리 (원)
    draw.ellipse([cx - 20*s, cy - 55*s, cx + 20*s, cy - 15*s], outline=LINE_COLOR, width=LINE_W)
    # 귀 (삼각형 2개)
    draw.polygon([(cx - 15*s, cy - 50*s), (cx - 20*s, cy - 75*s), (cx - 5*s, cy - 50*s)], outline=LINE_COLOR)
    draw.polygon([(cx + 5*s, cy - 50*s), (cx + 20*s, cy - 75*s), (cx + 15*s, cy - 50*s)], outline=LINE_COLOR)
    # 눈 (점)
    eye_offset = 8 * s
    draw.ellipse([cx - eye_offset - 3, cy - 40*s, cx - eye_offset + 3, cy - 34*s], fill=LINE_COLOR)
    draw.ellipse([cx + eye_offset - 3, cy - 40*s, cx + eye_offset + 3, cy - 34*s], fill=LINE_COLOR)
    # 주둥이 (작은 삼각형)
    draw.polygon([(cx, cy - 28*s), (cx - 8*s, cy - 18*s), (cx + 8*s, cy - 18*s)], outline=LINE_COLOR)
    # 꼬리 (곡선 대용 — 타원)
    tail_x = cx + 35*s * d
    draw.ellipse([tail_x - 15*s, cy + 10*s, tail_x + 15*s, cy + 45*s], outline=LINE_COLOR, width=LINE_W)
    # 다리 (선 2개)
    draw.line([(cx - 15*s, cy + 38*s), (cx - 15*s, cy + 70*s)], fill=LINE_COLOR, width=LINE_W)
    draw.line([(cx + 15*s, cy + 38*s), (cx + 15*s, cy + 70*s)], fill=LINE_COLOR, width=LINE_W)
    # 라벨
    draw.text((cx - 12, cy + 75*s), "여우", fill=LINE_COLOR)


def draw_crane(draw: ImageDraw.Draw, cx: int, cy: int, scale: float = 1.0, flip: bool = False):
    """두루미 실루엣"""
    s = scale
    d = -1 if flip else 1

    # 몸통 (타원, 세로 긴)
    draw.ellipse([cx - 20*s, cy - 10*s, cx + 20*s, cy + 40*s], outline=LINE_COLOR, width=LINE_W)
    # 목 (긴 선)
    draw.line([(cx, cy - 10*s), (cx + 5*s*d, cy - 60*s)], fill=LINE_COLOR, width=LINE_W)
    # 머리 (작은 원)
    head_x = cx + 5*s*d
    head_y = cy - 70*s
    draw.ellipse([head_x - 10*s, head_y, head_x + 10*s, head_y + 20*s], outline=LINE_COLOR, width=LINE_W)
    # 부리 (긴 삼각형)
    beak_dir = d
    draw.polygon([
        (head_x + 10*s*beak_dir, head_y + 8*s),
        (head_x + 35*s*beak_dir, head_y + 10*s),
        (head_x + 10*s*beak_dir, head_y + 14*s),
    ], outline=LINE_COLOR, fill=LINE_COLOR)
    # 눈 (점)
    draw.ellipse([head_x - 3, head_y + 6*s, head_x + 3, head_y + 12*s], fill=LINE_COLOR)
    # 다리 (긴 선 2개)
    draw.line([(cx - 8*s, cy + 38*s), (cx - 8*s, cy + 80*s)], fill=LINE_COLOR, width=LINE_W)
    draw.line([(cx + 8*s, cy + 38*s), (cx + 8*s, cy + 80*s)], fill=LINE_COLOR, width=LINE_W)
    # 라벨
    draw.text((cx - 18, cy + 85*s), "두루미", fill=LINE_COLOR)


def draw_table(draw: ImageDraw.Draw, cx: int, cy: int, w: int, h: int):
    """테이블"""
    draw.rectangle([cx - w//2, cy, cx + w//2, cy + h], outline=LINE_COLOR, width=LINE_W)
    # 다리
    draw.line([(cx - w//2 + 10, cy + h), (cx - w//2 + 10, cy + h + 50)], fill=LINE_COLOR, width=LINE_W)
    draw.line([(cx + w//2 - 10, cy + h), (cx + w//2 - 10, cy + h + 50)], fill=LINE_COLOR, width=LINE_W)


def draw_shallow_plate(draw: ImageDraw.Draw, cx: int, cy: int):
    """넓적하고 얕은 접시"""
    draw.ellipse([cx - 40, cy - 8, cx + 40, cy + 8], outline=LINE_COLOR, width=LINE_W)
    # 김 표시 (물결선)
    for i in range(3):
        x = cx - 15 + i * 15
        draw.arc([x, cy - 25, x + 10, cy - 10], start=0, end=180, fill=LIGHT_GRAY, width=2)


def draw_tall_jar(draw: ImageDraw.Draw, cx: int, cy: int):
    """목이 길고 좁은 항아리"""
    # 몸통
    draw.ellipse([cx - 25, cy - 10, cx + 25, cy + 40], outline=LINE_COLOR, width=LINE_W)
    # 목
    draw.rectangle([cx - 8, cy - 40, cx + 8, cy - 5], outline=LINE_COLOR, width=LINE_W)
    # 김
    for i in range(2):
        x = cx - 5 + i * 10
        draw.arc([x, cy - 60, x + 10, cy - 40], start=0, end=180, fill=LIGHT_GRAY, width=2)


def draw_fireplace(draw: ImageDraw.Draw, cx: int, cy: int):
    """벽난로"""
    # 프레임
    draw.rectangle([cx - 50, cy - 60, cx + 50, cy + 10], outline=LINE_COLOR, width=LINE_W)
    # 아치
    draw.arc([cx - 35, cy - 50, cx + 35, cy + 10], start=0, end=180, fill=LINE_COLOR, width=LINE_W)
    # 불꽃 (삼각형)
    draw.polygon([(cx - 15, cy + 5), (cx, cy - 30), (cx + 15, cy + 5)], outline=(200, 100, 50), width=2)
    draw.text((cx - 18, cy + 15), "벽난로", fill=LINE_COLOR)


def draw_trees(draw: ImageDraw.Draw, positions: list[tuple[int, int]]):
    """나무들"""
    for x, y in positions:
        # 줄기
        draw.rectangle([x - 5, y, x + 5, y + 40], outline=LINE_COLOR, width=LINE_W)
        # 잎 (삼각형)
        draw.polygon([(x - 25, y + 5), (x, y - 35), (x + 25, y + 5)], outline=LINE_COLOR, width=LINE_W)


def draw_house(draw: ImageDraw.Draw, cx: int, cy: int, label: str = "집"):
    """작은 집"""
    # 벽
    draw.rectangle([cx - 35, cy - 20, cx + 35, cy + 30], outline=LINE_COLOR, width=LINE_W)
    # 지붕
    draw.polygon([(cx - 45, cy - 20), (cx, cy - 55), (cx + 45, cy - 20)], outline=LINE_COLOR, width=LINE_W)
    # 문
    draw.rectangle([cx - 10, cy + 5, cx + 10, cy + 30], outline=LINE_COLOR, width=LINE_W)
    draw.text((cx - 12, cy + 35), label, fill=LINE_COLOR)


def draw_window(draw: ImageDraw.Draw, cx: int, cy: int):
    """창문"""
    draw.rectangle([cx - 25, cy - 25, cx + 25, cy + 25], outline=LINE_COLOR, width=LINE_W)
    draw.line([(cx, cy - 25), (cx, cy + 25)], fill=LINE_COLOR, width=2)
    draw.line([(cx - 25, cy), (cx + 25, cy)], fill=LINE_COLOR, width=2)


# ── 컷별 스케치 생성 함수 ──

def sketch_cut_1() -> Image.Image:
    """컷 1: 숲속 오솔길, 여우가 두루미 집 앞에서 초대하는 장면"""
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # 배경: 나무
    draw_trees(draw, [(100, 200), (200, 180), (800, 190), (900, 210)])

    # 두루미 집 (오른쪽)
    draw_house(draw, 750, 350, "두루미 집")

    # 오솔길 (아래쪽)
    draw.line([(0, 600), (W, 580)], fill=LIGHT_GRAY, width=20)

    # 여우 (왼쪽, 초대 포즈)
    draw_fox(draw, 300, 420, scale=1.5)

    # 두루미 (오른쪽, 인사)
    draw_crane(draw, 600, 400, scale=1.5, flip=True)

    # 노을빛 표시
    draw.text((W - 120, 30), "저녁 노을빛 ↓", fill=(200, 150, 100))

    return img


def sketch_cut_2() -> Image.Image:
    """컷 2: 여우 집 실내, 넓적한 접시에 수프 대접"""
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # 벽난로 (상단 중앙)
    draw_fireplace(draw, W // 2, 120)

    # 테이블 (중앙)
    draw_table(draw, W // 2, 380, 350, 30)

    # 접시 2개
    draw_shallow_plate(draw, W // 2 - 80, 375)
    draw_shallow_plate(draw, W // 2 + 80, 375)

    # 여우 (왼쪽, 혀 내밀기)
    draw_fox(draw, 280, 300, scale=1.5)
    draw.text((230, 250), "혀로 핥기 ↘", fill=(200, 100, 50))

    # 두루미 (오른쪽, 부리 내려다보기)
    draw_crane(draw, 720, 280, scale=1.5, flip=True)
    draw.text((660, 220), "부리 ↓ 접시", fill=(100, 100, 200))

    return img


def sketch_cut_3() -> Image.Image:
    """컷 3: 같은 식탁, 두루미 당황 + 여우 입꼬리"""
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw_fireplace(draw, W // 2, 120)
    draw_table(draw, W // 2, 380, 350, 30)
    draw_shallow_plate(draw, W // 2 - 80, 375)
    draw_shallow_plate(draw, W // 2 + 80, 375)

    # 여우 (입꼬리 올라감)
    draw_fox(draw, 280, 300, scale=1.5)
    draw.text((220, 250), "입꼬리 실룩 ↗", fill=(200, 100, 50))

    # 두루미 (당황)
    draw_crane(draw, 720, 280, scale=1.5, flip=True)
    draw.text((650, 220), "당황 😰", fill=(100, 100, 200))
    draw.text((640, 430), "접시 거의 안 줄음", fill=LIGHT_GRAY)

    return img


def sketch_cut_4() -> Image.Image:
    """컷 4: 숲속 오솔길 낮, 두루미가 여우를 초대"""
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw_trees(draw, [(80, 200), (180, 170), (820, 180), (920, 200)])
    draw.line([(0, 600), (W, 580)], fill=LIGHT_GRAY, width=20)

    # 두루미 (왼쪽, 초대 포즈)
    draw_crane(draw, 350, 400, scale=1.5)
    draw.text((300, 340), "초대 몸짓 →", fill=(100, 100, 200))

    # 여우 (오른쪽, 기대하는 표정)
    draw_fox(draw, 650, 420, scale=1.5, flip=True)
    draw.text((600, 360), "꼬리 살랑 ~", fill=(200, 100, 50))

    draw.text((W // 2 - 30, 30), "밝은 낮 ☀", fill=(200, 180, 50))

    return img


def sketch_cut_5() -> Image.Image:
    """컷 5: 두루미 집 실내, 항아리에 담긴 음식"""
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw_window(draw, W - 100, 150)
    draw_table(draw, W // 2, 380, 350, 30)

    # 항아리 2개
    draw_tall_jar(draw, W // 2 - 80, 340)
    draw_tall_jar(draw, W // 2 + 80, 340)

    # 두루미 (왼쪽, 부리를 항아리에)
    draw_crane(draw, 280, 280, scale=1.5)
    draw.text((230, 220), "부리 → 항아리 속", fill=(100, 100, 200))

    # 여우 (오른쪽, 당황)
    draw_fox(draw, 720, 300, scale=1.5, flip=True)
    draw.text((650, 250), "코 안 들어감!", fill=(200, 50, 50))

    return img


def sketch_cut_6() -> Image.Image:
    """컷 6: 두루미 웃고, 여우 반성"""
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw_window(draw, W - 100, 150)
    draw.text((W - 140, 200), "어둑한 숲길", fill=LIGHT_GRAY)

    draw_table(draw, W // 2, 380, 350, 30)
    draw_tall_jar(draw, W // 2, 340)

    # 두루미 (왼쪽, 미소)
    draw_crane(draw, 300, 280, scale=1.5)
    draw.text((250, 220), "걱정하는 척 미소", fill=(100, 100, 200))

    # 여우 (오른쪽, 고개 숙임)
    draw_fox(draw, 700, 320, scale=1.5, flip=True)
    draw.text((640, 260), "고개 숙임, 반성", fill=(200, 50, 50))
    draw.text((650, 450), "빈 배 움켜쥠", fill=(200, 100, 50))

    return img


SKETCH_FUNCS = {
    1: sketch_cut_1,
    2: sketch_cut_2,
    3: sketch_cut_3,
    4: sketch_cut_4,
    5: sketch_cut_5,
    6: sketch_cut_6,
}


def main():
    import argparse

    p = argparse.ArgumentParser(description="Generate rough sketch for a story cut.")
    p.add_argument("--story", required=True, help="스토리명")
    p.add_argument("--cut", required=True, type=int, help="컷 번호")
    args = p.parse_args()

    if args.cut not in SKETCH_FUNCS:
        print(f"ERROR: 컷 {args.cut}에 대한 스케치 함수가 없습니다.")
        return 1

    sketch_dir = PROJECT_ROOT / "temp-image" / args.story / "sketches"
    sketch_dir.mkdir(parents=True, exist_ok=True)

    img = SKETCH_FUNCS[args.cut]()
    out_path = sketch_dir / f"컷_{args.cut:02d}.png"
    img.save(out_path)
    print(f"→ 스케치 저장: {out_path}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
