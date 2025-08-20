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
from utils.prompt_generator import LendingPromptGenerator

# Page configuration
st.set_page_config(
    page_title="Marketing - AI Lending Platform",
    page_icon="📢",
    layout="wide"
)

# Initialize components
@st.cache_resource
def init_ai_assistant():
    return AILendingAssistant()

@st.cache_resource
def init_database():
    return LendingDatabase()

@st.cache_resource
def init_prompt_generator():
    return LendingPromptGenerator()

ai_assistant = init_ai_assistant()
db = init_database()
prompt_gen = init_prompt_generator()

# Main content
st.title("📢 AI Marketing Content Generator")
st.markdown("Generate compelling marketing content for various lending products and channels.")

# Create tabs for different marketing tools
tab1, tab2 = st.tabs(["📝 Content Generator", "🎯 Prompt Generator"])

with tab1:
    st.markdown("### 📊 Marketing Overview")
    
    # Marketing metrics overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Campaigns", "3", "↑ 1")
    with col2:
        st.metric("Active Campaigns", "3", "→ 0")
    with col3:
        st.metric("Avg. Engagement", "4.2%", "↑ 0.8%")
    with col4:
        st.metric("Conversion Rate", "2.1%", "↑ 0.3%")

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

    db.close()

with tab2:
    st.markdown("### 🎯 AI-Powered Prompt Generator")
    st.markdown("Create and enhance marketing prompts using AI assistance and pre-built templates.")
    
    # Prompt generation options
    prompt_mode = st.radio(
        "Choose your approach:",
        ["📋 Template-Based", "🤖 AI-Enhanced", "✨ Custom Creation"],
        horizontal=True
    )
    
    if prompt_mode == "📋 Template-Based":
        st.markdown("#### Select from Pre-Built Templates")
        
        # Get categories
        categories = prompt_gen.get_categories()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            selected_category = st.selectbox(
                "Loan Category:",
                options=[cat["key"] for cat in categories],
                format_func=lambda x: next(cat["name"] for cat in categories if cat["key"] == x)
            )
            
            # Get templates for selected category
            templates = prompt_gen.get_templates_by_category(selected_category)
            
            if templates:
                selected_template_idx = st.selectbox(
                    "Template:",
                    options=range(len(templates)),
                    format_func=lambda x: templates[x]["title"]
                )
                
                # Show template description
                st.info(f"**{templates[selected_template_idx]['title']}**")
                
                # Get variable options
                variables = prompt_gen.get_variable_options(selected_category, selected_template_idx)
                
                st.markdown("**Customize Variables:**")
                custom_vars = {}
                for var_name, options in variables.items():
                    custom_vars[var_name] = st.selectbox(
                        f"{var_name.replace('_', ' ').title()}:",
                        options=options,
                        key=f"var_{var_name}"
                    )
        
        with col2:
            if st.button("🎲 Generate Random Prompt", type="secondary"):
                result = prompt_gen.generate_prompt(selected_category, selected_template_idx)
                if result.get("success"):
                    st.success("**Generated Prompt:**")
                    st.write(result["prompt"])
                    
                    # Show variables used
                    with st.expander("Variables Used"):
                        for var, value in result["variables_used"].items():
                            st.write(f"**{var.replace('_', ' ').title()}:** {value}")
                else:
                    st.error(f"Error: {result.get('error')}")
            
            if st.button("🎯 Generate Custom Prompt", type="primary"):
                result = prompt_gen.generate_prompt(selected_category, selected_template_idx, custom_vars)
                if result.get("success"):
                    st.success("**Generated Prompt:**")
                    generated_prompt = result["prompt"]
                    st.write(generated_prompt)
                    
                    # Option to generate content from this prompt
                    st.markdown("---")
                    content_type = st.selectbox(
                        "Generate content as:",
                        ["marketing copy", "email campaign", "social media post", "landing page", "advertisement"]
                    )
                    
                    if st.button("🚀 Generate Content from Prompt"):
                        with st.spinner("Generating marketing content..."):
                            content_result = prompt_gen.generate_content_with_openai(generated_prompt, content_type)
                            
                            if content_result.get("success"):
                                st.success("**Generated Marketing Content:**")
                                st.write(content_result["content"])
                                
                                # Show usage stats
                                with st.expander("Generation Details"):
                                    st.write(f"**Tokens Used:** {content_result.get('tokens_used', 'N/A')}")
                                    st.write(f"**Content Type:** {content_result['content_type']}")
                                    st.code(content_result["prompt_used"], language=None)
                            else:
                                st.error(f"Error generating content: {content_result.get('error')}")
                else:
                    st.error(f"Error: {result.get('error')}")
    
    elif prompt_mode == "🤖 AI-Enhanced":
        st.markdown("#### Enhance Your Prompts with AI")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            basic_prompt = st.text_area(
                "Enter your basic prompt:",
                placeholder="e.g., Create a personal loan campaign for young professionals",
                height=100
            )
            
            enhancement_type = st.selectbox(
                "Enhancement Type:",
                ["detailed", "creative", "compliance", "conversion"],
                format_func=lambda x: {
                    "detailed": "🔍 More Detailed & Specific",
                    "creative": "🎨 Creative & Engaging", 
                    "compliance": "⚖️ Compliance-Focused",
                    "conversion": "📈 Conversion-Optimized"
                }[x]
            )
        
        with col2:
            if basic_prompt and st.button("✨ Enhance Prompt", type="primary"):
                with st.spinner("Enhancing your prompt..."):
                    result = prompt_gen.enhance_prompt_with_ai(basic_prompt, enhancement_type)
                    
                    if result.get("success"):
                        st.success("**Enhanced Prompt:**")
                        enhanced_prompt = result["enhanced_prompt"]
                        st.write(enhanced_prompt)
                        
                        # Option to generate variations
                        if st.button("🔄 Generate Variations"):
                            with st.spinner("Creating variations..."):
                                var_result = prompt_gen.generate_prompt_variations(enhanced_prompt)
                                
                                if var_result.get("success"):
                                    st.success("**Prompt Variations:**")
                                    for i, variation in enumerate(var_result["variations"], 1):
                                        st.write(f"**Variation {i}:** {variation}")
                                else:
                                    st.error(f"Error: {var_result.get('error')}")
                        
                        # Option to generate content
                        content_type = st.selectbox(
                            "Generate content as:",
                            ["marketing copy", "email campaign", "social media post", "landing page", "advertisement"],
                            key="enhance_content_type"
                        )
                        
                        if st.button("🚀 Generate Content", key="enhance_generate"):
                            with st.spinner("Generating content..."):
                                content_result = prompt_gen.generate_content_with_openai(enhanced_prompt, content_type)
                                
                                if content_result.get("success"):
                                    st.success("**Generated Content:**")
                                    st.write(content_result["content"])
                                else:
                                    st.error(f"Error: {content_result.get('error')}")
                    else:
                        st.error(f"Error: {result.get('error')}")
    
    else:  # Custom Creation
        st.markdown("#### Create Custom Prompts")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            loan_type = st.selectbox(
                "Loan Type:",
                ["personal loans", "business loans", "mortgages", "credit cards", "auto loans"]
            )
            
            audience = st.selectbox(
                "Target Audience:",
                ["young professionals", "small business owners", "first-time buyers", "families", "students", "retirees"]
            )
            
            goal = st.selectbox(
                "Marketing Goal:",
                ["increase applications", "build awareness", "drive conversions", "educate customers", "promote features"]
            )
        
        with col2:
            if st.button("💡 Get AI Suggestions", type="secondary"):
                suggestions = prompt_gen.get_prompt_suggestions(loan_type, audience, goal)
                
                st.success("**Prompt Suggestions:**")
                for i, suggestion in enumerate(suggestions, 1):
                    st.write(f"{i}. {suggestion}")
            
            custom_prompt_text = st.text_area(
                "Write your custom prompt:",
                placeholder="Create a compelling marketing campaign that...",
                height=120
            )
            
            if custom_prompt_text and st.button("🚀 Generate Content from Custom Prompt", type="primary"):
                content_type = st.selectbox(
                    "Content Type:",
                    ["marketing copy", "email campaign", "social media post", "landing page", "advertisement"],
                    key="custom_content_type"
                )
                
                with st.spinner("Generating content..."):
                    result = prompt_gen.generate_content_with_openai(custom_prompt_text, content_type)
                    
                    if result.get("success"):
                        st.success("**Generated Content:**")
                        st.write(result["content"])
                        
                        # Save option
                        if st.button("💾 Save to Campaign Database"):
                            conn = db.connect()
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO marketing_campaigns 
                                (campaign_name, target_audience, channel, content, ai_generated_content, start_date, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                f"Custom {loan_type.title()} Campaign",
                                audience,
                                "multi-channel",
                                custom_prompt_text,
                                result["content"],
                                datetime.now().date(),
                                "draft"
                            ))
                            conn.commit()
                            db.close()
                            st.success("Content saved to campaign database!")
                    else:
                        st.error(f"Error: {result.get('error')}")

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

# Sidebar information
with st.sidebar:
    st.markdown("### 🎯 Prompt Generator")
    st.info(
        """
        **Template-Based:**
        - Pre-built lending prompts
        - Customizable variables
        - Industry best practices
        
        **AI-Enhanced:**
        - Improve existing prompts
        - Add compliance elements
        - Optimize for conversion
        
        **Custom Creation:**
        - Build from scratch
        - AI-powered suggestions
        - Flexible approach
        """
    )
    
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

