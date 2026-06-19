# prompts/companies/cognizant.py
COGNIZANT_CONFIG = {
    "company_id":       "cognizant",
    "company_name":     "Cognizant (CTS)",
    "interviewer_name": "Deepak Pillai",
    "interviewer_role": "Technical HR Manager",
    "style": "Structured and formal, similar to TCS. Medium technical depth. "
             "Cognizant focuses on Java, OOP, and DBMS at fresher level.",
    "culture": "Work is personal. Values dedication, client focus, and team learning.",
    "tech_focus": "Java fundamentals, OOP (especially inheritance, polymorphism), "
                  "DBMS, SQL, data structures (arrays, linked lists), exception handling.",

    "verbal_technical_questions": """
DIFFICULTY: BASIC
Topics to generate questions from:
- OOP: What is the difference between method overloading and method overriding?
- OOP: What is abstraction — give a real-world analogy for it.
- Java: What is the difference between == and .equals() in Java?
- Java: What is a constructor? Can a constructor be private?
- DBMS: What is a JOIN in SQL? Explain with a simple two-table example.
- DBMS: What is the difference between a primary key and a unique key?
- DSA: What is an array? What are its advantages and disadvantages?
- Exception: What is an exception in programming? Give an example.

DIFFICULTY: INTERMEDIATE
Topics to generate questions from:
- OOP: What is the difference between an abstract class and an interface in Java?
- OOP: Explain the concept of encapsulation — how does it protect data?
- Java: What is the difference between ArrayList and LinkedList?
- Java: What is a try-catch block? When should you use finally?
- DBMS: What is database normalization? Explain with a practical example.
- DBMS: What is a stored procedure? How is it different from a regular SQL query?
- DSA: Explain binary search — what is the prerequisite for using it?
- DSA: What is a hash map? How does it achieve O(1) average lookup?

DIFFICULTY: ADVANCED
Topics to generate questions from:
- Java: What is multithreading? What is a race condition and how do you prevent it?
- OOP: Explain the Open/Closed Principle — how does it improve maintainability?
- DBMS: What are database indexes? When can an index hurt performance?
- DSA: Explain dynamic programming — what is the overlapping subproblems property?
""",

    "behavioral_questions": """
BEHAVIORAL DIMENSION: Team Dynamics
- A team project where someone was significantly stronger or weaker than you
- A situation where the team lost motivation mid-project — what you did
- Successfully delivering a project despite internal team disagreements

BEHAVIORAL DIMENSION: Learning Agility
- The fastest you ever learned a completely new concept under pressure
- Teaching yourself something with no structured guidance
- Recovering from a failed exam or assignment through a different study approach

BEHAVIORAL DIMENSION: Ownership & Accountability
- A mistake you made in a project that affected others — how you handled it
- Delivering something on time despite unexpected obstacles
- Saying no to something you genuinely could not commit to

BEHAVIORAL DIMENSION: Work Ethic
- Putting in extra effort when the minimum would have been acceptable
- A time you stayed with a difficult problem until you solved it
- Balancing quality vs speed when both were required
""",

    "hr_round_questions": """
STANDARD HR TOPICS:
- Why Cognizant over other IT companies?
- Shift availability: Are you open to night shifts for US/UK clients?
- Career path: Where do you want to be in your career in 3 years?
- Handling monotony: How do you stay motivated when work is repetitive?
- Feedback: What is the most critical feedback you have received and acted on?
""",

    "hr_trap_questions": """
TRAP TOPIC: Bond
Core test: Commitment awareness.
Sample angle: "CTS has a 1-year service bond — do you know what the exit terms are?"
Vary: Ask what their plan is if they receive a better offer during the bond period.

TRAP TOPIC: Academic concern
Core test: Honesty about record.
Sample angle: "Your academic record shows some inconsistency — can you walk me through it?"
Vary: Ask what specifically they did differently after a weak semester.

TRAP TOPIC: Night shift readiness
Core test: Real flexibility vs performative yes.
Sample angle: "Some of our clients are in the US — you may be working 5 PM to 2 AM IST regularly. Is that truly okay?"
""",
}
