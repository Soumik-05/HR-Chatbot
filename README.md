🤖 TalentScout - AI Hiring Assistant
📌 Introduction
TalentScout is an AI-powered hiring assistant that simplifies the candidate screening process. Instead of recruiters manually conducting repetitive first-round interviews, TalentScout automates the process by collecting candidate details, asking AI-generated technical questions, and evaluating answers in real time.

This ensures a faster, unbiased, and gamified interview experience while saving recruiters time and effort.
🎯 Objectives
- Automate initial candidate screening
- Generate role-specific questions using AI
- Provide real-time evaluation and scoring
- Create an engaging, gamified experience for candidates
- Save candidate data for HR review
🧩 Modules
1. Greeting Module
   - Welcomes the candidate
   - Explains the process
   - Asks for candidate’s name

2. Information Collection Module
   - Collects personal and professional details
   - Extracts email, phone, experience, position, skills

3. Question Generation Module
   - Uses Groq Llama3-70B model
   - Generates 5 domain-specific interview questions
   - Questions tagged with (domain) and (yes/no) or (open)

4. Evaluation Module
   - AI scores answers from 1–5
   - Provides constructive feedback
   - Stores answers with scores and feedback

5. Completion Module
   - Ends the interview with a summary
   - Saves candidate data in JSON for review
   - Displays a gamified success message 🎉
🔄 Flow of the System
1. Candidate enters their name
2. System asks for email, phone, experience, position, location, skills
3. AI generates 5 interview questions based on skills
4. Candidate answers each question
5. AI provides score + feedback
6. After final question → Completion message + Data saved
🛠️ Technologies Used
- Programming Language: Python 3.x
- Framework: Streamlit
- AI Model: Groq API – Llama3-70B
- Environment Variables: python-dotenv
- Data Storage: JSON files (auto-saved with timestamp)
- Styling: Custom CSS for chat-like UI
🚀 Setup & Installation
1. Clone the repository:
   git clone https://github.com/yourusername/talentscout-ai.git
   cd talentscout-ai

2. Install dependencies:
   pip install -r requirements.txt

3. Create a .env file with your Groq API key:
   GROQ_API_KEY=your_api_key_here

4. Run the app:
   streamlit run app.py
🔮 Future Enhancements
- Integrate with databases (Postgres, MongoDB) for large-scale storage
- Support for resume uploads and skill extraction
- Integration with ATS / HRMS systems
- Bias detection and fairness reporting
- Multi-language support for global hiring
✅ Conclusion
TalentScout demonstrates how AI can transform recruitment by automating initial interviews, ensuring unbiased evaluations, and creating a fun, gamified experience for candidates.

This project lays the foundation for smarter, faster, and fairer hiring. 🚀
