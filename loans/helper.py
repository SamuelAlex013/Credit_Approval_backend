from datetime import date


def calculate_credit_score(customer, loans):
    if customer.current_debt > customer.approved_limit:
        return 0  # Overutilization

    total_loans = len(loans)
    if total_loans == 0:
        return 50  # New customer

    # 1. Past Loans Paid on Time (40% weight)
    emis_paid = sum(loan.emis_paid_on_time for loan in loans)
    emis_total = sum(loan.tenure for loan in loans)
    on_time_ratio = emis_paid / emis_total if emis_total else 0
    score_on_time = on_time_ratio * 40

    # 2. Number of Loans Taken (15% weight)
    loan_count_score = max(0, (10 - total_loans)) * 1.5  # Max 15 points

    # 3. Loan Activity in Current Year (15% weight)
    current_year = date.today().year
    recent_loans = [l for l in loans if l.start_date.year == current_year]
    recent_activity_score = max(15 - (len(recent_loans) * 3), 0)  # Max 15 points

    # 4. Loan Approved Volume (30% weight)
    volume_ratio = customer.current_debt / customer.approved_limit if customer.approved_limit else 0
    volume_score = (1 - volume_ratio) * 30

    # Total Score
    total_score = score_on_time + loan_count_score + recent_activity_score + volume_score
    total_score = round(max(0, min(100, total_score)), 2)
    return total_score