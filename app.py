import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import sqlite3
from datetime import datetime, timedelta
import os
from ai_utils import AILendingAssistant
from database import LendingDatabase

# Page configuration
st.set_page_config(
    page_title="AI Lending Platform",
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

# Sidebar navigation
st.sidebar.title("🏦 AI Lending Platform")
st.sidebar.markdown("---")

pages = {
    "Dashboard": "📊",
    "KYC/KYB Onboarding": "👤",
    "Credit Scoring": "📈",
    "Marketing": "📢",
    "Customer Service": "💬",
    "Collections": "💰"
}

selected_page = st.sidebar.selectbox(
    "Navigate to:",
    list(pages.keys()),
    format_func=lambda x: f"{pages[x]} {x}"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    "This AI-powered lending platform demonstrates various use cases for consumer lending, "
    "including KYC/KYB verification, credit scoring, marketing automation, customer service, and collections."
)

# Main content area
if selected_page == "Dashboard":
    st.title("📊 AI Lending Platform Dashboard")
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
    
    db.close()

elif selected_page == "KYC/KYB Onboarding":
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

elif selected_page == "Credit Scoring":
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
                st.plotly_chart(fig_gauge, use_container_width=True)
            else:
                st.info("No credit score available for this customer")
        
        # Bank statement analysis
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
            
            # AI Analysis
            if st.button("Generate AI Analysis"):
                with st.spinner("Analyzing bank statement..."):
                    analysis = ai_assistant.analyze_bank_statement(bank_data)
                    st.subheader("AI Analysis Results")
                    st.write(analysis)
            
            # Risk indicators
            if bank_data['risk_indicators']:
                risk_data = json.loads(bank_data['risk_indicators'])
                st.subheader("Risk Indicators")
                
                risk_df = pd.DataFrame([
                    {"Indicator": "Overdrafts", "Value": risk_data.get('overdrafts', 0)},
                    {"Indicator": "Returned Payments", "Value": risk_data.get('returned_payments', 0)},
                    {"Indicator": "Gambling Transactions", "Value": "Yes" if risk_data.get('gambling_transactions') else "No"},
                    {"Indicator": "Irregular Income", "Value": "Yes" if risk_data.get('irregular_income') else "No"}
                ])
                st.dataframe(risk_df, use_container_width=True)
        else:
            st.info("No bank statement data available for this customer")
    
    db.close()

elif selected_page == "Marketing":
    st.title("📢 AI Marketing Content Generator")
    st.markdown("Generate targeted marketing content for different channels and audiences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        campaign_type = st.selectbox("Campaign Type:", [
            "Personal Loans",
            "Business Loans", 
            "Mortgages",
            "Credit Cards",
            "Investment Products"
        ])
        
        target_audience = st.selectbox("Target Audience:", [
            "Young professionals (25-35)",
            "Small business owners",
            "First-time home buyers",
            "High-income individuals",
            "Students",
            "Retirees"
        ])
    
    with col2:
        channel = st.selectbox("Marketing Channel:", [
            "email",
            "social_media", 
            "web",
            "sms"
        ])
        
        custom_prompt = st.text_area("Additional Instructions (optional):", 
                                   placeholder="Any specific requirements or tone preferences...")
    
    if st.button("Generate Marketing Content"):
        with st.spinner("Generating content..."):
            content = ai_assistant.generate_marketing_content(
                campaign_type, target_audience, channel, custom_prompt
            )
            
            st.subheader("Generated Marketing Content")
            st.write(content)
            
            # Save to database option
            if st.button("Save to Campaign Database"):
                conn = db.connect()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO marketing_campaigns 
                    (campaign_name, target_audience, channel, content, ai_generated_content, start_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"{campaign_type} - {target_audience}",
                    target_audience,
                    channel,
                    "AI Generated Content",
                    content,
                    datetime.now().date(),
                    "draft"
                ))
                conn.commit()
                db.close()
                st.success("Campaign saved to database!")
    
    # Display existing campaigns
    st.subheader("Existing Marketing Campaigns")
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT campaign_name, target_audience, channel, status, start_date FROM marketing_campaigns ORDER BY created_at DESC")
    campaigns = cursor.fetchall()
    
    if campaigns:
        campaigns_df = pd.DataFrame(campaigns, columns=['Campaign', 'Audience', 'Channel', 'Status', 'Start Date'])
        st.dataframe(campaigns_df, use_container_width=True)
    
    db.close()

