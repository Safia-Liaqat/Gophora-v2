"""
AI Validation Pipeline using LangChain and Multiple AI Models
Validates scraped opportunities for credibility, quality, and categorization
"""
import os
from typing import Dict, List, Optional
from datetime import datetime
import re
import logging

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for structured output
class OpportunityValidation(BaseModel):
    """Validation result schema"""
    is_legitimate: bool = Field(description="Whether the opportunity is legitimate")
    trust_score: int = Field(description="Trust score from 0-100")
    confidence: float = Field(description="Confidence level of validation (0.0-1.0)")
    red_flags: List[str] = Field(description="List of identified red flags")
    credibility_notes: str = Field(description="Notes about credibility assessment")


class OpportunityCategory(BaseModel):
    """Categorization result schema"""
    primary_category: str = Field(description="Primary category: Work, Education, Hobbies, or Contribution")
    subcategory: str = Field(description="Specific subcategory")
    skill_level: str = Field(description="Required skill level: zero, low, medium, high")
    is_immediate: bool = Field(description="Whether this is an immediate start opportunity")
    payment_timeframe: Optional[str] = Field(description="Expected payment timeframe")


class OpportunityMetadata(BaseModel):
    """Extracted metadata schema"""
    required_skills: List[str] = Field(description="List of required skills")
    salary_range: Optional[str] = Field(description="Salary or compensation range")
    location: str = Field(description="Job location or 'Remote'")
    experience_level: str = Field(description="Required experience level")
    time_commitment: Optional[str] = Field(description="Time commitment required")
    deadline: Optional[str] = Field(description="Application deadline if mentioned")
    

