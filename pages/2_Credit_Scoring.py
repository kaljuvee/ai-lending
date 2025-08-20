import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import sqlite3
from datetime import datetime
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_utils import AILendingAssistant
from database import LendingDatabase

# Page configuration
st.set_page_config(
    page_title="Credit Scoring - AI Lending Platform",
    page_icon="📈",
    layout="wide"
)

# Initialize AI assistant and database
@st.cache_resource
def init_ai_assistant():
    return AILendingAssistant()

@st.cache_resource
def init_database():
    return LendingDatabase()

ai_assistant = init_ai_assistant()
db = init_database()

st.title("📈 Credit Scoring & Underwriting")
st.markdown("AI-powered credit assessment and bank statement analysis")

# Customer selection
conn = db.connect()
cursor = conn.cursor()
cursor.execute("SELECT id, first_name, last_name, company_name, email FROM customers")
customers = cursor.fetchall()

customer_options = {}
for customer in customers:
    name = customer[3] if customer[3] else f"{customer[1]} {customer[2]}"
    customer_options[f"{name} ({customer[4]})"] = customer[0]

selected_customer = st.selectbox("Select Customer:", list(customer_options.keys()))
customer_id = customer_options[selected_customer]

# Get customer data
customer_data = ai_assistant.get_customer_data(customer_id)

if customer_data:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Customer Information")
        customer_info = customer_data['customer']
        st.write(f"**Name:** {customer_info.get('first_name', '')} {customer_info.get('last_name', '')}")
        if customer_info.get('company_name'):
            st.write(f"**Company:** {customer_info['company_name']}")
        st.write(f"**Email:** {customer_info['email']}")
        st.write(f"**Type:** {customer_info['customer_type'].title()}")
        st.write(f"**Country:** {customer_info['country']}")
    
    with col2:
        st.subheader("Credit Score")
        if customer_data['credit_score']:
            score = customer_data['credit_score']['score']
            st.metric("Current Score", score)
            
            # Score gauge
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Credit Score"},
                gauge = {
                    'axis': {'range': [300, 850]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [300, 580], 'color': "lightgray"},
                        {'range': [580, 670], 'color': "yellow"},
                        {'range': [670, 740], 'color': "lightgreen"},
                        {'range': [740, 850], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 700
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            # Credit factors
            if customer_data['credit_score']['factors']:
                factors = json.loads(customer_data['credit_score']['factors'])
                st.subheader("Credit Score Factors")
                factors_df = pd.DataFrame([
                    {"Factor": k.replace('_', ' ').title(), "Value": v}
                    for k, v in factors.items()
                ])
                st.dataframe(factors_df, use_container_width=True)
        else:
            st.info("No credit score available for this customer")
    
    # Bank statement analysis
    st.markdown("---")
    st.subheader("Bank Statement Analysis")
    if customer_data['bank_statement']:
        bank_data = customer_data['bank_statement']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Monthly Income", f"€{bank_data['monthly_income']:,.2f}")
        with col2:
            st.metric("Monthly Expenses", f"€{bank_data['monthly_expenses']:,.2f}")
        with col3:
            st.metric("Current Balance", f"€{bank_data['balance']:,.2f}")
        
        # Financial health chart
        income_expense_data = pd.DataFrame({
            'Category': ['Income', 'Expenses'],
            'Amount': [bank_data['monthly_income'], bank_data['monthly_expenses']]
        })
        
        fig_bar = px.bar(
            income_expense_data, 
            x='Category', 
            y='Amount',
            title="Monthly Income vs Expenses",
            color='Category',
            color_discrete_map={'Income': 'green', 'Expenses': 'red'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # AI Analysis
        if st.button("Generate AI Analysis", type="primary"):
            with st.spinner("Analyzing bank statement..."):
                analysis = ai_assistant.analyze_bank_statement(bank_data)
                st.subheader("AI Analysis Results")
                st.write(analysis)
        
        # Risk indicators
        if bank_data['risk_indicators']:
            risk_data = json.loads(bank_data['risk_indicators'])
            st.subheader("Risk Indicators")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Overdrafts", risk_data.get('overdrafts', 0))
                st.metric("Returned Payments", risk_data.get('returned_payments', 0))
            
            with col2:
                gambling = "Yes" if risk_data.get('gambling_transactions') else "No"
                irregular = "Yes" if risk_data.get('irregular_income') else "No"
                st.metric("Gambling Transactions", gambling)
                st.metric("Irregular Income", irregular)
            
            # Risk score calculation
            risk_score = (
                risk_data.get('overdrafts', 0) * 2 +
                risk_data.get('returned_payments', 0) * 3 +
                (5 if risk_data.get('gambling_transactions') else 0) +
                (3 if risk_data.get('irregular_income') else 0)
            )
            
            if risk_score <= 5:
                st.success(f"Low Risk Score: {risk_score}")
            elif risk_score <= 10:
                st.warning(f"Medium Risk Score: {risk_score}")
            else:
                st.error(f"High Risk Score: {risk_score}")
    else:
        st.info("No bank statement data available for this customer")

# Credit scoring overview
st.markdown("---")
st.subheader("Credit Scoring Overview")

cursor.execute("""
    SELECT c.first_name, c.last_name, c.company_name, cs.score, cs.score_date
    FROM credit_scores cs
    JOIN customers c ON cs.customer_id = c.id
    ORDER BY cs.score_date DESC
""")
all_scores = cursor.fetchall()

if all_scores:
    df_scores = pd.DataFrame(all_scores, columns=[
        'First Name', 'Last Name', 'Company', 'Score', 'Date'
    ])
    df_scores['Customer'] = df_scores.apply(
        lambda x: x['Company'] if pd.notna(x['Company']) else f"{x['First Name']} {x['Last Name']}", axis=1
    )
    
    # Score distribution chart
    fig_hist = px.histogram(
        df_scores, 
        x='Score', 
        nbins=20,
        title="Credit Score Distribution",
        labels={'Score': 'Credit Score', 'count': 'Number of Customers'}
    )
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Scores table
    display_df = df_scores[['Customer', 'Score', 'Date']]
    st.dataframe(display_df, use_container_width=True)

db.close()

# Sidebar information
with st.sidebar:
    st.markdown("### Credit Score Ranges")
    st.info(
        """
        **Excellent:** 740-850
        - Best interest rates
        - Premium products
        
        **Good:** 670-739
        - Competitive rates
        - Most products available
        
        **Fair:** 580-669
        - Higher interest rates
        - Limited options
        
        **Poor:** 300-579
        - Highest rates
        - Secured products only
        """
    )
    
    st.markdown("### Risk Factors")
    st.warning(
        """
        - Payment history (35%)
        - Credit utilization (30%)
        - Length of credit (15%)
        - Credit mix (10%)
        - New credit (10%)
        """
    )

