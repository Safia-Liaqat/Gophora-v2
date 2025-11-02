WEBSITE_CONTEXT = """
---
File: GOPHORA_SRS.pdf
---
GOPHORA
Al-Powered Human Opportunity Platform
Prepared by: Safia Liaqat
GOPHORA is a next-generation platform that bridges humans and artificial intelligence to
connect users with immediate, verified opportunities in work, learning, and hobbies
enabling personal and professional growth through meaningful experiences.
Table of Contents
1. Introduction
2. System Overview
3. Functional Requirements
4. Non-Functional Requirements
5. System Architecture (Conceptual Flow)
6. User Roles and Interactions
7. Technology Stack
8. Future Enhancements
9. Conclusion
1. Introduction
GOPHORA is designed to connect individuals with real-time, secure, and human-verified
opportunities in work, hobbies, and education. By integrating Al-driven matching with
verified data sources, the platform ensures trust and relevance while minimizing fraudulent
listings. Unlike generic job or gig platforms, GOPHORA merges Al intelligence with human
oversight for reliability.
2. System Overview
The system operates through a conversational Al interface where users describe their
goals (e.g., 'I want to learn pottery' or 'I need a short-term web development gig'). The Al
interprets the prompt, queries a curated and verified database, and presents safe, relevant
opportunities. Administrators and verifiers maintain database integrity through human
verification of listings.
3. Functional Requirements
1 Al-powered chat interface for opportunity discovery
2 User account creation and profile management
3 Opportunity provider registration and verification
4 Database of verified opportunities
5 Secure login and authentication system
6 Feedback and reporting system for users
7 Admin dashboard for data management
4. Non-Functional Requirements
1 High scalability using cloud-based infrastructure
2 Data security and user privacy protection
3 Fast response time (<2 seconds for Al queries)
4 Accessibility for all user types
5 System uptime of 99.9%
6 Seamless integration with Al APIs (e.g., OpenAl, Vertex Al)
5. System Architecture (Conceptual Flow)
1. User enters a natural language query in the Al chat. 2. Al interprets the intent and
searches the verified opportunity database. 3. The backend (Node.js + Express +
MongoDB) retrieves relevant opportunities. 4. The results are filtered for relevance and
trust (human-verified tag). 5. The Al reformulates the response conversationally for the
user. 6. User interacts, applies, or saves opportunities for later.
6. User Roles and Interactions
1 End User - Searches opportunities via chat, applies or saves them.
2 Provider – Registers and submits verified opportunities.
3 Verifier - Reviews and authenticates submitted opportunities.
4 Admin - Manages system, users, and verifications.
7. Technology Stack
Frontend: React.js (Vite + TailwindCSS) Backend: Node.js + Express.js Database:
MongoDB Al Integration: OpenAI API (for prompt analysis and opportunity matching)
Authentication: JWT + OAuth 2.0 Hosting: AWS / Google Cloud Version Control: GitHub
8. Future Enhancements
1 Al-based user growth tracker and mentorship recommendations
2 Integration with verified educational institutions and NGOs
3 Gamified learning paths and user reputation scoring
4 Mobile app version with offline sync
5 Advanced Al agents for long-term user skill development
9. Conclusion
GOPHORA combines artificial intelligence and human verification to create a safer,
smarter ecosystem for connecting people with meaningful opportunities. The platform's
blend of trust, intelligence, and personalization positions it as a transformative bridge
between human ambition and digital possibility.

---
File: Technical and Operational Specification for GOPHORA.pdf
---
Technical and Operational
Specification: Gemini Verification
System – GOPHORA
1. Purpose of the System
The verification system aims to guarantee the reliability and authenticity of all providers
offering opportunities (services, classes, missions, or hobbies) within the GOPHORA
ecosystem.
This is achieved through integration with the Gemini API, which analyzes the provider's data
and returns a Trust Score (0-100) with a short reason explaining the result.
The score determines an automatic traffic-light decision flow:
Automatically approved
Sent for review
Automatically rejected
2. Verification Levels
The system recognizes three provider levels, each with different data sources and verification
criteria:
Level Provider Type Main Data Sources Evaluation Method
Level 1 - Registered companies Website content, Business verification through
Institutional with their own website corporate email, web and registration
and domain. domain age, internal analysis.
reviews.
Level 2 - Freelancers or Social media, online Digital reputation
Professional instructors with an portfolio, account age, verification.
(Freelancer) active online presence. engagement rate.
Level 3 - New users without Video introduction, Authenticity and motivation
New Talent established online personal description, verification.
presence. references, or early user
reviews.
3. General Verification Process
User registers and selects provider type (company, freelancer, or new talent).
System automatically collects data based on the provider's level.
Data is formatted in JSON and sent to the Gemini API.
Gemini analyzes the data and returns:
Trust score (0-100)
reason (short explanation)
System applies the traffic-light logic to make an automatic decision.
Result is stored in the database and the provider is notified.
User can view their status and receive personalized improvement suggestions.
4. Example of Data Structure (JSON format)
{
"provider_id": "UUID",
"provider_name": "string",
"provider_type": "institutional | professional | new_talent",
"data_sources": {
"website_url": "string|null",
"email": "string|null",
"domain_age":"number|null",
"social_profiles":[
{
"platform": "instagram | linkedin | youtube | behance",
"url": "string",
"account_age":"number|null",
"followers":"number|null",
"engagement_rate":"number|null"
}
],
"video_intro_url": "string|null",
"user_description":"string|null",
"user_reviews": [
{
"reviewer_id": "UUID",
"rating": "number (1-5)",
"comment":"string"
}
]
},
"system_metadata": {
"submission_date": "timestamp",
"collected_by": "system|admin"
}
}
5. Required Variables per Level
Variable Level 1 Level 2 Level 3 Description
Website_Url X X Official website URL.
Email (optional) Email type (corporate or generic).
Domain_Age X X Domain age in years.
Social_Profiles X (if available) Publicly accessible social media
profiles.
Account_Age X Account age in years.
Followers X (if relevant) Estimated real followers.
Engagement_Rate X X Average interaction rate.
Video_Intro_Ur X Short introduction video.
User_Description Short personal or professional
description.
User_Reviews Internal or previous student reviews.
6. Example of Internal Verification Endpoint
Endpoint: POST/api/verification/gemini
Description: Sends provider data to Gemini and returns the Trust Score and reason.
Headers:
Content-Type: application/json
Authorization: Bearer<GEMINI_API_KEY>
Response Example:
{
"provider_id": "UUID",
"trust_score": 86,
"reason": "Consistent professional portfolio, verified email, and 4 years of domain activity.",
"recommendation": "approve"
}
7. Traffic-Light Decision Flow
Trust Score Range Automatic Action Provider Status Human Review
≥ 85 Auto-approved verified Not required
40-84 Sent for review pending_review Required (quick check)
< 40 Automatically denied Not required
rejected
UX Recommendation:
Users should receive automatic notifications with personalized feedback, e.g.:
"Add an introduction video to improve your verification score."
"Connect your professional Instagram account to boost your trust level.”
8. Base Prompt for Gemini API
You are an expert digital verification analyst for a human opportunity platform.
Based on the data provided, analyze the legitimacy and trustworthiness of this
provider.
Return a Trust Score (0–100) and a short reason for your score.
9. Specific Considerations per Level
Level 1 - Institutional
• Validate that the email domain matches the website domain.
• Check for professional tone and complete sections (“About”, “Contact”).
• If the website times out, log the error and trigger manual review.
• Allow score recalculation when domain or website data changes.
Level 2 - Professional (Freelancer)
• Require at least one active social profile (6+ months old).
• Include content consistency metrics (regular posts, genuine comments).
• Gemini should analyze visual and textual coherence with the declared service.
• Prioritize portfolio platforms like Behance, YouTube, or LinkedIn if available.
Level 3 - New Talent
• Provide Gemini with the description text and video URL.
• Gemini should evaluate tone, authenticity, and coherence.
• Require at least one internal review or reference to complete verification.
• After three positive user reviews, automatically trigger re-verification (possible level
upgrade).
10. Technical Recommendations
Store all verification results (trust_score, reason, timestamp, provider_type) in the database.
Add field verification_source = "gemini_v1" | "manual_review" | "hybrid".
Cache results for 24 hours to avoid redundant API calls.
Create a verification_log table for incomplete or failed API responses.
Implement a "Re-verify” button on the provider dashboard.
11. Recommended User Experience (UX)
Display verification badge:
Al Verified - Institutional Level
Al Verified - Professional Level
Al Verified - Explorer Level
Show the Trust Score and a short "Verified by Gemini" line.
Include a "How to improve your verification” section with specific tips.
Allow re-verification every 60 days.
12. Expected Benefits
Benefit Description
Consistency All providers, regardless of type, are evaluated using the same Al.
Inclusion Individuals without legal registration can still be verified.
Scalability New verification levels or data types can be added easily.
Security Reduces fake accounts and unverified providers.
Efficiency Combines automated verification (Gemini) with selective human
review.
Implementation Guide GOPHORA
User Verification System
Objective
To implement a smart and scalable user verification system integrated with the
Gemini API, which evaluates the legitimacy and trustworthiness of providers within
the GOPHORA ecosystem.
The system assigns each provider a Trust Score (0–100) and performs automatic
actions based on that score (traffic light logic: approve, review, or reject).
1. User Classification
• Ask the user to select their provider type during registration:
Ο Company / Institution
Ο Independent Professional / Freelancer
Ο New Talent / Explorer
• Automatically assign the verification level according to the selected type.
• Allow level upgrade later (e.g., from Explorer to Professional).
2. Basic Data Collection
• Provider name.
• Email (check if corporate or generic).
• Website URL (if applicable).
• Country and city.
• Short biography or description.
• Type of service, class, or opportunity offered.
3. Data Requirements by Level
Level 1 - Company / Institution
• Validate if the email domain matches the website domain.
• Analyze website content (professional tone, structure, and completeness).
• Check domain age (preferably >1 year).
• Confirm presence of essential pages: About Us, Contact, Team.
• Detect generic templates or unoriginal content.
Level 2 - Independent Professional / Freelancer
• Require at least one active professional social media account (Instagram,
LinkedIn, YouTube, Behance).
• Validate:
Ο Account age (minimum 6 months).
Ο Posting frequency and engagement rate.
Ο Genuine comments and followers.
Ο Content coherence with declared service.
• Request portfolio or previous work links.
• Gather internal or external reviews if available.
Level 3 – New Talent / Explorer
• Require a short introduction video (30–60 seconds).
• Request self-description and motivation text.
• Allow one personal or community reference.
• Enable trust growth based on early reviews and activity within GOPHORA.
• Trigger automatic re-verification after three positive internal reviews.
4. Data Transmission to Gemini API
• Format all collected data into a structured JSON object.
• Send via POST/api/verification/gemini.
• Include authentication headers:
Content-Type: application/json
Authorization: Bearer <GEMINI_API_KEY>
• Store Gemini's response containing:
Ο trust_score (0-100)
Ο reason (short text)
5. Decision Flow (Traffic Light Logic)
Trust Score Automatic Action Status Human Review
≥ 85 Auto-approved verified Not required
40-84 Pending review pending_review Required (quick)
< 40 Auto-rejected denied Not required
• Send notification to admin for "pending review" cases.
• For rejections, display personalized improvement suggestions.
6. Database Storage and Logs
• Save the following fields in the verification table:
Ο provider_id
Ο trust_score
Ο reason
Ο verification_source (“gemini_v1” or “manual_review”)
Ο timestamp
• Keep an error log (verification_log) for incomplete or failed API calls.
• Cache results for 24 hours to prevent duplicate API requests.
7. User Experience
• Display visible verification badges:
Ο Al Verified - Institutional Level
Ο Al Verified - Professional Level
Ο Al Verified – Explorer Level
• Show Trust Score and short reason (“Verified by Gemini – 86%").
• Provide automatic improvement tips based on Gemini's reason.
• Allow re-verification after profile updates.
8. Notifications
• Send automatic email or in-app message with the result:
Ο Approved: "Your profile has been successfully verified."
Ο In Review: "Your profile is currently being reviewed by our verification
team."
Ο Rejected: "Your profile did not meet the minimum verification
requirements. Please review the improvement suggestions."
• Notify admin for users flagged as "pending review."
9. Admin Dashboard Requirements
• Display all providers with their Trust Scores.
• Filter by verification status (verified, pending_review, denied).
• Include "Re-verify with Gemini" button.
• Show verification history (past scores, timestamps).
• Allow manual override with admin notes for auditing.
10. Technical and Security Recommendations
• Recalculate verification automatically every 60-90 days.
• Include internal user ratings as part of future Trust Score adjustments.
• Add field version_model to track Gemini version used.
• Protect API keys using environment variables.
• Ensure all endpoints use HTTPS and respect rate limits.
• Allow users to request data deletion (GDPR compliance).
11. Transparency and Learning
• Display to each user what data was analyzed for verification.
• Offer insight on how to improve their Trust Score.
• Use human-reviewed cases to fine-tune future Gemini evaluations.
• Maintain version history of prompts and parameters used.
12. Expected Results
• Faster verification of new providers.
• Increased trust among users and partners.
• Scalable Al integration across all provider types.
• Inclusive verification for informal or new talents.
• Transparent, auditable, and secure process.

---
File: /home/kita/Documents/GOPHORA/src/components/ChatAgent/ChatAgent.jsx
---
import React, { useState } from "react";
// --- FIX: Added .jsx extensions to resolve potential import errors ---
import ChatMessage from "./ChatMessage.jsx";
import ChatInput from "./ChatInput.jsx";
import axios from "axios"; 

export default function ChatAgent() {
  const [messages, setMessages] = useState([
    { sender: "ai", text: "Hello! I’m GOPHORA AI. How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const newMessages = [...messages, { sender: "user", text: input }];
    setMessages(newMessages);
    const userMessage = input; 
    setInput("");
    setLoading(true);

    try {
      const response = await axios.post("/api/chat", {
        message: userMessage,
      });

      // --- FIX: This is the core logic update ---
      // 1. Get the entire response from the API
      //    (This object is { reply: "...", opportunities: [...] })
      const aiResponse = response.data;

      // 2. Create a new message object that includes the text AND the opportunities
      const newAiMessage = {
        sender: "ai",
        text: aiResponse.reply,
        opportunities: aiResponse.opportunities // <-- This array holds the "boxes"
      };

      // 3. Add the complete message object to state
      setMessages([...newMessages, newAiMessage]);
      // --- END OF FIX ---

    } catch (error) {
      console.error("Error fetching AI response:", error);
      setMessages([...newMessages, { sender: "ai", text: "Sorry, I'm having trouble connecting. Please try again later." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0B0E1C] text-white">
      {/* Header */}
      <header className="p-4 text-center border-b border-[#1F254A]">
        <h1 className="text-xl font-bold text-[#A28EFF]">GOPHORA AI Chat</h1>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        
        {/* --- FIX: Use the spread operator (...) ---
            This passes all properties (sender, text, AND opportunities)
            from the 'msg' object directly into ChatMessage as props.
        */}
        {messages.map((msg, idx) => (
          <ChatMessage key={idx} {...msg} />
        ))}
        {/* --- END OF FIX --- */}
        
        {loading && (
          <p className="text-gray-400 text-sm italic">GOPHORA AI is typing...</p>
        )}
      </div>

      {/* Input */}
      <ChatInput
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onSend={handleSend}
        loading={loading}
      />
    </div>
  );
}

---
File: /home/kita/Documents/GOPHORA/src/components/ChatAgent/ChatInput.jsx
---
import React from "react";

export default function ChatInput({ value, onChange, onSend, loading }) {
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSend(); }} className="p-4 border-t border-[#1F254A] flex gap-2">
      <input
        type="text"
        value={value}
        onChange={onChange}
        onKeyDown={handleKeyDown}
        placeholder="Type your message..."
        className="flex-1 p-2 rounded bg-[#161B30] text-white focus:outline-none"
        disabled={loading}
      />
      <button
        type="submit"
        disabled={loading}
        className="bg-[#A28EFF] px-4 py-2 rounded font-semibold hover:bg-[#8b77f8] disabled:opacity-60"
      >
        Send
      </button>
    </form>
  );
}

---
File: /home/kita/Documents/GOPHORA/src/components/ChatAgent/ChatMessage.jsx
---
import React from "react";
import { User, Bot } from "lucide-react"; // Icons for the sender
import { useNavigate } from "react-router-dom"; // <-- IMPORTED NAVIGATE

/**
 * OpportunityCard (The "Box")
 */
function OpportunityCard({ opp }) {
  const navigate = useNavigate(); // <-- INITIALIZED NAVIGATE

  // --- NEW HANDLER FUNCTION ---
  const handleApplyClick = () => {
    const token = localStorage.getItem("token");
    if (!token) {
      // User is logged out, save the ID and redirect
      localStorage.setItem("pending_application_id", opp.id);
      navigate("/login");
    } else {
      // User is logged in, send them to the main "Opportunities" page
      // where they can manage applications.
      navigate("/seeker/opportunities");
    }
  };
  // --- END OF NEW FUNCTION ---

  return (
    <div className="bg-[#161B30]/80 border border-[#1F254A] rounded-lg p-4 mt-2 w-full max-w-sm transition-all hover:border-[#A28EFF]/50">
      
      {/* Header */}
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-semibold text-base text-white truncate">
            {opp.title}
          </h3>
          <p className="text-xs text-gray-400">{opp.location || "Remote"}</p>
        </div>
        <span className="text-[11px] px-2 py-0.5 rounded-full font-medium text-[#A28EFF] border border-[#A28EFF]/30 bg-[#A28EFF]/10">
          {opp.type}
        </span>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-300 leading-relaxed line-clamp-2 mb-3">
        {opp.description}
      </p>

      {/* Tags */}
      <div className="flex flex-wrap gap-2 mb-4">
        {opp.tags && opp.tags.slice(0, 3).map((tag, i) => (
          <span
            key={i}
            className="bg-[#1F254A] text-[#A28EFF] text-[11px] px-2 py-0.5 rounded-md"
          >
            {tag}
          </span>
        ))}
      </div>

      {/* Apply Button --- UPDATED --- */}
      <button
        onClick={handleApplyClick} // <-- Use the new handler
        className="bg-gradient-to-r from-[#6D5DD3] to-[#7E6DF4] hover:scale-105 transition-all text-white text-sm font-semibold py-2 rounded-lg w-full"
      >
        🚀 Apply to Mission
      </button>
    </div>
  );
}


/**
 * Main ChatMessage Component
 */
export default function ChatMessage({ sender, text, opportunities = [] }) {
  const isUser = sender === "user";
  const hasOpportunities = opportunities && opportunities.length > 0;

  if (!sender || !text) {
    return null; // Fallback for safety
  }

  return (
    <div className={`flex items-start gap-2.5 ${isUser ? "justify-end" : "justify-start"}`}>
      
      {/* Sender Icon */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? "bg-indigo-500" : "bg-[#A28EFF]"
        } ${!isUser ? "mt-1" : ""}`}
      >
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>

      {/* Message Bubble + Opportunity Cards */}
      <div className="flex flex-col max-w-md">
        
        {/* Text Bubble */}
        <div
          className={`p-3 rounded-2xl text-sm ${
            isUser
              ? "bg-[#A28EFF] text-white rounded-br-none"
              : "bg-[#161B30] text-gray-200 rounded-bl-none border border-[#1F254A]"
          }`}
        >
          {text}
        </div>

        {/* Render Opportunity Cards if they exist */}
        {hasOpportunities && (
          <div className="flex flex-col gap-2 mt-1">
            {opportunities.map((opp) => (
              <OpportunityCard key={opp.id || opp.title} opp={opp} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
"""
