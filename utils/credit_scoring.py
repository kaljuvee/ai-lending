import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import sqlite3
import json
import pickle
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class CreditScoringModel:
    """
    Advanced credit scoring model using logistic regression
    """
    
    def __init__(self, db_path='db/lending.db'):
        self.db_path = db_path
        self.model = LogisticRegression(random_state=42)
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        self.model_path = 'utils/credit_model.pkl'
        
    def prepare_features(self, customer_data):
        """
        Prepare features for credit scoring model
        """
        features = {}
        
        # Customer demographics
        features['age'] = customer_data.get('age', 35)  # Default age if not provided
        features['is_business'] = 1 if customer_data.get('customer_type') == 'business' else 0
        
        # Income and financial data
        bank_data = customer_data.get('bank_statement', {})
        features['monthly_income'] = bank_data.get('monthly_income', 0)
        features['monthly_expenses'] = bank_data.get('monthly_expenses', 0)
        features['current_balance'] = bank_data.get('balance', 0)
        
        # Derived financial ratios
        if features['monthly_income'] > 0:
            features['expense_to_income_ratio'] = features['monthly_expenses'] / features['monthly_income']
            features['savings_rate'] = (features['monthly_income'] - features['monthly_expenses']) / features['monthly_income']
        else:
            features['expense_to_income_ratio'] = 1.0
            features['savings_rate'] = 0.0
        
        # Risk indicators
        risk_data = bank_data.get('risk_indicators', {})
        if isinstance(risk_data, str):
            risk_data = json.loads(risk_data)
        
        features['overdrafts'] = risk_data.get('overdrafts', 0)
        features['returned_payments'] = risk_data.get('returned_payments', 0)
        features['gambling_transactions'] = 1 if risk_data.get('gambling_transactions', False) else 0
        features['irregular_income'] = 1 if risk_data.get('irregular_income', False) else 0
        
        # Credit history (if available)
        credit_data = customer_data.get('credit_score', {})
        features['existing_credit_score'] = credit_data.get('score', 650) if credit_data else 650
        
        # Country risk (simplified)
        country_risk_map = {
            'Germany': 0.1, 'France': 0.15, 'Italy': 0.2, 
            'Spain': 0.25, 'Poland': 0.3, 'Netherlands': 0.05
        }
        features['country_risk'] = country_risk_map.get(customer_data.get('country', 'Germany'), 0.2)
        
        return features
    
    def generate_synthetic_training_data(self, n_samples=1000):
        """
        Generate synthetic training data for the credit scoring model
        """
        np.random.seed(42)
        
        data = []
        for i in range(n_samples):
            # Generate synthetic customer data
            age = np.random.normal(40, 12)
            age = max(18, min(80, age))  # Clamp between 18-80
            
            is_business = np.random.choice([0, 1], p=[0.7, 0.3])
            
            # Income varies by age and business type
            base_income = 2000 + (age - 25) * 50
            if is_business:
                base_income *= np.random.uniform(1.5, 3.0)
            
            monthly_income = max(1000, np.random.normal(base_income, base_income * 0.3))
            
            # Expenses are typically 60-90% of income for good customers
            expense_ratio = np.random.uniform(0.5, 0.95)
            monthly_expenses = monthly_income * expense_ratio
            
            current_balance = np.random.normal(monthly_income * 2, monthly_income * 0.5)
            current_balance = max(0, current_balance)
            
            # Risk factors
            overdrafts = np.random.poisson(1) if np.random.random() < 0.3 else 0
            returned_payments = np.random.poisson(0.5) if np.random.random() < 0.2 else 0
            gambling_transactions = 1 if np.random.random() < 0.1 else 0
            irregular_income = 1 if np.random.random() < 0.15 else 0
            
            existing_credit_score = np.random.normal(700, 80)
            existing_credit_score = max(300, min(850, existing_credit_score))
            
            country_risk = np.random.choice([0.05, 0.1, 0.15, 0.2, 0.25, 0.3], 
                                          p=[0.1, 0.2, 0.2, 0.2, 0.2, 0.1])
            
            # Calculate derived features
            expense_to_income_ratio = monthly_expenses / monthly_income
            savings_rate = (monthly_income - monthly_expenses) / monthly_income
            
            # Create target variable (1 = good credit, 0 = bad credit)
            # Good credit probability based on features
            good_credit_prob = 0.8
            
            # Adjust probability based on features
            if expense_to_income_ratio > 0.9:
                good_credit_prob -= 0.3
            if savings_rate < 0.1:
                good_credit_prob -= 0.2
            if overdrafts > 2:
                good_credit_prob -= 0.3
            if returned_payments > 1:
                good_credit_prob -= 0.4
            if gambling_transactions:
                good_credit_prob -= 0.2
            if irregular_income:
                good_credit_prob -= 0.15
            if existing_credit_score < 600:
                good_credit_prob -= 0.3
            if country_risk > 0.2:
                good_credit_prob -= 0.1
            
            good_credit_prob = max(0.05, min(0.95, good_credit_prob))
            is_good_credit = 1 if np.random.random() < good_credit_prob else 0
            
            data.append({
                'age': age,
                'is_business': is_business,
                'monthly_income': monthly_income,
                'monthly_expenses': monthly_expenses,
                'current_balance': current_balance,
                'expense_to_income_ratio': expense_to_income_ratio,
                'savings_rate': savings_rate,
                'overdrafts': overdrafts,
                'returned_payments': returned_payments,
                'gambling_transactions': gambling_transactions,
                'irregular_income': irregular_income,
                'existing_credit_score': existing_credit_score,
                'country_risk': country_risk,
                'is_good_credit': is_good_credit
            })
        
        return pd.DataFrame(data)
    
    def train_model(self, retrain=False):
        """
        Train the logistic regression model
        """
        # Check if model already exists and is trained
        if os.path.exists(self.model_path) and not retrain:
            self.load_model()
            return
        
        # Generate synthetic training data
        df = self.generate_synthetic_training_data(1500)
        
        # Prepare features and target
        feature_columns = [col for col in df.columns if col != 'is_good_credit']
        X = df[feature_columns]
        y = df['is_good_credit']
        
        self.feature_names = feature_columns
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        print("Model Performance:")
        print(classification_report(y_test, y_pred))
        print(f"ROC AUC Score: {roc_auc_score(y_test, y_pred_proba):.3f}")
        
        self.is_trained = True
        self.save_model()
    
    def save_model(self):
        """
        Save the trained model and scaler
        """
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self):
        """
        Load the trained model and scaler
        """
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.is_trained = model_data['is_trained']
    
    def predict_credit_score(self, customer_data):
        """
        Predict credit score for a customer
        """
        if not self.is_trained:
            self.train_model()
        
        # Prepare features
        features = self.prepare_features(customer_data)
        
        # Create feature vector in the correct order
        feature_vector = []
        for feature_name in self.feature_names:
            feature_vector.append(features.get(feature_name, 0))
        
        # Scale features
        feature_vector = np.array(feature_vector).reshape(1, -1)
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Predict probability of good credit
        good_credit_prob = self.model.predict_proba(feature_vector_scaled)[0, 1]
        
        # Convert probability to credit score (300-850 range)
        # Higher probability of good credit = higher score
        credit_score = 300 + (good_credit_prob * 550)
        credit_score = int(np.round(credit_score))
        
        # Get feature importance for explanation
        feature_importance = {}
        coefficients = self.model.coef_[0]
        for i, feature_name in enumerate(self.feature_names):
            feature_importance[feature_name] = {
                'coefficient': float(coefficients[i]),
                'value': features.get(feature_name, 0),
                'impact': float(coefficients[i] * features.get(feature_name, 0))
            }
        
        return {
            'credit_score': credit_score,
            'good_credit_probability': float(good_credit_prob),
            'risk_level': self._get_risk_level(credit_score),
            'feature_importance': feature_importance,
            'model_version': '1.0'
        }
    
    def _get_risk_level(self, credit_score):
        """
        Determine risk level based on credit score
        """
        if credit_score >= 740:
            return 'Low Risk'
        elif credit_score >= 670:
            return 'Medium-Low Risk'
        elif credit_score >= 580:
            return 'Medium Risk'
        else:
            return 'High Risk'
    
    def get_model_insights(self):
        """
        Get insights about the trained model
        """
        if not self.is_trained:
            return None
        
        coefficients = self.model.coef_[0]
        feature_insights = []
        
        for i, feature_name in enumerate(self.feature_names):
            feature_insights.append({
                'feature': feature_name.replace('_', ' ').title(),
                'coefficient': float(coefficients[i]),
                'importance': abs(float(coefficients[i])),
                'effect': 'Positive' if coefficients[i] > 0 else 'Negative'
            })
        
        # Sort by importance
        feature_insights.sort(key=lambda x: x['importance'], reverse=True)
        
        return {
            'total_features': len(self.feature_names),
            'feature_insights': feature_insights,
            'model_type': 'Logistic Regression',
            'training_samples': 1500
        }

