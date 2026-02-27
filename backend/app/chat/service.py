from datetime import datetime
from typing import List, Optional, Dict, Any
from ..database import chat_sessions, chat_messages
from ..models.chat import (
    ChatSession, ChatSessionCreate, ChatMessageCreate, 
    ChatResponse, ChatSessionSummary, ChatMessage, 
    MessageRole, ChatIntent
)
from ..ai.groq_client import get_groq_client
from .tools import chat_tools
import uuid
import re


class ChatService:
    def __init__(self):
        self.groq_client = get_groq_client()

    async def create_session(self, session_data: ChatSessionCreate, user_id: str) -> ChatSession:
        """Create a new chat session"""
        session_dict = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": session_data.title,
            "messages": [],
            "context": {},
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await chat_sessions.insert_one(session_dict)
        
        # If initial message provided, add it
        if session_data.initial_message:
            message_data = ChatMessageCreate(content=session_data.initial_message)
            await self.process_message(session_dict["id"], message_data, user_id)
        
        return ChatSession(**session_dict)

    async def get_user_sessions(self, user_id: str) -> List[ChatSessionSummary]:
        """Get all chat sessions for a user"""
        cursor = chat_sessions.find(
            {"user_id": user_id, "is_active": True}
        ).sort("updated_at", -1)
        
        sessions = []
        async for session_doc in cursor:
            messages = session_doc.get("messages", [])
            last_message = messages[-1]["content"] if messages else None
            
            summary = ChatSessionSummary(
                id=session_doc["id"],
                title=session_doc.get("title"),
                message_count=len(messages),
                last_message=last_message,
                created_at=session_doc["created_at"],
                updated_at=session_doc["updated_at"]
            )
            sessions.append(summary)
        
        return sessions

    async def get_session(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        """Get a specific chat session"""
        session_doc = await chat_sessions.find_one({
            "id": session_id,
            "user_id": user_id,
            "is_active": True
        })
        
        if not session_doc:
            return None
        
        return ChatSession(**session_doc)

    async def process_message(
        self, 
        session_id: str, 
        message_data: ChatMessageCreate, 
        user_id: str
    ) -> ChatResponse:
        """Process user message and generate AI response"""
        # Get session
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError("Session not found")
        
        # Add user message
        user_message = ChatMessage(
            session_id=session_id,
            role=MessageRole.USER,
            content=message_data.content,
            metadata=message_data.metadata
        )
        
        # Update session with user message
        await chat_sessions.update_one(
            {"id": session_id},
            {
                "$push": {"messages": user_message.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Generate AI response with enhanced logic
        ai_response = await self._generate_ai_response(
            message_data.content, 
            session, 
            user_id
        )
        
        # Add AI message
        ai_message = ChatMessage(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=ai_response.content,
            metadata=ai_response.metadata
        )
        
        # Update session with AI message
        await chat_sessions.update_one(
            {"id": session_id},
            {
                "$push": {"messages": ai_message.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Update session title if it's the first exchange
        if not session.title and len(session.messages) == 0:
            title = self._generate_session_title(message_data.content)
            await chat_sessions.update_one(
                {"id": session_id},
                {"$set": {"title": title}}
            )
        
        return ai_response

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session"""
        result = await chat_sessions.update_one(
            {"id": session_id, "user_id": user_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def update_session_title(
        self, 
        session_id: str, 
        title: str, 
        user_id: str
    ) -> Optional[ChatSession]:
        """Update session title"""
        await chat_sessions.update_one(
            {"id": session_id, "user_id": user_id},
            {"$set": {"title": title, "updated_at": datetime.utcnow()}}
        )
        
        return await self.get_session(session_id, user_id)

    async def _generate_ai_response(
        self, 
        user_message: str, 
        session: ChatSession, 
        user_id: str
    ) -> ChatResponse:
        """Generate AI response with tool execution"""
        
        # 1. Classify intent using AI
        intent = await self._classify_intent_with_ai(user_message)
        
        # 2. Extract parameters from message
        params = self._extract_parameters(user_message, intent)
        
        # 3. Execute appropriate tool
        data = await self._execute_tool(intent, params, user_id)
        
        # 4. Generate response based on data
        response_content = await self._generate_response_from_data(
            user_message, intent, data
        )
        
        return ChatResponse(
            session_id=session.id,
            message_id=str(uuid.uuid4()),
            content=response_content,
            intent=intent,
            confidence=0.85,  # High confidence with AI classification
            data_sources=[intent.value],
            metadata={
                "tool_used": intent.value,
                "data": data,
                "parameters": params
            }
        )

    async def _classify_intent_with_ai(self, message: str) -> ChatIntent:
        """Classify intent using Groq AI"""
        try:
            intent_descriptions = {
                "revenue_query": "Questions about revenue, income, earnings, sales",
                "expense_query": "Questions about expenses, spending, costs, outflows",
                "top_customer_query": "Questions about top customers, best clients, biggest customers",
                "top_supplier_query": "Questions about top suppliers, vendors, expenses by supplier",
                "cashflow_query": "Questions about cash flow, cash balance, money movement",
                "trend_query": "Questions about trends, patterns, changes over time",
                "forecast_query": "Questions about predictions, forecasts, future projections",
                "comparison_query": "Questions comparing periods (this month vs last, etc.)",
                "entity_breakdown": "Questions about specific entities, companies, detailed breakdowns",
                "general_query": "General questions, greetings, help requests"
            }
            
            prompt = f"""Classify this user query into one of these intents:
            
{chr(10).join([f"- {k}: {v}" for k, v in intent_descriptions.items()])}

User query: "{message}"

Return ONLY the intent name (e.g., "revenue_query")."""
            
            response = await self.groq_client.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{
                    "role": "system",
                    "content": "You are an intent classifier for a financial assistant. Classify the user's query into the most appropriate intent category."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=30,
                temperature=0.1
            )
            
            intent_str = response.choices[0].message.content.strip().lower()
            
            # Map to enum
            intent_mapping = {
                "revenue_query": ChatIntent.REVENUE_QUERY,
                "expense_query": ChatIntent.EXPENSE_QUERY,
                "top_customer_query": ChatIntent.TOP_CUSTOMER_QUERY,
                "top_supplier_query": ChatIntent.TOP_SUPPLIER_QUERY,
                "cashflow_query": ChatIntent.CASHFLOW_QUERY,
                "trend_query": ChatIntent.TREND_QUERY,
                "forecast_query": ChatIntent.FORECAST_QUERY,
                "comparison_query": ChatIntent.COMPARISON_QUERY,
                "entity_breakdown": ChatIntent.ENTITY_BREAKDOWN,
                "general_query": ChatIntent.GENERAL_QUERY
            }
            
            return intent_mapping.get(intent_str, ChatIntent.GENERAL_QUERY)
            
        except Exception as e:
            print(f"Error classifying intent: {e}")
            # Fallback to basic classification
            return self._classify_intent_basic(message)

    def _extract_parameters(self, message: str, intent: ChatIntent) -> Dict[str, Any]:
        """Extract parameters from user message"""
        params = {}
        message_lower = message.lower()
        
        # Extract time period
        if any(word in message_lower for word in ["week", "this week", "last week"]):
            params["period"] = "week"
        elif any(word in message_lower for word in ["month", "this month", "last month"]):
            params["period"] = "month"
        elif any(word in message_lower for word in ["quarter", "this quarter", "last quarter"]):
            params["period"] = "quarter"
        elif any(word in message_lower for word in ["year", "this year", "last year"]):
            params["period"] = "year"
        else:
            params["period"] = "month"  # Default
        
        # Extract entity name for entity breakdown
        if intent == ChatIntent.ENTITY_BREAKDOWN:
            # Look for company names in quotes or after keywords
            patterns = [
                r'"([^"]+)"',  # Quoted text
                r'for\s+(\w+(?:\s+\w+)*)',  # "for [company]"
                r'about\s+(\w+(?:\s+\w+)*)',  # "about [company]"
                r'show\s+me\s+(\w+(?:\s+\w+)*)',  # "show me [company]"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    params["entity_name"] = match.group(1).strip()
                    break
        
        # Extract metric for trend queries
        if intent == ChatIntent.TREND_QUERY:
            if any(word in message_lower for word in ["revenue", "income"]):
                params["metric"] = "revenue"
            elif any(word in message_lower for word in ["expense", "spend"]):
                params["metric"] = "expenses"
            else:
                params["metric"] = "revenue"  # Default
        
        # Extract comparison periods
        if intent == ChatIntent.COMPARISON_QUERY:
            if "last month" in message_lower and "this month" in message_lower:
                params["period1"] = "this_month"
                params["period2"] = "last_month"
            else:
                params["period1"] = "this_month"
                params["period2"] = "last_month"
        
        return params

    async def _execute_tool(self, intent: ChatIntent, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Execute the appropriate tool based on intent"""
        try:
            if intent == ChatIntent.REVENUE_QUERY:
                return await chat_tools.get_revenue_summary(user_id, params.get("period", "month"))
            
            elif intent == ChatIntent.EXPENSE_QUERY:
                return await chat_tools.get_expense_summary(user_id, params.get("period", "month"))
            
            elif intent == ChatIntent.TOP_CUSTOMER_QUERY:
                return await chat_tools.get_top_customer(user_id, params.get("period", "month"))
            
            elif intent == ChatIntent.TOP_SUPPLIER_QUERY:
                return await chat_tools.get_top_supplier(user_id, params.get("period", "month"))
            
            elif intent == ChatIntent.CASHFLOW_QUERY:
                return await chat_tools.get_cashflow_summary(user_id, params.get("period", "month"))
            
            elif intent == ChatIntent.TREND_QUERY:
                return await chat_tools.get_trend_analysis(user_id, params.get("metric", "revenue"))
            
            elif intent == ChatIntent.FORECAST_QUERY:
                # Use existing forecast service
                from ..forecasting.prophet_service import prophet_service
                return await prophet_service.generate_cashflow_forecast(user_id, 30)
            
            elif intent == ChatIntent.COMPARISON_QUERY:
                return await chat_tools.get_comparison_data(
                    user_id, 
                    params.get("period1", "this_month"),
                    params.get("period2", "last_month")
                )
            
            elif intent == ChatIntent.ENTITY_BREAKDOWN:
                entity_name = params.get("entity_name", "")
                return await chat_tools.get_entity_breakdown(user_id, entity_name)
            
            else:
                return {"message": "I can help you with revenue, expenses, customers, cashflow, trends, and forecasts. Ask me about any of these topics!"}
        
        except Exception as e:
            print(f"Error executing tool {intent}: {e}")
            return {"error": f"Unable to retrieve data: {str(e)}"}

    async def _generate_response_from_data(
        self, 
        user_message: str, 
        intent: ChatIntent, 
        data: Dict[str, Any]
    ) -> str:
        """Generate natural language response from data"""
        
        if "error" in data:
            return f"I apologize, but I encountered an error: {data['error']}. Please try again or rephrase your question."
        
        if "message" in data:
            return data["message"]
        
        # Generate response based on intent and data
        if intent == ChatIntent.REVENUE_QUERY:
            period = data.get("period", "month")
            revenue = data.get("total_revenue", 0)
            count = data.get("transaction_count", 0)
            avg = data.get("average_transaction", 0)
            
            return f"For the {period}, your total revenue is ${revenue:,.2f} from {count} transactions, with an average of ${avg:,.2f} per transaction."
        
        elif intent == ChatIntent.EXPENSE_QUERY:
            period = data.get("period", "month")
            expenses = data.get("total_expenses", 0)
            count = data.get("transaction_count", 0)
            avg = data.get("average_transaction", 0)
            
            return f"For the {period}, your total expenses are ${expenses:,.2f} from {count} transactions, with an average of ${avg:,.2f} per transaction."
        
        elif intent == ChatIntent.TOP_CUSTOMER_QUERY:
            customer = data.get("customer_name", "Unknown")
            revenue = data.get("total_revenue", 0)
            count = data.get("transaction_count", 0)
            period = data.get("period", "month")
            
            return f"Your top customer for the {period} is {customer} with ${revenue:,.2f} in revenue from {count} transactions."
        
        elif intent == ChatIntent.TOP_SUPPLIER_QUERY:
            supplier = data.get("supplier_name", "Unknown")
            expenses = data.get("total_expenses", 0)
            count = data.get("transaction_count", 0)
            period = data.get("period", "month")
            
            return f"Your top supplier for the {period} is {supplier} with ${expenses:,.2f} in expenses from {count} transactions."
        
        elif intent == ChatIntent.CASHFLOW_QUERY:
            period = data.get("period", "month")
            revenue = data.get("total_revenue", 0)
            expenses = data.get("total_expenses", 0)
            net = data.get("net_cashflow", 0)
            
            cashflow_status = "positive" if net > 0 else "negative"
            return f"For the {period}, you have ${revenue:,.2f} in revenue and ${expenses:,.2f} in expenses, resulting in a {cashflow_status} cashflow of ${net:,.2f}."
        
        elif intent == ChatIntent.TREND_QUERY:
            metric = data.get("metric", "revenue")
            trend = data.get("trend", "stable")
            change = data.get("change_percent", 0)
            recent_avg = data.get("recent_average", 0)
            
            if trend == "increasing":
                return f"Your {metric} is trending upward with a {change:.1f}% increase. Recent average: ${recent_avg:,.2f}."
            elif trend == "decreasing":
                return f"Your {metric} is trending downward with a {change:.1f}% decrease. Recent average: ${recent_avg:,.2f}."
            else:
                return f"Your {metric} is stable with minimal change. Recent average: ${recent_avg:,.2f}."
        
        elif intent == ChatIntent.FORECAST_QUERY:
            if data.get("status") == "insufficient_data":
                return data.get("message", "Insufficient data for forecasting.")
            
            forecast = data.get("forecast", [])
            if forecast:
                projected_balance = data.get("metrics", {}).get("projected_balance", 0)
                return f"Based on your historical data, I project your balance to be ${projected_balance:,.2f} in 30 days. The forecast shows your cashflow trends."
            else:
                return "I'm unable to generate a forecast at this time. Please check back when you have more transaction history."
        
        elif intent == ChatIntent.COMPARISON_QUERY:
            period1 = data.get("period1", {})
            period2 = data.get("period2", {})
            revenue_change = data.get("revenue_change_percent", 0)
            expenses_change = data.get("expenses_change_percent", 0)
            net_change = data.get("net_change", 0)
            
            response = f"Comparing periods: "
            if revenue_change != 0:
                direction = "up" if revenue_change > 0 else "down"
                response += f"Revenue is {direction} {abs(revenue_change):.1f}%. "
            if expenses_change != 0:
                direction = "up" if expenses_change > 0 else "down"
                response += f"Expenses are {direction} {abs(expenses_change):.1f}%. "
            if net_change != 0:
                direction = "higher" if net_change > 0 else "lower"
                response += f"Net cashflow is ${abs(net_change):,.2f} {direction}."
            
            return response
        
        elif intent == ChatIntent.ENTITY_BREAKDOWN:
            entity = data.get("entity_name", "Unknown")
            total = data.get("total_amount", 0)
            revenue = data.get("revenue", 0)
            expenses = data.get("expenses", 0)
            count = data.get("transaction_count", 0)
            
            return f"For {entity}: Total activity ${total:,.2f} ({revenue:,.2f} revenue, {expenses:,.2f} expenses) across {count} transactions."
        
        else:
            return "I'm here to help you with your financial data. You can ask me about revenue, expenses, customers, cashflow, trends, forecasts, or specific entities."

    def _classify_intent_basic(self, message: str) -> ChatIntent:
        """Basic intent classification (fallback)"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["revenue", "income", "earnings"]):
            return ChatIntent.REVENUE_QUERY
        elif any(word in message_lower for word in ["expense", "spend", "cost"]):
            return ChatIntent.EXPENSE_QUERY
        elif any(word in message_lower for word in ["customer", "client"]):
            return ChatIntent.TOP_CUSTOMER_QUERY
        elif any(word in message_lower for word in ["supplier", "vendor"]):
            return ChatIntent.TOP_SUPPLIER_QUERY
        elif any(word in message_lower for word in ["cashflow", "cash flow"]):
            return ChatIntent.CASHFLOW_QUERY
        elif any(word in message_lower for word in ["trend", "trending"]):
            return ChatIntent.TREND_QUERY
        elif any(word in message_lower for word in ["forecast", "predict"]):
            return ChatIntent.FORECAST_QUERY
        elif any(word in message_lower for word in ["compare", "comparison"]):
            return ChatIntent.COMPARISON_QUERY
        else:
            return ChatIntent.GENERAL_QUERY

    def _generate_session_title(self, first_message: str) -> str:
        """Generate a title for the session based on first message"""
        # Simple title generation - take first 50 characters
        title = first_message[:50]
        if len(first_message) > 50:
            title += "..."
        return title


chat_service = ChatService()