class AIValidationPipeline:
    """AI-powered validation pipeline using multiple models"""
    
    def __init__(self):
        # Initialize Gemini models
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=self.gemini_api_key)
        
        # LangChain Gemini models
        self.gemini_chat = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=self.gemini_api_key,
            temperature=0.3
        )
        
        self.gemini_embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=self.gemini_api_key
        )
        
        # Optional: OpenAI for cross-validation
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_chat = ChatOpenAI(
                model="gpt-4",
                temperature=0.3,
                openai_api_key=openai_key
            )
        else:
            self.openai_chat = None
            logger.warning("OpenAI API key not found. Using Gemini only.")
        
        # Initialize parsers
        self.validation_parser = JsonOutputParser(pydantic_object=OpportunityValidation)
        self.category_parser = JsonOutputParser(pydantic_object=OpportunityCategory)
        self.metadata_parser = JsonOutputParser(pydantic_object=OpportunityMetadata)
        
        # Create validation chain
        self._setup_chains()
    
    def _setup_chains(self):
        """Setup LangChain prompts and chains"""
        
        # Validation prompt
        validation_template = """You are an expert at detecting fraudulent job postings and scams.
Analyze the following job opportunity and determine if it is legitimate.

Job Title: {title}
Company: {company}
Description: {description}
Source: {source}
URL: {url}

Look for red flags such as:
- Promises of unrealistic income
- Requests for upfront payment
- Poor grammar and spelling
- Vague job descriptions
- Requests for personal/financial information
- "Work from home" schemes
- Pyramid schemes or MLM

{format_instructions}

Provide your analysis:"""

        self.validation_prompt = PromptTemplate(
            template=validation_template,
            input_variables=["title", "company", "description", "source", "url"],
            partial_variables={"format_instructions": self.validation_parser.get_format_instructions()}
        )
        
        self.validation_chain = self.validation_prompt | self.gemini_chat | self.validation_parser
        
        # Categorization prompt
        category_template = """Analyze the following job opportunity and categorize it.

Job Title: {title}
Company: {company}
Description: {description}

Categories:
- Work: Paid employment, freelance, contract work
- Education: Learning opportunities, courses, teaching
- Hobbies: Creative projects, community activities
- Contribution: Volunteering, social impact, charity work

Skill Levels:
- zero: No skills required, anyone can start immediately
- low: Minimal skills, quick training provided
- medium: Some experience or skills required
- high: Advanced skills or extensive experience required

Determine if this is an IMMEDIATE opportunity (can start within 24-48 hours and get paid quickly).

{format_instructions}

Provide your categorization:"""

        self.category_prompt = PromptTemplate(
            template=category_template,
            input_variables=["title", "company", "description"],
            partial_variables={"format_instructions": self.category_parser.get_format_instructions()}
        )
        
        self.category_chain = self.category_prompt | self.gemini_chat | self.category_parser
        
        # Metadata extraction prompt
        metadata_template = """Extract detailed metadata from the following job opportunity.

Job Title: {title}
Company: {company}
Description: {description}
Location: {location}

Extract:
- Required skills (list specific technical or soft skills)
- Salary/compensation range (if mentioned)
- Location (remote, hybrid, specific city)
- Experience level (entry, mid, senior)
- Time commitment (full-time, part-time, hourly, project-based)
- Application deadline (if mentioned)

{format_instructions}

Extract the metadata:"""

        self.metadata_prompt = PromptTemplate(
            template=metadata_template,
            input_variables=["title", "company", "description", "location"],
            partial_variables={"format_instructions": self.metadata_parser.get_format_instructions()}
        )
        
        self.metadata_chain = self.metadata_prompt | self.gemini_chat | self.metadata_parser
    
    async def validate_opportunity(self, job_data: Dict) -> Dict:
        """
        Validate a scraped opportunity using AI
        Returns comprehensive validation result
        """
        try:
            # Extract job data
            title = job_data.get('title', '')
            company = job_data.get('company', '')
            description = job_data.get('description', '')
            source = job_data.get('source', '')
            url = job_data.get('url', '')
            location = job_data.get('location', '')
            
            # Run validation
            validation_result = await self.validation_chain.ainvoke({
                "title": title,
                "company": company,
                "description": description,
                "source": source,
                "url": url
            })
            
            # Run categorization
            category_result = await self.category_chain.ainvoke({
                "title": title,
                "company": company,
                "description": description
            })
            
            # Extract metadata
            metadata_result = await self.metadata_chain.ainvoke({
                "title": title,
                "company": company,
                "description": description,
                "location": location
            })
            
            # Generate embedding for semantic search
            embedding_text = f"{title} {company} {description}"
            embedding = self.gemini_embeddings.embed_query(embedding_text)
            
            # Compile full validation result
            full_result = {
                **job_data,
                "validation": validation_result,
                "category": category_result,
                "metadata": metadata_result,
                "embedding": embedding,
                "validated_at": datetime.utcnow().isoformat(),
                "validation_version": "1.0"
            }
            
            # Determine if job passes validation
            full_result["approved"] = (
                validation_result["is_legitimate"] and 
                validation_result["trust_score"] >= 70
            )
            
            return full_result
            
        except Exception as e:
            logger.error(f"Error validating opportunity: {e}")
            return {
                **job_data,
                "validation": {
                    "is_legitimate": False,
                    "trust_score": 0,
                    "confidence": 0.0,
                    "red_flags": ["Validation failed"],
                    "credibility_notes": f"Error during validation: {str(e)}"
                },
                "approved": False,
                "error": str(e)
            }
    
    def validate_opportunity_sync(self, job_data: Dict) -> Dict:
        """Synchronous version of validate_opportunity"""
        try:
            title = job_data.get('title', '')
            company = job_data.get('company', '')
            description = job_data.get('description', '')
            source = job_data.get('source', '')
            url = job_data.get('url', '')
            location = job_data.get('location', '')
            
            # Run validation
            validation_result = self.validation_chain.invoke({
                "title": title,
                "company": company,
                "description": description,
                "source": source,
                "url": url
            })
            
            # Run categorization
            category_result = self.category_chain.invoke({
                "title": title,
                "company": company,
                "description": description
            })
            
            # Extract metadata
            metadata_result = self.metadata_chain.invoke({
                "title": title,
                "company": company,
                "description": description,
                "location": location
            })
            
            # Generate embedding
            embedding_text = f"{title} {company} {description}"
            embedding = self.gemini_embeddings.embed_query(embedding_text)
            
            full_result = {
                **job_data,
                "validation": validation_result,
                "category": category_result,
                "metadata": metadata_result,
                "embedding": embedding,
                "validated_at": datetime.utcnow().isoformat(),
                "validation_version": "1.0"
            }
            
            full_result["approved"] = (
                validation_result["is_legitimate"] and 
                validation_result["trust_score"] >= 70
            )
            
            return full_result
            
        except Exception as e:
            logger.error(f"Error validating opportunity: {e}")
            return {
                **job_data,
                "validation": {
                    "is_legitimate": False,
                    "trust_score": 0,
                    "confidence": 0.0,
                    "red_flags": ["Validation failed"],
                    "credibility_notes": f"Error during validation: {str(e)}"
                },
                "approved": False,
                "error": str(e)
            }
    
    def batch_validate(self, jobs: List[Dict]) -> List[Dict]:
        """Validate multiple jobs in batch"""
        validated_jobs = []
        
        for job in jobs:
            try:
                validated = self.validate_opportunity_sync(job)
                validated_jobs.append(validated)
            except Exception as e:
                logger.error(f"Error in batch validation: {e}")
                continue
        
        return validated_jobs
    
    def filter_immediate_jobs(self, validated_jobs: List[Dict]) -> List[Dict]:
        """Filter for immediate, zero/low-skill jobs"""
        immediate_jobs = []
        
        for job in validated_jobs:
            if not job.get("approved"):
                continue
            
            category = job.get("category", {})
            
            # Check if it's immediate and low-skill
            if (category.get("is_immediate") and 
                category.get("skill_level") in ["zero", "low"]):
                immediate_jobs.append(job)
        
        return immediate_jobs
    
    def filter_skill_based_jobs(self, validated_jobs: List[Dict], user_skills: List[str] = None) -> List[Dict]:
        """Filter for skill-based jobs, optionally matching user skills"""
        skill_based_jobs = []
        
        for job in validated_jobs:
            if not job.get("approved"):
                continue
            
            category = job.get("category", {})
            metadata = job.get("metadata", {})
            
            # Check if it requires skills
            if category.get("skill_level") in ["medium", "high"]:
                # If user skills provided, check for match
                if user_skills:
                    required_skills = metadata.get("required_skills", [])
                    if any(skill.lower() in [rs.lower() for rs in required_skills] for skill in user_skills):
                        skill_based_jobs.append(job)
                else:
                    skill_based_jobs.append(job)
        
        return skill_based_jobs
