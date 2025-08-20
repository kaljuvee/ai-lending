import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import sqlite3
from datetime import datetime, timedelta
import os
from utils.ai_utils import AILendingAssistant
from utils.database import LendingDatabase

# Page configuration
st.set_page_config(
    page_title="AI Lending Platform - Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
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

# Main dashboard content
st.title("🏦 AI Lending Platform Dashboard")
st.markdown("Welcome to the AI-powered lending platform. Navigate through different modules using the sidebar.")

# Get database connection and summary data
conn = db.connect()
cursor = conn.cursor()

# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]
    st.metric("Total Customers", total_customers)

with col2:
    cursor.execute("SELECT COUNT(*) FROM kyc_kyb_data WHERE verification_status = 'approved'")
    approved_kyc = cursor.fetchone()[0]
    st.metric("Approved KYC/KYB", approved_kyc)

with col3:
    cursor.execute("SELECT AVG(score) FROM credit_scores")
    avg_score = cursor.fetchone()[0]
    st.metric("Avg Credit Score", f"{avg_score:.0f}" if avg_score else "N/A")

with col4:
    cursor.execute("SELECT SUM(outstanding_amount) FROM collections")
    total_collections = cursor.fetchone()[0]
    st.metric("Total Collections", f"€{total_collections:,.0f}" if total_collections else "€0")

st.markdown("---")

# Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("Customer Distribution")
    cursor.execute("SELECT customer_type, COUNT(*) as count FROM customers GROUP BY customer_type")
    customer_data = cursor.fetchall()
    df_customers = pd.DataFrame(customer_data, columns=['Type', 'Count'])
    
    fig_pie = px.pie(df_customers, values='Count', names='Type', title="Individual vs Business Customers")
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.subheader("KYC/KYB Status")
    cursor.execute("SELECT verification_status, COUNT(*) as count FROM kyc_kyb_data GROUP BY verification_status")
    kyc_data = cursor.fetchall()
    df_kyc = pd.DataFrame(kyc_data, columns=['Status', 'Count'])
    
    fig_bar = px.bar(df_kyc, x='Status', y='Count', title="Verification Status Distribution")
    st.plotly_chart(fig_bar, use_container_width=True)

# Collections heatmap
st.subheader("Collections Risk Heatmap")
cursor.execute("""
    SELECT c.first_name, c.last_name, c.company_name, col.outstanding_amount, col.days_overdue, col.collection_stage
    FROM collections col
    JOIN customers c ON col.customer_id = c.id
""")
collections_data = cursor.fetchall()

if collections_data:
    df_collections = pd.DataFrame(collections_data, columns=[
        'First Name', 'Last Name', 'Company', 'Outstanding', 'Days Overdue', 'Stage'
    ])
    df_collections['Customer'] = df_collections.apply(
        lambda x: x['Company'] if pd.notna(x['Company']) else f"{x['First Name']} {x['Last Name']}", axis=1
    )
    
    # Create risk score based on days overdue and amount
    df_collections['Risk Score'] = (df_collections['Days Overdue'] / 30) * (df_collections['Outstanding'] / 1000)
    
    fig_heatmap = px.density_heatmap(
        df_collections, 
        x='Days Overdue', 
        y='Outstanding',
        title="Collections Risk Heatmap (Days Overdue vs Outstanding Amount)"
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Collections table
    st.subheader("Collections Summary Table")
    display_df = df_collections[['Customer', 'Outstanding', 'Days Overdue', 'Stage']].copy()
    display_df['Outstanding'] = display_df['Outstanding'].apply(lambda x: f"€{x:,.2f}")
    st.dataframe(display_df, use_container_width=True)

# Recent activity
st.markdown("---")
st.subheader("Recent Activity")

col1, col2 = st.columns(2)

with col1:
    st.write("**Latest Customer Verifications**")
    cursor.execute("""
        SELECT c.first_name, c.last_name, k.verification_status, k.created_at
        FROM kyc_kyb_data k
        JOIN customers c ON k.customer_id = c.id
        ORDER BY k.created_at DESC
        LIMIT 5
    """)
    recent_kyc = cursor.fetchall()
    
    if recent_kyc:
        for row in recent_kyc:
            name = f"{row[0]} {row[1]}"
            status = row[2]
            date = row[3]
            
            if status == 'approved':
                st.success(f"✅ {name} - {status}")
            elif status == 'pending':
                st.warning(f"⏳ {name} - {status}")
            else:
                st.error(f"❌ {name} - {status}")

with col2:
    st.write("**Recent Customer Service Interactions**")
    cursor.execute("""
        SELECT c.first_name, c.last_name, cs.subject, cs.sentiment_score
        FROM customer_service cs
        JOIN customers c ON cs.customer_id = c.id
        ORDER BY cs.created_at DESC
        LIMIT 5
    """)
    recent_service = cursor.fetchall()
    
    if recent_service:
        for row in recent_service:
            name = f"{row[0]} {row[1]}"
            subject = row[2]
            sentiment = row[3]
            
            if sentiment and sentiment > 0.5:
                st.success(f"😊 {name} - {subject}")
            elif sentiment and sentiment < -0.5:
                st.error(f"😞 {name} - {subject}")
            else:
                st.info(f"😐 {name} - {subject}")

# System status
st.markdown("---")
st.subheader("System Status")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.success("🟢 Database: Online")
with col2:
    st.success("🟢 AI Services: Active")
with col3:
    st.success("🟢 API: Operational")
with col4:
    st.info("🔵 Last Update: " + datetime.now().strftime("%H:%M"))

db.close()

# Sidebar information
with st.sidebar:
    st.markdown("### Navigation")
    st.info(
        """
        Use the pages in the sidebar to navigate to different modules:
        
        📊 **Dashboard** - Overview and metrics
        👤 **Onboarding** - KYC/KYB verification
        📈 **Credit Scoring** - Risk assessment
        📢 **Marketing** - Campaign generation
        💬 **Customer Service** - AI support
        💰 **Collections** - Debt management
        """
    )
    
    st.markdown("### About")
    st.info(
        "This AI-powered lending platform demonstrates various use cases for consumer lending, "
        "including KYC/KYB verification, credit scoring, marketing automation, customer service, and collections."
    )
    
    st.markdown("### Quick Stats")
    
    # Create new connection for sidebar stats
    sidebar_conn = db.connect()
    sidebar_cursor = sidebar_conn.cursor()
    
    # Quick stats
    sidebar_cursor.execute("SELECT COUNT(*) FROM customers WHERE customer_type = 'individual'")
    individual_count = sidebar_cursor.fetchone()[0]
    
    sidebar_cursor.execute("SELECT COUNT(*) FROM customers WHERE customer_type = 'business'")
    business_count = sidebar_cursor.fetchone()[0]
    
    sidebar_cursor.execute("SELECT COUNT(*) FROM marketing_campaigns WHERE status = 'active'")
    active_campaigns = sidebar_cursor.fetchone()[0]
    
    st.metric("Individual Customers", individual_count)
    st.metric("Business Customers", business_count)
    st.metric("Active Campaigns", active_campaigns)
    
    sidebar_conn.close()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>AI Lending Platform - Demonstrating AI use cases in consumer lending</p>
        <p>Built with Streamlit, OpenAI, and SQLite</p>
    </div>
    """, 
    unsafe_allow_html=True
)

