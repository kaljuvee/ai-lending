import sqlite3
import os
from datetime import datetime, timedelta
import random
import json

class LendingDatabase:
    def __init__(self, db_path="lending.db"):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """Create all database tables"""
        cursor = self.conn.cursor()
        
        # Customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_type TEXT CHECK(customer_type IN ('individual', 'business')) NOT NULL,
                first_name TEXT,
                last_name TEXT,
                company_name TEXT,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                date_of_birth DATE,
                nationality TEXT,
                address TEXT,
                city TEXT,
                postal_code TEXT,
                country TEXT,
                registration_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # KYC/KYB data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kyc_kyb_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                verification_type TEXT CHECK(verification_type IN ('kyc', 'kyb')) NOT NULL,
                document_type TEXT,
                document_number TEXT,
                verification_status TEXT CHECK(verification_status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
                risk_score REAL,
                verification_notes TEXT,
                verified_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # Credit scores table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                score INTEGER CHECK(score >= 300 AND score <= 850),
                score_date DATE,
                bureau_name TEXT,
                factors TEXT, -- JSON string of factors affecting score
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # Bank statements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bank_statements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                statement_date DATE,
                bank_name TEXT,
                account_type TEXT,
                balance REAL,
                monthly_income REAL,
                monthly_expenses REAL,
                transaction_count INTEGER,
                statement_data TEXT, -- JSON string of detailed transactions
                risk_indicators TEXT, -- JSON string of risk factors
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # Marketing campaigns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marketing_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_name TEXT NOT NULL,
                target_audience TEXT,
                channel TEXT CHECK(channel IN ('email', 'sms', 'social_media', 'web')) NOT NULL,
                content TEXT,
                ai_generated_content TEXT,
                start_date DATE,
                end_date DATE,
                budget REAL,
                status TEXT CHECK(status IN ('draft', 'active', 'paused', 'completed')) DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Customer service interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_service (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                interaction_type TEXT CHECK(interaction_type IN ('chat', 'email', 'phone')) NOT NULL,
                subject TEXT,
                message TEXT,
                ai_response TEXT,
                sentiment_score REAL,
                resolution_status TEXT CHECK(resolution_status IN ('open', 'in_progress', 'resolved', 'closed')) DEFAULT 'open',
                priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'urgent')) DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        # Collections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                loan_id TEXT,
                outstanding_amount REAL,
                days_overdue INTEGER,
                collection_stage TEXT CHECK(collection_stage IN ('early', 'mid', 'late', 'legal')) DEFAULT 'early',
                last_contact_date DATE,
                next_action_date DATE,
                collection_notes TEXT,
                ai_generated_email TEXT,
                payment_plan TEXT, -- JSON string of payment plan details
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        ''')
        
        self.conn.commit()
    
    def populate_demo_data(self):
        """Populate database with European demo data"""
        cursor = self.conn.cursor()
        
        # Demo customers (mix of individuals and businesses)
        customers_data = [
            # Individual customers
            ('individual', 'Hans', 'Mueller', None, 'hans.mueller@email.de', '+49-30-12345678', '1985-03-15', 'German', 'Unter den Linden 1', 'Berlin', '10117', 'Germany', None),
            ('individual', 'Marie', 'Dubois', None, 'marie.dubois@email.fr', '+33-1-23456789', '1990-07-22', 'French', 'Champs-Élysées 100', 'Paris', '75008', 'France', None),
            ('individual', 'Giovanni', 'Rossi', None, 'giovanni.rossi@email.it', '+39-06-12345678', '1982-11-08', 'Italian', 'Via del Corso 50', 'Rome', '00186', 'Italy', None),
            ('individual', 'Anna', 'Kowalski', None, 'anna.kowalski@email.pl', '+48-22-1234567', '1988-05-12', 'Polish', 'Krakowskie Przedmieście 1', 'Warsaw', '00-068', 'Poland', None),
            ('individual', 'Carlos', 'García', None, 'carlos.garcia@email.es', '+34-91-1234567', '1975-09-30', 'Spanish', 'Gran Vía 25', 'Madrid', '28013', 'Spain', None),
            
            # Business customers
            ('business', None, None, 'TechStart GmbH', 'info@techstart.de', '+49-89-87654321', None, 'German', 'Maximilianstraße 10', 'Munich', '80539', 'Germany', 'HRB123456'),
            ('business', None, None, 'Innovation SARL', 'contact@innovation.fr', '+33-1-87654321', None, 'French', 'Boulevard Saint-Germain 200', 'Paris', '75007', 'France', '123456789'),
            ('business', None, None, 'Digital Solutions SRL', 'info@digitalsol.it', '+39-02-87654321', None, 'Italian', 'Corso Buenos Aires 15', 'Milan', '20124', 'Italy', 'MI-987654321'),
        ]
        
        cursor.executemany('''
            INSERT INTO customers (customer_type, first_name, last_name, company_name, email, phone, date_of_birth, nationality, address, city, postal_code, country, registration_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', customers_data)
        
        # Get customer IDs for foreign key references
        cursor.execute("SELECT id FROM customers")
        customer_ids = [row[0] for row in cursor.fetchall()]
        
        # KYC/KYB demo data
        kyc_data = []
        for i, customer_id in enumerate(customer_ids):
            verification_type = 'kyc' if i < 5 else 'kyb'  # First 5 are individuals
            doc_type = 'passport' if verification_type == 'kyc' else 'business_registration'
            status = random.choice(['approved', 'approved', 'pending', 'approved'])  # Mostly approved
            risk_score = random.uniform(0.1, 0.8)
            
            kyc_data.append((customer_id, verification_type, doc_type, f"DOC{customer_id:03d}", status, risk_score, f"Verification notes for customer {customer_id}"))
        
        cursor.executemany('''
            INSERT INTO kyc_kyb_data (customer_id, verification_type, document_type, document_number, verification_status, risk_score, verification_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', kyc_data)
        
        # Credit scores demo data
        credit_data = []
        for customer_id in customer_ids[:5]:  # Only for individual customers
            score = random.randint(650, 800)
            factors = json.dumps({
                "payment_history": random.choice(["excellent", "good", "fair"]),
                "credit_utilization": f"{random.randint(10, 40)}%",
                "length_of_credit": f"{random.randint(5, 15)} years",
                "credit_mix": random.choice(["diverse", "limited", "moderate"])
            })
            credit_data.append((customer_id, score, datetime.now().date(), "SCHUFA", factors))
        
        cursor.executemany('''
            INSERT INTO credit_scores (customer_id, score, score_date, bureau_name, factors)
            VALUES (?, ?, ?, ?, ?)
        ''', credit_data)
        
        # Bank statements demo data
        bank_data = []
        for customer_id in customer_ids:
            balance = random.uniform(5000, 50000)
            income = random.uniform(3000, 8000)
            expenses = random.uniform(2000, 6000)
            transactions = random.randint(50, 200)
            
            statement_data = json.dumps({
                "transactions": [
                    {"date": "2024-01-15", "description": "Salary", "amount": income},
                    {"date": "2024-01-16", "description": "Rent", "amount": -1200},
                    {"date": "2024-01-17", "description": "Groceries", "amount": -150},
                    {"date": "2024-01-18", "description": "Utilities", "amount": -200}
                ]
            })
            
            risk_indicators = json.dumps({
                "overdrafts": random.randint(0, 3),
                "returned_payments": random.randint(0, 2),
                "gambling_transactions": random.choice([True, False]),
                "irregular_income": random.choice([True, False])
            })
            
            bank_data.append((customer_id, datetime.now().date(), "Deutsche Bank", "checking", balance, income, expenses, transactions, statement_data, risk_indicators))
        
        cursor.executemany('''
            INSERT INTO bank_statements (customer_id, statement_date, bank_name, account_type, balance, monthly_income, monthly_expenses, transaction_count, statement_data, risk_indicators)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', bank_data)
        
        # Marketing campaigns demo data
        campaigns_data = [
            ("Personal Loan Spring Campaign", "Young professionals aged 25-35", "email", "Get your personal loan with competitive rates!", "AI-generated: Transform your dreams into reality with our flexible personal loans...", "2024-03-01", "2024-05-31", 50000.0, "active"),
            ("Business Growth Initiative", "SMEs with 2-5 years operation", "web", "Fuel your business growth with our business loans", "AI-generated: Accelerate your business success with tailored financing solutions...", "2024-02-15", "2024-06-15", 75000.0, "active"),
            ("Mortgage Awareness Campaign", "First-time home buyers", "social_media", "Your dream home awaits - competitive mortgage rates", "AI-generated: Step into homeownership with confidence through our comprehensive mortgage solutions...", "2024-01-01", "2024-12-31", 100000.0, "active"),
        ]
        
        cursor.executemany('''
            INSERT INTO marketing_campaigns (campaign_name, target_audience, channel, content, ai_generated_content, start_date, end_date, budget, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', campaigns_data)
        
        # Customer service demo data
        service_data = []
        for i, customer_id in enumerate(customer_ids[:6]):  # Some customers have service interactions
            subjects = ["Loan application inquiry", "Payment schedule question", "Account access issue", "Interest rate information"]
            messages = [
                "I would like to know more about your personal loan options.",
                "Can I modify my payment schedule for my existing loan?",
                "I'm having trouble accessing my online account.",
                "What are your current interest rates for business loans?"
            ]
            
            subject = random.choice(subjects)
            message = random.choice(messages)
            ai_response = f"Thank you for your inquiry about {subject.lower()}. Our team will assist you with this matter."
            sentiment = random.uniform(-0.2, 0.8)  # Mostly positive/neutral
            
            service_data.append((customer_id, "chat", subject, message, ai_response, sentiment, "resolved", "medium"))
        
        cursor.executemany('''
            INSERT INTO customer_service (customer_id, interaction_type, subject, message, ai_response, sentiment_score, resolution_status, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', service_data)
        
        # Collections demo data
        collections_data = []
        for i, customer_id in enumerate(customer_ids[:4]):  # Some customers in collections
            outstanding = random.uniform(1000, 15000)
            days_overdue = random.randint(15, 120)
            stage = "early" if days_overdue < 30 else "mid" if days_overdue < 60 else "late"
            
            payment_plan = json.dumps({
                "monthly_payment": outstanding / 12,
                "duration_months": 12,
                "interest_rate": 0.05,
                "start_date": "2024-02-01"
            })
            
            ai_email = f"Dear Customer, We notice your account has an outstanding balance of €{outstanding:.2f}. Please contact us to discuss payment options."
            
            collections_data.append((customer_id, f"LOAN{customer_id:03d}", outstanding, days_overdue, stage, datetime.now().date(), (datetime.now() + timedelta(days=7)).date(), f"Customer contacted on {datetime.now().date()}", ai_email, payment_plan))
        
        cursor.executemany('''
            INSERT INTO collections (customer_id, loan_id, outstanding_amount, days_overdue, collection_stage, last_contact_date, next_action_date, collection_notes, ai_generated_email, payment_plan)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', collections_data)
        
        self.conn.commit()
    
    def get_customer_summary(self):
        """Get summary statistics for dashboard"""
        cursor = self.conn.cursor()
        
        # Customer counts
        cursor.execute("SELECT customer_type, COUNT(*) FROM customers GROUP BY customer_type")
        customer_counts = dict(cursor.fetchall())
        
        # KYC/KYB status
        cursor.execute("SELECT verification_status, COUNT(*) FROM kyc_kyb_data GROUP BY verification_status")
        kyc_status = dict(cursor.fetchall())
        
        # Collections summary
        cursor.execute("SELECT collection_stage, COUNT(*), AVG(outstanding_amount) FROM collections GROUP BY collection_stage")
        collections_summary = cursor.fetchall()
        
        return {
            "customer_counts": customer_counts,
            "kyc_status": kyc_status,
            "collections_summary": collections_summary
        }

def initialize_database():
    """Initialize the database with schema and demo data"""
    db = LendingDatabase()
    db.connect()
    
    print("Creating database tables...")
    db.create_tables()
    
    print("Populating with demo data...")
    db.populate_demo_data()
    
    print("Database initialized successfully!")
    
    # Print summary
    summary = db.get_customer_summary()
    print(f"\nDatabase Summary:")
    print(f"Customers: {summary['customer_counts']}")
    print(f"KYC/KYB Status: {summary['kyc_status']}")
    print(f"Collections: {len(summary['collections_summary'])} stages")
    
    db.close()
    return True

if __name__ == "__main__":
    initialize_database()

