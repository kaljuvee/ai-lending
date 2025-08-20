import streamlit as st
import pandas as pd
import plotly.express as px
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
    page_title="Customer Service - AI Lending Platform",
    page_icon="💬",
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

st.title("💬 AI Customer Service Chat")
st.markdown("Intelligent customer support with context-aware responses")

# Customer selection for context
conn = db.connect()
cursor = conn.cursor()
cursor.execute("SELECT id, first_name, last_name, company_name, email FROM customers")
customers = cursor.fetchall()

customer_options = {"No specific customer": None}
for customer in customers:
    name = customer[3] if customer[3] else f"{customer[1]} {customer[2]}"
    customer_options[f"{name} ({customer[4]})"] = customer[0]

col1, col2 = st.columns([2, 1])

with col1:
    selected_customer = st.selectbox("Customer Context (optional):", list(customer_options.keys()))
    customer_id = customer_options[selected_customer]

with col2:
    if customer_id:
        st.success("✅ Customer context loaded")
    else:
        st.info("ℹ️ General support mode")

# Initialize chat history
if "service_chat_history" not in st.session_state:
    st.session_state.service_chat_history = []

# Chat interface
st.subheader("Customer Support Chat")

# Display chat history
for message in st.session_state.service_chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "sentiment" in message:
            if message["sentiment"] < -0.5:
                st.error("⚠️ Negative sentiment detected")
            elif message["sentiment"] > 0.5:
                st.success("😊 Positive sentiment")

