import os
import sqlite3
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.sql_database import SQLDatabase
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType
from langchain.schema import HumanMessage, SystemMessage
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SQLChatAssistant:
    def __init__(self, db_path=None):
        if db_path is None:
            # Default path: db/lending.db relative to project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            self.db_path = os.path.join(project_root, 'db', 'lending.db')
        else:
            self.db_path = db_path
            
        # Initialize OpenAI client
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize SQL database connection
        self.db = SQLDatabase.from_uri(f"sqlite:///{self.db_path}")
        
        # Create SQL agent
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.agent = create_sql_agent(
            llm=self.llm,
            toolkit=self.toolkit,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def get_database_schema(self) -> str:
        """Get a description of the database schema"""
        return self.db.get_table_info()
    
    def get_sample_queries(self) -> List[Dict[str, str]]:
        """Get sample queries users can try"""
        return [
            {
                "question": "How many customers do we have in total?",
                "category": "Customer Analytics"
            },
            {
                "question": "What's the average credit score of our customers?",
                "category": "Credit Analysis"
            },
            {
                "question": "Show me all customers with outstanding collections",
                "category": "Collections"
            },
            {
                "question": "Which customers have pending KYC verification?",
                "category": "Compliance"
            },
            {
                "question": "What's the total outstanding amount in collections?",
                "category": "Financial Metrics"
            },
            {
                "question": "Show me customers from Germany",
                "category": "Geographic Analysis"
            },
            {
                "question": "Which marketing campaigns are currently active?",
                "category": "Marketing"
            },
            {
                "question": "What are the most common customer service issues?",
                "category": "Customer Service"
            },
            {
                "question": "Show me business customers with their registration numbers",
                "category": "Business Analytics"
            },
            {
                "question": "What's the distribution of collection stages?",
                "category": "Risk Management"
            }
        ]
    
    def chat_with_database(self, question: str) -> Dict[str, Any]:
        """
        Process a natural language question and return SQL results
        """
        try:
            # Add context about the database structure
            context_prompt = f"""
            You are a helpful AI assistant that can answer questions about a lending database.
            
            Database Schema:
            {self.get_database_schema()}
            
            Important Notes:
            - The database contains European customer data
            - Customer types are 'individual' or 'business'
            - KYC/KYB verification statuses are 'pending', 'approved', or 'rejected'
            - Collection stages are 'early', 'mid', 'late', or 'legal'
            - All monetary amounts are in Euros
            - Dates are in YYYY-MM-DD format
            
            Please answer the following question: {question}
            
            If you need to write SQL, make sure to:
            1. Use proper table joins when needed
            2. Handle NULL values appropriately
            3. Format monetary values with Euro symbol
            4. Provide clear, business-friendly explanations
            """
            
            # Execute the query using the agent
            result = self.agent.run(context_prompt)
            
            return {
                "success": True,
                "answer": result,
                "question": question,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "answer": None,
                "question": question,
                "error": str(e)
            }
    
    def execute_direct_sql(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute a direct SQL query (for advanced users)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
            
            return {
                "success": True,
                "data": df,
                "query": sql_query,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "query": sql_query,
                "error": str(e)
            }
    
    def get_table_names(self) -> List[str]:
        """Get all table names in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tables
        except Exception as e:
            return []
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, str]]:
        """Get column information for a specific table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "name": row[1],
                    "type": row[2],
                    "nullable": not row[3],
                    "primary_key": bool(row[5])
                })
            conn.close()
            return columns
        except Exception as e:
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            tables = self.get_table_names()
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                stats[table] = count
            
            conn.close()
            return stats
            
        except Exception as e:
            return {}

