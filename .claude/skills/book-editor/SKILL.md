---
name: book-editor
description: tail-story, tail-localized, tail-translated를 조합하여 tail-bookform/{lang}에 최종 책 형식을 생성하는 진입점
---

# Book Editor Skill (진입점)

이 스킬은 book-editor 에이전트를 spawn하는 진입점이다.

## 사용법

예시 트리거:
- "여우와 두루미 bookform 만들어줘"
- "/book-editor 여우와 두루미"
- "/book-editor all" (전체 생성)

## 규약 (Convention)

### 입력

- 스토리 본문: `tail-story/{스토리명}.md`
- Expression/frontmatter 소스: `tail-localized/{lang}/{스토리명}.md`
- 번역 소스 (`<sub>` + 페이지별 `<!-- translation -->`): `tail-translated/{lang}/{스토리명}.md`
- 이미지: `tail-image/{스토리명}/cuts/컷{N}.jpeg`

### 출력

- `tail-bookform/{lang}/{스토리명}.md` (localized와 translated 모두 존재하는 언어별로 생성)

## 동작

1. 사용자의 요청에서 대상 스토리명을 파악한다
2. `tail-story/{스토리명}.md`가 존재하는지 확인한다 (없으면 에러 보고)
3. `tail-localized/` 및 `tail-translated/` 하위 폴더를 탐색하여 해당 스토리가 **양쪽 모두에 존재하는 언어**를 확인한다
   - 두 곳 중 한쪽에만 있는 언어는 건너뛰고 경고한다 (bookform 조합에 두 소스가 모두 필요하기 때문)
   - 어떤 언어에서도 양쪽이 다 갖춰지지 않았다면 에러 보고
4. `tail-bookform/{lang}/` 폴더가 없으면 생성한다
5. **양쪽에 존재하는 언어별로 book-editor 에이전트를 병렬 spawn한다**
   - 각 에이전트에 스토리명과 대상 언어를 전달한다
   - 동작:
     - story 본문 + 이미지 참조 교체
     - tail-translated의 `<sub>` 태그를 `#`/`##` 아래에 삽입
     - tail-localized의 `<!-- expressions -->`를 각 페이지 끝에 삽입
     - tail-translated의 페이지별 `<!-- translation -->` 블록을 **장 단위로 병합**하여 각 장 마지막 페이지 expressions 뒤에 삽입
     - tail-localized의 frontmatter `difficulty` 블록만 가져오기
   - 출력: `tail-bookform/{lang}/{스토리명}.md`
6. 모든 에이전트 완료 후 결과를 사용자에게 보고한다

## 선행 조건

book-editor는 localizer와 story-translator **양쪽 모두가 완료된 후에** 실행되어야 한다. 두 파이프라인은 서로 독립이므로 병렬로 돌릴 수 있으나, 결과물을 병합하는 단계에서 둘 다 필요하다.

## 병렬 실행

- **언어별 병렬**: 같은 스토리의 각 언어는 독립적이므로 동시 실행
- **스토리별 병렬**: 여러 스토리를 요청한 경우에도 스토리별로 병렬 실행 가능
