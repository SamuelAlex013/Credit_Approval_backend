from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, datetime
import json
from .models import Customer, Loan
from .helper import calculate_credit_score


class CustomerModelTest(TestCase):
    """Test cases for Customer model"""
    
    def setUp(self):
        self.customer_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'age': 30,
            'phone_number': '1234567890',
            'monthly_salary': 50000,
            'approved_limit': 1800000,
            'current_debt': 0
        }
    
    def test_customer_creation(self):
        """Test customer creation with valid data"""
        customer = Customer.objects.create(**self.customer_data)
        self.assertEqual(customer.first_name, 'John')
        self.assertEqual(customer.last_name, 'Doe')
        self.assertEqual(customer.age, 30)
        self.assertEqual(customer.monthly_salary, 50000)
        self.assertEqual(customer.approved_limit, 1800000)
        self.assertEqual(customer.current_debt, 0)
    
    def test_customer_str_representation(self):
        """Test customer string representation"""
        customer = Customer.objects.create(**self.customer_data)
        self.assertEqual(str(customer), "John Doe")
    
    def test_customer_id_auto_increment(self):
        """Test that customer_id is auto-incremented"""
        customer1 = Customer.objects.create(**self.customer_data)
        customer2_data = self.customer_data.copy()
        customer2_data['phone_number'] = '9876543210'
        customer2 = Customer.objects.create(**customer2_data)
        
        self.assertEqual(customer2.customer_id, customer1.customer_id + 1)


