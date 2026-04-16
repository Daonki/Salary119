from datetime import date, timedelta


def calculate_unpaid_wage(hourly_wage, work_days, daily_hours):
    """미지급 임금 계산"""
    return hourly_wage * daily_hours * work_days


def calculate_weekly_holiday_pay(hourly_wage, weekly_hours):
    """주휴수당 계산 (주 15시간 이상 근무 시)"""
    if weekly_hours < 15:
        return 0
    # 주휴수당 = 시급 × (주소정근로시간 / 40) × 8
    return hourly_wage * (weekly_hours / 40) * 8


def calculate_severance(monthly_wage, work_months):
    """퇴직금 계산 (1년 이상 근무 시)"""
    if work_months < 12:
        return 0
    # 퇴직금 = 평균임금 × 30일 × (근무연수)
    work_years = work_months / 12
    daily_wage = monthly_wage / 30
    return daily_wage * 30 * work_years


def calculate_delay_interest(unpaid_amount, delay_days):
    """지연이자 계산 (연 20%, 퇴직/사망 후 14일 초과 시)"""
    if delay_days <= 14:
        return 0
    effective_days = delay_days - 14
    return unpaid_amount * 0.20 * (effective_days / 365)


def calculate_total(
    hourly_wage,
    daily_hours,
    work_days,
    weekly_hours,
    monthly_wage,
    work_months,
    delay_days
):
    """전체 체불 금액 계산"""
    unpaid_wage = calculate_unpaid_wage(hourly_wage, work_days, daily_hours)
    weekly_holiday = calculate_weekly_holiday_pay(hourly_wage, weekly_hours)
    severance = calculate_severance(monthly_wage, work_months)
    total_unpaid = unpaid_wage + weekly_holiday + severance
    delay_interest = calculate_delay_interest(total_unpaid, delay_days)

    return {
        "미지급_임금": round(unpaid_wage),
        "주휴수당": round(weekly_holiday),
        "퇴직금": round(severance),
        "지연이자": round(delay_interest),
        "합계": round(total_unpaid + delay_interest)
    }


if __name__ == "__main__":
    # 테스트: 시급 10,000원, 하루 8시간, 30일 미지급, 주 40시간, 월급 2,000,000원, 근무 14개월, 30일 지연
    result = calculate_total(
        hourly_wage=10000,
        daily_hours=8,
        work_days=30,
        weekly_hours=40,
        monthly_wage=2000000,
        work_months=14,
        delay_days=30
    )

    print("=== 체불 금액 계산 결과 ===")
    for key, value in result.items():
        print(f"{key}: {value:,}원")