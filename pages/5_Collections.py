import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import sqlite3
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ai_utils import AILendingAssistant
from utils.database import LendingDatabase

# Page configuration
st.set_page_config(
    page_title="Collections - AI Lending Platform",
    page_icon="💰",
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

st.title("💰 AI Collections Management")
st.markdown("Automated collection email generation and management")

# Get collections data
conn = db.connect()
cursor = conn.cursor()
cursor.execute("""
    SELECT col.id, c.first_name, c.last_name, c.company_name, c.email,
           col.outstanding_amount, col.days_overdue, col.collection_stage, col.loan_id
    FROM collections col
    JOIN customers c ON col.customer_id = c.id
    ORDER BY col.days_overdue DESC
""")
collections = cursor.fetchall()

if collections:
    # Collections overview
    st.subheader("Collections Overview")
    
    collections_df = pd.DataFrame(collections, columns=[
        'ID', 'First Name', 'Last Name', 'Company', 'Email', 'Outstanding', 'Days Overdue', 'Stage', 'Loan ID'
    ])
    collections_df['Customer'] = collections_df.apply(
        lambda x: x['Company'] if pd.notna(x['Company']) else f"{x['First Name']} {x['Last Name']}", axis=1
    )
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_outstanding = collections_df['Outstanding'].sum()
        st.metric("Total Outstanding", f"€{total_outstanding:,.2f}")
    with col2:
        avg_days_overdue = collections_df['Days Overdue'].mean()
        st.metric("Average Days Overdue", f"{avg_days_overdue:.0f}")
    with col3:
        total_accounts = len(collections_df)
        st.metric("Accounts in Collections", total_accounts)
    with col4:
        high_risk = len(collections_df[collections_df['Days Overdue'] > 60])
        st.metric("High Risk Accounts", high_risk)
    
    # Collections visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Collections by stage
        stage_counts = collections_df['Stage'].value_counts()
        fig_stages = px.bar(
            x=stage_counts.index, 
            y=stage_counts.values,
            title="Collections by Stage",
            labels={'x': 'Collection Stage', 'y': 'Number of Accounts'},
            color=stage_counts.index,
            color_discrete_map={
                'early': 'green',
                'mid': 'yellow',
                'late': 'orange',
                'legal': 'red'
            }
        )
        st.plotly_chart(fig_stages, use_container_width=True)
    
    with col2:
        # Outstanding amount by stage
        stage_amounts = collections_df.groupby('Stage')['Outstanding'].sum()
        fig_amounts = px.pie(
            values=stage_amounts.values,
            names=stage_amounts.index,
            title="Outstanding Amount by Stage"
        )
        st.plotly_chart(fig_amounts, use_container_width=True)
    
    # Collections risk heatmap
    st.subheader("Collections Risk Heatmap")
    fig_heatmap = px.density_heatmap(
        collections_df, 
        x='Days Overdue', 
        y='Outstanding',
        title="Risk Heatmap: Days Overdue vs Outstanding Amount",
        labels={'Outstanding': 'Outstanding Amount (€)', 'Days Overdue': 'Days Overdue'}
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Email generation section
    st.markdown("---")
    st.subheader("Generate Collection Email")
    
    # Select customer for email generation
    customer_options = {}
    for _, row in collections_df.iterrows():
        key = f"{row['Customer']} - €{row['Outstanding']:,.2f} ({row['Days Overdue']} days overdue)"
        customer_options[key] = row['ID']
    
    selected_collection = st.selectbox("Select Account:", list(customer_options.keys()))
    collection_id = customer_options[selected_collection]
    
    # Get selected collection details
    selected_row = collections_df[collections_df['ID'] == collection_id].iloc[0]
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Customer:** {selected_row['Customer']}")
        st.write(f"**Loan ID:** {selected_row['Loan ID']}")
        st.write(f"**Outstanding:** €{selected_row['Outstanding']:,.2f}")
    with col2:
        st.write(f"**Days Overdue:** {selected_row['Days Overdue']}")
        st.write(f"**Current Stage:** {selected_row['Stage'].title()}")
        st.write(f"**Email:** {selected_row['Email']}")
    
    # Email generation options
    col1, col2 = st.columns(2)
    with col1:
        email_tone = st.selectbox("Email Tone:", [
            "Professional",
            "Friendly",
            "Firm",
            "Urgent"
        ])
    
    with col2:
        include_payment_plan = st.checkbox("Include Payment Plan Options", value=True)
    
    if st.button("Generate Collection Email", type="primary"):
        with st.spinner("Generating personalized collection email..."):
            customer_data = {
                "name": selected_row['Customer'],
                "email": selected_row['Email'],
                "loan_id": selected_row['Loan ID']
            }
            
            # Add tone to the prompt
            custom_instructions = f"Use a {email_tone.lower()} tone."
            if include_payment_plan:
                custom_instructions += " Include payment plan options."
            
            email_content = ai_assistant.generate_collection_email(
                customer_data,
                selected_row['Stage'],
                selected_row['Outstanding'],
                selected_row['Days Overdue']
            )
            
            st.subheader("Generated Collection Email")
            
            # Email preview
            with st.container():
                st.markdown("**Subject:** Payment Reminder - Account Update Required")
                st.markdown("**To:** " + selected_row['Email'])
                st.markdown("**From:** collections@ailending.com")
                st.markdown("---")
                st.text_area("Email Content:", email_content, height=300)
            
            # Email actions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Save Email"):
                    cursor.execute("""
                        UPDATE collections 
                        SET ai_generated_email = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    """, (email_content, collection_id))
                    conn.commit()
                    st.success("Email saved to database!")
            
            with col2:
                if st.button("Schedule Send"):
                    st.info("Email scheduled for sending (demo mode)")
            
            with col3:
                if st.button("Send Now"):
                    st.warning("Email sent (demo mode)")
    
    # Collections workflow
    st.markdown("---")
    st.subheader("Collections Workflow")
    
    workflow_stages = {
        "early": {
            "name": "Early Stage (15-30 days)",
            "color": "green",
            "actions": ["Friendly reminder", "Payment plan offer", "Account review"]
        },
        "mid": {
            "name": "Mid Stage (31-60 days)", 
            "color": "yellow",
            "actions": ["Formal notice", "Payment arrangement", "Account restriction"]
        },
        "late": {
            "name": "Late Stage (61-90 days)",
            "color": "orange", 
            "actions": ["Final notice", "Settlement offer", "Pre-legal warning"]
        },
        "legal": {
            "name": "Legal Stage (90+ days)",
            "color": "red",
            "actions": ["Legal notice", "Debt collection agency", "Court proceedings"]
        }
    }
    
    cols = st.columns(4)
    for i, (stage, info) in enumerate(workflow_stages.items()):
        with cols[i]:
            count = len(collections_df[collections_df['Stage'] == stage])
            st.metric(info['name'], count)
            for action in info['actions']:
                st.write(f"• {action}")
    
    # Collections performance metrics
    st.markdown("---")
    st.subheader("Collections Performance")
    
    # Mock performance data
    performance_data = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'Recovery Rate': [65, 68, 72, 70, 75, 78],
        'Average Days to Resolution': [45, 42, 38, 40, 35, 32]
    })
    
    col1, col2 = st.columns(2)
    with col1:
        fig_recovery = px.line(
            performance_data, 
            x='Month', 
            y='Recovery Rate',
            title="Monthly Recovery Rate (%)",
            markers=True
        )
        st.plotly_chart(fig_recovery, use_container_width=True)
    
    with col2:
        fig_resolution = px.bar(
            performance_data,
            x='Month',
            y='Average Days to Resolution', 
            title="Average Days to Resolution"
        )
        st.plotly_chart(fig_resolution, use_container_width=True)
    
    # Collections details table
    st.subheader("Collections Details Table")
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    with col1:
        stage_filter = st.multiselect(
            "Filter by Stage:",
            options=collections_df['Stage'].unique(),
            default=collections_df['Stage'].unique()
        )
    with col2:
        min_amount = st.number_input("Minimum Outstanding Amount:", min_value=0, value=0)
    with col3:
        min_days = st.number_input("Minimum Days Overdue:", min_value=0, value=0)
    
    # Apply filters
    filtered_collections = collections_df[
        (collections_df['Stage'].isin(stage_filter)) &
        (collections_df['Outstanding'] >= min_amount) &
        (collections_df['Days Overdue'] >= min_days)
    ]
    
    # Display filtered table
    display_df = filtered_collections[['Customer', 'Loan ID', 'Outstanding', 'Days Overdue', 'Stage']].copy()
    display_df['Outstanding'] = display_df['Outstanding'].apply(lambda x: f"€{x:,.2f}")
    
    # Color code by risk level
    def risk_color(row):
        if row['Days Overdue'] > 90:
            return ['background-color: #ffcccc'] * len(row)
        elif row['Days Overdue'] > 60:
            return ['background-color: #ffe6cc'] * len(row)
        elif row['Days Overdue'] > 30:
            return ['background-color: #ffffcc'] * len(row)
        else:
            return ['background-color: #ccffcc'] * len(row)
    
    styled_df = display_df.style.apply(risk_color, axis=1)
    st.dataframe(styled_df, use_container_width=True)

