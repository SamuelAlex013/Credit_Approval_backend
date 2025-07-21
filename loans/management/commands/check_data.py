from django.core.management.base import BaseCommand
from loans.models import Customer, Loan


class Command(BaseCommand):
    help = 'Check database status and record counts'

    def handle(self, *args, **options):
        try:
            customer_count = Customer.objects.count()
            loan_count = Loan.objects.count()
            
            self.stdout.write(f'Database Status:')
            self.stdout.write(f'  Customers: {customer_count}')
            self.stdout.write(f'  Loans: {loan_count}')
            
            if customer_count > 0:
                # Show some sample customer data
                sample_customers = Customer.objects.all()[:3]
                self.stdout.write('\nSample Customers:')
                for customer in sample_customers:
                    self.stdout.write(
                        f'  ID: {customer.customer_id}, '
                        f'Name: {customer.first_name} {customer.last_name}, '
                        f'Debt: {customer.current_debt}'
                    )
            
            if loan_count > 0:
                # Show some sample loan data
                sample_loans = Loan.objects.select_related('customer').all()[:3]
                self.stdout.write('\nSample Loans:')
                for loan in sample_loans:
                    self.stdout.write(
                        f'  Loan ID: {loan.loan_id}, '
                        f'Customer: {loan.customer.first_name} {loan.customer.last_name}, '
                        f'Amount: {loan.loan_amount}'
                    )
            
            if customer_count == 0 and loan_count == 0:
                self.stdout.write(
                    self.style.WARNING('No data found. Run "python manage.py load_excel_data" to load data.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Database contains data!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error checking database: {str(e)}')
            )
