import os
import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
from app.core.config import settings


class AIService:
    """AI service for entity extraction and classification using Google Gemini API"""
    
    def __init__(self):
        if not settings.GROQ_API_KEY:
            print("Warning: GROQ_API_KEY not set. AI features will be disabled.")
            self.client = None
        else:
            # Configure Gemini with the API key
            genai.configure(api_key=settings.GROQ_API_KEY)
            
            # List available models to debug
            try:
                models = genai.list_models()
                print("Available models:")
                for model in models:
                    print(f"  - {model.name}: {model.display_name}")
            except Exception as e:
                print(f"Error listing models: {e}")
            
            # Try to use the first available model that supports generateContent
            try:
                self.client = genai.GenerativeModel('gemini-2.5-flash')
                print("Using model: gemini-2.5-flash")
            except Exception as e:
                print(f"Error with gemini-2.5-flash: {e}")
                try:
                    self.client = genai.GenerativeModel('gemini-pro-latest')
                    print("Using model: gemini-pro-latest")
                except Exception as e2:
                    print(f"Error with gemini-pro-latest: {e2}")
                    try:
                        self.client = genai.GenerativeModel('gemini-flash-latest')
                        print("Using model: gemini-flash-latest")
                    except Exception as e3:
                        print(f"Error with gemini-flash-latest: {e3}")
                        self.client = None
    
    async def extract_entity(self, description: str) -> Optional[str]:
        """Extract entity name from transaction description"""
        if not self.client:
            return None
            
        try:
            prompt = f"""
            Extract the company or entity name from this transaction description: "{description}"
            
            Return ONLY the entity name, nothing else. Remove common words like 'PAYMENT', 'INVOICE', 'TRANSACTION', 'FEE', etc.
            """
            
            response = self.client.generate_content(prompt)
            entity = response.text.strip()
            
            return entity if entity else None
            
        except Exception as e:
            print(f"Error extracting entity: {e}")
            return None
    
    async def classify_category(self, description: str, amount: float) -> Optional[str]:
        """Classify transaction category using AI"""
        if not self.client:
            return None
            
        try:
            categories = [
                "Software & Subscriptions", "Office Expenses", "Marketing", 
                "Professional Services", "Travel & Transport", "Meals & Entertainment",
                "Rent/Utilities", "Equipment", "Taxes", "Other"
            ]
            
            prompt = f"""
            Classify this transaction into one of these categories: {', '.join(categories)}
            
            Description: "{description}"
            Amount: ${amount}
            
            Return ONLY the category name, nothing else.
            """
            
            response = self.client.generate_content(prompt)
            category = response.text.strip()
            
            # Validate category
            if category in categories:
                return category
            else:
                return "Other"
            
        except Exception as e:
            print(f"Error classifying category: {e}")
            return None
    
    async def generate_weekly_summary(self, weekly_data: dict) -> Optional[str]:
        """Generate AI-powered weekly financial summary"""
        if not self.client:
            return None
            
        try:
            # Prepare data for AI
            total_revenue = weekly_data.get("total_revenue", 0)
            total_expenses = weekly_data.get("total_expenses", 0)
            net_cashflow = total_revenue - total_expenses
            transaction_count = weekly_data.get("transaction_count", 0)
            top_customer = weekly_data.get("top_customer", "N/A")
            
            prompt = f"""
            Based on the following weekly financial data, provide a concise 2-3 sentence summary:
            
            - Total Revenue: ${total_revenue:,.2f}
            - Total Expenses: ${total_expenses:,.2f}
            - Net Cash Flow: ${net_cashflow:,.2f}
            - Transaction Count: {transaction_count}
            - Top Customer: {top_customer}
            
            Focus on cash flow health, revenue trends, and key insights. Be professional and actionable.
            """
            
            response = self.client.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error generating AI summary: {e}")
            return None
    
    async def generate_recommendations(self, user_data: Dict) -> Optional[List[str]]:
        """Generate AI-powered financial recommendations"""
        if not self.client:
            return None
            
        try:
            prompt = f"""Based on this financial data, provide 3 specific, actionable recommendations:
            
            Total Revenue: ${user_data.get('total_revenue', 0):.2f}
            Total Expenses: ${user_data.get('total_expenses', 0):.2f}
            Net Cash Flow: ${user_data.get('net_cashflow', 0):.2f}
            
            Return each recommendation on a new line, starting with a number (1., 2., 3.)
            """
            
            response = self.client.generate_content(prompt)
            text = response.text.strip()
            
            # Parse numbered list
            recommendations = []
            for line in text.split('\n'):
                clean_line = line.strip()
                if clean_line and (clean_line[0].isdigit() or clean_line.startswith('-')):
                    # Remove numbering/bullets
                    clean_line = clean_line[2:] if clean_line[0].isdigit() else clean_line[1:]
                    recommendations.append(clean_line.strip())
            
            return recommendations[:3]  # Return max 3 recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return None


# Global instance
ai_service = AIService()
