from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.test import RequestFactory
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

        # --- Step 6: Determine Approval Status Based on Credit Score ---
        approval = False
        reason = ""
        
        if credit_score > 50:
            approval = True
        elif 30 < credit_score <= 50:
            if corrected_interest_rate >= 12:
                approval = True
            else:
                reason = "Interest rate too low for credit score range 30-50"
        elif 10 < credit_score <= 30:
            if corrected_interest_rate >= 16:
                approval = True
            else:
                reason = "Interest rate too low for credit score range 10-30"
        else:  # credit_score <= 10
            approval = False
            reason = "Credit score too low (≤10)"

        # --- Step 7: Prepare Response ---
        response = {
            "customer_id": customer_id,
            "approval": approval,
            "interest_rate": interest_rate,
            "corrected_interest_rate": corrected_interest_rate,
            "tenure": tenure,
            "monthly_installment": round(monthly_installment, 2)
        }

        if not approval and reason:
            response["reason"] = reason
        elif not approval:
            response["reason"] = "Credit score too low"

        return JsonResponse(response, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def create_loan(request):
    """Create a new loan based on eligibility check"""
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


        
        # Create a mock request for the eligibility check
        factory = RequestFactory()
        eligibility_request = factory.post('/check-eligibility/', 
                                         json.dumps(data), 
                                         content_type='application/json')
        
        # Call check_eligibility function directly
        eligibility_response = check_eligibility(eligibility_request)
        eligibility_data = json.loads(eligibility_response.content)
        
        # Handle non-200 responses from eligibility check
        if eligibility_response.status_code != 200:
            return eligibility_response

        # Check if loan is approved
        if not eligibility_data.get("approval", False):
            # Map reason to appropriate message
            reason = eligibility_data.get("reason", "")
            if "Overutilized credit limit" in reason:
                message = "Loan not approved due to overutilized credit limit"
            elif "EMI burden" in reason:
                message = "Loan not approved due to existing EMI burden exceeding 50% of salary"
            else:
                message = "Loan not approved due to low credit score"
            
            return JsonResponse({
                "loan_id": None,
                "customer_id": customer_id,
                "loan_approved": False,
                "message": message,
                "monthly_installment": 0.0
            }, status=200)

        # --- Create Loan if Approved ---
        # Get customer instance
        customer = Customer.objects.get(customer_id=customer_id)
        
        corrected_interest_rate = eligibility_data["corrected_interest_rate"]
        monthly_installment = eligibility_data["monthly_installment"]
        loan_amount = float(loan_amount)
        tenure = int(tenure)
        
        # Calculate loan dates
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        start_date = date.today()
        end_date = start_date + relativedelta(months=tenure)
        
        # Create the loan
        loan = Loan.objects.create(
            customer=customer,
            loan_amount=loan_amount,
            tenure=tenure,
            interest_rate=corrected_interest_rate,  # Use corrected rate
            monthly_repayment=round(monthly_installment, 2),
            emis_paid_on_time=0,  # New loan, no EMIs paid yet
            start_date=start_date,
            end_date=end_date
        )
        
        # Update customer's current debt
        customer.current_debt += int(loan_amount)
        customer.save()
        
        return JsonResponse({
            "loan_id": loan.loan_id,
            "customer_id": customer_id,
            "loan_approved": True,
            "message": "Loan approved and created successfully",
            "monthly_installment": round(monthly_installment, 2)
        }, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def view_loan(request, loan_id):
    """
    View loan details and customer details for a specific loan ID
    """
    try:
        # Get the loan by ID
        loan = Loan.objects.select_related('customer').get(loan_id=loan_id)
        
        # Prepare response data
        response_data = {
            "loan_id": loan.loan_id,
            "customer": {
                "id": loan.customer.customer_id,
                "first_name": loan.customer.first_name,
                "last_name": loan.customer.last_name,
                "phone_number": loan.customer.phone_number,
                "age": loan.customer.age
            },
            "loan_amount": loan.loan_amount,
            "interest_rate": loan.interest_rate,
            "monthly_installment": loan.monthly_repayment,
            "tenure": loan.tenure
        }
        
        return JsonResponse(response_data, status=200)
        
    except Loan.DoesNotExist:
        return JsonResponse({"error": "Loan not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)