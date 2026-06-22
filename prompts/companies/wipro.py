# prompts/companies/wipro.py
WIPRO_CONFIG = {
    "company_id":       "wipro",
    "company_name":     "Wipro",
    "interviewer_name": "Vikhyat Nair",
    "interviewer_role": "HR Business Partner",
    "style": "Friendly and process-oriented. Less technically intense than TCS at "
             "fresher level. Focus on communication, team fit, and positive attitude.",
    "culture": "Spirit of Wipro: being respectful, making a difference, client trust.",
    "tech_focus": "OOP basics, Java or Python fundamentals, SQL basics, "
                  "SDLC phases, basic networking (HTTP, DNS, IP).",

    "verbal_technical_questions": """
DIFFICULTY: BASIC
Topics to generate questions from:
- OOP: Explain inheritance — give a real example outside the classic Animal/Dog example.
- OOP: What is the purpose of a constructor in a class?
- Basics: What is the difference between a compiler and an interpreter?
- Basics: What does it mean for a function to return a value?
- SQL: What is the difference between DELETE and TRUNCATE?
- HTTP: What is the difference between GET and POST? When do you use each?
- SDLC: What does SDLC stand for? Name and briefly explain its phases.
- Networking: What is an IP address? How is IPv4 different from IPv6?

DIFFICULTY: INTERMEDIATE
Topics to generate questions from:
- OOP: What is method overriding? How does it enable runtime polymorphism?
- OOP: What is the difference between an interface and an abstract class?
- SQL: What is a foreign key constraint? What happens if you violate it?
- SQL: Explain GROUP BY — when would you use it with COUNT or SUM?
- Networking: What is DNS? Trace the journey of a domain name to an IP address.
- API: What is an API? Explain it as if explaining to a non-technical person.
- Testing: What is the difference between unit testing and integration testing?
- Version control: What is Git? Explain commit, push, pull in simple terms.

DIFFICULTY: ADVANCED
Topics to generate questions from:
- OOP: Explain the Liskov Substitution Principle with a practical example.
- System: What is a microservices architecture? How does it differ from monolithic?
- SQL: What is a database transaction? Explain commit and rollback.
- Cloud: What is the difference between IaaS, PaaS, and SaaS?
""",

    "behavioral_questions": """
BEHAVIORAL DIMENSION: Conflict Resolution
- A group project where team members had completely different working styles
- A teammate who was not pulling their weight — what you did
- A disagreement with a professor or mentor — how you handled it respectfully

BEHAVIORAL DIMENSION: Ownership
- Taking on a task that was not your responsibility because it needed doing
- A situation where you had to fix someone else's mistake
- Completing a commitment even when conditions became difficult

BEHAVIORAL DIMENSION: Communication
- Explaining a technical concept to a non-technical audience
- A presentation that did not go as planned — what you learned
- Giving feedback to a peer that was hard to hear

BEHAVIORAL DIMENSION: Time Management
- Juggling exams, project deadlines, and extracurriculars simultaneously
- A time you underestimated how long something would take
- Planning and executing a long-term project from start to finish
""",

    "hr_round_questions": """
STANDARD HR TOPICS:
- Why Wipro specifically? What do you know about its business?
- Shift readiness: Are you open to US/UK client time zone shifts?
- Repetitive work: How do you stay engaged when work becomes routine?
- Career at Wipro: What does your 3-year career path look like here?
- Learning: What is one technology trend you have been following recently?
- Values fit: What does "making a difference" mean to you in a professional context?
""",

    "hr_trap_questions": """
TRAP TOPIC: Bond clause
Core test: Awareness and commitment.
Sample angle: "Wipro has a 1-year bond with a ₹75,000 exit penalty — are you aware and okay with it?"
Vary: Ask what they would do if a better offer came during the bond period.

TRAP TOPIC: Academic record
Core test: Honesty and recovery mindset.
Sample angle: "I see a dip in your marks in one semester — can you explain what happened?"
Vary: Ask whether that experience changed how they approach challenges.

TRAP TOPIC: Bench period
Core test: Self-motivation when unassigned.
Sample angle: "Wipro may keep you on bench for 2-3 months before your first project — how would you use that time?"

TRAP TOPIC: Lower CTC
Core test: Flexibility vs hard expectations.
Sample angle: "Our fresher CTC may be lower than what you expected — is that a dealbreaker for you?"
""",
}