# Chat input
if prompt := st.chat_input("How can I help you today?"):
    # Add user message to chat history
    st.session_state.service_chat_history.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get customer context if selected
    customer_context = None
    if customer_id:
        customer_context = ai_assistant.get_customer_data(customer_id)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Processing your request..."):
            response = ai_assistant.customer_service_chat(prompt, customer_context)
            st.write(response)
            
            # Analyze sentiment
            sentiment = ai_assistant.analyze_sentiment(prompt)
            if sentiment['score'] < -0.5:
                st.warning("⚠️ Negative sentiment detected. Consider escalating to human agent.")
                st.write(f"Sentiment analysis: {sentiment['explanation']}")
    
    # Add assistant response to chat history with sentiment
    st.session_state.service_chat_history.append({
        "role": "assistant", 
        "content": response,
        "sentiment": sentiment['score']
    })
    
    # Save interaction to database
    if customer_id:
        cursor.execute("""
            INSERT INTO customer_service 
            (customer_id, interaction_type, subject, message, ai_response, sentiment_score, resolution_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            "chat",
            "General Inquiry",
            prompt,
            response,
            sentiment['score'],
            "resolved"
        ))
        conn.commit()

# Chat controls
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Clear Chat History"):
        st.session_state.service_chat_history = []
        st.rerun()

with col2:
    if st.button("Escalate to Human Agent"):
        st.warning("🔄 Escalating to human agent...")
        st.info("A human agent will be with you shortly.")

with col3:
    if st.button("End Conversation"):
        st.success("✅ Conversation ended. Thank you for contacting us!")

# Customer service analytics
st.markdown("---")
st.subheader("Customer Service Analytics")

# Service metrics
cursor.execute("SELECT COUNT(*) FROM customer_service")
total_interactions = cursor.fetchone()[0]

cursor.execute("SELECT AVG(sentiment_score) FROM customer_service WHERE sentiment_score IS NOT NULL")
avg_sentiment = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM customer_service WHERE resolution_status = 'resolved'")
resolved_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(DISTINCT customer_id) FROM customer_service")
unique_customers = cursor.fetchone()[0]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Interactions", total_interactions)
with col2:
    st.metric("Avg Sentiment", f"{avg_sentiment:.2f}" if avg_sentiment else "N/A")
with col3:
    resolution_rate = (resolved_count / total_interactions * 100) if total_interactions > 0 else 0
    st.metric("Resolution Rate", f"{resolution_rate:.1f}%")
with col4:
    st.metric("Unique Customers", unique_customers)

# Sentiment analysis chart
cursor.execute("""
    SELECT 
        CASE 
            WHEN sentiment_score >= 0.5 THEN 'Positive'
            WHEN sentiment_score <= -0.5 THEN 'Negative'
            ELSE 'Neutral'
        END as sentiment_category,
        COUNT(*) as count
    FROM customer_service 
    WHERE sentiment_score IS NOT NULL
    GROUP BY sentiment_category
""")
sentiment_data = cursor.fetchall()

if sentiment_data:
    df_sentiment = pd.DataFrame(sentiment_data, columns=['Sentiment', 'Count'])
    fig_sentiment = px.pie(
        df_sentiment, 
        values='Count', 
        names='Sentiment',
        title="Customer Sentiment Distribution",
        color_discrete_map={
            'Positive': 'green',
            'Neutral': 'yellow', 
            'Negative': 'red'
        }
    )
    st.plotly_chart(fig_sentiment, use_container_width=True)

# Recent interactions table
st.subheader("Recent Customer Service Interactions")
cursor.execute("""
    SELECT c.first_name, c.last_name, c.company_name, cs.subject, 
           cs.sentiment_score, cs.resolution_status, cs.created_at
    FROM customer_service cs
    JOIN customers c ON cs.customer_id = c.id
    ORDER BY cs.created_at DESC
    LIMIT 10
""")
interactions = cursor.fetchall()

if interactions:
    interactions_df = pd.DataFrame(interactions, columns=[
        'First Name', 'Last Name', 'Company', 'Subject', 'Sentiment', 'Status', 'Date'
    ])
    interactions_df['Customer'] = interactions_df.apply(
        lambda x: x['Company'] if pd.notna(x['Company']) else f"{x['First Name']} {x['Last Name']}", axis=1
    )
    
    # Color code sentiment
    def sentiment_color(val):
        if val >= 0.5:
            return 'background-color: lightgreen'
        elif val <= -0.5:
            return 'background-color: lightcoral'
        else:
            return 'background-color: lightyellow'
    
    display_df = interactions_df[['Customer', 'Subject', 'Sentiment', 'Status', 'Date']]
    styled_df = display_df.style.applymap(sentiment_color, subset=['Sentiment'])
    st.dataframe(styled_df, use_container_width=True)

# Common issues and responses
st.markdown("---")
st.subheader("Common Issues & Quick Responses")

common_issues = {
    "Loan Application Status": "Your loan application is currently under review. You can expect a decision within 2-3 business days.",
    "Payment Schedule": "You can modify your payment schedule by logging into your account or contacting our support team.",
    "Interest Rates": "Our current interest rates vary based on loan type and creditworthiness. Personal loans start at 4.9% APR.",
    "Account Access": "If you're having trouble accessing your account, try resetting your password or contact our technical support.",
    "Document Upload": "You can upload required documents through your online account or email them to documents@ailending.com"
}

for issue, response in common_issues.items():
    with st.expander(f"❓ {issue}"):
        st.write(response)
        if st.button(f"Use this response", key=f"use_{issue}"):
            st.session_state.service_chat_history.append({
                "role": "assistant", 
                "content": response,
                "sentiment": 0.5
            })
            st.success("Response added to chat!")

db.close()

# Sidebar information
with st.sidebar:
    st.markdown("### Support Categories")
    st.info(
        """
        **Account Management:**
        - Login issues
        - Password reset
        - Profile updates
        
        **Loan Services:**
        - Application status
        - Payment schedules
        - Interest rates
        
        **Technical Support:**
        - Website issues
        - Mobile app help
        - Document upload
        
        **General Inquiries:**
        - Product information
        - Terms & conditions
        - Contact details
        """
    )
    
    st.markdown("### Escalation Triggers")
    st.warning(
        """
        🚨 **Auto-escalate when:**
        - Sentiment score < -0.7
        - Complaint keywords detected
        - Multiple failed attempts
        - Customer requests human agent
        """
    )
    
    st.markdown("### Performance Targets")
    st.success(
        """
        🎯 **KPIs:**
        - Response time: < 30 seconds
        - Resolution rate: > 85%
        - Customer satisfaction: > 4.0/5
        - First contact resolution: > 70%
        """
    )

