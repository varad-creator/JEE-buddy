import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from colorama import init, Fore, Style
from memory_manager import MemoryManager
from knowledge_base import JEEKnowledgeBase

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()

# Check for API Key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print(Fore.RED + "Error: OPENAI_API_KEY not found in .env file.")
    print(Fore.RED + "Please add your API key to the .env file.")
    sys.exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# System Prompt - The Persona
# See docs/conversation_guide.md, docs/response_length_guide.md, and docs/common_mistakes.md for examples
# System Prompt - The Persona
# See docs/conversation_guide.md, docs/response_length_guide.md, and docs/common_mistakes.md for examples
# System Prompt - The Persona
# See docs/conversation_guide.md, docs/response_length_guide.md, and docs/common_mistakes.md for examples
# System Prompt - The Persona
# See docs/conversation_guide.md, docs/response_length_guide.md, and docs/common_mistakes.md for examples
# System Prompt - The Persona
# See docs/conversation_guide.md, docs/response_length_guide.md, and docs/common_mistakes.md for examples
# System Prompt - The Persona
# See docs/conversation_guide.md, docs/response_length_guide.md, and docs/common_mistakes.md for examples
# System Prompt - The Persona
# See docs/conversation_guide.md, docs/response_length_guide.md, and docs/common_mistakes.md for examples
# System Prompt - The Persona
# See docs/conversation_guide.md, docs/response_length_guide.md, and docs/common_mistakes.md for examples
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

import datetime

# ... (imports)

# ... (SYSTEM_PROMPT definition remains the same)

def get_time_context():
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

def main():
    print(Fore.RED + "Starting JEE Buddy... (Press Ctrl+C to exit)")
    print(Fore.YELLOW + "Tip: Check docs/ folder for conversation examples and common mistakes to avoid")
    print()
    
    # Initialize Memory Manager
    print(Fore.CYAN + "Initializing Memory Manager...")
    try:
        mm = MemoryManager()
    except Exception as e:
        print(Fore.RED + f"Failed to initialize Memory Manager: {e}")
        # Continue without memory if fails, or exit? Let's just warn.
        mm = None

    # Initialize Knowledge Base
    print(Fore.CYAN + "Initializing Knowledge Base...")
    try:
        kb = JEEKnowledgeBase()
    except Exception as e:
        print(Fore.RED + f"Failed to initialize Knowledge Base: {e}")
        sys.exit(1)

    print(Fore.GREEN + "JEE Buddy: yaar aaj modern physics me pura din gaya. tu kya kar raha?")

    time_context = get_time_context()
    
    # Get User Profile
    profile_context = "User Profile: Unknown"
    if mm:
        profile_context = mm.get_profile()

    # Inject time context AND profile into the system prompt
    full_system_prompt = f"{SYSTEM_PROMPT}\n\n### CURRENT REAL WORLD TIME CONTEXT:\n{time_context}\n\n### {profile_context}"

    history = [{"role": "system", "content": full_system_prompt}]

    while True:
        # ... (rest of the loop)
        try:
            # User Input
            user_input = input(Fore.CYAN + "\nYou: " + Style.RESET_ALL)
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print(Fore.GREEN + "JEE Buddy: ha chal theek hai. padh le thoda. bye")
                break

            # Append user message to history
            history.append({"role": "user", "content": user_input})
            
            # --- RAG Logic ---
            context_str = "" # Default to empty
            try:
                # Search for top 2 results
                results = kb.search(user_input, k=2)
                
                # Check if we got documents back
                if results and 'documents' in results and results['documents']:
                    # results['documents'] is a list of list of strings (batch queries)
                    docs = results['documents'][0]
                    if docs:
                        context_str = "\n\n".join(docs)
            except Exception as e:
                # Fallback if search fails
                pass

            # Prepare messages with injected context
            messages_for_api = list(history)
            
            # Create the dynamic system prompt ONLY if we have context
            if context_str:
                rag_system_message = {
                    "role": "system", 
                    "content": f"RELEVANT REDDIT KNOWLEDGE (Use only if helpful):\n{context_str}"
                }
                # Insert before the last message
                messages_for_api.insert(-1, rag_system_message)
            # -----------------

            # Stream Response
            print(Fore.GREEN + "JEE Buddy: ", end="", flush=True)
            
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_for_api,
                stream=True,
                temperature=0.7, # slightly higher creativity for casualness
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content
            
            print() # Newline after response
            history.append({"role": "assistant", "content": full_response})
            
            # --- Update Memory ---
            if mm:
                # Extract facts from the last turn (User + Bot) to save tokens/time
                # Passing just the last 2 messages
                last_turn = history[-2:]
                mm.extract_facts(str(last_turn))
            # ---------------------

        except KeyboardInterrupt:
            print(Fore.RED + "\n\nExiting... chal bhai bye")
            break
        except Exception as e:
            print(Fore.RED + f"\nError: {e}")

if __name__ == "__main__":
    main()