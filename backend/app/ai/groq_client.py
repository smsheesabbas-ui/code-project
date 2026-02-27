import os
from typing import Optional, Dict, Any
from groq import Groq
from ..config import settings


class GroqClient:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.client = Groq(api_key=settings.GROQ_API_KEY)
    
    async def extract_entity(self, description: str) -> tuple[str, float]:
        """Extract entity name from transaction description"""
        try:
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{
                    "role": "system",
                    "content": "Extract the company or entity name from this transaction description. Return ONLY the entity name, nothing else. If no clear entity is found, return 'Unknown'."
                }, {
                    "role": "user",
                    "content": description
                }],
                max_tokens=50,
                temperature=0.1
            )
            
            entity_name = response.choices[0].message.content.strip()
            confidence = 0.9 if entity_name != "Unknown" else 0.1
            
            return entity_name, confidence
            
        except Exception as e:
            print(f"Error extracting entity: {e}")
            return "Unknown", 0.0
    
    async def categorize_transaction(self, description: str, amount: float) -> tuple[str, float]:
        """Categorize transaction based on description and amount"""
        categories = [
            "Software & Subscriptions",
            "Office Expenses", 
            "Marketing",
            "Professional Services",
            "Travel & Transport",
            "Meals & Entertainment",
            "Rent/Utilities",
            "Equipment",
            "Taxes",
            "Other"
        ]
        
        try:
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{
                    "role": "system",
                    "content": f"""Categorize this transaction into one of these categories: {', '.join(categories)}.
                    Consider the description and amount. Return ONLY the category name, nothing else."""
                }, {
                    "role": "user", 
                    "content": f"Description: {description}\nAmount: ${amount}"
                }],
                max_tokens=30,
                temperature=0.1
            )
            
            category = response.choices[0].message.content.strip()
            
            # Validate category
            if category not in categories:
                category = "Other"
                confidence = 0.3
            else:
                confidence = 0.8
            
            return category, confidence
            
        except Exception as e:
            print(f"Error categorizing transaction: {e}")
            return "Other", 0.0
    
    async def generate_weekly_summary(self, transactions_data: Dict[str, Any]) -> str:
        """Generate AI-powered weekly summary"""
        try:
            prompt = f"""Generate a concise weekly financial summary based on this data:
            
            Total Revenue: ${transactions_data.get('total_revenue', 0):.2f}
            Total Expenses: ${transactions_data.get('total_expenses', 0):.2f}
            Net Income: ${transactions_data.get('net_income', 0):.2f}
            Top Customer: {transactions_data.get('top_customer', 'N/A')}
            Top Expense Category: {transactions_data.get('top_expense_category', 'N/A')}
            Transaction Count: {transactions_data.get('transaction_count', 0)}
            
            Write a 2-3 sentence summary in a professional but friendly tone."""
            
            response = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{
                    "role": "system",
                    "content": "You are a financial assistant providing weekly summaries. Be concise and helpful."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Unable to generate weekly summary at this time."
    
    async def generate_recommendations(self, financial_data: Dict[str, Any]) -> list[str]:
        """Generate AI-powered financial recommendations"""
        try:
            prompt = f"""Based on this financial data, provide 3 specific, actionable recommendations:
            
            Cash Balance: ${financial_data.get('cash_balance', 0):.2f}
            Monthly Burn Rate: ${financial_data.get('monthly_burn', 0):.2f}
            Revenue Growth: {financial_data.get('revenue_growth', 0):.1f}%
            Top Expense: {financial_data.get('top_expense', 'N/A')}
            Customer Concentration: {financial_data.get('customer_concentration', 0):.1f}%
            
            Return recommendations as a numbered list (1., 2., 3.) with each on a new line."""
            
            response = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{
                    "role": "system",
                    "content": "You are a financial advisor. Provide practical, specific recommendations based on the data."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=200,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse numbered list
            recommendations = []
            for line in content.split('\n'):
                if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-')):
                    rec = line.strip()
                    # Remove numbering if present
                    if rec[0].isdigit():
                        rec = rec.split('.', 1)[-1].strip()
                    elif rec.startswith('-'):
                        rec = rec[1:].strip()
                    recommendations.append(rec)
            
            return recommendations[:3]  # Ensure max 3 recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return ["Unable to generate recommendations at this time."]


# Global instance
groq_client = None

def get_groq_client() -> GroqClient:
    global groq_client
    if groq_client is None:
        groq_client = GroqClient()
    return groq_client
