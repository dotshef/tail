---
name: tail-image
description: tail-raw의 동화 마크다운에서 이미지 자산(theme.yaml, prompts.json, cover.png, cuts/컷N.jpeg)을 생성하는 진입점
---

# Tail Image Skill (진입점)

이 스킬은 tail-image-planner → build-image.py → tail-image-qc 순으로 이미지 파이프라인을 오케스트레이션한다.

## 사용법

예시 트리거:
- "여우와 두루미 이미지 만들어줘"
- "/tail-image 여우와 두루미"
- "/tail-image all" (전체 생성)

## 규약 (Convention)

### 입력

- 원본 동화: `tail-raw/{스토리}.md`

### 출력

- `tail-image/{스토리}/theme.yaml`
- `tail-image/{스토리}/prompts.json`
- `tail-image/{스토리}/cover.png`
- `tail-image/{스토리}/cuts/컷N.jpeg`

컷 개수는 raw의 `**[컷 N] ...**` 마커 수와 정확히 일치해야 한다. Korean 파일명(`컷1.jpeg` 등)은 bookform/PDF 파이프라인이 기대하는 규약이므로 유지한다.

## 동작

1. 사용자의 요청에서 대상 스토리명을 파악한다
2. `tail-raw/{스토리}.md`가 존재하는지 확인한다 (없으면 에러 보고)
3. `tail-image/{스토리}/cuts/` 폴더가 없으면 생성한다
4. **tail-image-planner 에이전트를 spawn한다**
   - 입력: 스토리명
   - 출력: `theme.yaml`, `prompts.json`
5. **build-image.py를 Bash로 실행한다**
   ```bash
   python image-builder/build-image.py "{스토리}"
   ```
   - 출력: `cover.png`, `cuts/컷N.jpeg`
6. **tail-image-qc 에이전트를 spawn한다**
   - 입력: 스토리명
   - 출력: stdout 마지막 줄에 `regenerate: 3,5` 또는 `regenerate: none` 형식
7. **재생성 컷이 있으면 build-image.py 재호출**
   ```bash
   python image-builder/build-image.py "{스토리}" --cuts 3,5
   ```
   - 재시도 후 다시 qc 호출. 최대 2회 반복까지만 자동 진행하고, 그 이상은 사용자에게 보고
8. 최종 결과를 사용자에게 보고한다

## 선행 조건

- `tail-raw/{스토리}.md`가 존재해야 한다
- `OPENAI_API_KEY` 환경변수가 설정되어 있어야 한다 (build-image.py가 사용)

다른 파이프라인(story-writer, vocab-analyzer 등)과 독립적으로 실행 가능.

## 병렬 실행

- **스토리별 병렬**: 여러 스토리를 요청한 경우 스토리별로 (planner + build + qc) 한 세트씩 병렬 실행
- 같은 스토리 내에서는 planner → build → qc 순차 (의존성)
