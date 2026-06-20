# prompts/companies/accenture.py
ACCENTURE_CONFIG = {
    "company_id":       "accenture",
    "company_name":     "Accenture",
    "interviewer_name": "Meera Krishnan",
    "interviewer_role": "Campus Recruiting Lead",
    "style": "Corporate but warm. Accenture is a consulting firm — they weight "
             "communication, presentation, and client-facing maturity heavily.",
    "culture": "Client value creation, one global network, respect for individuals, "
               "best people, integrity and transparency.",
    "tech_focus": "OOP, basic data structures, SQL, REST APIs, agile methodology, "
                  "cloud awareness (IaaS/PaaS/SaaS), version control basics.",

    "verbal_technical_questions": """
DIFFICULTY: BASIC
Topics to generate questions from:
- OOP: Explain encapsulation — give an example from a real application.
- SQL: What is the difference between SQL and NoSQL? When would you use each?
- API: What is a REST API? How does a client communicate with a server?
- Basics: What is the difference between frontend and backend development?
- Agile: What is agile methodology? What is a sprint?
- Git: What is version control? Name 3 common Git commands and explain them.
- Cloud: What is cloud computing? Name one advantage over on-premise servers.
- HTTP: What is the difference between HTTP and HTTPS?

DIFFICULTY: INTERMEDIATE
Topics to generate questions from:
- OOP: Explain the difference between a class and an object — with a code-level analogy.
- SQL: What is a transaction? What does ACID stand for?
- API: What is the difference between GET, POST, PUT, DELETE in REST?
- Testing: What is unit testing? Why is it important before deployment?
- Agile: What is the difference between Scrum and Kanban?
- Security: What is SQL injection? How do you prevent it?
- System: What is a database schema? How does it differ from a database?
- OOP: Explain the Single Responsibility Principle — why does it reduce bugs?

DIFFICULTY: ADVANCED
Topics to generate questions from:
- Architecture: What is a microservices architecture? Name one advantage and one challenge.
- API: What is GraphQL? How does it differ from REST?
- DevOps: What is Docker? What problem does containerisation solve?
- Security: What is OAuth? How does token-based authentication work?
""",

    "behavioral_questions": """
BEHAVIORAL DIMENSION: Client Communication
- Explaining a complex technical issue to someone non-technical
- A situation where stakeholder expectations were misaligned with reality
- Handling a request you did not have the answer to immediately

BEHAVIORAL DIMENSION: Consulting Mindset
- Identifying a problem in a process and proposing a structured solution
- A time you had to present findings or recommendations to an audience
- Persuading someone to change their approach using data or logic

BEHAVIORAL DIMENSION: Working Under Ambiguity
- A project where requirements were unclear or kept changing
- Making a decision with incomplete information
- Starting a task with no clear instructions

BEHAVIORAL DIMENSION: Multitasking
- Handling multiple responsibilities simultaneously in college
- Switching context between completely different tasks in a day
- Prioritising when everything seems equally urgent
""",

    "hr_round_questions": """
STANDARD HR TOPICS:
- Why consulting and why Accenture specifically?
- Client site travel: Are you comfortable working at client locations across India?
- Project switching: Accenture projects rotate — how do you handle constant change?
- Client pressure: How do you handle a demanding client who is never satisfied?
- Values: What does "integrity" mean to you in a professional context?
- Growth: What kind of role do you want to be in 5 years from now?
""",

    "hr_trap_questions": """
TRAP TOPIC: Travel commitment
Core test: Real flexibility or just interview-day yes?
Sample angle: "This role may require you to be at client sites 4 days a week — are you genuinely okay with that?"
Vary: Ask how they would handle being away from home for weeks at a time.

TRAP TOPIC: Standardised CTC
Core test: Maturity around compensation.
Sample angle: "Accenture's fresher package is non-negotiable — does that work for you?"
Vary: Ask what their minimum acceptable CTC is and why.

TRAP TOPIC: Domain unpredictability
Core test: Flexibility vs preferences.
Sample angle: "Your first project might be in SAP or mainframe — completely different from your BTech focus. How would you approach that?"
""",
}
