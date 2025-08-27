# app.py
import streamlit as st
import json, re, os, random
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from groq import Groq

# Load .env
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---------------- Streamlit page ----------------
st.set_page_config(
    page_title="TalentScout - AI Hiring Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- CSS ----------------
st.markdown(
    """
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 10px;
        border-radius: 15px;
        margin: 5px 0;
        margin-left: 20%;
        text-align: right;
    }
    .bot-message {
        background-color: #e9ecef;
        color: #333;
        padding: 10px;
        border-radius: 15px;
        margin: 5px 0;
        margin-right: 20%;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(40,167,69,0.7); }
        70% { box-shadow: 0 0 0 10px rgba(40,167,69,0); }
        100% { box-shadow: 0 0 0 0 rgba(40,167,69,0); }
    }
    .completed-step {
        animation: pulse 1.5s infinite;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- Data model ----------------
@dataclass
class CandidateInfo:
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    experience: Optional[str] = None
    position: Optional[str] = None
    location: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    responses: Optional[Dict[str, dict]] = None


# ---------------- Hiring Assistant ----------------
class HiringAssistant:
    def __init__(self):
        self.conversation_states = {
            "GREETING": "greeting",
            "COLLECTING_INFO": "collecting_info",
            "TECH_QUESTIONS": "tech_questions",
            "COMPLETED": "completed",
            "ENDED": "ended",
        }
        self.required_fields = [
            "name","email","phone","experience","position","location","tech_stack"
        ]
        self.ending_keywords = ["bye","exit","quit","end","stop"]

        self.known_techs = [
            "python","javascript","react","node","node.js","sql",
            "postgres","mysql","java","aws","gcp","azure",
            "docker","kubernetes","ui/ux","figma","sketch","adobe xd",
            "photoshop","illustrator","canva","product","pm"
        ]
        self.groq_model = "llama3-70b-8192"

    def get_greeting_message(self) -> str:
        return (
            "🤖 **Welcome to TalentScout - AI Hiring Assistant!**\n\n"
            "I’ll collect a few details and then ask **AI-generated interview questions** "
            "tailored to your skills.\n\n👉 Please tell me your **full name** to begin."
            "\n\n*(Type 'bye' anytime to exit)*"
        )

    # ---------------- Extractors ----------------
    def extract_email(self, text: str) -> Optional[str]:
        m = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
        return m.group(0) if m else None

    def extract_phone(self, text: str) -> Optional[str]:
        m = re.search(r"(\+?\d[\d\-\s\(\)]{7,}\d)", text)
        if m:
            return re.sub(r"[^\d+]", "", m.group(1))
        return None

    def extract_tech_stack(self, text: str) -> List[str]:
        txt = (text or "").lower()
        found = []
        for tech in self.known_techs:
            if tech in txt:
                found.append("node.js" if tech=="node" else tech)
        return sorted(list(dict.fromkeys(found)))

    # ---------------- AI Question Generator ----------------
    def generate_ai_questions_for_skills(self, skills: List[str], count: int = 5) -> List[str]:
        if not skills: return []
        skills_str = ", ".join(skills)
        prompt = f"""
Generate {count} interview questions for a candidate with skills: {skills_str}.
Rules:
- Prefix each with the domain, e.g. (python), (ui/ux).
- If yes/no, end with (yes/no). Else end with (open).
- Output only {count} questions, one per line.
"""
        try:
            resp = client.chat.completions.create(
                model=self.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=400,
            )
            text = resp.choices[0].message.content.strip()
            lines = [re.sub(r"^\s*\d+[\.\)]\s*", "", l).strip() for l in text.splitlines() if l.strip()]
            # 🔹 Filter out intro lines
            questions = [l for l in lines if "(" in l and ")" in l]
            if len(questions) < count:
                while len(questions) < count:
                    questions.append(f"({skills[0]}) Describe a project using {skills[0]}. (open)")
            return questions[:count]
        except Exception as e:
            return [f"({skills[0]}) Fallback question on {skills[0]}. (open)"]

    def generate_technical_questions(self, stack: List[str]) -> List[str]:
        return self.generate_ai_questions_for_skills(stack, count=5)

    # ---------------- Evaluation ----------------
    def evaluate_response_ai(self, question: str, answer: str) -> dict:
        prompt = f"""
Evaluate this interview answer.

Question:
{question}
Answer:
{answer}

Respond exactly in this format:
Score: <1-5>
Feedback: <1-2 short sentences>
"""
        try:
            resp = client.chat.completions.create(
                model=self.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=200,
            )
            text = resp.choices[0].message.content.strip()
            score = 3
            m = re.search(r"Score\s*:\s*(\d)", text)
            if m: score = int(m.group(1))
            m2 = re.search(r"Feedback\s*:\s*(.+)", text, re.DOTALL)
            feedback = m2.group(1).strip() if m2 else text
            return {"score": score, "feedback": feedback}
        except Exception as e:
            return {"score": 0, "feedback": f"Error: {e}"}

    # ---------------- Conversation ----------------
    def process_user_input(self, user_input: str, candidate: CandidateInfo, state: str):
        if self.is_ending_keyword(user_input):
            return self.get_ending_message(), self.conversation_states["ENDED"]

        if state == self.conversation_states["GREETING"]:
            candidate.name = user_input.strip()
            return f"Nice to meet you, {candidate.name}! 👋 What is your **email**?", self.conversation_states["COLLECTING_INFO"]

        if state == self.conversation_states["COLLECTING_INFO"]:
            return self.collect_info(user_input, candidate)

        if state == self.conversation_states["TECH_QUESTIONS"]:
            return self.handle_questions(user_input, candidate)

        return "Could you rephrase?", state

    def collect_info(self, user_input: str, c: CandidateInfo):
        if not c.email:
            e = self.extract_email(user_input)
            if e:
                c.email = e
                return "📧 Got it! Now, your **phone**?", self.conversation_states["COLLECTING_INFO"]
            return "Please provide a valid email.", self.conversation_states["COLLECTING_INFO"]

        if not c.phone:
            p = self.extract_phone(user_input)
            if p:
                c.phone = p
                return "📱 Great! How many **years of experience** do you have?", self.conversation_states["COLLECTING_INFO"]
            return "That didn’t look like a phone number.", self.conversation_states["COLLECTING_INFO"]

        if not c.experience:
            c.experience = user_input.strip()
            return "💼 Nice! What **position** are you applying for?", self.conversation_states["COLLECTING_INFO"]

        if not c.position:
            c.position = user_input.strip()
            return "🎯 Got it! What’s your **location**?", self.conversation_states["COLLECTING_INFO"]

        if not c.location:
            c.location = user_input.strip()
            return "🌍 Cool! Please list your **skills/tools**.", self.conversation_states["COLLECTING_INFO"]

        if not c.tech_stack:
            stack = self.extract_tech_stack(user_input)
            if not stack:
                pos = (c.position or "").lower()
                if "design" in pos or "ux" in pos or "ui" in pos: stack = ["ui/ux"]
                elif "product" in pos: stack = ["product"]

            if stack:
                c.tech_stack = stack; c.responses = {}
                qs = self.generate_technical_questions(stack)
                st.session_state.technical_questions = qs
                st.session_state.current_question_index = 0
                return f"🚀 Skills noted: {', '.join(stack)}\n\n**Q1:** {qs[0]}", self.conversation_states["TECH_QUESTIONS"]

            return "Couldn’t detect skills. Please list clearly.", self.conversation_states["COLLECTING_INFO"]

        return "All info collected, moving to technical questions.", self.conversation_states["TECH_QUESTIONS"]

    def handle_questions(self, user_input: str, c: CandidateInfo):
        qs = st.session_state.get("technical_questions", [])
        idx = st.session_state.get("current_question_index", 0)
        if idx < len(qs):
            q = qs[idx]
            result = self.evaluate_response_ai(q, user_input)
            c.responses[q] = {"answer": user_input, "score": result["score"], "feedback": result["feedback"]}
            st.session_state.current_question_index += 1
            if st.session_state.current_question_index < len(qs):
                nxt = st.session_state.current_question_index
                return f"👍 Thanks! (AI scored {result['score']}/5)\n\n**Q{nxt+1}:** {qs[nxt]}", self.conversation_states["TECH_QUESTIONS"]
            return self.complete(c), self.conversation_states["COMPLETED"]
        return "Something went wrong.", self.conversation_states["TECH_QUESTIONS"]

    def complete(self, c: CandidateInfo):
        self.save(c)
        return f"🎉 Congrats {c.name}, you finished! ✅ We’ll review and get back to you."

    def get_ending_message(self): 
        return "👋 Thanks for chatting with TalentScout!"

    def is_ending_keyword(self, text: str): 
        return any(k in (text or "").lower() for k in self.ending_keywords)

    def save(self, c: CandidateInfo):
        os.makedirs("candidate_data", exist_ok=True)
        data = {
            "timestamp": datetime.now().isoformat(),
            "name": c.name,"email": c.email,"phone": c.phone,
            "experience": c.experience,"position": c.position,
            "location": c.location,"tech_stack": c.tech_stack,
            "responses": c.responses,
        }
        with open(f"candidate_data/{datetime.now().strftime('%Y%m%d_%H%M%S')}.json","w") as f:
            json.dump(data,f,indent=2)


# ---------------- Main App ----------------
def main():
    if "assistant" not in st.session_state: st.session_state.assistant = HiringAssistant()
    if "candidate" not in st.session_state: st.session_state.candidate = CandidateInfo()
    if "conversation_history" not in st.session_state: st.session_state.conversation_history = []
    if "current_state" not in st.session_state: st.session_state.current_state = st.session_state.assistant.conversation_states["GREETING"]
    if "initialized" not in st.session_state:
        st.session_state.conversation_history.append({"role":"assistant","content":st.session_state.assistant.get_greeting_message()})
        st.session_state.initialized = True
        st.session_state.technical_questions = []; st.session_state.current_question_index = 0

    initials = st.session_state.candidate.name[0].upper() if st.session_state.candidate.name else "?"
    st.markdown(
        f"""
    <div class="main-header">
      <div style='display:flex; justify-content:center; gap:1rem; align-items:center;'>
        <div style='width:70px;height:70px;border-radius:50%;background:#ff9800;
                    display:flex;align-items:center;justify-content:center;
                    color:white;font-size:28px;font-weight:bold;'>{initials}</div>
        <div>
          <h1>🤖 TalentScout - AI Hiring Assistant</h1>
          <p>Gamified candidate screening with AI-powered questions</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("💬 Conversation")
        for msg in st.session_state.conversation_history:
            html = f'<div class="user-message">{msg["content"]}</div>' if msg["role"]=="user" else f'<div class="bot-message">{msg["content"]}</div>'
            st.markdown(html, unsafe_allow_html=True)

        if st.session_state.current_state != st.session_state.assistant.conversation_states["ENDED"]:
            user_input = st.text_input("Your response:", key="user_input", placeholder="Type your response here...")
            if st.button("Send") and user_input.strip():
                st.session_state.conversation_history.append({"role":"user","content":user_input})
                resp, new = st.session_state.assistant.process_user_input(user_input, st.session_state.candidate, st.session_state.current_state)
                st.session_state.current_state = new
                st.session_state.conversation_history.append({"role":"assistant","content":resp})
                if new == st.session_state.assistant.conversation_states["COMPLETED"]: st.balloons()
                st.rerun()
        else:
            st.info("Session ended. Refresh to start a new one.")

    with col2:
        st.subheader("📊 Progress Timeline")
        steps = [("📝 Getting to know you","collecting_info",0),
                 ("💡 Brain workout","tech_questions",0),
                 ("🎉 You did it!","completed",0),
                 ("👋 See you soon","ended",0)]
        order = {"greeting":0,"collecting_info":0,"tech_questions":1,"completed":2,"ended":3}
        current_step = order.get(st.session_state.current_state,0)
        html = '<div style="display:flex;flex-direction:column;gap:1rem;">'
        for i,(label,state,_) in enumerate(steps):
            if i<current_step: icon,cls,color="✅","completed-step","#28a745"
            elif i==current_step: icon,cls,color="🟢","","#007bff"
            else: icon,cls,color="⚪","","#6c757d"
            html += f"<div class='{cls}' style='padding:0.5rem;border-left:3px solid {color};'><b>{icon} {label}</b></div>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    with st.expander("🔧 Debug / Internal State"):
        st.write("AI questions:", st.session_state.get("technical_questions", []))
        st.write("Current index:", st.session_state.get("current_question_index", 0))
        st.write("Candidate:", st.session_state.candidate)


if __name__ == "__main__":
    main()



