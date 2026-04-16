import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from rag_pipeline import search_law, generate_response
from calculator import calculate_total
from form_generator import generate_complaint_form, generate_content_certified_mail
from agency_guide import get_agency_guide, get_labor_office_info

st.set_page_config(page_title="급여119", page_icon="🚨", layout="wide")

st.title("🚨 급여119")
st.caption("임금체불 피해자를 위한 AI 완결형 대응 서비스")

# 사이드바 - 진행 단계
with st.sidebar:
    st.header("📋 대응 단계")
    step = st.radio("현재 단계를 선택하세요", [
        "1단계: 상황 입력 및 법령 검색",
        "2단계: 체불 금액 계산",
        "3단계: 서식 자동생성",
        "4단계: 기관 연계 안내"
    ])

    st.divider()
    st.caption("💡 순서대로 진행하면 더 정확한 결과를 얻을 수 있어요.")

# ── 1단계: 상황 입력 및 법령 검색 ──
if step == "1단계: 상황 입력 및 법령 검색":
    st.header("1단계: 상황 입력 및 법령 검색")

    query = st.text_area(
        "피해 상황을 입력하세요",
        placeholder="예) 3개월째 월급을 못 받고 있습니다. 사장이 연락을 안 받아요.",
        height=120
    )

    if st.button("법령 검색 및 대응 가이드 생성", type="primary"):
        if query:
            with st.spinner("관련 법령 검색 중..."):
                results = search_law(query, top_k=3)

            st.subheader("📚 관련 법령")
            for r in results:
                with st.expander(f"{r['법령명']} 제{r['조문번호']}조 {r['조문제목']} (유사도: {r['score']:.3f})"):
                    st.write(r['text'])

            with st.spinner("AI 대응 가이드 생성 중..."):
                answer = generate_response(query, results)

            st.subheader("💡 AI 대응 가이드")
            st.markdown(answer)
        else:
            st.warning("상황을 입력해주세요.")

# ── 2단계: 체불 금액 계산 ──
elif step == "2단계: 체불 금액 계산":
    st.header("2단계: 체불 금액 계산")

    col1, col2 = st.columns(2)

    with col1:
        hourly_wage = st.number_input("시급 (원)", min_value=0, value=10030, step=100)
        daily_hours = st.number_input("일일 근무시간 (시간)", min_value=0, max_value=24, value=8)
        work_days = st.number_input("미지급 근무일수 (일)", min_value=0, value=30)

    with col2:
        weekly_hours = st.number_input("주간 근무시간 (시간)", min_value=0, max_value=168, value=40)
        monthly_wage = st.number_input("월 급여 (원)", min_value=0, value=2096270, step=10000)
        work_months = st.number_input("총 근무개월수", min_value=0, value=14)
        delay_days = st.number_input("임금 지연일수 (일)", min_value=0, value=30)

    if st.button("금액 계산", type="primary"):
        result = calculate_total(
            hourly_wage=hourly_wage,
            daily_hours=daily_hours,
            work_days=work_days,
            weekly_hours=weekly_hours,
            monthly_wage=monthly_wage,
            work_months=work_months,
            delay_days=delay_days
        )

        st.subheader("💰 계산 결과")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("미지급 임금", f"{result['미지급_임금']:,}원")
        col2.metric("주휴수당", f"{result['주휴수당']:,}원")
        col3.metric("퇴직금", f"{result['퇴직금']:,}원")
        col4.metric("지연이자", f"{result['지연이자']:,}원")
        col5.metric("합계", f"{result['합계']:,}원")

        st.session_state['unpaid_amount'] = result['합계']
        st.session_state['work_months'] = work_months
        st.success("✅ 계산 완료! 3단계에서 서식을 생성하세요.")

