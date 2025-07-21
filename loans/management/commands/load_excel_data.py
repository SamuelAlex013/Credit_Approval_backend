from django.core.management.base import BaseCommand
from django.conf import settings
from loans.tasks import ingest_customer_data, ingest_loan_data
import os


class Command(BaseCommand):
    help = 'Load customer and loan data from Excel files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customer-file',
            type=str,
            default='data/customer_data.xlsx',
            help='Path to customer data Excel file'
        )
        parser.add_argument(
            '--loan-file',
            type=str,
            default='data/loan_data.xlsx',
            help='Path to loan data Excel file'
        )

    def handle(self, *args, **options):
        # Get file paths
        customer_file = options['customer_file']
        loan_file = options['loan_file']
        
        # Make paths absolute if they're relative
        if not os.path.isabs(customer_file):
            customer_file = os.path.join(settings.BASE_DIR, customer_file)
        if not os.path.isabs(loan_file):
            loan_file = os.path.join(settings.BASE_DIR, loan_file)
        
        # Check if files exist
        if not os.path.exists(customer_file):
            self.stdout.write(
                self.style.ERROR(f'Customer data file not found: {customer_file}')
            )
            return
        
        if not os.path.exists(loan_file):
            self.stdout.write(
                self.style.ERROR(f'Loan data file not found: {loan_file}')
            )
            return
        
        # Load customer data
        self.stdout.write('Loading customer data...')
        try:
            customer_result = ingest_customer_data(customer_file)
            self.stdout.write(
                self.style.SUCCESS(f'Customer data: {customer_result}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading customer data: {str(e)}')
            )
            return
        
        # Load loan data
        self.stdout.write('Loading loan data...')
        try:
            loan_result = ingest_loan_data(loan_file)
            self.stdout.write(
                self.style.SUCCESS(f'Loan data: {loan_result}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading loan data: {str(e)}')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS('Successfully loaded all data!')
        )
