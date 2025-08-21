import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import sqlite3
from datetime import datetime
import os
import sys
import numpy as np

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ai_utils import AILendingAssistant
from utils.database import LendingDatabase
from utils.credit_scoring import CreditScoringModel

# Page configuration
st.set_page_config(
    page_title="Credit Scoring - AI Lending Platform",
    page_icon="📈",
    layout="wide"
)

# Initialize AI assistant, database, and credit scoring model
@st.cache_resource
def init_ai_assistant():
    return AILendingAssistant()

@st.cache_resource
def init_database():
    return LendingDatabase()

@st.cache_resource
def init_credit_model():
    model = CreditScoringModel()
    model.train_model()  # This will load existing model or train new one
    return model

ai_assistant = init_ai_assistant()
db = init_database()
credit_model = init_credit_model()

st.title("📈 Credit Scoring & Underwriting")
st.markdown("AI-powered credit assessment with advanced logistic regression modeling")

# Add tabs for different views
tab1, tab2, tab3 = st.tabs(["Customer Assessment", "Model Insights", "Batch Scoring"])

with tab1:
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
            st.subheader("Advanced Credit Scoring")
            
            # Generate new credit score using logistic regression
            if st.button("🔄 Generate ML Credit Score", type="primary"):
                with st.spinner("Running logistic regression model..."):
                    # Predict credit score using ML model
                    prediction_result = credit_model.predict_credit_score(customer_data)
                    
                    # Store the new score in session state
                    st.session_state.ml_prediction = prediction_result
            
            # Display ML prediction results
            if 'ml_prediction' in st.session_state:
                prediction = st.session_state.ml_prediction
                
                col2a, col2b = st.columns(2)
                with col2a:
                    st.metric("ML Credit Score", prediction['credit_score'])
                    st.metric("Risk Level", prediction['risk_level'])
                
                with col2b:
                    st.metric("Good Credit Probability", f"{prediction['good_credit_probability']:.1%}")
                    
                    # Risk color coding
                    risk_color = {
                        'Low Risk': 'green',
                        'Medium-Low Risk': 'lightgreen', 
                        'Medium Risk': 'orange',
                        'High Risk': 'red'
                    }
                    st.markdown(f"<div style='padding: 10px; background-color: {risk_color.get(prediction['risk_level'], 'gray')}; border-radius: 5px; text-align: center; color: white; font-weight: bold;'>{prediction['risk_level']}</div>", unsafe_allow_html=True)
                
                # Advanced score gauge
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = prediction['credit_score'],
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "ML Credit Score"},
                    delta = {'reference': 650, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
                    gauge = {
                        'axis': {'range': [300, 850]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [300, 580], 'color': "red"},
                            {'range': [580, 670], 'color': "orange"},
                            {'range': [670, 740], 'color': "lightgreen"},
                            {'range': [740, 850], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': prediction['credit_score']
                        }
                    }
                ))
                fig_gauge.update_layout(height=350)
                st.plotly_chart(fig_gauge, use_container_width=True)
                
                # Feature importance analysis
                st.subheader("🔍 Feature Impact Analysis")
                
                feature_importance = prediction['feature_importance']
                
                # Create feature importance dataframe
                importance_data = []
                for feature, data in feature_importance.items():
                    importance_data.append({
                        'Feature': feature.replace('_', ' ').title(),
                        'Value': data['value'],
                        'Coefficient': data['coefficient'],
                        'Impact': data['impact'],
                        'Effect': 'Positive' if data['coefficient'] > 0 else 'Negative'
                    })
                
                importance_df = pd.DataFrame(importance_data)
                importance_df = importance_df.sort_values('Impact', key=abs, ascending=False)
                
                # Feature importance chart
                fig_importance = px.bar(
                    importance_df.head(8), 
                    x='Impact', 
                    y='Feature',
                    orientation='h',
                    title="Top Feature Impacts on Credit Score",
                    color='Effect',
                    color_discrete_map={'Positive': 'green', 'Negative': 'red'}
                )
                fig_importance.update_layout(height=400)
                st.plotly_chart(fig_importance, use_container_width=True)
                
                # Feature details table
                st.subheader("📊 Detailed Feature Analysis")
                display_df = importance_df[['Feature', 'Value', 'Impact', 'Effect']].round(3)
                st.dataframe(display_df, use_container_width=True)
            
            else:
                # Show existing credit score if available
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
                else:
                    st.info("Click 'Generate ML Credit Score' to assess this customer using our advanced logistic regression model")

        # Bank statement analysis
        st.markdown("---")
        st.subheader("📋 Bank Statement Analysis")
        if customer_data['bank_statement']:
            bank_data = customer_data['bank_statement']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Monthly Income", f"€{bank_data['monthly_income']:,.2f}")
            with col2:
                st.metric("Monthly Expenses", f"€{bank_data['monthly_expenses']:,.2f}")
            with col3:
                st.metric("Current Balance", f"€{bank_data['balance']:,.2f}")
            with col4:
                # Calculate and display debt-to-income ratio
                if bank_data['monthly_income'] > 0:
                    dti_ratio = bank_data['monthly_expenses'] / bank_data['monthly_income']
                    st.metric("Expense Ratio", f"{dti_ratio:.1%}")
                else:
                    st.metric("Expense Ratio", "N/A")
            
            # Financial health visualization
            col1, col2 = st.columns(2)
            
            with col1:
                # Income vs Expenses
                income_expense_data = pd.DataFrame({
                    'Category': ['Income', 'Expenses', 'Net Savings'],
                    'Amount': [
                        bank_data['monthly_income'], 
                        bank_data['monthly_expenses'],
                        bank_data['monthly_income'] - bank_data['monthly_expenses']
                    ]
                })
                
                fig_bar = px.bar(
                    income_expense_data, 
                    x='Category', 
                    y='Amount',
                    title="Monthly Financial Overview",
                    color='Category',
                    color_discrete_map={
                        'Income': 'green', 
                        'Expenses': 'red',
                        'Net Savings': 'blue'
                    }
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                # Financial health pie chart
                if bank_data['monthly_income'] > 0:
                    savings = bank_data['monthly_income'] - bank_data['monthly_expenses']
                    if savings > 0:
                        pie_data = pd.DataFrame({
                            'Category': ['Expenses', 'Savings'],
                            'Amount': [bank_data['monthly_expenses'], savings]
                        })
                        
                        fig_pie = px.pie(
                            pie_data, 
                            values='Amount', 
                            names='Category',
                            title="Income Allocation",
                            color_discrete_map={'Expenses': 'red', 'Savings': 'green'}
                        )
                        st.plotly_chart(fig_pie, use_container_width=True)
            
            # Risk indicators
            if bank_data['risk_indicators']:
                risk_data = json.loads(bank_data['risk_indicators']) if isinstance(bank_data['risk_indicators'], str) else bank_data['risk_indicators']
                
                st.subheader("⚠️ Risk Indicators")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Overdrafts", risk_data.get('overdrafts', 0))
                with col2:
                    st.metric("Returned Payments", risk_data.get('returned_payments', 0))
                with col3:
                    gambling = "Yes" if risk_data.get('gambling_transactions') else "No"
                    st.metric("Gambling Transactions", gambling)
                with col4:
                    irregular = "Yes" if risk_data.get('irregular_income') else "No"
                    st.metric("Irregular Income", irregular)
                
                # Risk score calculation
                risk_score = (
                    risk_data.get('overdrafts', 0) * 2 +
                    risk_data.get('returned_payments', 0) * 3 +
                    (5 if risk_data.get('gambling_transactions') else 0) +
                    (3 if risk_data.get('irregular_income') else 0)
                )
                
                if risk_score <= 5:
                    st.success(f"✅ Low Risk Score: {risk_score}")
                elif risk_score <= 10:
                    st.warning(f"⚠️ Medium Risk Score: {risk_score}")
                else:
                    st.error(f"🚨 High Risk Score: {risk_score}")
        else:
            st.info("No bank statement data available for this customer")

with tab2:
    st.subheader("🧠 Machine Learning Model Insights")
    
    # Get model insights
    model_insights = credit_model.get_model_insights()
    
    if model_insights:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Model Type", model_insights['model_type'])
        with col2:
            st.metric("Training Samples", model_insights['training_samples'])
        with col3:
            st.metric("Features Used", model_insights['total_features'])
        
        st.subheader("📈 Feature Importance in Model")
        
        # Create feature importance chart
        feature_insights = model_insights['feature_insights'][:10]  # Top 10 features
        
        importance_df = pd.DataFrame(feature_insights)
        
        fig_model_importance = px.bar(
            importance_df, 
            x='importance', 
            y='feature',
            orientation='h',
            title="Model Feature Importance (Top 10)",
            color='effect',
            color_discrete_map={'Positive': 'green', 'Negative': 'red'}
        )
        fig_model_importance.update_layout(height=500)
        st.plotly_chart(fig_model_importance, use_container_width=True)
        
        # Feature details
        st.subheader("🔍 Feature Details")
        display_insights = pd.DataFrame(feature_insights)
        display_insights['coefficient'] = display_insights['coefficient'].round(4)
        display_insights['importance'] = display_insights['importance'].round(4)
        st.dataframe(display_insights, use_container_width=True)
        
        # Model explanation
        st.subheader("📚 How the Model Works")
        st.info("""
        **Logistic Regression Credit Scoring Model**
        
        This model uses logistic regression to predict the probability that a customer will be a "good credit" customer. 
        The model considers multiple factors:
        
        - **Financial Ratios**: Income, expenses, savings rate
        - **Risk Indicators**: Overdrafts, returned payments, gambling
        - **Demographics**: Age, business vs individual
        - **Credit History**: Existing credit score
        - **Geographic Risk**: Country-based risk assessment
        
        The final credit score is calculated by converting the probability of good credit to a score between 300-850.
        Higher probability = Higher credit score.
        """)

with tab3:
    st.subheader("📊 Batch Credit Scoring")
    
    # Get all customers for batch processing
    cursor.execute("SELECT id, first_name, last_name, company_name, email FROM customers")
    all_customers = cursor.fetchall()
    
    if st.button("🚀 Score All Customers", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        batch_results = []
        
        for i, customer in enumerate(all_customers):
            customer_id = customer[0]
            name = customer[3] if customer[3] else f"{customer[1]} {customer[2]}"
            
            status_text.text(f"Scoring customer: {name}")
            
            # Get customer data and predict
            customer_data = ai_assistant.get_customer_data(customer_id)
            if customer_data:
                prediction = credit_model.predict_credit_score(customer_data)
                
                batch_results.append({
                    'Customer': name,
                    'Email': customer[4],
                    'ML Credit Score': prediction['credit_score'],
                    'Risk Level': prediction['risk_level'],
                    'Good Credit Probability': f"{prediction['good_credit_probability']:.1%}"
                })
            
            progress_bar.progress((i + 1) / len(all_customers))
        
        status_text.text("Batch scoring complete!")
        
        # Display results
        if batch_results:
            results_df = pd.DataFrame(batch_results)
            
            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                avg_score = results_df['ML Credit Score'].mean()
                st.metric("Average Score", f"{avg_score:.0f}")
            with col2:
                high_risk_count = len(results_df[results_df['Risk Level'] == 'High Risk'])
                st.metric("High Risk Customers", high_risk_count)
            with col3:
                low_risk_count = len(results_df[results_df['Risk Level'] == 'Low Risk'])
                st.metric("Low Risk Customers", low_risk_count)
            with col4:
                total_customers = len(results_df)
                st.metric("Total Scored", total_customers)
            
            # Score distribution
            fig_dist = px.histogram(
                results_df, 
                x='ML Credit Score', 
                nbins=20,
                title="Credit Score Distribution (All Customers)",
                labels={'ML Credit Score': 'Credit Score', 'count': 'Number of Customers'}
            )
            st.plotly_chart(fig_dist, use_container_width=True)
            
            # Risk level distribution
            risk_counts = results_df['Risk Level'].value_counts()
            fig_risk = px.pie(
                values=risk_counts.values, 
                names=risk_counts.index,
                title="Risk Level Distribution"
            )
            st.plotly_chart(fig_risk, use_container_width=True)
            
            # Results table
            st.subheader("📋 Detailed Results")
            st.dataframe(results_df, use_container_width=True)
            
            # Download results
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name=f"credit_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

# Credit scoring overview (existing customers)
st.markdown("---")
st.subheader("📈 Historical Credit Scores")

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
        title="Historical Credit Score Distribution",
        labels={'Score': 'Credit Score', 'count': 'Number of Customers'}
    )
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Scores table
    display_df = df_scores[['Customer', 'Score', 'Date']]
    st.dataframe(display_df, use_container_width=True)

db.close()

# Sidebar information
with st.sidebar:
    st.markdown("### 🎯 Credit Score Ranges")
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
    
    st.markdown("### ⚖️ ML Model Features")
    st.warning(
        """
        **Key Factors:**
        - Income & Expense Ratios
        - Savings Rate
        - Risk Indicators
        - Credit History
        - Demographics
        - Geographic Risk
        
        **Model:** Logistic Regression
        **Accuracy:** ~85% on test data
        """
    )
    
    st.markdown("### 🔄 Model Updates")
    if st.button("Retrain Model"):
        with st.spinner("Retraining model..."):
            credit_model.train_model(retrain=True)
            st.success("Model retrained successfully!")
            st.experimental_rerun()

