# API 호출 없이 순수하게 데이터 반환만 하는 모듈
def get_agency_guide(step, unpaid_amount=0, is_retired=False):
    """현재 단계에 따른 기관 연계 안내 반환"""

    guides = {
        # 3가지 상황에 대한 안내 정보를 딕셔너리로 미리 정의해둔 거 title, agencies, checklist
        "진정_전": {
            "title": "📋 노동청 진정 전 단계",
            "agencies": [
                {
                    "name": "고용노동부 노동포털",
                    "description": "임금체불 진정서 온라인 접수",
                    "url": "https://minwon.moel.go.kr",
                    "action": "진정서 접수하기"
                },
                {
                    "name": "관할 지방고용노동청",
                    "description": "직접 방문 접수 및 상담 가능",
                    "url": "https://www.moel.go.kr/local/intro.do",
                    "action": "관할 노동청 찾기"
                }
            ],
            "checklist": [
                "근로계약서 사본 준비",
                "임금명세서 또는 통장 입금 내역 준비",
                "근무일지 또는 출퇴근 기록 준비",
                "카카오톡 등 대화 내역 캡처"
            ]
        },
        "진정_후": {
            "title": "📋 노동청 진정 후 단계",
            "agencies": [
                {
                    "name": "근로복지공단",
                    "description": "대지급금(체당금) 신청 — 사업주 잠적·도산 시",
                    "url": "https://www.kcomwel.or.kr",
                    "action": "대지급금 신청하기"
                },
                {
                    "name": "대한법률구조공단",
                    "description": "무료 법률 상담 및 소송 지원",
                    "url": "https://www.klac.or.kr",
                    "action": "무료 상담 신청"
                }
            ],
            "checklist": [
                "체불확인서 발급 (진정 후 약 2주 소요)",
                "체불확인서 발급 후 30일 이내 대지급금 신청",
                "진정 후 2개월 미해결 시 법률구조공단 연계"
            ]
        },
        "소액체당금": {
            "title": "💰 소액체당금 신청 단계",
            "agencies": [
                {
                    "name": "근로복지공단",
                    "description": "소액체당금 간편 신청 — 퇴직 근로자 대상, 임금/퇴직금 최대 1,000만원",
                    "url": "https://www.kcomwel.or.kr",
                    "action": "소액체당금 신청"
                }
            ],
            "checklist": [
                "체불확인서 준비",
                "신분증 준비",
                "통장 사본 준비",
                "근로복지공단 지사 방문 또는 온라인 신청"
            ]
        }
    }

    # 상황에 따라 적절한 단계 자동 판단
    if is_retired:
        recommended = "소액체당금"
    elif step == "진정_전":
        recommended = "진정_전"
    else:
        recommended = "진정_후"

    return guides[recommended], recommended


def get_labor_office_info(region):
    """지역별 관할 노동청 정보"""
    offices = {
        "서울": {"name": "서울지방고용노동청", "phone": "02-2250-5701", "address": "서울 중구 퇴계로 173"},
        "부산": {"name": "부산지방고용노동청", "phone": "051-850-6300", "address": "부산 연제구 중앙대로 1000"},
        "대구": {"name": "대구지방고용노동청", "phone": "053-667-6000", "address": "대구 북구 옥산로 45"},
        "인천": {"name": "인천지방고용노동청", "phone": "032-460-4500", "address": "인천 남동구 은봉로 82"},
        "광주": {"name": "광주지방고용노동청", "phone": "062-975-6400", "address": "광주 북구 첨단과기로 208"},
        "대전": {"name": "대전지방고용노동청", "phone": "042-480-6200", "address": "대전 서구 청사로 136"},
        "울산": {"name": "울산지방고용노동청", "phone": "052-228-1800", "address": "울산 남구 삼산로 243"},
        "경기": {"name": "경기지청", "phone": "031-259-0114", "address": "경기 수원시 영통구 반달로 87"},
    }
    return offices.get(region, offices["서울"])


if __name__ == "__main__":
    # 테스트
    print("=== 기관 연계 안내 테스트 ===\n")

    guide, step = get_agency_guide("진정_전", unpaid_amount=4855532)
    print(f"추천 단계: {step}")
    print(f"제목: {guide['title']}\n")

    print("연계 기관:")
    for agency in guide['agencies']:
        print(f"  - {agency['name']}: {agency['description']}")
        print(f"    URL: {agency['url']}")

    print("\n체크리스트:")
    for item in guide['checklist']:
        print(f"  □ {item}")

    print("\n=== 관할 노동청 ===")
    office = get_labor_office_info("부산")
    print(f"{office['name']}")
    print(f"전화: {office['phone']}")
    print(f"주소: {office['address']}")