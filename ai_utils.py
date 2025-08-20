import openai
import os
from dotenv import load_dotenv
import json
import sqlite3
from datetime import datetime
import pandas as pd

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

class AILendingAssistant:
    def __init__(self, db_path="lending.db"):
        self.db_path = db_path
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def kyc_kyb_chat(self, message, customer_type="individual", conversation_history=None):
        """Handle KYC/KYB chat interactions"""
        if conversation_history is None:
            conversation_history = []
        
        system_prompt = f"""
        You are a KYC/KYB (Know Your Customer/Know Your Business) specialist for a European lending institution.
        You are helping with {'individual customer' if customer_type == 'individual' else 'business'} onboarding.
        
        For individual customers (KYC), collect:
        - Full name, date of birth, nationality
        - Address and contact information
        - Identity document details (passport, ID card)
        - Employment information and income
        - Source of funds
        
        For business customers (KYB), collect:
        - Company name and registration details
        - Business address and contact information
        - Ownership structure and beneficial owners
        - Business activities and revenue
        - Financial statements
        
        Be professional, compliant with EU regulations (GDPR, AML directives), and guide the customer through the process step by step.
        Ask one question at a time and explain why each piece of information is needed.
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"I apologize, but I'm experiencing technical difficulties. Please try again later. Error: {str(e)}"
    
    def analyze_bank_statement(self, statement_data):
        """Analyze bank statement for credit assessment"""
        system_prompt = """
        You are a credit analyst specializing in bank statement analysis for lending decisions.
        Analyze the provided bank statement data and provide insights on:
        
        1. Income stability and regularity
        2. Expense patterns and financial discipline
        3. Risk indicators (overdrafts, returned payments, gambling)
        4. Cash flow trends
        5. Overall creditworthiness assessment
        
        Provide a structured analysis with risk score (1-10, where 1 is lowest risk) and recommendations.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this bank statement data: {json.dumps(statement_data, indent=2)}"}
                ],
                temperature=0.3,
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error analyzing bank statement: {str(e)}"
    
    def generate_marketing_content(self, campaign_type, target_audience, channel, custom_prompt=""):
        """Generate marketing content using AI"""
        system_prompt = f"""
        You are a marketing specialist for a European lending institution.
        Create compelling marketing content for {campaign_type} targeting {target_audience} for {channel} channel.
        
        Guidelines:
        - Comply with EU financial advertising regulations
        - Be clear about terms and conditions
        - Focus on benefits and value proposition
        - Use appropriate tone for the target audience
        - Include call-to-action
        
        {custom_prompt}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate marketing content for {campaign_type}"}
                ],
                temperature=0.8,
                max_tokens=600
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating marketing content: {str(e)}"
    
    def customer_service_chat(self, customer_message, customer_context=None):
        """Handle customer service inquiries"""
        system_prompt = """
        You are a helpful customer service representative for a European lending institution.
        Provide professional, empathetic, and accurate responses to customer inquiries.
        
        Common topics include:
        - Loan applications and status
        - Payment schedules and modifications
        - Interest rates and terms
        - Account access issues
        - General banking questions
        
        Always be polite, helpful, and if you cannot resolve an issue, offer to escalate to a human representative.
        Comply with GDPR and banking regulations.
        """
        
        context_info = ""
        if customer_context:
            context_info = f"Customer context: {json.dumps(customer_context, indent=2)}"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{context_info}\n\nCustomer message: {customer_message}"}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"I apologize for the technical issue. Please contact our support team directly. Error: {str(e)}"
    
    def generate_collection_email(self, customer_data, collection_stage, outstanding_amount, days_overdue):
        """Generate collection emails based on stage and customer data"""
        stage_prompts = {
            "early": "Generate a friendly reminder email for early-stage collections (15-30 days overdue)",
            "mid": "Generate a more formal collection email for mid-stage collections (31-60 days overdue)",
            "late": "Generate a firm but professional collection email for late-stage collections (60+ days overdue)",
            "legal": "Generate a final notice email before legal action for severely overdue accounts"
        }
        
        system_prompt = f"""
        You are a collections specialist for a European lending institution.
        {stage_prompts.get(collection_stage, "Generate a collection email")}
        
        Guidelines:
        - Be professional and respectful
        - Comply with EU debt collection regulations
        - Offer payment plan options when appropriate
        - Include clear next steps and contact information
        - Maintain empathetic tone while being firm about obligations
        
        Customer details: {json.dumps(customer_data, indent=2)}
        Outstanding amount: €{outstanding_amount}
        Days overdue: {days_overdue}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate a {collection_stage} stage collection email"}
                ],
                temperature=0.6,
                max_tokens=600
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating collection email: {str(e)}"
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of customer messages"""
        system_prompt = """
        Analyze the sentiment of the following text and return a score between -1 (very negative) and 1 (very positive).
        Also provide a brief explanation of the sentiment.
        Return the response as JSON with 'score' and 'explanation' fields.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            return {"score": 0.0, "explanation": f"Error analyzing sentiment: {str(e)}"}
    
    def get_customer_data(self, customer_id):
        """Retrieve customer data for AI context"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Get customer basic info
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            return None
        
        # Get additional data
        cursor.execute("SELECT * FROM kyc_kyb_data WHERE customer_id = ?", (customer_id,))
        kyc_data = cursor.fetchall()
        
        cursor.execute("SELECT * FROM credit_scores WHERE customer_id = ? ORDER BY score_date DESC LIMIT 1", (customer_id,))
        credit_score = cursor.fetchone()
        
        cursor.execute("SELECT * FROM bank_statements WHERE customer_id = ? ORDER BY statement_date DESC LIMIT 1", (customer_id,))
        bank_statement = cursor.fetchone()
        
        conn.close()
        
        return {
            "customer": dict(customer),
            "kyc_data": [dict(row) for row in kyc_data],
            "credit_score": dict(credit_score) if credit_score else None,
            "bank_statement": dict(bank_statement) if bank_statement else None
        }

