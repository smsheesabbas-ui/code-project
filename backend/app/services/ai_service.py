import os
import groq
from typing import Dict, List, Optional, Tuple
from app.core.config import settings


class AIService:
    """AI service for entity extraction and classification using Groq API"""
    
    def __init__(self):
        if not settings.GROQ_API_KEY:
            print("Warning: GROQ_API_KEY not set. AI features will be disabled.")
            self.client = None
        else:
            self.client = groq.Groq(api_key=settings.GROQ_API_KEY)
    
    async def extract_entity(self, description: str) -> Optional[str]:
        """Extract entity name from transaction description"""
        if not self.client:
            return None
            
        try:
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {
                        "role": "system",
                        "content": "Extract the company or entity name from the transaction description. Return ONLY the entity name, nothing else. Remove common words like 'PAYMENT', 'INVOICE', 'TRANSACTION', 'FEE', etc."
                    },
                    {
                        "role": "user", 
                        "content": description
                    }
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            entity_name = response.choices[0].message.content.strip()
            return entity_name if entity_name else None
            
        except Exception as e:
            print(f"Error extracting entity: {e}")
            return None
    
    async def classify_category(self, description: str, amount: float) -> Optional[str]:
        """Classify transaction category using AI"""
        if not self.client:
            return None
            
        try:
            # Determine transaction type based on amount
            transaction_type = "revenue" if amount >= 0 else "expense"
            
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {
                        "role": "system",
                        "content": f"""Classify this {transaction_type} transaction into one of these categories:
                        
                        For revenue: Software Sales, Consulting Services, Product Sales, Other Revenue, Interest Income, Refunds
                        
                        For expenses: Software & Subscriptions, Office Expenses, Marketing, Professional Services, Travel & Transport, Meals & Entertainment, Rent/Utilities, Equipment, Taxes, Bank Fees, Other Expenses
                        
                        Return ONLY the category name, nothing else."""
                    },
                    {
                        "role": "user",
                        "content": f"Description: {description}\nAmount: ${abs(amount)}"
                    }
                ],
                max_tokens=30,
                temperature=0.1
            )
            
            category = response.choices[0].message.content.strip()
            return category if category else None
            
        except Exception as e:
            print(f"Error classifying category: {e}")
            return None
    
    async def generate_weekly_summary(self, user_data: Dict) -> Optional[str]:
        """Generate AI-powered weekly financial summary"""
        if not self.client:
            return None
            
        try:
            prompt = f"""Generate a concise weekly financial summary based on this data:
            
            Total Revenue: ${user_data.get('total_revenue', 0):.2f}
            Total Expenses: ${user_data.get('total_expenses', 0):.2f}
            Net Income: ${user_data.get('net_income', 0):.2f}
            Transaction Count: {user_data.get('transaction_count', 0)}
            Top Customer: {user_data.get('top_customer', 'N/A')}
            Top Expense Category: {user_data.get('top_expense_category', 'N/A')}
            
            Write a 2-3 sentence summary that is helpful and actionable. Focus on key insights and trends."""
            
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful financial assistant. Write concise, actionable financial summaries."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return None
    
    async def generate_recommendations(self, user_data: Dict) -> Optional[List[str]]:
        """Generate AI-powered financial recommendations"""
        if not self.client:
            return None
            
        try:
            prompt = f"""Based on this financial data, provide 3 specific, actionable recommendations:
            
            Total Revenue: ${user_data.get('total_revenue', 0):.2f}
            Total Expenses: ${user_data.get('total_expenses', 0):.2f}
            Net Income: ${user_data.get('net_income', 0):.2f}
            Top Expense: {user_data.get('top_expense_category', 'N/A')} (${user_data.get('top_expense_amount', 0):.2f})
            Customer Concentration: {user_data.get('customer_concentration', 0):.1f}
            
            Return recommendations as a numbered list (1., 2., 3.). Focus on improving cash flow, reducing costs, or managing risks."""
            
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial advisor. Provide specific, actionable recommendations based on financial data."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            recommendations_text = response.choices[0].message.content.strip()
            
            # Parse numbered list
            recommendations = []
            for line in recommendations_text.split('\n'):
                if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-')):
                    # Remove numbering and clean up
                    clean_line = line.strip()
                    if clean_line[0].isdigit():
                        clean_line = '.'.join(clean_line.split('.')[1:]).strip()
                    elif clean_line.startswith('-'):
                        clean_line = clean_line[1:].strip()
                    
                    if clean_line:
                        recommendations.append(clean_line)
            
            return recommendations[:3]  # Return max 3 recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return None


# Global instance
ai_service = AIService()
