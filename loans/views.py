from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from loans.models import Customer
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
