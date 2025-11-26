"""
Intelligent AI Chatbot using LangChain and Gemini
- Answers any user question with accurate information
- Provides job recommendations from database
- Uses RAG (Retrieval Augmented Generation) for context-aware responses
"""
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntelligentChatbot:
    """Advanced chatbot with LangChain and Gemini AI"""
    
    def __init__(self, firestore_helper):
        self.firestore = firestore_helper
        
        # Initialize Gemini
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash-latest",
                google_api_key=self.gemini_api_key,
                temperature=0.7,
                max_tokens=2000
            )
            
            self.ai_enabled = True
            logger.info("✅ Intelligent chatbot initialized with Gemini AI")
        else:
            self.ai_enabled = False
            logger.warning("⚠️ GEMINI_API_KEY not found - using fallback mode")
        
        # Simple conversation history storage
        self.chat_history = []
        
        # Setup prompt template
        self._setup_prompt()
    
    def _setup_prompt(self):
        """Setup the chatbot prompt template"""
        
        self.system_prompt = """You are Gophora AI, an intelligent job search assistant. You help users find job opportunities, answer career-related questions, and provide guidance.

Your capabilities:
1. Answer ANY question the user asks - technical, general knowledge, career advice, etc.
2. Search and recommend jobs from the database when relevant
3. Provide detailed, accurate, and helpful responses
4. Be conversational and friendly while remaining professional

Current context:
- You have access to a job database with various opportunities
- You can search jobs by skills, location, title, or description
- You provide direct links to apply for jobs

When discussing jobs:
- Always include the source URL for applying
- Mention key details like company, location, and requirements
- Be honest about job availability

Guidelines:
- Be accurate and factual
- If you don't know something, say so clearly
- Provide helpful suggestions and next steps
- Keep responses concise but comprehensive
- Use a friendly, professional tone

Previous conversation:
{chat_history}

User's question: {user_message}

Database context (if relevant): {job_context}

Your response:"""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_message}")
        ])
    
    def _search_relevant_jobs(self, user_message: str, limit: int = 5) -> List[Dict]:
        """Search for relevant jobs based on user message"""
        try:
            from backend.firebase_config import FirestoreCollections
            
            # Extract potential job keywords
            message_lower = user_message.lower()
            
            # Common job search keywords
            job_keywords = ['job', 'jobs', 'work', 'opportunity', 'opportunities', 
                          'hiring', 'position', 'role', 'career', 'apply']
            
            # Skills to search for
            skills = ['python', 'javascript', 'java', 'react', 'node', 'sql', 
                     'aws', 'docker', 'machine learning', 'data science', 
                     'customer service', 'marketing', 'sales', 'design']
            
            # Check if user is asking about jobs
            is_job_query = any(keyword in message_lower for keyword in job_keywords)
            
            if not is_job_query:
                # Check if specific skills mentioned
                mentioned_skills = [skill for skill in skills if skill in message_lower]
                if not mentioned_skills:
                    return []
            
            # Get jobs from both collections
            jobs = []
            
            # Get immediate jobs
            immediate_jobs = self.firestore.get_all_documents(
                FirestoreCollections.IMMEDIATE_JOBS,
                limit=limit
            )
            jobs.extend(immediate_jobs)
            
            # Get skill-based jobs
            skill_jobs = self.firestore.get_all_documents(
                FirestoreCollections.SKILL_BASED_JOBS,
                limit=limit
            )
            jobs.extend(skill_jobs)
            
            # Filter by relevance if specific skills mentioned
            if 'mentioned_skills' in locals() and mentioned_skills:
                filtered_jobs = []
                for job in jobs:
                    job_text = f"{job.get('title', '')} {job.get('description', '')} {' '.join(job.get('skills', []))}".lower()
                    if any(skill in job_text for skill in mentioned_skills):
                        filtered_jobs.append(job)
                jobs = filtered_jobs
            
            return jobs[:limit]
            
        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            return []
    
    def _format_job_context(self, jobs: List[Dict]) -> str:
        """Format jobs as context for the AI"""
        if not jobs:
            return "No relevant jobs found in database."
        
        context = "Available job opportunities:\n\n"
        
        for i, job in enumerate(jobs, 1):
            context += f"{i}. {job.get('title', 'Unknown Title')}\n"
            context += f"   Company: {job.get('company', 'Not specified')}\n"
            context += f"   Location: {job.get('location', 'Remote')}\n"
            
            if job.get('description'):
                desc = job.get('description', '')[:200] + "..." if len(job.get('description', '')) > 200 else job.get('description', '')
                context += f"   Description: {desc}\n"
            
            if job.get('skills'):
                context += f"   Skills: {', '.join(job.get('skills', [])[:5])}\n"
            
            if job.get('source_url'):
                context += f"   Apply: {job.get('source_url')}\n"
            
            context += "\n"
        
        return context
    
    async def chat(self, user_message: str, user_id: Optional[str] = None) -> Dict:
        """
        Process user message and generate intelligent response
        
        Args:
            user_message: User's question/message
            user_id: Optional user ID for personalization
        
        Returns:
            Dict with response and relevant jobs
        """
        try:
            # Search for relevant jobs
            relevant_jobs = self._search_relevant_jobs(user_message)
            job_context = self._format_job_context(relevant_jobs)
            
            if self.ai_enabled:
                try:
                    logger.info(f"Processing with Gemini AI: {user_message[:50]}...")
                    
                    # Build the prompt with simpler template
                    prompt_text = f"""You are Gophora AI, a helpful job search assistant.

User's question: {user_message}

Available jobs context: {job_context if job_context else "No specific jobs found"}

Instructions:
- Answer the user's question directly and naturally
- If they ask about jobs, mention relevant opportunities
- If they ask general questions (like "where is pakistan"), just answer normally
- Be friendly and conversational

Your response:"""

                    # Direct API call without complex chains
                    ai_response = self.llm.invoke(prompt_text)
                    
                    # Extract text from AI message
                    response = ai_response.content if hasattr(ai_response, 'content') else str(ai_response)
                    
                    logger.info(f"Gemini response received: {response[:100] if len(response) > 100 else response}...")
                    
                    # Save to history
                    self.chat_history.append(HumanMessage(content=user_message))
                    self.chat_history.append(AIMessage(content=response))
                    
                except Exception as ai_error:
                    logger.error(f"Gemini API error: {ai_error}", exc_info=True)
                    response = self._generate_fallback_response(user_message, relevant_jobs)
                
            else:
                # Fallback response
                response = self._generate_fallback_response(user_message, relevant_jobs)
            
            return {
                "response": response,
                "opportunities": relevant_jobs[:3],  # Return top 3 jobs
                "timestamp": datetime.utcnow().isoformat(),
                "ai_powered": self.ai_enabled
            }
            
        except Exception as e:
            logger.error(f"Chatbot error: {e}", exc_info=True)
            
            return {
                "response": f"I apologize, but I encountered an error: {str(e)}. Please try asking your question differently.",
                "opportunities": [],
                "timestamp": datetime.utcnow().isoformat(),
                "ai_powered": False
            }
    
    def _generate_fallback_response(self, message: str, jobs: List[Dict]) -> str:
        """Generate response when AI is not available"""
        message_lower = message.lower()
        
        # Job search queries
        if any(word in message_lower for word in ['job', 'work', 'opportunity', 'hiring']):
            if jobs:
                response = f"I found {len(jobs)} opportunities for you! Here are some options:\n\n"
                for i, job in enumerate(jobs[:3], 1):
                    response += f"{i}. **{job.get('title')}** at {job.get('company', 'Unknown Company')}\n"
                    response += f"   Location: {job.get('location', 'Remote')}\n"
                    if job.get('source_url'):
                        response += f"   Apply here: {job.get('source_url')}\n"
                    response += "\n"
                return response
            else:
                return "I couldn't find any jobs matching your criteria right now. We're constantly updating our database. Try asking about specific skills like 'Python jobs' or 'remote positions'."
        
        # General queries
        return "I'm here to help you find job opportunities! Try asking me things like:\n- 'Find me Python developer jobs'\n- 'What remote jobs are available?'\n- 'Show me entry-level positions'\n\nFeel free to ask me anything!"
    
    def clear_memory(self):
        """Clear conversation history"""
        self.chat_history = []
        logger.info("Conversation memory cleared")