elif selected_page == "Customer Service":
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
    
    selected_customer = st.selectbox("Customer Context (optional):", list(customer_options.keys()))
    customer_id = customer_options[selected_customer]
    
    # Initialize chat history
    if "service_chat_history" not in st.session_state:
        st.session_state.service_chat_history = []
    
    # Display chat history
    for message in st.session_state.service_chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
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
        
        # Add assistant response to chat history
        st.session_state.service_chat_history.append({"role": "assistant", "content": response})
        
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
    
    # Clear chat button
    if st.button("Clear Chat History"):
        st.session_state.service_chat_history = []
        st.rerun()
    
    # Recent service interactions
    st.subheader("Recent Customer Service Interactions")
    cursor.execute("""
        SELECT c.first_name, c.last_name, c.company_name, cs.subject, cs.sentiment_score, cs.resolution_status, cs.created_at
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
        display_df = interactions_df[['Customer', 'Subject', 'Sentiment', 'Status', 'Date']]
        st.dataframe(display_df, use_container_width=True)
    
    db.close()

elif selected_page == "Collections":
    st.title("💰 AI Collections Management")
    st.markdown("Automated collection email generation and management")
    
    # Get collections data
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT col.id, c.first_name, c.last_name, c.company_name, c.email,
               col.outstanding_amount, col.days_overdue, col.collection_stage
        FROM collections col
        JOIN customers c ON col.customer_id = c.id
        ORDER BY col.days_overdue DESC
    """)
    collections = cursor.fetchall()
    
    if collections:
        # Collections overview
        st.subheader("Collections Overview")
        
        collections_df = pd.DataFrame(collections, columns=[
            'ID', 'First Name', 'Last Name', 'Company', 'Email', 'Outstanding', 'Days Overdue', 'Stage'
        ])
        collections_df['Customer'] = collections_df.apply(
            lambda x: x['Company'] if pd.notna(x['Company']) else f"{x['First Name']} {x['Last Name']}", axis=1
        )
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Outstanding", f"€{collections_df['Outstanding'].sum():,.2f}")
        with col2:
            st.metric("Average Days Overdue", f"{collections_df['Days Overdue'].mean():.0f}")
        with col3:
            st.metric("Accounts in Collections", len(collections_df))
        with col4:
            high_risk = len(collections_df[collections_df['Days Overdue'] > 60])
            st.metric("High Risk Accounts", high_risk)
        
        # Collections by stage chart
        stage_counts = collections_df['Stage'].value_counts()
        fig_stages = px.bar(
            x=stage_counts.index, 
            y=stage_counts.values,
            title="Collections by Stage",
            labels={'x': 'Collection Stage', 'y': 'Number of Accounts'}
        )
        st.plotly_chart(fig_stages, use_container_width=True)
        
        # Email generation
        st.subheader("Generate Collection Email")
        
        # Select customer for email generation
        customer_options = {}
        for _, row in collections_df.iterrows():
            customer_options[f"{row['Customer']} - €{row['Outstanding']:,.2f} ({row['Days Overdue']} days)"] = row['ID']
        
        selected_collection = st.selectbox("Select Account:", list(customer_options.keys()))
        collection_id = customer_options[selected_collection]
        
        # Get selected collection details
        selected_row = collections_df[collections_df['ID'] == collection_id].iloc[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Customer:** {selected_row['Customer']}")
            st.write(f"**Outstanding:** €{selected_row['Outstanding']:,.2f}")
        with col2:
            st.write(f"**Days Overdue:** {selected_row['Days Overdue']}")
            st.write(f"**Current Stage:** {selected_row['Stage'].title()}")
        
        if st.button("Generate Collection Email"):
            with st.spinner("Generating personalized collection email..."):
                customer_data = {
                    "name": selected_row['Customer'],
                    "email": selected_row['Email']
                }
                
                email_content = ai_assistant.generate_collection_email(
                    customer_data,
                    selected_row['Stage'],
                    selected_row['Outstanding'],
                    selected_row['Days Overdue']
                )
                
                st.subheader("Generated Collection Email")
                st.text_area("Email Content:", email_content, height=300)
                
                # Update database with generated email
                cursor.execute("""
                    UPDATE collections 
                    SET ai_generated_email = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (email_content, collection_id))
                conn.commit()
                
                st.success("Email generated and saved to database!")
        
        # Collections table
        st.subheader("Collections Details Table")
        display_df = collections_df[['Customer', 'Outstanding', 'Days Overdue', 'Stage']].copy()
        display_df['Outstanding'] = display_df['Outstanding'].apply(lambda x: f"€{x:,.2f}")
        st.dataframe(display_df, use_container_width=True)
    
    else:
        st.info("No accounts currently in collections.")
    
    db.close()

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

