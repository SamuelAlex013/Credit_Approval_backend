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


class CreateLoanViewTest(TestCase):
    """Test cases for create loan view"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('create_loan')
        self.customer = Customer.objects.create(
            first_name='Loan',
            last_name='Applicant',
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
    
    def test_create_loan_success(self):
        """Test successful loan creation for eligible customer"""
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_request),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        
        self.assertIsNotNone(response_data['loan_id'])
        self.assertEqual(response_data['customer_id'], self.customer.customer_id)
        self.assertTrue(response_data['loan_approved'])
        self.assertEqual(response_data['message'], 'Loan approved and created successfully')
        self.assertGreater(response_data['monthly_installment'], 0)
        
        # Verify loan was created in database
        loan = Loan.objects.get(loan_id=response_data['loan_id'])
        self.assertEqual(loan.customer, self.customer)
        self.assertEqual(loan.loan_amount, 500000)
        self.assertEqual(loan.tenure, 24)
        # New customer has credit score = 50, which falls in condition 30 < score <= 50
        # So interest rate gets corrected to 12% if original rate < 12%
        self.assertEqual(loan.interest_rate, 12.0)  
        
        # Verify customer debt was updated
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.current_debt, 500000)
    
    def test_create_loan_customer_not_found(self):
        """Test loan creation for non-existent customer"""
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
    
    def test_create_loan_overutilized_customer(self):
        """Test loan creation for overutilized customer"""
        self.customer.current_debt = 4000000  # More than approved limit
        self.customer.save()
        
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_request),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertIsNone(response_data['loan_id'])
        self.assertFalse(response_data['loan_approved'])
        self.assertEqual(response_data['message'], 'Loan not approved due to overutilized credit limit')
        self.assertEqual(response_data['monthly_installment'], 0.0)
        
        # Verify no loan was created
        self.assertEqual(Loan.objects.count(), 0)
    
    def test_create_loan_high_emi_burden(self):
        """Test loan creation for customer with high EMI burden"""
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
        
        self.assertIsNone(response_data['loan_id'])
        self.assertFalse(response_data['loan_approved'])
        self.assertEqual(response_data['message'], 'Loan not approved due to existing EMI burden exceeding 50% of salary')
        
        # Verify only the existing loan exists (no new loan created)
        self.assertEqual(Loan.objects.count(), 1)
    
    def test_create_loan_interest_rate_correction(self):
        """Test loan creation with interest rate correction for medium credit score"""
        # Create loan history to get credit score in 30-50 range
        # Keep EMI burden under 50% to avoid rejection
        Loan.objects.create(
            customer=self.customer,
            loan_amount=1000000,
            tenure=24,
            interest_rate=10.0,
            monthly_repayment=20000,  # 20% of salary
            emis_paid_on_time=8,  # 33% payment rate - poor
            start_date=date(2023, 1, 1),
            end_date=date(2024, 12, 31)
        )
        
        # Create second loan with poor payment
        Loan.objects.create(
            customer=self.customer,
            loan_amount=500000,
            tenure=12,
            interest_rate=12.0,
            monthly_repayment=20000,  # Total EMI: 40% of salary - within limit
            emis_paid_on_time=3,  # 25% payment rate - poor
            start_date=date(2022, 1, 1),
            end_date=date(2022, 12, 31)
        )
        
        # Higher debt utilization to reduce score further
        self.customer.current_debt = 3200000  # ~89% of approved limit
        self.customer.save()
        
        low_rate_request = self.valid_request.copy()
        low_rate_request['interest_rate'] = 8.0  # Below 12%
        
        response = self.client.post(
            self.url,
            data=json.dumps(low_rate_request),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        
        self.assertTrue(response_data['loan_approved'])
        self.assertIsNotNone(response_data['loan_id'])
        
        # Verify loan was created with corrected interest rate
        loan = Loan.objects.get(loan_id=response_data['loan_id'])
        self.assertEqual(loan.interest_rate, 12.0)  # Corrected to 12%
    
    def test_create_loan_missing_fields(self):
        """Test loan creation with missing required fields"""
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
    
    def test_create_loan_low_credit_score(self):
        """Test loan creation for customer with very low credit score <= 10"""
        # To get credit score <= 10, we need to minimize all components:
        # 1. Payment history: 0% (0 points)
        # 2. Loan count: 15+ loans (0 points) 
        # 3. Recent activity: Many recent loans (0 points)
        # 4. Volume ratio: Near 100% utilization (near 0 points)
        
        # Create 20 loans with 0% payment history, many in current year
        current_year = date.today().year
        for i in range(20):
            Loan.objects.create(
                customer=self.customer,
                loan_amount=50000,
                tenure=12,
                interest_rate=16.0,
                monthly_repayment=2000,  # Total EMI will be 40000 (40% of salary)
                emis_paid_on_time=0,  # 0% payment rate
                start_date=date(current_year, 1, 1),  # All in current year for penalty
                end_date=date(current_year, 12, 31)
            )
        
        # Maximum debt utilization (99.9% of limit) to minimize volume score
        self.customer.current_debt = 3596400  # 99.9% of 3600000
        self.customer.save()
        
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_request),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        self.assertIsNone(response_data['loan_id'])
        self.assertFalse(response_data['loan_approved'])
        self.assertEqual(response_data['message'], 'Loan not approved due to low credit score')
        
        # Verify only existing loans exist (no new loan created)
        self.assertEqual(Loan.objects.count(), 20)


class ViewLoanViewTest(TestCase):
    """Test cases for view loan view"""
    
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            first_name='John',
            last_name='Doe',
            age=30,
            phone_number='1234567890',
            monthly_salary=100000,
            approved_limit=3600000,
            current_debt=500000
        )
        
        self.loan = Loan.objects.create(
            customer=self.customer,
            loan_amount=500000,
            tenure=24,
            interest_rate=12.0,
            monthly_repayment=25000,
            emis_paid_on_time=12,
            start_date=date(2024, 1, 1),
            end_date=date(2025, 12, 31)
        )
        
        self.url = reverse('view_loan', kwargs={'loan_id': self.loan.loan_id})
    
    def test_view_loan_success(self):
        """Test successful loan detail retrieval"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Check loan details
        self.assertEqual(response_data['loan_id'], self.loan.loan_id)
        self.assertEqual(response_data['loan_amount'], 500000.0)
        self.assertEqual(response_data['interest_rate'], 12.0)
        self.assertEqual(response_data['monthly_installment'], 25000.0)
        self.assertEqual(response_data['tenure'], 24)
        
        # Check customer details in response
        customer_data = response_data['customer']
        self.assertEqual(customer_data['id'], self.customer.customer_id)
        self.assertEqual(customer_data['first_name'], 'John')
        self.assertEqual(customer_data['last_name'], 'Doe')
        self.assertEqual(customer_data['phone_number'], '1234567890')
        self.assertEqual(customer_data['age'], 30)
    
    def test_view_loan_not_found(self):
        """Test loan detail retrieval for non-existent loan"""
        non_existent_url = reverse('view_loan', kwargs={'loan_id': 99999})
        response = self.client.get(non_existent_url)
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Loan not found')
    
    def test_view_loan_invalid_loan_id(self):
        """Test loan detail retrieval with invalid loan ID format"""
        # This should be handled by Django's URL pattern validation
        # but we can test with a string that doesn't match int pattern
        invalid_url = '/view-loan/invalid_id/'
        response = self.client.get(invalid_url)
        
        # Should return 404 as URL pattern won't match
        self.assertEqual(response.status_code, 404)
    
    def test_view_loan_response_structure(self):
        """Test that the response contains all required fields"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Check all required fields are present
        required_fields = ['loan_id', 'customer', 'loan_amount', 'interest_rate', 'monthly_installment', 'tenure']
        for field in required_fields:
            self.assertIn(field, response_data)
        
        # Check customer object has required fields
        customer_required_fields = ['id', 'first_name', 'last_name', 'phone_number', 'age']
        customer_data = response_data['customer']
        for field in customer_required_fields:
            self.assertIn(field, customer_data)
    
    def test_view_loan_multiple_loans_same_customer(self):
        """Test viewing specific loan when customer has multiple loans"""
        # Create another loan for the same customer
        loan2 = Loan.objects.create(
            customer=self.customer,
            loan_amount=300000,
            tenure=12,
            interest_rate=10.5,
            monthly_repayment=27000,
            emis_paid_on_time=6,
            start_date=date(2023, 6, 1),
            end_date=date(2024, 5, 31)
        )
        
        # Test viewing the first loan
        response1 = self.client.get(self.url)
        self.assertEqual(response1.status_code, 200)
        data1 = json.loads(response1.content)
        self.assertEqual(data1['loan_id'], self.loan.loan_id)
        self.assertEqual(data1['loan_amount'], 500000.0)
        
        # Test viewing the second loan
        url2 = reverse('view_loan', kwargs={'loan_id': loan2.loan_id})
        response2 = self.client.get(url2)
        self.assertEqual(response2.status_code, 200)
        data2 = json.loads(response2.content)
        self.assertEqual(data2['loan_id'], loan2.loan_id)
        self.assertEqual(data2['loan_amount'], 300000.0)
        
        # Both should have the same customer data
        self.assertEqual(data1['customer'], data2['customer'])


class CompleteWorkflowTest(TestCase):
    """Integration test for the complete loan workflow including view_loan"""
    
    def test_complete_workflow_with_view_loan(self):
        """Test complete workflow: register → create_loan → view_loan"""
        client = Client()
        
        # Step 1: Register customer
        register_data = {
            'first_name': 'Complete',
            'last_name': 'Workflow',
            'age': 35,
            'monthly_income': 90000,
            'phone_number': '8888888888'
        }
        
        register_response = client.post(
            reverse('register'),
            data=json.dumps(register_data),
            content_type='application/json'
        )
        
        self.assertEqual(register_response.status_code, 201)
        customer_data = json.loads(register_response.content)
        customer_id = customer_data['customer_id']
        
        # Step 2: Create loan
        loan_data = {
            'customer_id': customer_id,
            'loan_amount': 800000,
            'interest_rate': 11.0,
            'tenure': 36
        }
        
        create_loan_response = client.post(
            reverse('create_loan'),
            data=json.dumps(loan_data),
            content_type='application/json'
        )
        
        self.assertEqual(create_loan_response.status_code, 201)
        loan_response_data = json.loads(create_loan_response.content)
        
        self.assertTrue(loan_response_data['loan_approved'])
        loan_id = loan_response_data['loan_id']
        self.assertIsNotNone(loan_id)
        
        # Step 3: View loan details
        view_loan_response = client.get(reverse('view_loan', kwargs={'loan_id': loan_id}))
        
        self.assertEqual(view_loan_response.status_code, 200)
        view_data = json.loads(view_loan_response.content)
        
        # Verify loan details match what was created
        self.assertEqual(view_data['loan_id'], loan_id)
        self.assertEqual(view_data['loan_amount'], 800000.0)
        self.assertEqual(view_data['tenure'], 36)
        
        # New customer should get corrected interest rate of 12% since credit score = 50
        # which falls in 30 < score <= 50 range and original rate (11%) < 12%
        self.assertEqual(view_data['interest_rate'], 12.0)
        
        # Verify customer details
        customer_info = view_data['customer']
        self.assertEqual(customer_info['id'], customer_id)
        self.assertEqual(customer_info['first_name'], 'Complete')
        self.assertEqual(customer_info['last_name'], 'Workflow')
        self.assertEqual(customer_info['phone_number'], '8888888888')
        self.assertEqual(customer_info['age'], 35)
        
        # Verify monthly installment is present and positive
        self.assertGreater(view_data['monthly_installment'], 0)
    
    def test_complete_workflow_with_view_loans(self):
        """Test complete workflow: register → create_loan → view_loans"""
        client = Client()
        
        # Step 1: Register customer
        register_data = {
            'first_name': 'Multi',
            'last_name': 'Loan',
            'age': 40,
            'monthly_income': 100000,
            'phone_number': '7777777777'
        }
        
        register_response = client.post(
            reverse('register'),
            data=json.dumps(register_data),
            content_type='application/json'
        )
        
        self.assertEqual(register_response.status_code, 201)
        customer_data = json.loads(register_response.content)
        customer_id = customer_data['customer_id']
        
        # Step 2: Create first loan
        loan1_data = {
            'customer_id': customer_id,
            'loan_amount': 400000,
            'interest_rate': 10.0,
            'tenure': 24
        }
        
        create_loan1_response = client.post(
            reverse('create_loan'),
            data=json.dumps(loan1_data),
            content_type='application/json'
        )
        
        self.assertEqual(create_loan1_response.status_code, 201)
        loan1_response_data = json.loads(create_loan1_response.content)
        
        # Step 3: Create second loan
        loan2_data = {
            'customer_id': customer_id,
            'loan_amount': 200000,
            'interest_rate': 11.0,
            'tenure': 12
        }
        
        create_loan2_response = client.post(
            reverse('create_loan'),
            data=json.dumps(loan2_data),
            content_type='application/json'
        )
        
        self.assertEqual(create_loan2_response.status_code, 201)
        loan2_response_data = json.loads(create_loan2_response.content)
        
        # Step 4: View all loans for customer
        view_loans_response = client.get(reverse('view_loans_by_customer', kwargs={'customer_id': customer_id}))
        
        self.assertEqual(view_loans_response.status_code, 200)
        loans_data = json.loads(view_loans_response.content)
        
        # Verify we get both loans
        self.assertIsInstance(loans_data, list)
        self.assertEqual(len(loans_data), 2)
        
        # Verify loan IDs match what was created
        loan_ids = [loan['loan_id'] for loan in loans_data]
        self.assertIn(loan1_response_data['loan_id'], loan_ids)
        self.assertIn(loan2_response_data['loan_id'], loan_ids)
        
        # Verify all fields are present
        for loan in loans_data:
            self.assertIn('loan_id', loan)
            self.assertIn('loan_amount', loan)
            self.assertIn('interest_rate', loan)
            self.assertIn('monthly_installment', loan)
            self.assertIn('repayments_left', loan)
            
            # All new loans should have full tenure as repayments_left
            self.assertGreater(loan['repayments_left'], 0)


class ViewLoansByCustomerViewTest(TestCase):
    """Test cases for view loans by customer view"""
    
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(
            first_name='Jane',
            last_name='Smith',
            age=28,
            phone_number='9876543210',
            monthly_salary=80000,
            approved_limit=2880000,
            current_debt=800000
        )
        
        # Create multiple loans for this customer
        self.loan1 = Loan.objects.create(
            customer=self.customer,
            loan_amount=500000,
            tenure=24,
            interest_rate=12.0,
            monthly_repayment=25000,
            emis_paid_on_time=10,
            start_date=date(2024, 1, 1),
            end_date=date(2025, 12, 31)
        )
        
        self.loan2 = Loan.objects.create(
            customer=self.customer,
            loan_amount=300000,
            tenure=12,
            interest_rate=10.5,
            monthly_repayment=27000,
            emis_paid_on_time=6,
            start_date=date(2023, 6, 1),
            end_date=date(2024, 5, 31)
        )
        
        self.url = reverse('view_loans_by_customer', kwargs={'customer_id': self.customer.customer_id})
    
    def test_view_loans_by_customer_success(self):
        """Test successful retrieval of all loans for a customer"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Should return a list of loans
        self.assertIsInstance(response_data, list)
        self.assertEqual(len(response_data), 2)
        
        # Check loan details (order might vary, so check both loans exist)
        loan_ids = [loan['loan_id'] for loan in response_data]
        self.assertIn(self.loan1.loan_id, loan_ids)
        self.assertIn(self.loan2.loan_id, loan_ids)
        
        # Check structure of first loan item
        loan_item = response_data[0]
        required_fields = ['loan_id', 'loan_amount', 'interest_rate', 'monthly_installment', 'repayments_left']
        for field in required_fields:
            self.assertIn(field, loan_item)
    
    def test_view_loans_by_customer_repayments_calculation(self):
        """Test that repayments_left is calculated correctly"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Find loan1 in response
        loan1_data = next(loan for loan in response_data if loan['loan_id'] == self.loan1.loan_id)
        
        # loan1: tenure=24, emis_paid_on_time=10, so repayments_left = 24-10 = 14
        self.assertEqual(loan1_data['repayments_left'], 14)
        
        # Find loan2 in response
        loan2_data = next(loan for loan in response_data if loan['loan_id'] == self.loan2.loan_id)
        
        # loan2: tenure=12, emis_paid_on_time=6, so repayments_left = 12-6 = 6
        self.assertEqual(loan2_data['repayments_left'], 6)
    
    def test_view_loans_by_customer_not_found(self):
        """Test loans retrieval for non-existent customer"""
        non_existent_url = reverse('view_loans_by_customer', kwargs={'customer_id': 99999})
        response = self.client.get(non_existent_url)
        
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Customer not found')
    
    def test_view_loans_empty_list_for_customer_with_no_loans(self):
        """Test loans retrieval for customer with no loans"""
        # Create customer with no loans
        customer_no_loans = Customer.objects.create(
            first_name='Empty',
            last_name='Loans',
            age=30,
            phone_number='1111111111',
            monthly_salary=50000,
            approved_limit=1800000,
            current_debt=0
        )
        
        url = reverse('view_loans_by_customer', kwargs={'customer_id': customer_no_loans.customer_id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Should return empty list
        self.assertIsInstance(response_data, list)
        self.assertEqual(len(response_data), 0)
    
    def test_view_loans_by_customer_all_fields_present(self):
        """Test that all required fields are present in loan items"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        for loan_item in response_data:
            # Check all required fields according to specification
            self.assertIn('loan_id', loan_item)
            self.assertIn('loan_amount', loan_item)
            self.assertIn('interest_rate', loan_item)
            self.assertIn('monthly_installment', loan_item)
            self.assertIn('repayments_left', loan_item)
            
            # Check data types
            self.assertIsInstance(loan_item['loan_id'], int)
            self.assertIsInstance(loan_item['loan_amount'], (int, float))
            self.assertIsInstance(loan_item['interest_rate'], (int, float))
            self.assertIsInstance(loan_item['monthly_installment'], (int, float))
            self.assertIsInstance(loan_item['repayments_left'], int)
    
    def test_view_loans_by_customer_fully_paid_loan(self):
        """Test repayments_left calculation for fully paid loan"""
        # Create a fully paid loan
        fully_paid_loan = Loan.objects.create(
            customer=self.customer,
            loan_amount=100000,
            tenure=6,
            interest_rate=15.0,
            monthly_repayment=18000,
            emis_paid_on_time=6,  # All EMIs paid
            start_date=date(2023, 1, 1),
            end_date=date(2023, 6, 30)
        )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Find the fully paid loan
        fully_paid_data = next(loan for loan in response_data if loan['loan_id'] == fully_paid_loan.loan_id)
        
        # Should have 0 repayments left
        self.assertEqual(fully_paid_data['repayments_left'], 0)
