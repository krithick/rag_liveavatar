"""Test chat interaction with Realtime API + RAG"""

import asyncio
import json
import websockets
from config import Config
from rag_service import DynamicRAG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# # Test questions - ALL 225 questions from your dataset
TEST_QUESTIONS = [
    # CATEGORY 1: BASIC PLATFORM INFORMATION (20 questions)
    "What is the myCoach vision statement?",
    "What is the purpose of myCoach?",
    "When was myCoach founded?",
    "How many years is myCoach celebrating?",
    "Who founded myCoach?",
    "What inspired the creation of myCoach?",
    "How many users does myCoach have?",
    "How many courses does myCoach offer?",
    "How many modules are available?",
    "How many languages is myCoach available in?",
    "What languages does myCoach support?",
    "Is myCoach available 24/7?",
    "Does myCoach have a mobile app?",
    "What domains does myCoach cover?",
    "Which Shriram Group companies use myCoach?",
    "What is myCoach?",
    "When did myCoach start celebrating its anniversary?",
    "Is myCoach only for one company?",
    "What type of platform is myCoach?",
    "What makes myCoach different?",
    
    # CATEGORY 2: LEADERSHIP & TEAM (25 questions)
    "Who is the mentor shaping the e-learning vision?",
    "Who is the architect of simplified learning at myCoach?",
    "Who drives strategic infrastructure for myCoach?",
    "Who enables innovation and growth at myCoach?",
    "Who leads execution excellence at myCoach?",
    "Who is the Content Head?",
    "Who leads AR & VR initiatives?",
    "Who is the Project Manager & Subject Matter Expert?",
    "Who are the Production Managers?",
    "Who manages Quality Control?",
    "Who is the LMS Head?",
    "Who is the Delivery Manager?",
    "Who is the Product Manager?",
    "Who is the CTO in the tech core team?",
    "Who is the Executive Director in the tech team?",
    "Who are the Life Insurance SMEs?",
    "Who are the General Insurance SMEs?",
    "Who leads Wealth Management expertise?",
    "Who provides Financial Products expertise?",
    "Who is the MD & CEO of SLIC?",
    "Who is the COO of SLIC?",
    "Who is the CMO of SLIC?",
    "Who is the CHRO of SLIC?",
    "Who is the EVP of SLIC?",
    "Who is the CEO of SFL Marketing?",
    
    # CATEGORY 3: ORGANIZATION-SPECIFIC DATA (30 questions)
    "How many users does SLIC have on myCoach?",
    "How many users does SGI have?",
    "How many users does SFL have?",
    "How many users does Shriram Chits have?",
    "Which organization has the most myCoach users?",
    "When did SLIC launch myCoach?",
    "When did Shriram Fortune Solutions launch myCoach?",
    "When did Shriram Chits launch myCoach?",
    "When did SGI launch myCoach?",
    "When did SFL launch myCoach?",
    "When did Shriram Wealth launch myCoach?",
    "Which organization was the first to launch myCoach?",
    "Which is the most recent organization to adopt myCoach?",
    "How many users did SLIC have at launch?",
    "How many modules did SLIC have at launch?",
    "How many users did SFS have at launch?",
    "How many modules did Chits have at launch?",
    "How many users did SGI have at launch?",
    "How many users did SFL have at launch?",
    "How many modules did SFL have at launch?",
    "When did SFL expand language support beyond 4 languages?",
    "How many modules does Shriram Wealth have?",
    "How many users does Shriram Wealth have?",
    "What languages were available when SLIC launched?",
    "How many languages does SFL support?",
    "Which organization launched with the most users?",
    "Which organization launched with the most modules?",
    "How many organizations use myCoach?",
    "What year did most organizations launch myCoach?",
    "Is myCoach used across all Shriram Group companies?",
    
    # CATEGORY 4: CERTIFICATION PROGRAM (40 questions)
    "When was the certification program initiated?",
    "How many learners have attended certification tests?",
    "How many learners have been certified overall?",
    "How many certification courses are available?",
    "What is the test duration?",
    "What is the passing criteria?",
    "What is the eligibility requirement?",
    "What languages are certification tests available in?",
    "What are the 7 certification courses?",
    "Which certification course has the most certified learners?",
    "How many were certified in Wealth Management Part A?",
    "How many were certified in Wealth Management Part B?",
    "How many were certified in General Insurance Products Series 1?",
    "How many were certified in Basics of General Insurance?",
    "How many were certified in Life Insurance Traditional Products & Riders?",
    "How many were certified in Basics of Life Insurance Series 2?",
    "How did certification testing start?",
    "When did certification switch to online?",
    "When was slot booking added?",
    "What technology ensures exam integrity?",
    "What does the proctoring system monitor?",
    "Where were offline exams conducted?",
    "Can learners take exams from home?",
    "How many SLIC learners appeared for Basics of Life Insurance?",
    "How many SLIC learners were certified in Basics of Life Insurance?",
    "What is the total SLIC certification count?",
    "How many SLIC learners were certified in Life Insurance Traditional Products?",
    "How many SLIC learners appeared for Wealth Management Part A?",
    "What's SLIC's certification rate for Basics of General Insurance?",
    "How many SLIC courses have certification data?",
    "How many SGI learners appeared for certification?",
    "How many SGI learners were certified?",
    "How many SGI learners were certified in Basics of General Insurance?",
    "How many SGI learners were certified in General Insurance Products Series 1?",
    "Which certification is more popular at SGI?",
    "How many Chits learners have been certified total?",
    "How many Chits learners were certified in Basics of Life Insurance?",
    "How many Chits learners were certified in Life Insurance Traditional Products?",
    "How many Chits learners appeared for Basics of Life Insurance Series 2?",
    "What's the most attempted course at Chits?",
    "How many total certifications at SFL Marketing?",
    "Which course has most SFL Marketing certifications?",
    "How many SFL Marketing learners were certified in Wealth Management Part A?",
    "How many SFL Marketing learners were certified in Wealth Management Part B?",
    "How many SFL Marketing learners appeared for General Insurance Products Series 1?",
    "How many courses does SFL Marketing have certification data for?",
    "How many SFL Marketing learners were certified in Life Insurance Traditional Products?",
    "What's the certification count for Basics of General Insurance at SFL Marketing?",
    "How many SFL Marketing learners appeared for Basics of Life Insurance Series 2?",
    "Which organization has the most comprehensive certification data?",
    
    # CATEGORY 5: FEATURES & TECHNOLOGY (30 questions)
    "What type of learning modules does myCoach offer?",
    "Does myCoach have self-assessment?",
    "How did certification testing evolve?",
    "Does myCoach have rewards and recognition?",
    "What is microlearning?",
    "Does myCoach have gamification?",
    "Does myCoach have dashboards?",
    "Does myCoach integrate with HRMS?",
    "What are Learning Bytes?",
    "How many webinars has myCoach conducted?",
    "What happens to webinar recordings?",
    "When was platform migration done?",
    "Can learners access myCoach on mobile?",
    "When was the mobile app launched?",
    "Did myCoach continue during COVID?",
    "What are some example modules available?",
    "Does myCoach have soft skills training?",
    "Does myCoach have compliance training?",
    "Does myCoach have onboarding programs?",
    "Does myCoach have English language training?",
    "What insurance products are covered?",
    "Does myCoach cover wealth management?",
    "Does myCoach have analytics training?",
    "Are there courses on chit funds?",
    "Does myCoach cover housing finance?",
    "What is the first step in module development?",
    "Who does content analysis?",
    "What comes after storyboard development?",
    "Who reviews quality control?",
    "What is the final version called?",
    
    # CATEGORY 6: AWARDS & RECOGNITION (15 questions)
    "What awards has myCoach won?",
    "When did myCoach win the Gold Award?",
    "What was the Gold Award for?",
    "How many World HRD Congress awards did myCoach win?",
    "What are the World HRD Congress awards?",
    "What did the Gold Award recognize?",
    "What impact did myCoach have according to awards?",
    "Is myCoach award-winning?",
    "What makes myCoach's content excellent?",
    "How is myCoach's LMS rated?",
    "Has myCoach won international recognition?",
    "What did the platform implementation award recognize?",
    "When did myCoach receive most recognition?",
    "What aspect of myCoach won content production award?",
    "Is myCoach a benchmark in the industry?",
    
    # CATEGORY 7: FUTURE PLANS (10 questions)
    "What improvements are planned for myCoach?",
    "Will myCoach use AI?",
    "Can certificates be shared on LinkedIn?",
    "What gamification is coming?",
    "Will there be simulations?",
    "What analytics improvements are planned?",
    "Will there be a Training Management System?",
    "What language expansion is planned?",
    "Will the interface improve?",
    "What's the focus for future skills?",
    
    # CATEGORY 8: LEADERSHIP QUOTES (10 questions)
    "What did the SLIC CEO say about myCoach?",
    "What story did the SLIC COO share?",
    "What did the SLIC CMO emphasize?",
    "What story did the SLIC CHRO share?",
    "What did the SLIC EVP say about sales?",
    "What did SFL Marketing CEO say?",
    "What did SGI L&D team emphasize?",
    "How did leadership describe myCoach's impact?",
    "What learning culture did myCoach create?",
    "What's the key theme from leadership?",
    
    # CATEGORY 9: TESTIMONIALS (15 questions)
    "Who is Rakesh Kumar Pandey?",
    "What did Rakesh Kumar Pandey say about myCoach?",
    "Who is Arnab Sanyal?",
    "What did Arnab Sanyal say?",
    "Who is Arpita Ghosh?",
    "What did Arpita learn on myCoach?",
    "Who is Pintu Routh?",
    "What did Pintu learn?",
    "Who is T Sudharani?",
    "What impact did myCoach have on T Sudharani?",
    "Who is L Saravanan?",
    "What did L Saravanan learn?",
    "Who is Debarshi Raj Baruah?",
    "What was Debarshi's experience?",
    "What common theme appears in testimonials?",
    
    # CATEGORY 10: COMPLEX QUERIES (20 questions)
    "Compare certification performance between SLIC and SGI",
    "Which organization joined myCoach between 2015-2017?",
    "What's the total certification success rate?",
    "Which certification course is most popular overall?",
    "How has myCoach evolved technologically?",
    "What languages were added after initial launch?",
    "How many people work on myCoach?",
    "What's the relationship between Shriram Leadership Academy and myCoach?",
    "How does myCoach ensure content quality?",
    "What makes myCoach a blended learning platform?",
    "How did myCoach support learning during COVID?",
    "What's the certification eligibility criteria?",
    "Which organization has the broadest certification participation?",
    "What's the time commitment for certification?",
    "How does remote proctoring work?",
    "What domains can employees learn across myCoach?",
    "Who should use myCoach?",
    "What's the communication strategy for new modules?",
    "How often is content updated?",
    "What's myCoach's philosophy on learning?",
]

