from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from loans.models import Customer, Loan
from loans.helper import calculate_credit_score
from datetime import datetime
import math
import json

@csrf_exempt
@require_http_methods(["POST"])
def register_customer(request):
    try:
        # Parse JSON body
        data = json.loads(request.body)

        first_name = data.get('first_name')
        last_name = data.get('last_name')
        age = data.get('age')
        monthly_income = int(data.get('monthly_income'))
        phone_number = data.get('phone_number')

        # Calculate approved_limit = 36 * monthly_income (rounded to nearest lakh)
        approved_limit = round(36 * monthly_income, -5)

        # Create new customer
        customer = Customer.objects.create(
            first_name=first_name,
            last_name=last_name,
            age=age,
            phone_number=phone_number,
            monthly_salary=monthly_income,
            approved_limit=approved_limit,
            current_debt=0
        )

        # Prepare response
        response = {
            "customer_id": customer.customer_id,
            "name": f"{first_name} {last_name}",
            "age": age,
            "monthly_income": monthly_income,
            "approved_limit": approved_limit,
            "phone_number": phone_number
        }

        return JsonResponse(response, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    


@csrf_exempt
@require_http_methods(["POST"])
def check_eligibility(request):
    try:
        # Parse request
        data = json.loads(request.body)
        customer_id = data.get('customer_id')
        loan_amount = data.get('loan_amount')
        interest_rate = data.get('interest_rate')
        tenure = data.get('tenure')

        # Validate required fields
        if not all([customer_id, loan_amount, interest_rate, tenure]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        # Convert to appropriate types
        loan_amount = float(loan_amount)
        interest_rate = float(interest_rate)
        tenure = int(tenure)

        # Fetch customer
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return JsonResponse({"error": "Customer not found"}, status=404)

        # Fetch historical loans
        loans = Loan.objects.filter(customer=customer)

        # --- Step 1: Calculate Credit Score ---
        credit_score = calculate_credit_score(customer, loans)

        # --- Step 2: Check Overutilization ---
        if credit_score == 0:
            return JsonResponse({
                "customer_id": customer_id,
                "approval": False,
                "reason": "Overutilized credit limit",
                "interest_rate": interest_rate,
                "corrected_interest_rate": interest_rate,
                "tenure": tenure,
                "monthly_installment": 0.0
            }, status=200)

        # --- Step 3: Determine Corrected Interest Rate ---
        corrected_interest_rate = interest_rate
        if 30 < credit_score <= 50:
            if interest_rate < 12:
                corrected_interest_rate = 12
        elif 10 < credit_score <= 30:
            if interest_rate < 16:
                corrected_interest_rate = 16

        # --- Step 4: Check Existing EMI Burden ---
        total_existing_emi = sum(loan.monthly_repayment for loan in loans)
        if total_existing_emi > 0.5 * customer.monthly_salary:
            return JsonResponse({
                "customer_id": customer_id,
                "approval": False,
                "reason": "Existing EMI burden exceeds 50% of salary",
                "interest_rate": interest_rate,
                "corrected_interest_rate": corrected_interest_rate,
                "tenure": tenure,
                "monthly_installment": 0.0
            }, status=200)

        # --- Step 5: Calculate Monthly Installment ---
        R = corrected_interest_rate / (12 * 100)
        N = tenure
        try:
            monthly_installment = (loan_amount * R * (1 + R) ** N) / ((1 + R) ** N - 1)
        except ZeroDivisionError:
            monthly_installment = 0.0

        # --- Step 6: Determine Approval Status ---
        approval = False
        if credit_score > 50:
            approval = True
        elif 30 < credit_score <= 50 and corrected_interest_rate >= 12:
            approval = True
        elif 10 < credit_score <= 30 and corrected_interest_rate >= 16:
            approval = True

        # --- Step 7: Prepare Response ---
        response = {
            "customer_id": customer_id,
            "approval": approval,
            "interest_rate": interest_rate,
            "corrected_interest_rate": corrected_interest_rate,
            "tenure": tenure,
            "monthly_installment": round(monthly_installment, 2)
        }

        if not approval:
            response["reason"] = "Credit score too low"

        return JsonResponse(response, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)