else:
    st.info("No accounts currently in collections.")

db.close()

# Sidebar information
with st.sidebar:
    st.markdown("### Collection Stages")
    st.info(
        """
        **Early (15-30 days):**
        - Friendly reminders
        - Payment plan offers
        - Customer outreach
        
        **Mid (31-60 days):**
        - Formal notices
        - Account restrictions
        - Payment arrangements
        
        **Late (61-90 days):**
        - Final notices
        - Settlement offers
        - Pre-legal warnings
        
        **Legal (90+ days):**
        - Legal proceedings
        - Collection agencies
        - Asset recovery
        """
    )
    
    st.markdown("### Best Practices")
    st.success(
        """
        ✅ Maintain professional tone
        ✅ Document all interactions
        ✅ Offer payment solutions
        ✅ Follow regulatory guidelines
        ✅ Escalate appropriately
        """
    )
    
    st.markdown("### Compliance")
    st.warning(
        """
        ⚠️ EU Debt Collection Directive
        ⚠️ GDPR data protection
        ⚠️ Fair debt practices
        ⚠️ Consumer protection laws
        """
    )
    
    st.markdown("### Key Metrics")
    st.metric("Target Recovery Rate", "75%")
    st.metric("Avg Resolution Time", "35 days")
    st.metric("Customer Satisfaction", "3.8/5")

