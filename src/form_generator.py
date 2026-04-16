import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from datetime import date

load_dotenv(Path(__file__).parent.parent / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_complaint_form(
    worker_name,
    worker_address,
    worker_phone,
    employer_name,
    company_name,
    company_address,
    work_start_date,
    work_end_date,
    unpaid_amount,
    unpaid_period,
    job_type="근로자"
):
    """노동청 진정서 초안 자동생성"""

    prompt = f"""아래 정보를 바탕으로 고용노동부 노동청에 제출할 임금체불 진정서 초안을 작성해주세요.
형식은 실제 진정서 양식에 맞게 작성하고, 근로기준법 조문을 근거로 명시해주세요.

[진정인 정보]
- 이름: {worker_name}
- 주소: {worker_address}
- 연락처: {worker_phone}

[피진정인 정보]
- 사업주 이름: {employer_name}
- 사업장명: {company_name}
- 사업장 주소: {company_address}

[근무 정보]
- 근무 기간: {work_start_date} ~ {work_end_date}
- 직종: {job_type}
- 체불 기간: {unpaid_period}
- 체불 금액: {unpaid_amount:,}원

[작성 지침]
1. 진정 취지, 진정 이유, 증거 자료 목록 순서로 작성
2. 근로기준법 제36조(금품청산), 제43조(임금지급) 조문 인용
3. 사실관계를 명확하고 간결하게 작성
4. 마지막에 제출일과 진정인 서명란 포함
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content


def generate_content_certified_mail(
    worker_name,
    employer_name,
    company_name,
    unpaid_amount,
    deadline_days=7
):
    """내용증명 초안 자동생성"""

    prompt = f"""아래 정보를 바탕으로 임금 지급을 요구하는 내용증명 초안을 작성해주세요.
법적 효력이 있는 내용증명 형식으로 작성하고, 근로기준법 조문을 근거로 명시해주세요.

[발신인]
- 이름: {worker_name}

[수신인]
- 사업주: {employer_name}
- 사업장명: {company_name}

[내용]
- 체불 금액: {unpaid_amount:,}원
- 지급 요청 기한: 본 내용증명 수령 후 {deadline_days}일 이내

[작성 지침]
1. 제목: 임금 지급 촉구 내용증명
2. 발신·수신인 정보
3. 체불 사실 및 법적 근거 (근로기준법 제36조, 제43조, 제37조 지연이자 조항)
4. 지급 요청 및 미이행 시 법적 조치 예고
5. 발송일 및 서명란
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    # 테스트
    print("=== 진정서 생성 ===\n")
    complaint = generate_complaint_form(
        worker_name="홍길동",
        worker_address="부산광역시 연제구 000로 00",
        worker_phone="010-0000-0000",
        employer_name="김사장",
        company_name="(주)테스트식당",
        company_address="부산광역시 동래구 000로 00",
        work_start_date="2025-06-01",
        work_end_date="2025-12-31",
        unpaid_amount=4855532,
        unpaid_period="2025년 10월 ~ 12월",
        job_type="서빙"
    )
    print(complaint)

    print("\n\n=== 내용증명 생성 ===\n")
    mail = generate_content_certified_mail(
        worker_name="홍길동",
        employer_name="김사장",
        company_name="(주)테스트식당",
        unpaid_amount=4855532,
        deadline_days=7
    )
    print(mail)