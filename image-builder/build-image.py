"""prompts.json → tail-image 컷 이미지 빌드 스크립트

Usage:
    python image-builder/build-image.py <story_name> [--cuts 1,3,5] [--cover-only] [--no-cover]

동작:
    1. tail-image/{story}/prompts.json 을 읽고
    2. style_hint + characters 요약 + cut.prompt + ' Avoid: ' + negative_prompt 로 메인 prompt 합성
    3. OpenAI gpt-image-2 API 호출
    4. b64(또는 url) 응답을 디코드해 tail-image/{story}/cover.png 및 cuts/컷N.jpeg 로 저장

환경:
    OPENAI_API_KEY 환경변수 필수

예시:
    # 전체 생성 (cover + 모든 cuts)
    python image-builder/build-image.py "여우와 두루미"

    # 특정 컷만 재생성 (cover 제외)
    python image-builder/build-image.py "여우와 두루미" --cuts 3,5

    # cover만 재생성
    python image-builder/build-image.py "여우와 두루미" --cover-only

    # cover 빼고 모든 컷
    python image-builder/build-image.py "여우와 두루미" --no-cover
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.request
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

BASE = Path("c:/D/tail")
IMAGE_DIR = BASE / "tail-image"

load_dotenv(BASE / ".env")

MODEL = "gpt-image-2"
CUT_SIZE = "1200x896"
COVER_SIZE = "1200x896"


def compose_prompt(
    prompts_data: dict,
    cut: dict | None = None,
    is_cover: bool = False,
) -> str:
    style_hint = prompts_data.get("style_hint", "")
    negative = prompts_data.get("negative_prompt", "")
    characters = prompts_data.get("characters", {})

    char_summary = " ".join(f"{name}: {desc}." for name, desc in characters.items())

    if is_cover:
        cover = prompts_data.get("cover", {})
        scene = cover.get("prompt", "")
    else:
        assert cut is not None
        scene = cut.get("prompt", "")

    parts = [style_hint, char_summary, scene]
    if negative:
        parts.append(f"Avoid: {negative}.")

    return " ".join(p.strip() for p in parts if p and p.strip())


def generate_one(client: OpenAI, prompt: str, size: str, output_path: Path) -> None:
    response = client.images.generate(
        model=MODEL,
        prompt=prompt,
        size=size,
        n=1,
    )
    item = response.data[0]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    b64 = getattr(item, "b64_json", None)
    if b64:
        output_path.write_bytes(base64.b64decode(b64))
        return

    url = getattr(item, "url", None)
    if url:
        with urllib.request.urlopen(url) as r:
            output_path.write_bytes(r.read())
        return

    raise RuntimeError(f"응답에 b64_json도 url도 없습니다: {output_path.name}")


def decide_cover(args: argparse.Namespace) -> bool:
    if args.cover_only:
        return True
    if args.no_cover:
        return False
    if args.cuts:
        return False  # 부분 재생성 시 cover는 명시 요청 없으면 건너뜀
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("story", help="스토리 폴더명 (예: '여우와 두루미')")
    parser.add_argument("--cuts", help="재생성할 컷 번호 콤마 구분 (예: 1,3,5)")
    parser.add_argument("--cover-only", action="store_true", help="cover.png만 생성")
    parser.add_argument("--no-cover", action="store_true", help="cover.png 건너뜀")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPEN_AI_API")
    if not api_key:
        print("ERROR: OPENAI_API_KEY(또는 OPEN_AI_API) 환경변수가 설정되지 않았습니다.", file=sys.stderr)
        return 2
    os.environ["OPENAI_API_KEY"] = api_key

    story_dir = IMAGE_DIR / args.story
    prompts_path = story_dir / "prompts.json"
    if not prompts_path.exists():
        print(f"ERROR: {prompts_path} 가 존재하지 않습니다.", file=sys.stderr)
        return 2

    prompts_data = json.loads(prompts_path.read_text(encoding="utf-8"))
    cuts = prompts_data.get("cuts", [])

    if args.cuts:
        target_nums = {int(n) for n in args.cuts.split(",") if n.strip()}
        cuts_to_render = [c for c in cuts if int(c.get("cut", 0)) in target_nums]
        if len(cuts_to_render) != len(target_nums):
            requested = sorted(target_nums)
            found = sorted(int(c.get("cut", 0)) for c in cuts_to_render)
            missing = sorted(set(requested) - set(found))
            print(f"WARN: prompts.json에 존재하지 않는 컷 번호: {missing}", file=sys.stderr)
    else:
        cuts_to_render = [] if args.cover_only else cuts

    cover_should_render = decide_cover(args)

    client = OpenAI()
    succeeded: list[str] = []
    failed: list[str] = []

    if cover_should_render:
        cover_path = story_dir / "cover.png"
        try:
            print(f"[cover] generating -> {cover_path.name}")
            prompt = compose_prompt(prompts_data, is_cover=True)
            generate_one(client, prompt, COVER_SIZE, cover_path)
            succeeded.append("cover")
            print(f"[cover] OK")
        except Exception as exc:
            failed.append(f"cover: {exc}")
            print(f"[cover] FAIL: {exc}", file=sys.stderr)

    for cut in cuts_to_render:
        n = cut.get("cut")
        cut_path = story_dir / "cuts" / f"컷{n}.jpeg"
        try:
            print(f"[컷 {n}] generating -> {cut_path.name}")
            prompt = compose_prompt(prompts_data, cut=cut)
            generate_one(client, prompt, CUT_SIZE, cut_path)
            succeeded.append(f"컷{n}")
            print(f"[컷 {n}] OK")
        except Exception as exc:
            failed.append(f"컷{n}: {exc}")
            print(f"[컷 {n}] FAIL: {exc}", file=sys.stderr)

    print()
    print(f"SUCCESS: {', '.join(succeeded) if succeeded else '(none)'}")
    if failed:
        print(f"FAILED: {'; '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
