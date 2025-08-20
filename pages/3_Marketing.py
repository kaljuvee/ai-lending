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
    page_title="Marketing - AI Lending Platform",
    page_icon="📢",
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

st.title("📢 AI Marketing Content Generator")
st.markdown("Generate targeted marketing content for different channels and audiences")

# Content generation form
st.subheader("Generate New Campaign Content")

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

if st.button("Generate Marketing Content", type="primary"):
    with st.spinner("Generating content..."):
        content = ai_assistant.generate_marketing_content(
            campaign_type, target_audience, channel, custom_prompt
        )
        
        st.subheader("Generated Marketing Content")
        st.write(content)
        
        # Save to database option
        col1, col2 = st.columns([1, 1])
        with col1:
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
        
        with col2:
            # Copy to clipboard functionality
            st.code(content, language=None)

# Campaign management
st.markdown("---")
st.subheader("Campaign Management")

conn = db.connect()
cursor = conn.cursor()

# Campaign statistics
cursor.execute("SELECT status, COUNT(*) FROM marketing_campaigns GROUP BY status")
status_data = cursor.fetchall()

if status_data:
    col1, col2, col3, col4 = st.columns(4)
    status_dict = dict(status_data)
    
    with col1:
        st.metric("Total Campaigns", sum(status_dict.values()))
    with col2:
        st.metric("Active", status_dict.get('active', 0))
    with col3:
        st.metric("Draft", status_dict.get('draft', 0))
    with col4:
        st.metric("Completed", status_dict.get('completed', 0))

# Campaign performance chart
cursor.execute("SELECT channel, COUNT(*) as count FROM marketing_campaigns GROUP BY channel")
channel_data = cursor.fetchall()

if channel_data:
    df_channels = pd.DataFrame(channel_data, columns=['Channel', 'Count'])
    fig_pie = px.pie(
        df_channels, 
        values='Count', 
        names='Channel',
        title="Campaigns by Channel"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# Display existing campaigns
st.subheader("Existing Marketing Campaigns")
cursor.execute("""
    SELECT campaign_name, target_audience, channel, status, start_date, budget, created_at
    FROM marketing_campaigns 
    ORDER BY created_at DESC
""")
campaigns = cursor.fetchall()

if campaigns:
    campaigns_df = pd.DataFrame(campaigns, columns=[
        'Campaign', 'Audience', 'Channel', 'Status', 'Start Date', 'Budget', 'Created'
    ])
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.multiselect(
            "Filter by Status:",
            options=campaigns_df['Status'].unique(),
            default=campaigns_df['Status'].unique()
        )
    with col2:
        channel_filter = st.multiselect(
            "Filter by Channel:",
            options=campaigns_df['Channel'].unique(),
            default=campaigns_df['Channel'].unique()
        )
    with col3:
        audience_filter = st.multiselect(
            "Filter by Audience:",
            options=campaigns_df['Audience'].unique(),
            default=campaigns_df['Audience'].unique()
        )
    
    # Apply filters
    filtered_df = campaigns_df[
        (campaigns_df['Status'].isin(status_filter)) &
        (campaigns_df['Channel'].isin(channel_filter)) &
        (campaigns_df['Audience'].isin(audience_filter))
    ]
    
    st.dataframe(filtered_df, use_container_width=True)
    
    # Campaign details
    if not filtered_df.empty:
        selected_campaign = st.selectbox(
            "View Campaign Details:",
            options=filtered_df['Campaign'].tolist()
        )
        
        if selected_campaign:
            cursor.execute("""
                SELECT ai_generated_content 
                FROM marketing_campaigns 
                WHERE campaign_name = ?
            """, (selected_campaign,))
            content_result = cursor.fetchone()
            
            if content_result and content_result[0]:
                st.subheader(f"Content for: {selected_campaign}")
                st.write(content_result[0])
else:
    st.info("No campaigns found. Generate your first campaign above!")

# Social media integration section
st.markdown("---")
st.subheader("Social Media Integration")

social_platforms = {
    "Facebook": "👥 Facebook Business",
    "Instagram": "📸 Instagram Business", 
    "LinkedIn": "💼 LinkedIn Ads",
    "Twitter": "🐦 Twitter Ads",
    "YouTube": "📺 YouTube Ads"
}

st.info("Connect your social media accounts to automatically publish campaigns")

cols = st.columns(len(social_platforms))
for i, (platform, display_name) in enumerate(social_platforms.items()):
    with cols[i]:
        st.button(f"Connect {display_name}", disabled=True)

# A/B testing section
st.markdown("---")
st.subheader("A/B Testing")

col1, col2 = st.columns(2)
with col1:
    st.info(
        """
        **Version A Performance:**
        - Click Rate: 3.2%
        - Conversion: 1.8%
        - Engagement: 45 sec
        """
    )

with col2:
    st.info(
        """
        **Version B Performance:**
        - Click Rate: 4.1%
        - Conversion: 2.3%
        - Engagement: 52 sec
        """
    )

db.close()

# Sidebar information
with st.sidebar:
    st.markdown("### Marketing Channels")
    st.info(
        """
        **Email Marketing:**
        - Personalized campaigns
        - Automated sequences
        - Performance tracking
        
        **Social Media:**
        - Multi-platform posting
        - Audience targeting
        - Engagement analytics
        
        **Web Content:**
        - Landing pages
        - Blog articles
        - SEO optimization
        
        **SMS Marketing:**
        - Short, impactful messages
        - High open rates
        - Immediate delivery
        """
    )
    
    st.markdown("### Best Practices")
    st.success(
        """
        ✅ Personalize content
        ✅ A/B test campaigns
        ✅ Track performance
        ✅ Comply with regulations
        ✅ Optimize for mobile
        """
    )
    
    st.markdown("### Compliance")
    st.warning(
        """
        ⚠️ GDPR compliance required
        ⚠️ Financial advertising rules
        ⚠️ Opt-in consent needed
        ⚠️ Clear terms & conditions
        """
    )