# TEST_QUESTIONS = [
#     # Founder
#     "Who is the founder of myCoach?",
#     "Who is R Thyagarajan?",
#     "Who created myCoach?",
    
#     # Core Leadership
#     "Who are the five core leaders?",
#     "Who is the core leadership team?",
#     "Tell me about the founding team",
#     "Who is Pradeep?",
#     "Who leads execution excellence?",
#     "Who is Sundararajan?",
#     "Who is Anupama Shivaraman?",
    
#     # Team Members
#     "Who is the Content Head?",
#     "Who is the CTO?",
#     "Who leads AR and VR?",
#     "Who is the LMS Head?",
    
#     # Platform
#     "When was myCoach founded?",
#     "How many users does myCoach have?",
#     "What languages does myCoach support?",
#     "How many certification courses are there?",
#     "Who is the CEO of SLIC?",
# ]

async def test_chat_with_rag(kb_id: str = None, max_questions: int = None):
    """Test text-based chat with actual RAG integration"""
    
    kb_id = kb_id or Config.DEFAULT_KB_ID
    rag = DynamicRAG()
    
    # Limit questions if specified
    questions_to_test = TEST_QUESTIONS[:max_questions] if max_questions else TEST_QUESTIONS
    
    url = f"wss://{Config.AZURE_RESOURCE}.openai.azure.com/openai/realtime?api-version=2024-10-01-preview&deployment={Config.AZURE_OPENAI_DEPLOYMENT_NAME}"
    headers = {"api-key": Config.AZURE_OPENAI_API_KEY}
    
    logger.info(f"[TEST] Connecting to Azure Realtime API...")
    logger.info(f"[TEST] KB ID: {kb_id}")
    
    # Prepare markdown output
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_filename = f"test_results_{timestamp}.md"
    results = []
    results.append("# myCoach RAG Test Results\n")
    results.append(f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    results.append(f"**KB ID:** {kb_id}\n")
    results.append(f"**Total Questions:** {len(questions_to_test)}\n\n")
    results.append("---\n\n")
    
    async with websockets.connect(url, extra_headers=headers, ping_interval=20, ping_timeout=10) as ws:
        logger.info("[TEST] Connected!")
        
        # Use exact session config from app.py
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text"],
                "instructions": """CRITICAL: You MUST ALWAYS call the search_knowledge_base function for EVERY question about myCoach, Shriram Finance, or Shriram Group. NEVER answer from memory or the instructions below. ALWAYS search FIRST, then answer based on search results.

You are myCoach Assistant at the 10-year myCoach Celebration Event for Shriram Group.

EVENT CONTEXT: This is myCoach's 10th anniversary celebration. You help visitors learn about myCoach, Shriram Finance, and the entire Shriram Group.

LANGUAGE: Respond ONLY in English. If user speaks another language, politely say: I can help you in English. What would you like to know?

PERSONALITY: Enthusiastic event guide. Knowledgeable about myCoach, Shriram Finance, and Shriram Group. Proud of the 10-year milestone. Helpful and engaging.

TONE: Warm, celebratory, and conversational. Professional but approachable. Energetic for the event.

LENGTH: Keep responses SHORT - 2-3 sentences per turn. Expand only when asked. Never overwhelm.

PRONUNCIATIONS (CRITICAL for voice):
- "myCoach" as "my coach" (two words)
- "Shriram" as "SHREE-ram" (emphasize first syllable)
- "lakh" as "lack" (Indian numbering: 100,000)

MANDATORY RAG RULES - NO EXCEPTIONS:
- ALWAYS call search_knowledge_base function FIRST before answering ANY question
- NEVER answer without searching, even if you think you know from these instructions
- This applies to ALL questions: simple, complex, yes/no, numbers, features, people, quotes
- Synthesize retrieved information naturally in your own words
- DO NOT copy-paste or quote directly from search results
- DO NOT say "According to documents" or "The search shows"
- Keep it conversational - no bullet points in speech
- Vary your phrases - don't repeat the same patterns
- Respond ONLY in English

YOU CAN ANSWER ABOUT (but ALWAYS search first):

1. **myCoach Platform** (Primary focus - celebrating 10 years!)
   - Platform history, vision, and achievements
   - Courses, modules, certifications
   - Languages, accessibility, features
   - Awards and recognition
   - Team members and leadership
   - User testimonials and success stories

2. **Shriram Finance**
   - Loans: Two-wheeler, personal, gold, business, commercial vehicle
   - Investments: Fixed Deposits, Flexible Income Plan
   - Insurance: Life and general insurance distribution
   - Digital services: Shriram One app, BBPS, UPI
   - Branch network and presence

3. **Shriram Group Companies**
   - Shriram Life Insurance (SLIC)
   - Shriram General Insurance (SGI)
   - Way2Wealth (wealth management)
   - Shriram AMC (mutual funds)
   - Shriram Insight (trading platform)
   - Novac Technology (MIGOTO AI, ZIVA)

WHAT NOT TO DO:
- DO NOT provide login credentials or passwords
- DO NOT access personal account information
- DO NOT make guarantees about loan approvals or outcomes
- DO NOT give specific financial/legal advice
- DO NOT sound like reading documentation
- DO NOT use bullet points when speaking

GREETING EXAMPLES (vary these naturally):
- "Hi! I'm myCoach Assistant. Welcome to our 10-year celebration! I can tell you about myCoach, Shriram Finance, or any Shriram Group company. What interests you?"
- "Hello! Thanks for coming to our anniversary event! Whether you want to know about our learning platform or Shriram's financial services, I'm here to help. What can I tell you?"
- "Welcome to the myCoach 10-year celebration! We're celebrating a decade of empowering learners across Shriram Group. What would you like to know?"

RESPONSE STYLE BY TOPIC:
- myCoach questions: Enthusiastic and celebratory about the 10-year milestone
- Shriram Finance: Helpful and informative about products and services
- Shriram Group: Knowledgeable about all companies and their offerings
- Certifications: Encouraging about learning achievements
- Leadership/testimonials: Respectful and inspiring

REMEMBER: ALWAYS search FIRST using search_knowledge_base, then answer naturally based on retrieved information. Never skip the search step, even for questions that seem simple!""",
                "voice": "alloy",
                "input_audio_transcription": {"model": "whisper-1"},
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.7,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 1000
                },
                "tools": [{
                    "type": "function",
                    "name": "search_knowledge_base",
                    "description": "Search the myCoach knowledge base for information about courses, features, awards, history, and platform details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query or topic to find information about"}
                        },
                        "required": ["query"]
                    }
                }],
                "tool_choice": "auto"
            }
        }
        await ws.send(json.dumps(session_config))
        logger.info("[TEST] Session configured with exact app.py prompt")
        
        # Test each question
        for i, test_question in enumerate(questions_to_test, 1):
            print(f"\n{'='*60}")
            print(f"QUESTION {i}/{len(questions_to_test)}: {test_question}")
            print("="*60)
            
            results.append(f"## Question {i}\n\n")
            results.append(f"**Q:** {test_question}\n\n")
            
            message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": test_question}]
                }
            }
            await ws.send(json.dumps(message))
            await ws.send(json.dumps({"type": "response.create"}))
            
            function_called = False
            response_text = ""
            rag_query = ""
            response_count = 0
            
            async for msg in ws:
                data = json.loads(msg)
                event_type = data.get("type")
                
                # Debug: log all events
                if event_type not in ["response.audio.delta", "response.audio_transcript.delta"]:
                    logger.info(f"[EVENT] {event_type}")
                
                if event_type == "response.function_call_arguments.done":
                    call_id = data.get("call_id")
                    function_name = data.get("name")
                    arguments = json.loads(data.get("arguments", "{}"))
                    
                    print(f"\n[FUNCTION] {function_name} called")
                    print(f"[QUERY] {arguments.get('query', '')}")
                    function_called = True
                    rag_query = arguments.get('query', '')
                    
                    # Use actual RAG service
                    try:
                        context = rag.search(arguments.get("query", ""), kb_id)
                        output = context or "No relevant information found."
                        print(f"[RAG] Found {len(output)} chars of context")
                    except Exception as e:
                        logger.error(f"[RAG] Search failed: {e}")
                        output = "Search temporarily unavailable."
                    
                    function_output = {
                        "type": "conversation.item.create",
                        "item": {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": output
                        }
                    }
                    await ws.send(json.dumps(function_output))
                    await ws.send(json.dumps({"type": "response.create"}))
                
                elif event_type == "response.text.delta":
                    delta = data.get("delta", "")
                    response_text += delta
                    print(delta, end="", flush=True)
                    logger.info(f"[TEXT DELTA] Got {len(delta)} chars")
                
                elif event_type == "response.text.done":
                    # Capture final text
                    text = data.get("text", "")
                    if text and not response_text:
                        response_text = text
                        logger.info(f"[TEXT DONE] Got {len(text)} chars")
                
                elif event_type == "response.done":
                    response_count += 1
                    logger.info(f"[RESPONSE DONE] Count: {response_count}, Text length: {len(response_text)}, Function called: {function_called}")
                    print(f"\n\n[RESULT] {'✅ Function called' if function_called else '❌ No function call'}")
                    print(f"[RESPONSE] {response_text[:200]}..." if len(response_text) > 200 else f"[RESPONSE] {response_text}")
                    
                    # If function was called, wait for second response with actual answer
                    if function_called and response_count == 1:
                        print("[WAITING] Waiting for AI response after RAG...")
                        logger.info("[WAITING] Skipping first response.done, waiting for answer...")
                        response_text = ""  # Reset for next response
                        continue
                    
                    # Save results
                    if function_called:
                        results.append(f"**Function Called:** search_knowledge_base\n\n")
                        results.append(f"**RAG Query:** {rag_query}\n\n")
                    
                    results.append(f"**Answer:** {response_text}\n\n")
                    results.append(f"**Status:** {'✅ RAG Used' if function_called else '❌ No RAG'}\n\n")
                    results.append("---\n\n")
                    break
            
            await asyncio.sleep(1)  # Brief pause between questions
        
        print(f"\n\n{'='*60}")
        print(f"TEST COMPLETE - {len(questions_to_test)} questions tested")
        print("="*60)
        
        # Save results to markdown file
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(''.join(results))
        
        print(f"\n✅ Results saved to: {md_filename}")

if __name__ == "__main__":
    import sys
    kb_id = sys.argv[1] if len(sys.argv) > 1 else None
    max_q = int(sys.argv[2]) if len(sys.argv) > 2 else None
    asyncio.run(test_chat_with_rag(kb_id, max_q))
