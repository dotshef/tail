"""
Gemini 2.5 Flash Image(Nano Banana)를 사용해 동화 컷 이미지를 생성하는 스크립트.

사용법:
    python scripts/gen_image.py --story "여우와 두루미" --prompts-json "temp-image/여우와 두루미/prompts.json" --cut 1

동작:
    1. prompts.json에서 해당 cut 번호의 prompt와 style_hint를 조회
    2. temp-image/{story}/ref-image/*.png|jpg|jpeg|webp 를 모두 레퍼런스로 로드
    3. Gemini API에 레퍼런스 + (style_hint + prompt) 전송
    4. 응답 이미지를 temp-image/{story}/cuts/컷_{NN}.png 로 저장

환경변수:
    GEMINI_API_KEY — Google AI Studio 발급 키
    (프로젝트 루트의 .env 파일에서 자동 로드됨)

종료 코드:
    0 성공
    1 레퍼런스 없음 / prompts.json 없음 / 해당 컷 없음
    2 API 오류 / 환경 오류
    3 응답에 이미지 없음
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# 프로젝트 루트(이 파일의 부모의 부모)를 기준으로 경로 해석
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(env_path: Path) -> None:
    """프로젝트 루트의 .env 파일을 읽어 환경변수로 주입한다.
    python-dotenv 의존성 없이 동작하는 최소 구현."""
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # 기존 환경변수가 있으면 덮어쓰지 않음
        os.environ.setdefault(key, value)


load_dotenv(PROJECT_ROOT / ".env")

SUPPORTED_REF_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
MODEL_NAME = "gemini-2.5-flash-image"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate story cut image via Gemini.")
    p.add_argument("--story", required=True, help="스토리명 (예: '여우와 두루미')")
    p.add_argument(
        "--prompts-json",
        required=True,
        help="prompts.json 경로 (prompt-writer가 생성)",
    )
    p.add_argument("--cut", required=True, type=int, help="컷 번호 (정수)")
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
    return [
        f
        for f in sorted(ref_dir.iterdir())
        if f.is_file() and f.suffix.lower() in SUPPORTED_REF_EXTS
    ]


def load_cut_prompt(prompts_json: Path, cut_num: int) -> tuple[str, str, str]:
    """prompts.json에서 해당 cut의 (prompt, style_hint, aspect_ratio)를 조회한다."""
    data = json.loads(prompts_json.read_text(encoding="utf-8"))
    style_hint = data.get("style_hint", "")
    aspect_ratio = data.get("aspect_ratio", "4:3")
    for cut_entry in data.get("cuts", []):
        if cut_entry.get("cut") == cut_num:
            return cut_entry["prompt"], style_hint, aspect_ratio
    raise KeyError(f"prompts.json에 컷 {cut_num}이(가) 없습니다.")


def build_final_prompt(cut_prompt: str, style_hint: str, aspect_ratio: str) -> str:
    """컷 프롬프트에 공통 스타일 힌트와 비율을 합쳐 최종 프롬프트를 만든다."""
    parts = [
        "레퍼런스 이미지의 캐릭터와 아트 스타일을 정확히 유지하여 다음 장면을 그려줘.",
        "",
        f"장면: {cut_prompt}",
    ]
    if style_hint:
        parts += ["", f"스타일: {style_hint}"]
    parts += ["", f"비율: 가로:세로 = {aspect_ratio}"]
    return "\n".join(parts)


def main() -> int:
    args = parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY 환경변수가 설정되지 않았습니다.", file=sys.stderr)
        return 2

    story_dir = PROJECT_ROOT / "temp-image" / args.story
    ref_dir = story_dir / "ref-image"
    cuts_dir = story_dir / "cuts"

    # prompts.json 로드
    prompts_path = Path(args.prompts_json)
    if not prompts_path.is_absolute():
        prompts_path = PROJECT_ROOT / prompts_path
    if not prompts_path.exists():
        print(f"ERROR: prompts.json을 찾을 수 없습니다: {prompts_path}", file=sys.stderr)
        return 1

    try:
        cut_prompt, style_hint, aspect_ratio = load_cut_prompt(prompts_path, args.cut)
    except KeyError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: prompts.json 읽기 실패: {e}", file=sys.stderr)
        return 1

    # 레퍼런스 로드
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

    final_prompt = build_final_prompt(cut_prompt, style_hint, aspect_ratio)

    print(f"[{args.story}] 컷 {args.cut}")
    print(f"  레퍼런스 {len(refs)}장 사용")
    print(f"  프롬프트 길이: {len(final_prompt)}자")

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[*ref_parts, final_prompt],
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
