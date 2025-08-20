# AI Lending Platform MVP

A comprehensive Python MVP application demonstrating various AI use cases for consumer lending, built with Streamlit, OpenAI, and SQLite.

## 🏦 Overview

This AI-powered lending platform showcases practical applications of artificial intelligence in the financial services sector, specifically focusing on consumer lending processes. The application demonstrates how AI can streamline and enhance various aspects of lending operations while maintaining compliance with European regulations.

## ✨ Features

### 1. 📊 Dashboard
- **Real-time Metrics**: Total customers, approved KYC/KYB, average credit scores, and collections overview
- **Interactive Visualizations**: Customer distribution charts, KYC/KYB status tracking
- **Collections Risk Heatmap**: Visual representation of risk based on days overdue and outstanding amounts
- **Summary Tables**: Comprehensive collections data with customer details

### 2. 👤 KYC/KYB Customer Onboarding
- **AI-Powered Chat Interface**: Interactive chat assistant for customer verification
- **Dual Mode Support**: Separate workflows for individual customers (KYC) and businesses (KYB)
- **Regulatory Compliance**: GDPR and EU AML directive compliant processes
- **Document Collection**: Guided collection of required verification documents
- **Real-time Assistance**: Step-by-step guidance through the onboarding process

### 3. 📈 Credit Scoring & Underwriting
- **Customer Selection**: Choose from existing customers in the database
- **Credit Score Visualization**: Interactive gauge showing credit scores with risk bands
- **Bank Statement Analysis**: AI-powered analysis of financial data
- **Risk Assessment**: Comprehensive risk indicators and scoring
- **Financial Metrics**: Monthly income, expenses, and balance tracking

### 4. 📢 AI Marketing Content Generator
- **Campaign Types**: Personal loans, business loans, mortgages, credit cards, investment products
- **Target Audiences**: Customizable audience segments (young professionals, SMEs, first-time buyers, etc.)
- **Multi-Channel Support**: Email, social media, web, and SMS campaigns
- **AI Content Generation**: Automated creation of compelling marketing content
- **Campaign Management**: Save and track marketing campaigns in the database

### 5. 💬 Customer Service Chat
- **Intelligent Support**: Context-aware AI responses to customer inquiries
- **Customer Context**: Integration with customer data for personalized support
- **Sentiment Analysis**: Real-time sentiment detection with escalation alerts
- **Multi-topic Support**: Loan applications, payment schedules, account issues, and general banking
- **Interaction Tracking**: Complete history of customer service interactions

### 6. 💰 Collections Management
- **Collections Overview**: Key metrics including total outstanding amounts and risk accounts
- **Stage-based Management**: Early, mid, late, and legal collection stages
- **AI Email Generation**: Automated, personalized collection emails based on customer stage
- **Risk Visualization**: Charts showing collections by stage and risk distribution
- **Payment Plan Integration**: Structured payment plan management

## 🛠 Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **AI/ML**: OpenAI GPT-4 for natural language processing
- **Database**: SQLite for local data storage
- **Visualization**: Plotly for interactive charts and graphs
- **Data Processing**: Pandas for data manipulation
- **Environment Management**: python-dotenv for configuration

## 📋 Prerequisites

- Python 3.11 or higher
- OpenAI API key
- Git for version control

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/kaljuvee/ai-lending.git
cd ai-lending
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```bash
cp env.sample .env
```

Edit the `.env` file and add your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Initialize Database
```bash
python database.py
```

This will create the SQLite database with demo European customer data.

### 5. Run the Application
```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## 📊 Database Schema

The application uses SQLite with the following main tables:

- **customers**: Individual and business customer information
- **kyc_kyb_data**: Verification data and status
- **credit_scores**: Credit scoring information and factors
- **bank_statements**: Financial data and transaction analysis
- **marketing_campaigns**: Campaign management and AI-generated content
- **customer_service**: Support interactions and sentiment analysis
- **collections**: Outstanding accounts and collection management

## 🌍 Demo Data

The application comes pre-populated with European demo data including:

- **8 Customers**: Mix of individual and business customers from Germany, France, Italy, Poland, and Spain
- **Credit Scores**: Realistic credit scoring data with factors
- **Bank Statements**: Sample financial data with risk indicators
- **Collections**: Sample overdue accounts in various stages
- **Service Interactions**: Historical customer service data

## 🔧 Configuration

### OpenAI Integration
The application integrates with OpenAI's GPT-4 model for:
- Natural language processing in chat interfaces
- Content generation for marketing campaigns
- Sentiment analysis of customer interactions
- Bank statement analysis and risk assessment

### Compliance Features
- **GDPR Compliance**: Data protection and privacy considerations
- **EU AML Directives**: Anti-money laundering compliance
- **Financial Regulations**: Adherence to European financial advertising standards

## 📱 Usage Guide

### Navigation
Use the sidebar to navigate between different modules:
1. **Dashboard**: Overview and key metrics
2. **KYC/KYB Onboarding**: Customer verification
3. **Credit Scoring**: Credit assessment and analysis
4. **Marketing**: Content generation and campaign management
5. **Customer Service**: AI-powered support chat
6. **Collections**: Debt collection and management

### Key Workflows

#### Customer Onboarding
1. Select customer type (individual/business)
2. Use the chat interface to guide customers through verification
3. Collect required documents and information
4. Review and approve verification status

#### Credit Assessment
1. Select a customer from the dropdown
2. Review credit score and financial metrics
3. Analyze bank statement data
4. Generate AI-powered risk assessment

#### Collections Management
1. Review collections overview and metrics
2. Select accounts requiring attention
3. Generate personalized collection emails
4. Track payment plans and follow-ups

## 🔒 Security Considerations

- **API Key Management**: Store OpenAI API keys securely in environment variables
- **Data Protection**: Local SQLite database for sensitive customer data
- **Access Control**: Implement proper authentication in production deployments
- **Compliance**: Regular audits for regulatory compliance

## 🚀 Deployment

### Streamlit Cloud Deployment
1. Push code to GitHub repository
2. Connect to Streamlit Cloud
3. Configure secrets for API keys
4. Deploy application

### Local Production Deployment
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## 📈 Future Enhancements

- **Machine Learning Models**: Custom credit scoring models
- **Advanced Analytics**: Predictive analytics for collections
- **Integration APIs**: Third-party financial data providers
- **Mobile Optimization**: Enhanced mobile user experience
- **Multi-language Support**: Localization for different European markets
- **Advanced Reporting**: Comprehensive business intelligence dashboards

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

For support and questions:
- Create an issue in the GitHub repository
- Review the documentation and demo data
- Check the troubleshooting section below

## 🔧 Troubleshooting

### Common Issues

**OpenAI API Errors**
- Verify your API key is correctly set in the `.env` file
- Check your OpenAI account has sufficient credits
- Ensure you're using a supported model (GPT-4)

**Database Issues**
- Run `python database.py` to reinitialize the database
- Check file permissions for the SQLite database file
- Verify the database schema matches the application requirements

**Streamlit Issues**
- Clear Streamlit cache: `streamlit cache clear`
- Restart the application
- Check for port conflicts on 8501

## 📊 Performance Metrics

The application demonstrates:
- **Response Time**: Sub-second response for most operations
- **Scalability**: Handles multiple concurrent users
- **Reliability**: Robust error handling and graceful degradation
- **User Experience**: Intuitive interface with professional design

---

**Built with ❤️ for the European lending industry**

*This MVP demonstrates the potential of AI in transforming traditional lending processes while maintaining regulatory compliance and customer focus.*