# ── 3단계: 서식 자동생성 ──
elif step == "3단계: 서식 자동생성":
    st.header("3단계: 서식 자동생성")

    form_type = st.radio("서식 종류", ["진정서", "내용증명"])

    unpaid_amount = st.session_state.get('unpaid_amount', 0)
    unpaid_amount = st.number_input("체불 금액 (원)", min_value=0, value=unpaid_amount, step=10000)

    if form_type == "진정서":
        col1, col2 = st.columns(2)
        with col1:
            worker_name = st.text_input("이름")
            worker_address = st.text_input("주소")
            worker_phone = st.text_input("연락처")
            job_type = st.text_input("직종", value="근로자")
        with col2:
            employer_name = st.text_input("사업주 이름")
            company_name = st.text_input("사업장명")
            company_address = st.text_input("사업장 주소")
            work_start_date = st.text_input("근무 시작일 (예: 2024-01-01)")
            work_end_date = st.text_input("근무 종료일 (예: 2024-12-31)")
            unpaid_period = st.text_input("체불 기간 (예: 2024년 10월~12월)")

        if st.button("진정서 생성", type="primary"):
            if worker_name and employer_name:
                with st.spinner("진정서 생성 중..."):
                    result = generate_complaint_form(
                        worker_name=worker_name,
                        worker_address=worker_address,
                        worker_phone=worker_phone,
                        employer_name=employer_name,
                        company_name=company_name,
                        company_address=company_address,
                        work_start_date=work_start_date,
                        work_end_date=work_end_date,
                        unpaid_amount=unpaid_amount,
                        unpaid_period=unpaid_period,
                        job_type=job_type
                    )
                st.subheader("📄 진정서 초안")
                st.markdown(result)
                st.download_button("진정서 다운로드", result, file_name="진정서.txt", mime="text/plain")
            else:
                st.warning("이름과 사업주 이름을 입력해주세요.")

    else:
        col1, col2 = st.columns(2)
        with col1:
            worker_name = st.text_input("이름")
        with col2:
            employer_name = st.text_input("사업주 이름")
            company_name = st.text_input("사업장명")
            deadline_days = st.number_input("지급 요청 기한 (일)", min_value=1, value=7)

        if st.button("내용증명 생성", type="primary"):
            if worker_name and employer_name:
                with st.spinner("내용증명 생성 중..."):
                    result = generate_content_certified_mail(
                        worker_name=worker_name,
                        employer_name=employer_name,
                        company_name=company_name,
                        unpaid_amount=unpaid_amount,
                        deadline_days=deadline_days
                    )
                st.subheader("📄 내용증명 초안")
                st.markdown(result)
                st.download_button("내용증명 다운로드", result, file_name="내용증명.txt", mime="text/plain")
            else:
                st.warning("이름과 사업주 이름을 입력해주세요.")

# ── 4단계: 기관 연계 안내 ──
elif step == "4단계: 기관 연계 안내":
    st.header("4단계: 기관 연계 안내")

    col1, col2 = st.columns(2)
    with col1:
        current_step = st.selectbox("현재 진행 단계", ["진정_전", "진정_후"])
        is_retired = st.checkbox("퇴직하셨나요?")
    with col2:
        region = st.selectbox("지역", ["부산", "서울", "대구", "인천", "광주", "대전", "울산", "경기"])

    unpaid_amount = st.session_state.get('unpaid_amount', 0)

    guide, recommended = get_agency_guide(current_step, unpaid_amount=unpaid_amount, is_retired=is_retired)

    st.subheader(guide['title'])

    st.subheader("🏢 연계 기관")
    for agency in guide['agencies']:
        with st.expander(agency['name']):
            st.write(agency['description'])
            st.link_button(agency['action'], agency['url'])

    st.subheader("✅ 준비 체크리스트")
    for item in guide['checklist']:
        st.checkbox(item)

    st.divider()
    st.subheader("📍 관할 노동청")
    office = get_labor_office_info(region)
    col1, col2, col3 = st.columns(3)
    col1.metric("기관명", office['name'])
    col2.metric("전화번호", office['phone'])
    col3.metric("주소", office['address'])