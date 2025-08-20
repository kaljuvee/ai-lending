import streamlit as st
import pandas as pd
import json
import sqlite3
from datetime import datetime
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ai_utils import AILendingAssistant
from utils.database import LendingDatabase

# Page configuration
st.set_page_config(
    page_title="KYC/KYB Onboarding - AI Lending Platform",
    page_icon="👤",
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

st.title("👤 KYC/KYB Customer Onboarding")
st.markdown("AI-powered customer verification and onboarding process")

# Customer type selection
customer_type = st.selectbox("Select Customer Type:", ["individual", "business"])

# Chat interface
st.subheader(f"{'KYC' if customer_type == 'individual' else 'KYB'} Chat Assistant")

# Initialize chat history
if f"chat_history_{customer_type}" not in st.session_state:
    st.session_state[f"chat_history_{customer_type}"] = []

# Display chat history
for message in st.session_state[f"chat_history_{customer_type}"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input(f"Ask about {customer_type} onboarding requirements..."):
    # Add user message to chat history
    st.session_state[f"chat_history_{customer_type}"].append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            response = ai_assistant.kyc_kyb_chat(
                prompt, 
                customer_type, 
                st.session_state[f"chat_history_{customer_type}"][:-1]
            )
            st.write(response)
    
    # Add assistant response to chat history
    st.session_state[f"chat_history_{customer_type}"].append({"role": "assistant", "content": response})

# Clear chat button
if st.button("Clear Chat History"):
    st.session_state[f"chat_history_{customer_type}"] = []
    st.rerun()

# KYC/KYB Status Overview
st.markdown("---")
st.subheader("Verification Status Overview")

conn = db.connect()
cursor = conn.cursor()

# Get KYC/KYB statistics
cursor.execute("""
    SELECT verification_status, COUNT(*) as count 
    FROM kyc_kyb_data 
    GROUP BY verification_status
""")
status_data = cursor.fetchall()

if status_data:
    col1, col2, col3 = st.columns(3)
    
    status_dict = dict(status_data)
    
    with col1:
        st.metric("Approved", status_dict.get('approved', 0))
    with col2:
        st.metric("Pending", status_dict.get('pending', 0))
    with col3:
        st.metric("Rejected", status_dict.get('rejected', 0))

# Recent verifications table
st.subheader("Recent Verifications")
cursor.execute("""
    SELECT c.first_name, c.last_name, c.company_name, k.verification_type, 
           k.verification_status, k.risk_score, k.created_at
    FROM kyc_kyb_data k
    JOIN customers c ON k.customer_id = c.id
    ORDER BY k.created_at DESC
    LIMIT 10
""")
recent_verifications = cursor.fetchall()

if recent_verifications:
    df_verifications = pd.DataFrame(recent_verifications, columns=[
        'First Name', 'Last Name', 'Company', 'Type', 'Status', 'Risk Score', 'Date'
    ])
    df_verifications['Customer'] = df_verifications.apply(
        lambda x: x['Company'] if pd.notna(x['Company']) else f"{x['First Name']} {x['Last Name']}", axis=1
    )
    display_df = df_verifications[['Customer', 'Type', 'Status', 'Risk Score', 'Date']]
    st.dataframe(display_df, use_container_width=True)

db.close()

# Sidebar information
with st.sidebar:
    st.markdown("### KYC/KYB Information")
    st.info(
        """
        **KYC (Know Your Customer)** for individuals:
        - Identity verification
        - Address confirmation
        - Source of funds
        - Risk assessment
        
        **KYB (Know Your Business)** for companies:
        - Business registration
        - Ownership structure
        - Beneficial owners
        - Business activities
        """
    )
    
    st.markdown("### Compliance")
    st.success("✅ GDPR Compliant")
    st.success("✅ EU AML Directive")
    st.success("✅ PCI DSS Standards")

