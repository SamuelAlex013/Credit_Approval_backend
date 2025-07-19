from celery import shared_task
import pandas as pd
from django.conf import settings
import os
from .models import Customer, Loan

@shared_task
def ingest_customer_data(file_path):
    """
    Reads customer_data.xlsx and stores records in Customer table.
    """
    try:
        df = pd.read_excel(file_path)

        for _, row in df.iterrows():
            Customer.objects.update_or_create(
                customer_id=row['Customer ID'],
                defaults={
                    'first_name': row['First Name'],
                    'last_name': row['Last Name'],
                    'age': row['Age'],
                    'phone_number': str(row['Phone Number']),
                    'monthly_salary': row['Monthly Salary'],
                    'approved_limit': row['Approved Limit'],
                    'current_debt': 0
                }
            )
        return "Customer data ingested successfully."
    except Exception as e:
        return f"Error ingesting customer data: {str(e)}"


@shared_task
def ingest_loan_data(file_path):
    """
    Reads loan_data.xlsx and stores records in Loan table, updating customer's current debt.
    """
    try:
        df = pd.read_excel(file_path)

        for _, row in df.iterrows():
            customer = Customer.objects.filter(customer_id=row['Customer ID']).first()
            if customer:
                # Calculate remaining debt based on EMIs left
                emis_paid = int(row['EMIs paid on Time'])
                monthly_payment = int(row['Monthly payment'])
                total_tenure = int(row['Tenure'])

                remaining_debt = max(0, (total_tenure - emis_paid) * monthly_payment)

                # Create or update loan
                Loan.objects.update_or_create(
                    loan_id=row['Loan ID'],
                    defaults={
                        'loan_amount': row['Loan Amount'],
                        'tenure': row['Tenure'],
                        'interest_rate': row['Interest Rate'],
                        'monthly_repayment': monthly_payment,
                        'emis_paid_on_time': emis_paid,
                        'start_date': pd.to_datetime(row['Date of Approval']).date(),
                        'end_date': pd.to_datetime(row['End Date']).date(),
                        'customer': customer
                    }
                )

                # Update customer's current debt
                customer.current_debt += remaining_debt
                customer.save()

        return "Loan data ingested successfully."
    except Exception as e:
        return f"Error ingesting loan data: {str(e)}"

