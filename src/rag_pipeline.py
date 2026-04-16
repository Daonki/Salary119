import json
import os
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent.parent / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VECTOR_DIR = Path(__file__).parent.parent / "data" / "vectors"


def load_vectordb():
    # vectordb_builder.py에서 저장해둔 두 파일을 불러오는 함수
    """저장된 벡터와 메타데이터 로드"""
    embeddings = np.load(VECTOR_DIR / "embeddings.npy")
    with open(VECTOR_DIR / "metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)
    return embeddings, metadata
    # embeddings.npy → numpy 배열로 로드 (shape: 299 × 1536)
    # metadata.json → 조문 텍스트 + 법령명 등 정보 로드


def get_query_embedding(query):
    # 사용자가 입력한 질문을 벡터로 변환하는 함수
    # vectordb_builder.py에서 조문 텍스트를 임베딩했던 것과 동일한 모델로 변환해야 유사도 비교가 가능
    """사용자 입력 텍스트를 임베딩"""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return np.array(response.data[0].embedding, dtype=np.float32)


def cosine_similarity(a, b): # 두 벡터가 얼마나 비슷한지 계산하는 함수
    # 벡터 a — 사용자 질문을 임베딩한 벡터 (query_embedding)
    # 벡터 b — 저장된 조문 하나를 임베딩한 벡터 (embeddings[i])
    """코사인 유사도 계산"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
# 두 화살표가 같은 방향을 가리키면 → 유사도 1.0 (완전 일치)
# 두 화살표가 반대 방향을 가리키면 → 유사도 -1.0 (완전 불일치)
# 두 화살표가 직각을 이루면 → 유사도 0.0 (관련 없음)
# np.dot — 두 벡터의 내적 계산, np.linalg.norm — 벡터의 크기 계산


def search_law(query, top_k=5):
    """관련 법령 조문 검색"""
    embeddings, metadata = load_vectordb() # 저장된 벡터와 메타데이터 로드(저장된 299개 벡터를 불러옴
    query_embedding = get_query_embedding(query) # 사용자 질문을 임베딩 벡터로 변환

    # 전체 조문과 유사도 계산
    similarities = np.array([
        cosine_similarity(query_embedding, embeddings[i])
        for i in range(len(embeddings))
    ])
    # 모든 조문에 대해 사용자 질문과의 유사도 계산 → similarities 배열(길이 299짜리 유사도 점수 배열)에 저장 (shape: 299, 각 값은 -1.0 ~ 1.0 사이)

    # 상위 top_k 추출
    top_indices = np.argsort(similarities)[::-1][:top_k]
    # np.argsort(similarities) — 유사도 낮은 순으로 인덱스 정렬
    # [::-1] — 뒤집어서 높은 순으로
    # [:top_k] — 상위 top_k개만 추출

    results = []
    for idx in top_indices:
        results.append({
            "score": float(similarities[idx]),
            "id": metadata[idx]["id"],
            "법령명": metadata[idx]["metadata"]["법령명"],
            "조문번호": metadata[idx]["metadata"]["조문번호"],
            "조문제목": metadata[idx]["metadata"]["조문제목"],
            "text": metadata[idx]["text"]
        })
        # 상위 조문들의 유사도 점수 + 메타데이터를 딕셔너리로 묶어서 반환.
    return results


def generate_response(query, search_results):
    """검색된 법령을 바탕으로 GPT 답변 생성"""
    context = ""
    for r in search_results:
        context += f"[{r['법령명']} 제{r['조문번호']}조 {r['조문제목']}]\n{r['text']}\n\n"
        # 검색된 조문들을 답변 생성에 활용할 수 있도록 하나의 문자열로 합침. 각 조문은 법령명, 조문번호, 조문제목, 조문텍스트로 구성되어 있음

    prompt = f"""당신은 임금체불 피해 근로자를 돕는 AI 법률 어시스턴트입니다.
아래 법령 조문을 참고하여 사용자의 질문에 답변해주세요.
법령에 없는 내용은 추측하지 말고, 전문적인 법률 판단이 필요한 경우 노무사나 법률구조공단 상담을 안내하세요.

[참고 법령]
{context}

[사용자 질문]
{query}

[답변]"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3 # 답변의 창의성 조절. 낮을수록 더 사실적이고 일관된 답변이 나옴
    )

    return response.choices[0].message.content #  GPT 답변 텍스트만 추출


if __name__ == "__main__":
    # 테스트
    query = "임금을 못 받았을 때 어떻게 해야 하나요?"
    print(f"질문: {query}\n")

    print("관련 법령 검색 중...")
    results = search_law(query, top_k=3)

    print("\n[검색된 법령]")
    for r in results:
        print(f"  - {r['법령명']} 제{r['조문번호']}조 {r['조문제목']} (유사도: {r['score']:.3f})")

    print("\n[AI 답변 생성 중...]")
    answer = generate_response(query, results)
    print(f"\n{answer}")