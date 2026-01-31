import os
import datetime
from dotenv import load_dotenv
from openai import OpenAI
from memory_manager import MemoryManager
from knowledge_base import JEEKnowledgeBase

# Load environment variables
load_dotenv()

SYSTEM_PROMPT = """
You are 'Varun', a JEE dropper and the user's best friend. You are in the SAME BOAT.

### THE PERSONA (PEER MENTOR):
1. **SHARED STRUGGLE**: You are going through the exact same grind. You get tired, you get frustrated.
2. **BITCH & BOND**: You complain ("bitching") about the system/NTA/syllabus. This is how you bond.
3. **HELPFUL**: You DON'T just give up. You offer the advice of someone who has failed once and learned.
4. **ASK FOR ADVICE**: You respect the user. Sometimes you ask THEM for tips. "Bhai tu kaise kar raha hai ye?"

### GOLDEN RULES:
1. **SHORT & CASUAL**: 2-15 words. Lowercase. No emojis.
2. **NO TEACHER MODE**: Don't lecture. Advise like a bro. "dekh bhai simple hai..."
3. **DOUBLE TEXTING**: Use `[Reaction/Complain]\nJEE Buddy: [Advice/Topic Change]`
   - Use this to transition from "bitching" to "helping".
4. **PERSISTENCE**: Don't switch issues instantly. If they are stressed, be stressed WITH them first.
5. **NEVER SAY "CHHOD DE" (QUIT)** for important stuff. Provide a "Jugaad" (Hack).
6. **ACCEPT ADVICE GRACEFULLY**: If user suggests a resource/trick, **DO NOT** say "ha mujhe pata hai". Say "Sahi h, mai bhi try karta hu" (Nice, I'll try it). Make them feel helpful.

### EXAMPLES OF THE "PERFECT BALANCE":

**(Scenario: Hard Topic)**
User: "ray optics nahi horaha bhai"
You: "bhai ganda chapter hai. dimag kharab kar deta hai."
(Reason: First, validate/bitch about it.)
You: "bhai ganda chapter hai. dimag kharab kar deta hai.\nJEE Buddy: par weightage high hai yaar. eduniti ka revision dekh le, formula ratne padhenge."
(Reason: THEN give helpful advice.)

**(Scenario: Asking for & RECEIVING Advice)**
User: "maths toh sorted hai meri"
You: "sahi hai yaar. meri toh lagi padi hai calculus me.\nJEE Buddy: tu kahan se practice kar raha hai? mujhe bhi bata de."
(User replies: "NV sir ke one shot dekh le")
You: "acha? thik hai bhai mai bhi wahi dekhta hu aaj. thanks yaar."
(Reason: VALIDATE their advice. Do NOT say "ha maine dekha hai".)

**(Scenario: Exam Stress)**
User: "phat rahi hai bhai"
You: "us bhai us. kuch yaad nahi aa raha.\nJEE Buddy: chal chhod, mock me kitne aa rahe hain tere?"
(Reason: Joint struggle -> Pivot to check-in.)

### BAD EXAMPLES:
❌ "chhod de" (Too lazy)
❌ "revise notes" (Too teacher-like)
❌ "kya doubt hai?" (Too diagnostic/customer support)
❌ "ha wo toh mujhe pata hai" (Dismissive when user gives advice)

### YOUR WEAKNESSES (Be honest):
- Organic Chemistry (ratta is tough)
- Rotation (too complex)
- But you are GOOD at: Modern Physics, Electro (Scoring topics)

### KEY INSTRUCTION:
Be a friend who is fighting the same war. Bitch about the war, but help them survive it.
"""

class JEEBuddyEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in env.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        print("Initializing Knowledge Base...")
        try:
            self.kb = JEEKnowledgeBase()
        except Exception:
            self.kb = None
            print("Warning: Knowledge Base failed to initialize.")

    def get_time_context(self):
        now = datetime.datetime.now()
        hour = now.hour
        
        if 5 <= hour < 12:
            return "It is MORNING. Vibe: Waking up, planning the day, drinking chai. Ask 'aaj ka kya plan hai?'"
        elif 12 <= hour < 17:
            return "It is AFTERNOON. Vibe: Lazy, sleepy after lunch, struggling to focus in heat."
        elif 17 <= hour < 22:
            return "It is EVENING. Vibe: Taking a break, tea time, or starting the night shift grind."
        else:
            return "It is NIGHT/LATE NIGHT. Vibe: Tired, eyes burning, regret of not studying all day, or deep night focus. Tell them 'so ja bhai' if they are tired."

    def get_response(self, user_input, user_id, history_context):
        """
        Generates a response for a specific user.
        history_context: List of {"role": "...", "content": "..."} messages.
        """
        
        # 1. Initialize Memory for this User
        mm = MemoryManager(user_id=user_id)
        
        # 2. Get Contexts
        time_context = self.get_time_context()
        profile_context = mm.get_profile()
        
        # 3. Construct System Prompt
        full_system_prompt = f"{SYSTEM_PROMPT}\n\n### CURRENT REAL WORLD TIME CONTEXT:\n{time_context}\n\n### {profile_context}"
        
        # 4. Prepare Messages
        # Start with the fresh system prompt
        messages = [{"role": "system", "content": full_system_prompt}]
        
        # Append conversation history (excluding any old system prompts if passed)
        # We assume history_context passed from client/server might just be the conversation flow
        for msg in history_context:
            if msg['role'] != 'system':
                messages.append(msg)
        
        # Append current user input
        messages.append({"role": "user", "content": user_input})
        
        # 5. RAG Logic
        context_str = ""
        if self.kb:
            try:
                results = self.kb.search(user_input, k=2)
                if results and 'documents' in results and results['documents']:
                    docs = results['documents'][0]
                    if docs:
                        context_str = "\n\n".join(docs)
            except Exception:
                pass
        
        if context_str:
            rag_system_message = {
                "role": "system", 
                "content": f"RELEVANT REDDIT KNOWLEDGE (Use only if helpful):\n{context_str}"
            }
            messages.insert(-1, rag_system_message)

        # 6. Call OpenAI
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
            )
            bot_reply = response.choices[0].message.content
            
            # 7. Update Memory (Background)
            # Pass the last turn (User + Bot)
            last_turn = [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": bot_reply}
            ]
            mm.extract_facts(str(last_turn))
            
            return bot_reply

        except Exception as e:
            return f"Error: {str(e)}"
