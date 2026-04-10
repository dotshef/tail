# -*- coding: utf-8 -*-
"""
어휘 난이도 분석 스크립트 (analyze-vocab.py)

역할:
  동화 마크다운의 어휘를 TOPIK 급수 기준으로 분석하여 vocabulary_level을 산출한다.
  LLM 에이전트가 직접 판단할 때 발생하는 결과 편차를 제거하기 위해,
  같은 입력에 대해 항상 동일한 JSON을 출력하는 결정적 스크립트이다.

동작 흐름:
  1. 텍스트 추출    — 마크다운에서 frontmatter, 주석, 이미지, 헤딩, 대사 태그 제거
  2. 형태소 분석    — kiwipiepy로 명사/동사/형용사/부사/어근 추출 (용언은 기본형 변환)
  3. CSV 사전 로드  — difficulty-voca/TOPIK_{1-6}_words.csv 로드, 동음이의어/슬래시 정규화
  4. 대조           — 정확/부분 매칭으로 등재·미등재 분리
  5. 가중 평균 계산 — 각 단어의 급수(미등재=5급)를 점수로 평균, 반올림하여 레벨 결정

가중 평균 → vocabulary_level 변환:
  < 1.5 → 1   |  1.5~2.5 → 2  |  2.5~3.5 → 3
  3.5~4.5 → 4 |  4.5~5.5 → 5  |  5.5+   → 6

사용법:
  python -X utf8 analyze-vocab.py "<입력파일.md>"

출력(JSON, stdout):
  {
    "total_words", "registered_count", "unregistered_count",
    "unregistered_ratio", "weighted_avg", "vocabulary_level",
    "level_distribution", "registered", "unregistered"
  }

의존성: kiwipiepy (순수 C++ 기반 한국어 형태소 분석기)
"""

import sys
import os
import re
import csv
import json
from kiwipiepy import Kiwi

# 분석 대상 품사 태그 (체언 + 용언 어간)
TARGET_TAGS = {
    'NNG',   # 일반명사
    'NNP',   # 고유명사
    'VV',    # 동사
    'VA',    # 형용사
    'VV-I',  # 불규칙 동사
    'VA-I',  # 불규칙 형용사
    'MAG',   # 일반부사
    'XR',    # 어근
}


def extract_text(md_path):
    """마크다운에서 본문 텍스트만 추출 (헤딩, 이미지, 주석, frontmatter 제외)"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # frontmatter 제거
    content = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)
    # HTML 주석 제거
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    # 이미지 참조 제거
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    # 볼드 컷 마커 제거
    content = re.sub(r'\*\*\[컷 \d+\].*?\*\*', '', content)
    # 헤딩 제거
    content = re.sub(r'^#{1,4}\s+.*$', '', content, flags=re.MULTILINE)
    # 원작자 제거
    content = re.sub(r'^- 원작자:.*$', '', content, flags=re.MULTILINE)
    # 대사 태그에서 캐릭터명 제거, 대사 텍스트만 남김
    content = re.sub(r'^- \S+:\s*', '', content, flags=re.MULTILINE)

    return content.strip()


def analyze_morphemes(text):
    """형태소 분석 후 고유 어간/단어를 추출"""
    kiwi = Kiwi()
    tokens = kiwi.tokenize(text)

    words = {}
    for t in tokens:
        if t.tag in TARGET_TAGS and len(t.form) >= 2:
            # 용언은 기본형으로 변환 (어간 + 다)
            if t.tag.startswith('VV') or t.tag.startswith('VA'):
                lemma = t.form + '다'
            else:
                lemma = t.form

            if lemma not in words:
                words[lemma] = t.tag

    return words


def load_csv_vocab(voca_dir):
    """TOPIK CSV 파일에서 어휘 사전 구축"""
    vocab_dict = {}
    for level in range(1, 7):
        csv_path = os.path.join(voca_dir, f'TOPIK_{level}_words.csv')
        if not os.path.exists(csv_path):
            continue
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 헤더 스킵
            for row in reader:
                if len(row) >= 3:
                    word = row[2].strip()
                    # 동음이의어 번호 제거 (가게02 → 가게)
                    word_clean = re.sub(r'\d+$', '', word)
                    # 슬래시로 구분된 복수 형태 처리 (가로01/가로02 → 가로)
                    for w in word_clean.split('/'):
                        w = re.sub(r'\d+$', '', w).strip()
                        if w and w not in vocab_dict:
                            vocab_dict[w] = level
    return vocab_dict


def match_vocab(words, vocab_dict):
    """추출된 단어를 CSV 사전과 대조"""
    registered = {}    # {단어: 급수}
    unregistered = []  # [단어]

    for lemma, tag in words.items():
        matched = False
        # 정확히 일치
        if lemma in vocab_dict:
            registered[lemma] = vocab_dict[lemma]
            matched = True
        else:
            # 용언: '다' 제거한 어간으로도 검색
            if lemma.endswith('다'):
                stem = lemma[:-1]
                for dict_word, level in vocab_dict.items():
                    if dict_word == stem or dict_word == lemma:
                        registered[lemma] = level
                        matched = True
                        break
            # 명사: 부분 매칭 (2글자 이상 어근이 포함된 경우)
            if not matched and len(lemma) >= 2:
                for dict_word, level in vocab_dict.items():
                    if len(dict_word) >= 2 and (lemma == dict_word or dict_word.startswith(lemma) or lemma.startswith(dict_word)):
                        registered[lemma] = level
                        matched = True
                        break

        if not matched:
            unregistered.append(lemma)

    return registered, unregistered


def main():
    if len(sys.argv) < 2:
        print("Usage: python -X utf8 analyze-vocab.py <input.md>", file=sys.stderr)
        sys.exit(1)

    md_path = sys.argv[1]
    script_dir = os.path.dirname(os.path.abspath(__file__))
    voca_dir = os.path.join(script_dir, 'difficulty-voca')

    # 1. 텍스트 추출
    text = extract_text(md_path)

    # 2. 형태소 분석
    words = analyze_morphemes(text)

    # 3. CSV 로드 & 대조
    vocab_dict = load_csv_vocab(voca_dir)
    registered, unregistered = match_vocab(words, vocab_dict)

    # 4. 통계
    total = len(registered) + len(unregistered)
    level_dist = {}
    for word, level in registered.items():
        key = f'{level}급'
        level_dist[key] = level_dist.get(key, 0) + 1

    # 5. 가중 평균 계산 (미등재 = 5급 취급)
    level_sum = sum(level for level in registered.values()) + len(unregistered) * 5
    weighted_avg = round(level_sum / total, 1) if total > 0 else 0

    # 가중 평균 → vocabulary_level 변환 (반올림 기반)
    if weighted_avg < 1.5:
        vocab_level = 1
    elif weighted_avg < 2.5:
        vocab_level = 2
    elif weighted_avg < 3.5:
        vocab_level = 3
    elif weighted_avg < 4.5:
        vocab_level = 4
    elif weighted_avg < 5.5:
        vocab_level = 5
    else:
        vocab_level = 6

    result = {
        'total_words': total,
        'registered_count': len(registered),
        'unregistered_count': len(unregistered),
        'unregistered_ratio': round(len(unregistered) / total * 100, 1) if total > 0 else 0,
        'weighted_avg': weighted_avg,
        'vocabulary_level': vocab_level,
        'level_distribution': level_dist,
        'registered': {w: f'{l}급' for w, l in sorted(registered.items(), key=lambda x: x[1])},
        'unregistered': sorted(unregistered),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
