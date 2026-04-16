import json
import os
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent.parent / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) # OpenAI API 연결 객체. 이걸로 임베딩 요청 보냄

RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
VECTOR_DIR = Path(__file__).parent.parent / "data" / "vectors"


def extract_articles(law_data): 
    # 법령 데이터에서 조문별로 텍스트 추출하는 함수. 법령 데이터 구조에 맞게 조문번호, 제목, 내용, 항, 호 등을 조합해서 하나의 텍스트 덩어리로 만듦
    chunks = []
    law_name = law_data.get("법령", {}).get("기본정보", {}).get("법령명_한글", "")
    articles = law_data.get("법령", {}).get("조문", {}).get("조문단위", [])
    # 법령 JSON 구조가 법령 → 기본정보 → 법령명_한글 이렇게 중첩돼 있어서 단계별로 파고드는 방식으로 법령명과 조문 리스트를 추출. 
    # 조문단위가 하나면 dict 형태로 오고 여러 개면 list 형태로 오기 때문에 get("조문단위", [])로 기본값을 빈 리스트로 줘서 일관된 처리 가능

    for article in articles:
        if article.get("조문여부") == "전문":
            continue
        # 조문여부: "전문" → 장/절 구분 텍스트 ("제1장 총칙", "제2장 근로계약"...)
        # "전문"은 실제 법률 내용이 없고 그냥 목차 구분선 역할. 임베딩할 필요가 없으니까 스킵

        조문번호 = article.get("조문번호", "")
        조문제목 = article.get("조문제목", "")
        조문내용 = article.get("조문내용", "")
        가지번호 = article.get("조문가지번호", "")

        항_list = article.get("항", [])
        if isinstance(항_list, dict):
            항_list = [항_list]
            # 항이 1개면 dict로, 여러 개면 list로 오는 경우가 있어서 항상 list로 통일

        항_text = ""
        for 항 in 항_list:
            항내용 = 항.get("항내용", "")
            # 1단계: 항내용이 리스트인지 확인
            if isinstance(항내용, list):
                # 2단계: 리스트 안의 각 요소를 처리
                항내용 = " ".join([
                    x if isinstance(x, str)   # x가 문자열이면 그대로
                    else " ".join(x)          # x가 또 리스트면 이어붙이기
                    for x in 항내용])
            # 3단계: 항_text에 추가
            항_text += 항내용 + " "
            # 결국 어떤 형태로 오든 하나의 문자열로 만드는 게 목표

            호_list = 항.get("호", [])
            if isinstance(호_list, dict):
                호_list = [호_list]
            for 호 in 호_list:
                호내용 = 호.get("호내용", "")
                if isinstance(호내용, list):
                    호내용 = " ".join([x if isinstance(x, str) else " ".join(x) for x in 호내용])
                항_text += 호내용 + " "

        chunk_text = f"{조문내용} {항_text}".strip() # 조문내용 + 항 전체 텍스트를 하나의 청크로 합치기. 이게 나중에 임베딩되는 단위
        if not chunk_text:
            continue

        조문_id = f"{law_name}_{조문번호}"
        # 조문 ID 만드는 부분. 예를 들어 근로기준법 43조의2면 근로기준법_43의2
        if 가지번호:
            조문_id += f"의{가지번호}"

        chunks.append({
            "id": 조문_id,
            "text": chunk_text,
            "metadata": {
                "법령명": law_name,
                "조문번호": 조문번호,
                "조문제목": 조문제목,
                "가지번호": 가지번호
            }
        })

    return chunks


def get_embeddings(texts, batch_size=20): 
    # 299개 텍스트(5개 법령에서 추출한 조문 수 합계)를 한 번에 보내면 API 부하가 크니까 20개씩 잘라서 보냄
    all_embeddings = []
    for i in range(0, len(texts), batch_size): # 0, 20, 40, 60... 이렇게 20씩 증가하면서 반복
        batch = texts[i:i+batch_size]
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=batch
        )
        batch_embeddings = [e.embedding for e in response.data] # response.data = 임베딩 결과 리스트
        # batch_embeddings에서 각 임베딩 벡터값만 추출해서 batch_embeddings 리스트에 저장
        all_embeddings.extend(batch_embeddings)
        print(f"  임베딩 {i+len(batch)}/{len(texts)} 완료")
    return all_embeddings


def build_vectordb():
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)

    json_files = list(RAW_DATA_DIR.glob("*.json"))
    print(f"총 {len(json_files)}개 법령 파일 처리 시작\n")

    all_chunks = []
    for json_file in json_files:
        law_name = json_file.stem
        print(f"[{law_name}] 파싱 중...")

        with open(json_file, "r", encoding="utf-8") as f:
            law_data = json.load(f)

        chunks = extract_articles(law_data)
        print(f"  {len(chunks)}개 조문 추출")
        all_chunks.extend(chunks)
        # 5개 법령 JSON을 순서대로 읽어서 조문 추출 후 all_chunks에 다 모아둠

    print(f"\n총 {len(all_chunks)}개 조문 임베딩 시작...")
    texts = [c["text"] for c in all_chunks]
    embeddings = get_embeddings(texts)
    # all_chunks에서 텍스트만 뽑아서 임베딩 요청

    # numpy 저장
    embeddings_array = np.array(embeddings, dtype=np.float32)
    np.save(VECTOR_DIR / "embeddings.npy", embeddings_array)
    # 임베딩 결과를 numpy 배열로 변환 후 .npy 파일로 저장
    # shape은 (299, 1536) — 299개 조문, 각 1536차원 벡터

    # 메타데이터 저장
    metadata = [{"id": c["id"], "text": c["text"], "metadata": c["metadata"]} for c in all_chunks]
    with open(VECTOR_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    # 벡터랑 별도로 조문 텍스트랑 법령명, 조문번호 등 메타데이터를 JSON으로 저장. 나중에 검색 결과 보여줄 때 필요

    print(f"\n저장 완료!")
    print(f"  임베딩: {VECTOR_DIR / 'embeddings.npy'}")
    print(f"  메타데이터: {VECTOR_DIR / 'metadata.json'}")
    print(f"  총 {len(all_chunks)}개 조문")


if __name__ == "__main__":
    build_vectordb()