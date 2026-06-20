# prompts/companies/tcs.py
"""
TCS company config for interviewphodo.com
==========================================
DESIGN RULE: These are TOPIC POOLS and DIFFICULTY TIERS — not a fixed question list.
Gemini reads these as inspiration and generates fresh, contextual questions every
session. The memory system (Step 18) prevents cross-session repetition on top of this.
Never instruct Gemini to copy these verbatim.
"""

TCS_CONFIG = {
    "company_id":       "tcs",
    "company_name":     "TCS (Tata Consultancy Services)",
    "interviewer_name": "Ramesh Iyer",
    "interviewer_role": "Senior HR Manager",
    "style": "Formal and structured. TCS is India's largest IT employer. They prioritize "
             "attitude, trainability, and 2-year commitment over deep technical skills.",
    "culture": "Integrity, respect, excellence, continuous learning. 2-year bond standard.",
    "tech_focus": "OOP (4 pillars with real examples), DBMS (normalization, SQL), "
                  "OS (process vs thread, deadlock, paging), basic DSA (arrays, sorting — "
                  "verbal explanation of approach and time complexity), networking basics.",

    # ── TECHNICAL TOPIC POOL ─────────────────────────────────────────────────
    # 25 topic areas across 3 difficulty tiers.
    # Gemini picks 4 fresh angles from these per session — never copies verbatim.
    "verbal_technical_questions": """
DIFFICULTY: BASIC (use for session 1 or weak performers)
Topics to generate questions from:
- OOP: What is encapsulation and why does it matter? Real-world analogy expected.
- OOP: Explain inheritance. How does it reduce code duplication?
- OOP: What is polymorphism? Give an example from daily life.
- OOP: What is abstraction? How is it different from encapsulation?
- DBMS: What is a primary key? What makes it different from a unique key?
- DBMS: What is a foreign key? How does it link two tables?
- OS: What is the difference between a process and a thread?
- DSA: What is an array? When would you use a linked list instead?
- DSA: What is a stack? Give a real-world use case.
- Networking: What is the difference between TCP and UDP?

DIFFICULTY: INTERMEDIATE (use for session 2+ or good performers)
Topics to generate questions from:
- OOP: Explain method overloading vs method overriding with examples.
- OOP: What is a constructor? When would you use a parameterised constructor?
- DBMS: Explain 1NF, 2NF, 3NF normalization in simple terms with a small example.
- DBMS: What is a JOIN? Explain INNER JOIN vs LEFT JOIN with a use case.
- DBMS: What is an index? How does it improve query performance?
- OS: What is a deadlock? What are the four conditions required for it?
- OS: Explain paging and segmentation — what problem do they solve?
- DSA: Walk me through how binary search works. What is its time complexity?
- DSA: Explain the difference between BFS and DFS. When would you prefer each?
- DSA: What is a hash table? How does it handle collisions?

DIFFICULTY: ADVANCED (use for session 3+ or high performers)
Topics to generate questions from:
- OOP: What is the SOLID principle? Explain any two with examples.
- DBMS: What is a transaction? Explain ACID properties with a real scenario.
- DBMS: What is a stored procedure? How is it different from a function?
- OS: What is virtual memory? How does the OS manage it?
- DSA: What is dynamic programming? When would you use it over recursion?
- DSA: Explain the time and space complexity of merge sort vs quick sort.
""",

    # ── BEHAVIORAL TOPIC POOL ────────────────────────────────────────────────
    # 20 topic areas across 5 behavioral dimensions.
    # Gemini generates contextual STAR-format questions from these — never copies.
    "behavioral_questions": """
BEHAVIORAL DIMENSION: Teamwork & Conflict
- A situation where team members strongly disagreed on an approach
- Working with a difficult team member who was not contributing
- A time when you had to convince your team to change direction
- Coordinating across different skill levels in a group project

BEHAVIORAL DIMENSION: Handling Failure & Learning
- A project or assignment you failed at — what exactly went wrong
- A time you received harsh feedback — how you responded
- A technical mistake you made and how you fixed it
- A situation where you had to start over from scratch

BEHAVIORAL DIMENSION: Taking Initiative
- Going beyond what was assigned to improve a project
- Identifying a problem nobody else noticed and solving it
- Self-learning a skill specifically to contribute better

BEHAVIORAL DIMENSION: Working Under Pressure
- Managing multiple deadlines simultaneously in college
- A situation where requirements changed at the last minute
- Dealing with a high-stakes presentation or viva under pressure

BEHAVIORAL DIMENSION: Leadership & Communication
- Leading a team even without formal authority
- Explaining a complex technical concept to a non-technical person
- A situation where you had to take responsibility for a team failure
""",

    # ── HR TOPIC POOL ────────────────────────────────────────────────────────
    "hr_round_questions": """
STANDARD HR TOPICS (generate fresh variations each session):
- Motivation: Why TCS specifically vs other IT companies?
- Career vision: Where do you see yourself in 3-5 years?
- Self-awareness: What is your biggest professional weakness with a real example?
- Work style: How do you handle working under a manager you disagree with?
- Learning: How do you stay updated with new technologies outside college?
- Teamwork: What kind of team environment brings out your best work?
- Adaptability: How quickly can you shift to a completely new technology stack?
- Work-life: How do you manage stress during demanding project phases?
""",

    # ── TRAP QUESTIONS ───────────────────────────────────────────────────────
    # These test real readiness for actual TCS interviews.
    # Gemini generates a natural variation — keeps the core test, varies wording.
    "hr_trap_questions": """
TRAP TOPIC: Bond clause
Core test: Will the student commit to 2 years? Do they know the implications?
Sample angle: "TCS requires a 2-year commitment — are you comfortable with that?"
Vary: ask about their understanding of what happens if they break the bond early.

TRAP TOPIC: Relocation
Core test: Is the student genuinely flexible or just saying yes?
Sample angle: "We may post you to any city — what if it is somewhere you have never been?"
Vary: ask about a specific city they mentioned NOT wanting to go to.

TRAP TOPIC: CTC expectation
Core test: Do they know how to answer this without underselling or being unrealistic?
Sample angle: "What salary are you expecting as a fresher at TCS?"
Vary: ask what they would do if the offer is lower than they expected.

TRAP TOPIC: Competing offers
Core test: Honesty and loyalty signal.
Sample angle: "Do you have any other offer letters at the moment?"
Vary: ask what they would do if a competitor offered 20% more.

TRAP TOPIC: Why not product companies
Core test: Is their motivation for TCS genuine or is it a fallback?
Sample angle: "Why TCS when product companies pay 3-4x more for freshers?"
Vary: ask about their long-term career plan if TCS is their first choice.
""",
}
