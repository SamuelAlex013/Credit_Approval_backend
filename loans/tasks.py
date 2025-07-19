from celery import shared_task
import pandas as pd
from django.conf import settings
from django.db import transaction
from collections import defaultdict
from .models import Customer, Loan


@shared_task
def ingest_customer_data(file_path):
    try:
        df = pd.read_excel(file_path)

        customer_ids = df['Customer ID'].tolist()
        existing_customers = Customer.objects.filter(customer_id__in=customer_ids)
        existing_dict = {cust.customer_id: cust for cust in existing_customers}

        customers_to_create = []
        customers_to_update = []

        for _, row in df.iterrows():
            customer_id = row['Customer ID']
            data = {
                'first_name': row['First Name'],
                'last_name': row['Last Name'],
                'age': row['Age'],
                'phone_number': str(row['Phone Number']),
                'monthly_salary': row['Monthly Salary'],
                'approved_limit': row['Approved Limit'],
            }
            if customer_id in existing_dict:
                cust = existing_dict[customer_id]
                for field, value in data.items():
                    setattr(cust, field, value)
                customers_to_update.append(cust)
            else:
                customers_to_create.append(Customer(customer_id=customer_id, current_debt=0, **data))

        if customers_to_update:
            Customer.objects.bulk_update(
                customers_to_update,
                fields=[
                    'first_name', 'last_name', 'age', 'phone_number',
                    'monthly_salary', 'approved_limit'
                ]
            )

        if customers_to_create:
            Customer.objects.bulk_create(customers_to_create)

        return "Customer data ingested successfully."
    except Exception as e:
        return f"Error ingesting customer data: {str(e)}"


@shared_task
def ingest_loan_data(file_path):
    try:
        with transaction.atomic():
            df = pd.read_excel(file_path)
            df['Loan ID'] = pd.to_numeric(df['Loan ID'], errors='coerce').fillna(0).astype(int)
            df = df[df['Loan ID'] > 0]
            df = df.drop_duplicates(subset=['Loan ID'])

            loan_ids = df['Loan ID'].tolist()
            customer_ids = df['Customer ID'].unique()

            # Delete existing loans
            deleted_count = Loan.objects.filter(loan_id__in=loan_ids).delete()[0]
            print(f"Deleted {deleted_count} loans")

            # Fetch customers
            customers = Customer.objects.filter(customer_id__in=customer_ids)
            customer_dict = {cust.customer_id: cust for cust in customers}

            # Prepare loans and debt updates
            loan_list = []
            customer_debts = defaultdict(int)

            for _, row in df.iterrows():
                customer_id = row['Customer ID']
                customer = customer_dict.get(customer_id)
                if not customer:
                    continue

                # Calculate remaining debt
                emis_paid = int(row['EMIs paid on Time'])
                monthly_payment = int(row['Monthly payment'])
                total_tenure = int(row['Tenure'])
                remaining_debt = max(0, (total_tenure - emis_paid) * monthly_payment)

                loan_list.append(
                    Loan(
                        loan_id=row['Loan ID'],
                        loan_amount=row['Loan Amount'],
                        tenure=row['Tenure'],
                        interest_rate=row['Interest Rate'],
                        monthly_repayment=monthly_payment,
                        emis_paid_on_time=emis_paid,
                        start_date=pd.to_datetime(row['Date of Approval']).date(),
                        end_date=pd.to_datetime(row['End Date']).date(),
                        customer=customer
                    )
                )
                customer_debts[customer_id] += remaining_debt

            # Bulk create loans
            Loan.objects.bulk_create(loan_list)

            # Update customer debt
            customers_to_update = []
            for customer_id, debt in customer_debts.items():
                customer = customer_dict[customer_id]
                customer.current_debt = debt
                customers_to_update.append(customer)

            Customer.objects.bulk_update(customers_to_update, ['current_debt'])

            return {
                "status": "success",
                "deleted": deleted_count,
                "created_loans": len(loan_list),
                "updated_customers": len(customers_to_update)
            }

    except Exception as e:
        return f"Error ingesting loan data: {str(e)}"