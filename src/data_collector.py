import requests # 인터넷 주소로 데이터 요청하는 라이브러리. 법제처 API 호출할 때 씀
import json # JSON 형식으로 데이터를 저장하기 위한 라이브러리. API에서 받은 데이터를 JSON 파일로 저장할 때 씀
import os # 운영체제 관련 기능을 제공하는 라이브러리. 환경변수에서 API 키를 읽어올 때 씀 (os.getenv)
import time # 시간 관련 기능을 제공하는 라이브러리. API 호출 사이에 딜레이를 주기 위해 씀 (time.sleep)
from pathlib import Path # 파일 경로를 쉽게 다루기 위한 라이브러리. 데이터 저장 경로를 만들 때 씀 (Path(__file__).parent.parent / "data" / "raw")
from dotenv import load_dotenv # .env 파일에서 환경변수를 로드하는 라이브러리. API 키를 .env 파일에 저장하고 불러올 때 씀 (load_dotenv)

load_dotenv(Path(__file__).parent.parent / ".env")

OC = os.getenv("LAW_OC")

LAW_LIST = [
    "근로기준법",
    "최저임금법",
    "근로자퇴직급여 보장법",
    "임금채권보장법",
    "소액사건심판법"
]

def search_law(law_name):
    url = "http://www.law.go.kr/DRF/lawSearch.do"
    params = {"OC": OC, "target": "law", "type": "JSON", "query": law_name}
    response = requests.get(url, params=params)
    data = response.json()

    laws = data.get("LawSearch", {}).get("law", []) 
    # API 응답구조 {"LawSearch": {"law": [...]}}
    # data.get("LawSearch", {}) LawSearch 키 없으면 빈 dict 반환
    # .get("law", []) law 키 없으면 빈 리스트 반환
    if not laws:
        print(f"  검색 결과 없음: {law_name}")
        return None
    if isinstance(laws, dict):
        laws = [laws]
    for law in laws:
        if law.get("법령명한글") == law_name:
            return law.get("법령일련번호")
    return laws[0].get("법령일련번호")

def get_law_articles(mst): 
    # 법령일련번호(MST)로 해당 법령의 조문 데이터를 가져오는 함수 구조는 search_law랑 똑같고 엔드포인트랑 파라미터만 다름
    url = "http://www.law.go.kr/DRF/lawService.do"
    params = {"OC": OC, "target": "law", "MST": mst, "type": "JSON"}
    response = requests.get(url, params=params)
    return response.json()

def save_law_data(data, filename):
    save_dir = Path(__file__).parent.parent / "data" / "raw"
    save_dir.mkdir(parents=True, exist_ok=True) 
    # 부모 디렉토리까지 모두 생성, 이미 있으면 에러 안 나게 -> data/raw 폴더가 없으면 만들고, 있으면 그냥 넘어감
    path = save_dir / f"{filename}.json"
    with open(path, "w", encoding="utf-8") as f: # 파일 열고 작업 끝나면 자동으로 닫히게 하는 with 구문
        json.dump(data, f, ensure_ascii=False, indent=2) 
        # JSON 파일로 저장, ensure_ascii=False는 한글 깨짐 방지(False 안 하면 \uAC00 같은 유니코드로 저장됨)
        # indent=2는 JSON 들여쓰기 2칸으로 보기 좋게 저장
    print(f"  저장 완료: {path}")

if __name__ == "__main__": # 이 파일이 직접 실행될 때만 아래 코드가 실행되도록 하는 구문. 다른 파일에서 import할 때는 실행 안 됨
    for law_name in LAW_LIST:
        print(f"\n[{law_name}] 수집 중...")
        mst = search_law(law_name)
        if not mst:
            continue # MST 못 찾으면 다음 법령으로 넘어감
        print(f"  MST: {mst}")
        data = get_law_articles(mst)
        save_law_data(data, law_name)
        print(f"[{law_name}] 완료")
        time.sleep(0.5) # API 과부하 방지 위해 0.5초 딜레이