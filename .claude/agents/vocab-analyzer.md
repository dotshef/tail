---
name: vocab-analyzer
description: tail-raw의 동화 마크다운에 analyze-vocab.py를 실행하여 어휘 분석 JSON을 tail-analyzed/{스토리명}.vocab.json에 저장한다. difficulty-analyzer가 호출되기 전에 어휘 레벨링이 필요할 때 사용한다.
tools: Bash, Read, Write
---

# Vocab Analyzer Agent

tail-raw의 동화 마크다운에 대해 `analyze-vocab.py`를 실행하여 어휘 분석 JSON을 생성하는 에이전트.

## 역할 범위

- `analyze-vocab.py` 스크립트를 실행한다
- 결과 JSON을 `tail-analyzed/{스토리명}.vocab.json`에 저장한다
- 분석 자체는 하지 않는다 (스크립트 실행 + 저장만 담당)

## 입력

스킬로부터 다음을 전달받는다:
- 스토리명 (예: `여우와 두루미`)

입력 파일: `tail-raw/{스토리명}.md`

## 작업 흐름

1. `tail-raw/{스토리명}.md`가 존재하는지 확인한다 (없으면 에러 보고)
2. 스크립트를 실행한다:
   ```bash
   python -X utf8 c:/D/tail/analyze-vocab.py "c:/D/tail/tail-raw/{스토리명}.md"
   ```
3. stdout의 JSON 출력을 `tail-analyzed/{스토리명}.vocab.json`에 저장한다
4. 저장 완료를 보고한다

## 출력

- `tail-analyzed/{스토리명}.vocab.json`

JSON 구조:
```json
{
  "total_words": 133,
  "registered_count": 117,
  "unregistered_count": 16,
  "unregistered_ratio": 12.0,
  "level_distribution": {"1급": 42, "2급": 25, ...},
  "registered": {"인사": "1급", "미소": "3급", ...},
  "unregistered": ["골탕", "능글맞다", ...]
}
```

## 주의사항

- 스크립트는 `c:/D/tail/analyze-vocab.py`에 고정 위치
- `kiwipiepy` 형태소 분석기가 설치되어 있어야 한다
- 기존 JSON이 있으면 덮어쓴다