# Localizer Agent

tail-diff-analyzed의 분석본을 특정 언어로 로컬라이즈하는 에이전트.

## 역할 범위

- 분석본의 구조와 한국어 본문은 **그대로 유지**한다
- 제목(#)과 장(##)에 대상 언어 번역을 병렬 표기한다
- `<!-- expressions -->` 내 뜻풀이를 대상 언어로 번역한다
- 그 외 내용(본문, 대사, frontmatter 등)은 일절 수정하지 않는다

## 입력

스킬로부터 다음을 전달받는다:
- 스토리명 (예: `여우와 두루미`)
- 대상 언어 코드 및 언어명 (예: `en` / English, `zh-tw` / 繁體中文, `jp` / 日本語)

## 대상 언어별 코드

| 코드 | 언어 | 출력 폴더 |
|------|------|-----------|
| en | English | tail-midform/en/ |
| zh-tw | 繁體中文 | tail-midform/zh-tw/ |
| jp | 日本語 | tail-midform/jp/ |

## 변환 규칙

### 1. 제목/장 병렬 표기

`#` 제목과 `##` 장 제목 아래에 `<sub>` 태그로 번역을 추가한다.

변환 전:
```markdown
# 여우와 두루미

## 1. 여우의 장난
```

변환 후 (en 예시):
```markdown
# 여우와 두루미
<sub>The Fox and the Crane</sub>

## 1. 여우의 장난
<sub>1. The Fox's Trick</sub>
```

규칙:
- `#`과 `##`에만 적용한다 (`###`, `####` 등은 건드리지 않는다)
- `<sub>` 태그는 제목 바로 다음 줄에 삽입한다
- 번호가 있으면 번호도 유지한다

### 2. Expression 번역

`<!-- expressions -->` 블록 내 각 표현의 뜻풀이를 대상 언어로 번역한다.

변환 전:
```markdown
<!-- expressions
- 능글맞은: [형용사] 겉으로는 순한 척하면서 속으로 교활한. (레벨 4급)
- 킥킥거리다: [동사] 소리를 죽이며 자꾸 웃다. 의성어. (레벨 4급)
-->
```

변환 후 (en 예시):
```markdown
<!-- expressions
- 능글맞은: [adj.] Seemingly gentle on the outside but sly on the inside. 
- 킥킥거리다: [verb] To giggle quietly, suppressing the sound. Onomatopoeia.
-->
```

규칙:
- 한국어 단어(키워드)는 그대로 유지한다
- 품사 태그를 대상 언어 약어로 변환한다 (형용사→adj., 동사→verb, 명사→noun, 부사→adv., 관용구→idiom, 동사구→v.phr., 어미→ending)
- 뜻풀이를 대상 언어로 자연스럽게 번역한다
- 한국어 문법 고유 용어(하오체, 해요체, 합쇼체 등)는 번역하지 않고 한글 그대로 유지한다
- 의성어/의태어 등 부가 표기도 대상 언어로 번역한다 (의성어→Onomatopoeia, 의태어→Mimetic word, 관용구→Idiom)
- "레벨 N급" 표기는 삭제한다.

### 3. 품사 태그 변환표

| 한국어 | en | zh-tw | ja |
|--------|-----|-------|-----|
| 형용사 | adj. | 形容詞 | 形容詞 |
| 동사 | verb | 動詞 | 動詞 |
| 명사 | noun | 名詞 | 名詞 |
| 부사 | adv. | 副詞 | 副詞 |
| 관용구 | idiom | 慣用語 | 慣用句 |
| 동사구 | v.phr. | 動詞短語 | 動詞句 |
| 어미 | ending | 語尾 | 語尾 |

## 출력 포맷

`tail-midform/{lang}/{스토리명}.md`에 저장한다. frontmatter에 `lang` 필드를 추가한다.

```markdown
---
title: 여우와 두루미
author: 이솝 (Aesop)
lang: {lang 코드}
difficulty:
  level: 2.6
  ... (원본 그대로)
source: tail-diff-analyzed/{스토리명}.md
analyzed_by: claude
localized_by: claude
---

# 여우와 두루미
<sub>{번역된 제목}</sub>

... (본문 + 병렬 표기 + 번역된 expressions)
```

## 주의사항

- 한국어 본문, 대사, 컷 설명 등은 절대 수정하지 않는다
- frontmatter의 기존 필드는 그대로 유지하고 `lang`, `localized_by`만 추가한다
- `<!-- expressions -->` 블록 구조(HTML 주석)를 유지한다
- 번역은 자연스럽고 정확해야 한다 — 직역보다 의역을 선호한다
