"""
Gemini 2.5 Flash Image(Nano Banana)를 사용해 동화 컷 이미지를 생성하는 스크립트.

사용법:
    python scripts/gen_image.py --story "여우와 두루미" --cut 1 --scene "여우와 두루미가 인사하는 장면"

동작:
    1. temp-image/{story}/ref-image/*.png|jpg|jpeg|webp 를 모두 레퍼런스로 로드
    2. Gemini API에 레퍼런스 + 장면 프롬프트 전송
    3. 응답 이미지를 temp-image/{story}/cuts/컷_{NN}.png 로 저장

환경변수:
    GEMINI_API_KEY — Google AI Studio 발급 키

종료 코드:
    0 성공
    1 레퍼런스 없음
    2 API 오류
    3 응답에 이미지 없음
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# 프로젝트 루트(이 파일의 부모의 부모)를 기준으로 경로 해석
PROJECT_ROOT = Path(__file__).resolve().parent.parent

SUPPORTED_REF_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
MODEL_NAME = "gemini-2.5-flash-image"

PROMPT_TEMPLATE = """레퍼런스 이미지의 캐릭터와 아트 스타일을 정확히 유지하여 다음 장면을 그려줘.

장면: {scene}

요구사항:
- 가로 16:9 비율
- 캐릭터는 레퍼런스와 동일한 외형 유지
- 동화책 일러스트 스타일
- 따뜻하고 부드러운 색감
- 텍스트/자막 없음
"""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate story cut image via Gemini.")
    p.add_argument("--story", required=True, help="스토리명 (예: '여우와 두루미')")
    p.add_argument("--cut", required=True, type=int, help="컷 번호 (정수)")
    p.add_argument("--scene", required=True, help="장면 설명 (한 줄)")
    p.add_argument(
        "--temperature",
        type=float,
        default=0.4,
        help="생성 temperature (기본 0.4)",
    )
    return p.parse_args()


def load_reference_images(ref_dir: Path) -> list[Path]:
    if not ref_dir.exists():
        return []
    files = [
        f
        for f in sorted(ref_dir.iterdir())
        if f.is_file() and f.suffix.lower() in SUPPORTED_REF_EXTS
    ]
    return files


def main() -> int:
    args = parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY 환경변수가 설정되지 않았습니다.", file=sys.stderr)
        return 2

    story_dir = PROJECT_ROOT / "temp-image" / args.story
    ref_dir = story_dir / "ref-image"
    cuts_dir = story_dir / "cuts"

    refs = load_reference_images(ref_dir)
    if not refs:
        print(
            f"ERROR: 레퍼런스 이미지가 없습니다: {ref_dir}\n"
            f"ref-image 폴더에 캐릭터/스타일 레퍼런스를 먼저 넣어주세요.",
            file=sys.stderr,
        )
        return 1

    cuts_dir.mkdir(parents=True, exist_ok=True)

    # 지연 임포트: genai SDK 미설치 환경에서도 인자 파싱은 동작하도록
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print(
            "ERROR: google-genai 패키지가 설치되지 않았습니다. "
            "`pip install google-genai` 를 실행해주세요.",
            file=sys.stderr,
        )
        return 2

    client = genai.Client(api_key=api_key)

    # 레퍼런스 이미지를 Part로 변환
    ref_parts = []
    for ref_path in refs:
        mime = f"image/{ref_path.suffix.lstrip('.').lower()}"
        if mime == "image/jpg":
            mime = "image/jpeg"
        ref_parts.append(
            types.Part.from_bytes(
                data=ref_path.read_bytes(),
                mime_type=mime,
            )
        )

    prompt = PROMPT_TEMPLATE.format(scene=args.scene)

    print(f"[{args.story}] 컷 {args.cut}: {args.scene}")
    print(f"  레퍼런스 {len(refs)}장 사용")

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[*ref_parts, prompt],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                temperature=args.temperature,
            ),
        )
    except Exception as e:
        print(f"ERROR: Gemini API 호출 실패: {e}", file=sys.stderr)
        return 2

    # 응답에서 이미지 바이트 추출
    image_bytes: bytes | None = None
    for candidate in response.candidates or []:
        for part in candidate.content.parts or []:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                image_bytes = part.inline_data.data
                break
        if image_bytes:
            break

    if not image_bytes:
        print("ERROR: 응답에 이미지 데이터가 없습니다.", file=sys.stderr)
        return 3

    out_path = cuts_dir / f"컷_{args.cut:02d}.png"
    out_path.write_bytes(image_bytes)
    print(f"  → 저장: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