class LoanModelTest(TestCase):
    """Test cases for Loan model"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name='Jane',
            last_name='Smith',
            age=25,
            phone_number='1112223333',
            monthly_salary=60000,
            approved_limit=2160000,
            current_debt=0
        )
        
        self.loan_data = {
            'customer': self.customer,
            'loan_amount': 100000.0,
            'tenure': 12,
            'interest_rate': 10.5,
            'monthly_repayment': 8500.0,
            'emis_paid_on_time': 8,
            'start_date': date(2024, 1, 1),
            'end_date': date(2024, 12, 31)
        }
    
    def test_loan_creation(self):
        """Test loan creation with valid data"""
        loan = Loan.objects.create(**self.loan_data)
        self.assertEqual(loan.customer, self.customer)
        self.assertEqual(loan.loan_amount, 100000.0)
        self.assertEqual(loan.tenure, 12)
        self.assertEqual(loan.interest_rate, 10.5)
        self.assertEqual(loan.monthly_repayment, 8500.0)
        self.assertEqual(loan.emis_paid_on_time, 8)
    
    def test_loan_str_representation(self):
        """Test loan string representation"""
        loan = Loan.objects.create(**self.loan_data)
        expected_str = f"Loan {loan.loan_id} - Customer {self.customer.customer_id}"
        self.assertEqual(str(loan), expected_str)
    
    def test_loan_foreign_key_relationship(self):
        """Test loan-customer foreign key relationship"""
        loan = Loan.objects.create(**self.loan_data)
        self.assertEqual(loan.customer.first_name, 'Jane')
        self.assertEqual(loan.customer.last_name, 'Smith')


class CreditScoreHelperTest(TestCase):
    """Test cases for credit score calculation helper function"""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name='Test',
            last_name='User',
            age=28,
            phone_number='5555555555',
            monthly_salary=80000,
            approved_limit=2880000,
            current_debt=500000
        )
    
    def test_overutilization_returns_zero(self):
        """Test that overutilization returns credit score of 0"""
        self.customer.current_debt = 3000000  # More than approved limit
        self.customer.save()
        
        loans = []
        score = calculate_credit_score(self.customer, loans)
        self.assertEqual(score, 0)
    
    def test_new_customer_returns_fifty(self):
        """Test that new customer with no loans returns score of 50"""
        loans = []
        score = calculate_credit_score(self.customer, loans)
        self.assertEqual(score, 50)
    
    def test_credit_score_calculation_with_loans(self):
        """Test credit score calculation with existing loans"""
        # Create test loans
        loan1 = Loan.objects.create(
            customer=self.customer,
            loan_amount=200000,
            tenure=12,
            interest_rate=12.0,
            monthly_repayment=18000,
            emis_paid_on_time=10,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        
        loan2 = Loan.objects.create(
            customer=self.customer,
            loan_amount=150000,
            tenure=6,
            interest_rate=15.0,
            monthly_repayment=26000,
            emis_paid_on_time=6,
            start_date=date(2023, 6, 1),
            end_date=date(2023, 11, 30)
        )
        
        loans = [loan1, loan2]
        score = calculate_credit_score(self.customer, loans)
        
        # Score should be between 0 and 100
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        self.assertIsInstance(score, float)
    
    def test_perfect_payment_history(self):
        """Test credit score with perfect payment history"""
        loan = Loan.objects.create(
            customer=self.customer,
            loan_amount=100000,
            tenure=12,
            interest_rate=10.0,
            monthly_repayment=9000,
            emis_paid_on_time=12,  # All EMIs paid on time
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        
        loans = [loan]
        score = calculate_credit_score(self.customer, loans)
        
        # Should have a high score due to perfect payment history
        self.assertGreater(score, 70)


class RegisterCustomerViewTest(TestCase):
    """Test cases for register customer view"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('register')
        self.valid_data = {
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'age': 32,
            'monthly_income': 75000,
            'phone_number': '9998887777'
        }
    
    def test_register_customer_success(self):
        """Test successful customer registration"""
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        
        self.assertIn('customer_id', response_data)
        self.assertEqual(response_data['name'], 'Alice Johnson')
        self.assertEqual(response_data['age'], 32)
        self.assertEqual(response_data['monthly_income'], 75000)
        self.assertEqual(response_data['approved_limit'], 2700000)  # 36 * 75000
        self.assertEqual(response_data['phone_number'], '9998887777')
    
    def test_register_customer_missing_fields(self):
        """Test registration with missing required fields"""
        incomplete_data = {
            'first_name': 'Bob',
            'age': 25
            # Missing last_name, monthly_income, phone_number
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_register_customer_invalid_json(self):
        """Test registration with invalid JSON"""
        response = self.client.post(
            self.url,
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_approved_limit_calculation(self):
        """Test approved limit calculation and rounding"""
        test_data = self.valid_data.copy()
        test_data['monthly_income'] = 73000  # Should round to nearest lakh
        
        response = self.client.post(
            self.url,
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        
        # 36 * 73000 = 2628000, rounded to nearest lakh = 2600000
        self.assertEqual(response_data['approved_limit'], 2600000)


class CheckEligibilityViewTest(TestCase):
    """Test cases for check eligibility view"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('check_eligibility')
        self.customer = Customer.objects.create(
            first_name='Charlie',
            last_name='Brown',
            age=35,
            phone_number='1234567890',
            monthly_salary=100000,
            approved_limit=3600000,
            current_debt=0
        )
        
        self.valid_request = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 500000,
            'interest_rate': 10.0,
            'tenure': 24
        }
    
    def test_check_eligibility_success_high_score(self):
        """Test eligibility check for customer with high credit score"""
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_request),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertEqual(response_data['customer_id'], self.customer.customer_id)
        self.assertTrue(response_data['approval'])  # New customer should be approved
        self.assertIn('monthly_installment', response_data)
        self.assertGreater(response_data['monthly_installment'], 0)
    
    def test_check_eligibility_customer_not_found(self):
        """Test eligibility check for non-existent customer"""
        invalid_request = self.valid_request.copy()
        invalid_request['customer_id'] = 99999
        
        response = self.client.post(
            self.url,
            data=json.dumps(invalid_request),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Customer not found')
    
    def test_check_eligibility_missing_fields(self):
        """Test eligibility check with missing required fields"""
        incomplete_request = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 500000
            # Missing interest_rate and tenure
        }
        
        response = self.client.post(
            self.url,
            data=json.dumps(incomplete_request),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Missing required fields')
    
    def test_check_eligibility_overutilized_credit(self):
        """Test eligibility check for overutilized customer"""
        self.customer.current_debt = 4000000  # More than approved limit
        self.customer.save()
        
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_request),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertFalse(response_data['approval'])
        self.assertEqual(response_data['reason'], 'Overutilized credit limit')
        self.assertEqual(response_data['monthly_installment'], 0.0)
    
    def test_check_eligibility_high_emi_burden(self):
        """Test eligibility check for customer with high existing EMI burden"""
        # Create existing loan with high monthly repayment
        Loan.objects.create(
            customer=self.customer,
            loan_amount=2000000,
            tenure=36,
            interest_rate=12.0,
            monthly_repayment=60000,  # 60% of 100000 salary
            emis_paid_on_time=12,
            start_date=date(2024, 1, 1),
            end_date=date(2026, 12, 31)
        )
        
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_request),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertFalse(response_data['approval'])
        self.assertEqual(response_data['reason'], 'Existing EMI burden exceeds 50% of salary')
    
    def test_interest_rate_correction_medium_score(self):
        """Test interest rate correction for medium credit score"""
        # Create multiple loan history for medium credit score (30-50)
        # Loan 1: Poor payment history
        Loan.objects.create(
            customer=self.customer,
            loan_amount=1000000,
            tenure=24,
            interest_rate=10.0,
            monthly_repayment=45000,
            emis_paid_on_time=12,  # 50% payment rate
            start_date=date(2023, 1, 1),
            end_date=date(2024, 12, 31)
        )
        
        # Loan 2: Another loan with poor payment
        Loan.objects.create(
            customer=self.customer,
            loan_amount=500000,
            tenure=12,
            interest_rate=12.0,
            monthly_repayment=45000,
            emis_paid_on_time=4,  # 33% payment rate
            start_date=date(2022, 1, 1),
            end_date=date(2022, 12, 31)
        )
        
        # High debt utilization for lower score
        self.customer.current_debt = 3000000  # ~83% of approved limit
        self.customer.save()
        
        low_rate_request = self.valid_request.copy()
        low_rate_request['interest_rate'] = 8.0  # Below 12%
        
        response = self.client.post(
            self.url,
            data=json.dumps(low_rate_request),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Should correct interest rate to 12% for medium score
        self.assertEqual(response_data['corrected_interest_rate'], 12.0)


class IntegrationTest(TestCase):
    """Integration tests for the complete workflow"""
    
    def test_complete_loan_application_workflow(self):
        """Test complete workflow from customer registration to loan eligibility"""
        client = Client()
        
        # Step 1: Register customer
        register_data = {
            'first_name': 'Integration',
            'last_name': 'Test',
            'age': 30,
            'monthly_income': 80000,
            'phone_number': '9999999999'
        }
        
        register_response = client.post(
            reverse('register'),
            data=json.dumps(register_data),
            content_type='application/json'
        )
        
        self.assertEqual(register_response.status_code, 201)
        customer_data = json.loads(register_response.content)
        customer_id = customer_data['customer_id']
        
        # Step 2: Check loan eligibility
        eligibility_data = {
            'customer_id': customer_id,
            'loan_amount': 1000000,
            'interest_rate': 10.0,
            'tenure': 36
        }
        
        eligibility_response = client.post(
            reverse('check_eligibility'),
            data=json.dumps(eligibility_data),
            content_type='application/json'
        )
        
        self.assertEqual(eligibility_response.status_code, 200)
        eligibility_result = json.loads(eligibility_response.content)
        
        # New customer should be approved with credit score of 50
        self.assertTrue(eligibility_result['approval'])
        self.assertGreater(eligibility_result['monthly_installment'], 0)
        self.assertEqual(eligibility_result['customer_id'], customer_id)
    
    def test_workflow_with_existing_loans(self):
        """Test workflow with customer having existing loan history"""
        # Create customer with loan history
        customer = Customer.objects.create(
            first_name='Existing',
            last_name='Customer',
            age=40,
            phone_number='8888888888',
            monthly_salary=120000,
            approved_limit=4320000,
            current_debt=800000
        )
        
        # Add existing loan
        Loan.objects.create(
            customer=customer,
            loan_amount=800000,
            tenure=36,
            interest_rate=11.0,
            monthly_repayment=25000,
            emis_paid_on_time=30,  # Good payment history
            start_date=date(2022, 1, 1),
            end_date=date(2024, 12, 31)
        )
        
        client = Client()
        eligibility_data = {
            'customer_id': customer.customer_id,
            'loan_amount': 500000,
            'interest_rate': 9.0,
            'tenure': 24
        }
        
        response = client.post(
            reverse('check_eligibility'),
            data=json.dumps(eligibility_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        
        # Should be approved due to good payment history
        self.assertTrue(result['approval'])
        self.assertGreater(result['monthly_installment'], 0)
