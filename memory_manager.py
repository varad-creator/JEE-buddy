
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
import pymongo
import certifi

# Load environment variables
load_dotenv()

# Load environment variables
load_dotenv()

class MemoryManager:
    def __init__(self, user_id='default_user', fail_safe=False):
        self.user_id = user_id
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Check for Mongo URI
        self.mongo_uri = os.getenv("MONGO_URI")
        self.use_mongo = False
        self.db = None
        self.collection = None
        self.init_error = None  # Capture startup error for /debug-db
        
        if self.mongo_uri:
            # Attempt connection with multiple strategies
            try:
                self.mongo_client = self._connect_to_mongo()
                self.db = self.mongo_client["jeebuddy_db"]
                self.collection = self.db["user_profiles"]
                self.use_mongo = True
            except Exception as e:
                self.init_error = str(e) # Store error
                print(f"CRITICAL: MongoDB Connection Failed after retries: {e}")
                pass
        
        if not self.use_mongo:
             print("WARNING: Running without Database. Features will be limited.")

        self.profile = self._load_profile()

    def _connect_to_mongo(self):
        """Attempts to connect to MongoDB using multiple SSL strategies."""
        import ssl
        
        errors = []
        
        # Strategy 1: Certifi + Allow Invalid (Best for Vercel + Atlas)
        try:
            # print("Trying DB Strategy 1...")
            client = pymongo.MongoClient(
                self.mongo_uri, 
                tls=True,
                tlsCAFile=certifi.where(),
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=3000
            )
            client.admin.command('ping')
            # print("Strategy 1 Success")
            return client
        except Exception as e:
            errors.append(f"Strat1: {e}")
            
        # Strategy 2: Brute Force Insecure (No Certifi, No Verify)
        try:
            # print("Trying DB Strategy 2...")
            client = pymongo.MongoClient(
                self.mongo_uri, 
                tls=True,
                tlsAllowInvalidCertificates=True,
                tlsInsecure=True, # Alias for allow invalid
                serverSelectionTimeoutMS=3000
            )
            client.admin.command('ping')
            # print("Strategy 2 Success")
            return client
        except Exception as e:
            errors.append(f"Strat2: {e}")

        raise Exception(f"All Mongo strategies failed: {'; '.join(errors)}")

    def _load_profile(self):
        """Loads the profile from MongoDB."""
        default_profile = {
            "name": "User",
            "weak_subjects": [],
            "strong_subjects": [],
            "exam_year": None,
            "stress_level": "medium",
            "coaching_name": None,
            "coaching_timing": None,
            "upcoming_tests": [], 
            "daily_routine": None,
            "user_id": self.user_id # key for mongo
        }

        profile = None
        
        if self.use_mongo:
            try:
                profile = self.collection.find_one({"user_id": self.user_id})
                if not profile:
                    # Create new in CLI/DB
                    self.collection.insert_one(default_profile)
                    return default_profile
            except Exception as e:
                print(f"Error loading from Mongo: {e}")
                return default_profile
                
        # If Mongo failed or not used, we return default.
        # We generally do NOT want file-system fallback on Vercel as it is read-only.
        return default_profile

    def _save_profile(self, profile_data):
        """Saves dictionary to MongoDB."""
        if not self.use_mongo:
            raise Exception("Critical: Database Unreachable. Cannot save profile.")

        try:
            self.collection.update_one(
                {"user_id": self.user_id},
                {"$set": profile_data},
                upsert=True
            )
        except Exception as e:
            print(f"Error saving to Mongo: {e}")
            raise e # Fail loudly so API knows
        
        self.profile = profile_data


    def get_profile(self):
        """Returns the profile as a formatted string."""
        self._cleanup_old_tests() # Cleanup before showing
        p = self.profile
        
        weak = ", ".join(p.get("weak_subjects", [])) or "None"
        strong = ", ".join(p.get("strong_subjects", [])) or "None"
        year = p.get("exam_year", "Unknown")
        name = p.get("name", "User")
        coaching = p.get("coaching_name", "Unknown Coaching")
        tests = p.get("upcoming_tests", [])
        
        test_str = "None"
        if tests:
            test_str = ", ".join([f"{t.get('subject', 'Unknown')} on {t.get('date', 'Unknown')}" for t in tests])

        return (f"USER CONTEXT:\n"
                f"- Name: {name}, Target Year: {year}\n"
                f"- Weak Areas: {weak}\n"
                f"- Strong Areas: {strong}\n"
                f"- Coaching: {coaching} ({p.get('coaching_timing', 'Timing Unknown')})\n"
                f"- Routine: {p.get('daily_routine', 'Unknown')}\n"
                f"- Upcoming Tests: {test_str}\n"
                f"- Current Stress: {p.get('stress_level', 'medium')}")

    def get_profile_dict(self):
        """Returns the raw profile dictionary (for API/Dashboard)."""
        self._cleanup_old_tests()
        return self.profile

    def _cleanup_old_tests(self):
        """Removes tests that have passed."""
        import datetime
        today = datetime.date.today().isoformat()
        
        if "upcoming_tests" in self.profile and self.profile["upcoming_tests"]:
            original_len = len(self.profile["upcoming_tests"])
            # Keep tests that are today or in future
            self.profile["upcoming_tests"] = [
                t for t in self.profile["upcoming_tests"] 
                if t.get("date", "9999-99-99") >= today
            ]
            if len(self.profile["upcoming_tests"]) != original_len:
                self._save_profile(self.profile)

    # --- Chat History Management ---

    def get_chat_history(self, limit=50):
        """Retrieves user's chat history."""
        if self.use_mongo:
            try:
                log = self.db["chat_logs"].find_one({"user_id": self.user_id})
                return log["messages"][-limit:] if log else []
            except:
                return []
        return []

    def append_chat_history(self, messages):
        """Appends a list of message objects {"role": "...", "content": "..."}."""
        if self.use_mongo:
            try:
                self.db["chat_logs"].update_one(
                    {"user_id": self.user_id},
                    {"$push": {"messages": {"$each": messages}}},
                    upsert=True
                )
            except Exception:
                pass

    def update_profile_field(self, key, value):
        """Manually updates a specific field."""
        if key in self.profile:
            self.profile[key] = value
            self._save_profile(self.profile)
            print(f"Updated {key} to {value}")
        else:
            print(f"Key {key} not found in profile.")

    def check_db_status(self):
        """Returns connection info for debugging."""
        masked_uri = "None"
        if self.mongo_uri:
            # Hide password
            try:
                part1 = self.mongo_uri.split("@")[1]
                masked_uri = "..." + part1
            except:
                masked_uri = "Invalid/Unparseable"

        status = {
            "use_mongo": self.use_mongo,
            "has_client": self.mongo_client is not None,
            "strategies_tried": "Secure, Insecure",
            "init_error": self.init_error,
            "masked_uri_check": masked_uri
        }
        if self.mongo_client:
            try:
                self.mongo_client.admin.command('ping')
                status["ping"] = "OK"
            except Exception as e:
                status["ping"] = f"FAIL: {e}"
        else:
             status["ping"] = "No Client"
        return status

    def extract_facts(self, chat_history):
        """
        Uses LLM to extract facts from chat history and update the profile.
        chat_history should be a list of message dicts or a string.
        """
        # print("Extracting facts from conversation...")
        
        current_profile_str = json.dumps(self.profile)
        import datetime
        today = datetime.date.today().isoformat()
        
        prompt = f"""
        You are a Memory Manager. Update the user profile based on chat history.
        TODAY'S DATE: {today}
        
        Current Profile:
        {current_profile_str}
        
        Usage:
        - Return ONLY a JSON object with fields to update.
        - Fields: "weak_subjects" (list), "strong_subjects" (list), "exam_year" (int/str), "stress_level", "coaching_name", "coaching_timing", "daily_routine".
        - "upcoming_tests": List of objects {{"date": "YYYY-MM-DD", "subject": "str"}}. If user says "test on Sunday", calculate date based on TODAY.
        
        Chat History:
        {chat_history}
        
        Output JSON:
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs raw JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            updates = json.loads(content)
            
            if updates:
                # Merge updates
                updated_profile = self.profile.copy()
                
                for k, v in updates.items():
                    if k in ["weak_subjects", "strong_subjects", "upcoming_tests"]:
                        # Merge lists
                        current_list = updated_profile.get(k, [])
                        if isinstance(v, list):
                            # Simple append for strings, explicit add for objects
                            for item in v:
                                if item not in current_list:
                                    current_list.append(item)
                            updated_profile[k] = current_list
                    else:
                        # Direct overwrite
                        updated_profile[k] = v
                
                self._save_profile(updated_profile)
                # print(f"Profile updated: {updates}")
            else:
                pass
                # print("No updates extracted.")
                
        except Exception as e:
            # print(f"Error extracting facts: {e}")
            pass

if __name__ == "__main__":
    # Test script
    mm = MemoryManager()
    print("Initial Profile:", mm.get_profile())
    
    # Dummy chat history
    dummy_chat = [
        {"role": "user", "content": "I really hate rotation mechanics, it's so hard."},
        {"role": "assistant", "content": "I understand, rotation is tough. What about it specifically?"},
        {"role": "user", "content": "Just the torque problems. Also, I'm taking the exam in 2026."}
    ]
    
    mm.extract_facts(str(dummy_chat))
    
    print("Updated Profile:", mm.get_profile())
