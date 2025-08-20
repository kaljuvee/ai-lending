import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.sql_chat import SQLChatAssistant

# Page configuration
st.set_page_config(
    page_title="Database Chat - AI Lending Platform",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize SQL Chat Assistant
@st.cache_resource
def init_sql_chat():
    return SQLChatAssistant()

try:
    sql_chat = init_sql_chat()
except Exception as e:
    st.error(f"Failed to initialize SQL Chat: {str(e)}")
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown("## 💬 Database Chat")
    st.markdown("Ask questions about our lending data in natural language!")
    
    st.markdown("### 📊 Database Overview")
    try:
        db_stats = sql_chat.get_database_stats()
        for table, count in db_stats.items():
            st.metric(table.replace('_', ' ').title(), count)
    except:
        st.info("Database statistics unavailable")
    
    st.markdown("### 📋 Available Tables")
    try:
        tables = sql_chat.get_table_names()
        for table in tables:
            with st.expander(f"📄 {table}"):
                columns = sql_chat.get_table_columns(table)
                for col in columns:
                    icon = "🔑" if col["primary_key"] else "📝"
                    st.write(f"{icon} **{col['name']}** ({col['type']})")
    except:
        st.info("Table information unavailable")
    
    st.markdown("### 💡 Tips")
    st.info("""
    **Try asking:**
    - "How many customers do we have?"
    - "Show me pending KYC verifications"
    - "What's our total collections amount?"
    - "Which customers are from Germany?"
    - "Show me high-risk accounts"
    """)

# Main content
st.title("💬 Database Chat Assistant")
st.markdown("Ask questions about your lending data using natural language. The AI will convert your questions to SQL and provide insights.")

# Chat interface
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🗣️ Ask Your Question")
    
    # Sample questions
    st.markdown("#### 🎯 Sample Questions")
    sample_queries = sql_chat.get_sample_queries()
    
    # Group sample queries by category
    categories = {}
    for query in sample_queries:
        category = query["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(query["question"])
    
    # Display sample questions in tabs
    tab_names = list(categories.keys())
    tabs = st.tabs(tab_names)
    
    for i, (category, questions) in enumerate(categories.items()):
        with tabs[i]:
            for question in questions:
                if st.button(question, key=f"sample_{question}"):
                    st.session_state.selected_question = question
    
    # Chat input
    user_question = st.text_area(
        "Your Question:",
        value=st.session_state.get('selected_question', ''),
        height=100,
        placeholder="Ask anything about the database... e.g., 'How many customers have overdue payments?'"
    )
    
    col_ask, col_clear = st.columns([1, 1])
    with col_ask:
        ask_button = st.button("🤖 Ask Database", type="primary", use_container_width=True)
    with col_clear:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            if 'chat_history' in st.session_state:
                del st.session_state.chat_history
            if 'selected_question' in st.session_state:
                del st.session_state.selected_question
            st.rerun()

with col2:
    st.markdown("### ⚙️ Advanced Options")
    
    with st.expander("🔧 Direct SQL Query"):
        st.markdown("For advanced users who want to write SQL directly:")
        sql_query = st.text_area(
            "SQL Query:",
            height=100,
            placeholder="SELECT * FROM customers WHERE country = 'Germany';"
        )
        
        if st.button("▶️ Execute SQL"):
            if sql_query.strip():
                with st.spinner("Executing SQL query..."):
                    result = sql_chat.execute_direct_sql(sql_query)
                    
                    if result["success"]:
                        st.success("Query executed successfully!")
                        if not result["data"].empty:
                            st.dataframe(result["data"], use_container_width=True)
                        else:
                            st.info("Query returned no results.")
                    else:
                        st.error(f"SQL Error: {result['error']}")
    
    with st.expander("📊 Database Schema"):
        try:
            schema = sql_chat.get_database_schema()
            st.code(schema, language="sql")
        except:
            st.error("Could not load database schema")

# Process question
if ask_button and user_question.strip():
    with st.spinner("🤔 Thinking and querying database..."):
        result = sql_chat.chat_with_database(user_question)
        
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Add to chat history
        st.session_state.chat_history.append({
            "question": user_question,
            "result": result,
            "timestamp": datetime.now()
        })

# Display chat history
if 'chat_history' in st.session_state and st.session_state.chat_history:
    st.markdown("### 💭 Chat History")
    
    # Reverse to show newest first
    for i, chat in enumerate(reversed(st.session_state.chat_history)):
        with st.container():
            st.markdown(f"**🙋 Question #{len(st.session_state.chat_history) - i}** ({chat['timestamp'].strftime('%H:%M:%S')})")
            st.info(chat["question"])
            
            if chat["result"]["success"]:
                st.markdown("**🤖 AI Assistant:**")
                st.success(chat["result"]["answer"])
            else:
                st.markdown("**❌ Error:**")
                st.error(f"Sorry, I encountered an error: {chat['result']['error']}")
            
            st.divider()

# Footer with instructions
st.markdown("---")
st.markdown("""
### 📚 How to Use Database Chat

1. **Natural Language**: Ask questions in plain English about your lending data
2. **Sample Questions**: Click on any sample question to get started
3. **Advanced SQL**: Use the sidebar for direct SQL queries if you're comfortable with SQL
4. **Chat History**: All your questions and answers are saved in the session

**Examples of what you can ask:**
- Customer analytics: "How many individual vs business customers do we have?"
- Risk analysis: "Show me customers with credit scores below 600"
- Collections: "What's the average days overdue for each collection stage?"
- Geographic data: "List all customers by country"
- Financial metrics: "What's our total outstanding amount?"

The AI will automatically generate appropriate SQL queries and provide business-friendly explanations of the results.
""")

# Add some styling
st.markdown("""
<style>
.stButton > button {
    width: 100%;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    height: 50px;
    padding-left: 20px;
    padding-right: 20px;
}
</style>
""", unsafe_allow_html=True)

