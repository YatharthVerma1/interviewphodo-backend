# prompts/companies/infosys.py
INFOSYS_CONFIG = {
    "company_id":       "infosys",
    "company_name":     "Infosys",
    "interviewer_name": "Priya Sharma",
    "interviewer_role": "Talent Acquisition Lead",
    "style": "Moderately formal. Infosys values problem-solving attitude, adaptability, "
             "and learning mindset. More conversational than TCS. No bond.",
    "culture": "Learning agility, teamwork, client-first mindset, continuous improvement.",
    "tech_focus": "Data structures (arrays, linked lists, stacks, queues — conceptual), "
                  "algorithms (sorting, searching — verbal approach), OOP, SQL, "
                  "Python or Java basics, how the internet works.",

    "verbal_technical_questions": """
DIFFICULTY: BASIC
Topics to generate questions from:
- DSA: What is the difference between a stack and a queue? Give real-world examples.
- DSA: What is an array? What is its main limitation?
- OOP: Explain inheritance — give a practical, original example not from textbooks.
- OOP: What is encapsulation? How does it help in large projects?
- SQL: What is the difference between WHERE and HAVING in SQL?
- SQL: Explain what a JOIN does — why would you need it?
- Basics: What is a variable? What is the difference between int and float?
- Networking: What happens step by step when you type google.com in a browser?

DIFFICULTY: INTERMEDIATE
Topics to generate questions from:
- DSA: What is a linked list? Code-wise, how is it different from an array in memory?
- DSA: Explain bubble sort — why is it inefficient for large data?
- DSA: Walk me through binary search. What must be true about the data first?
- OOP: What is polymorphism? Show how the same method behaves differently.
- OOP: What is an abstract class? When would you use it vs an interface?
- SQL: Write a query to find the second highest salary — explain your logic verbally.
- SQL: What is database indexing and when does it actually slow things down?
- Algorithms: Explain recursion — give a problem where recursion is elegant.

DIFFICULTY: ADVANCED
Topics to generate questions from:
- DSA: What is a binary search tree? What is its worst-case time complexity and why?
- DSA: Explain dynamic programming vs memoization — what is the difference?
- OOP: What is the difference between composition and inheritance? When to prefer which?
- System: What is a REST API? How does it differ from SOAP?
- System: Explain the client-server model — how does HTTP fit in?
""",

    "behavioral_questions": """
BEHAVIORAL DIMENSION: Problem Solving
- A technical problem you solved that initially seemed impossible
- A time you used an unconventional approach to fix something
- How you approach debugging a problem you have never seen before

BEHAVIORAL DIMENSION: Adaptability
- Learning an entirely new tool or framework under time pressure
- Switching roles or responsibilities mid-project
- Working on a project outside your comfort zone

BEHAVIORAL DIMENSION: Initiative
- Adding something to a project that nobody asked for but made it better
- Identifying a process improvement in your team or project
- Self-studying something specifically to help your team

BEHAVIORAL DIMENSION: Collaboration
- Resolving a disagreement within a project group
- Helping a struggling team member without making them feel bad
- Working with someone whose skill level was very different from yours

BEHAVIORAL DIMENSION: Accountability
- Taking responsibility for a mistake that affected your team
- Delivering something incomplete and explaining it honestly
- A commitment you made that you could not keep — how you handled it
""",

    "hr_round_questions": """
STANDARD HR TOPICS:
- Why Infosys over TCS or Wipro? What specifically attracted you?
- Adaptability: What if your first project is completely outside your domain?
- Learning speed: How do you pick up a new programming language quickly?
- Work motivation: What excites you most about a career in IT?
- Longevity: What would make you want to stay at Infosys for 5+ years?
- Self-awareness: What feedback do you get most often from peers or professors?
- Communication: How would you explain a technical issue to a non-technical client?
""",

    "hr_trap_questions": """
TRAP TOPIC: No bond — commitment test
Core test: Does the student plan to leave as soon as they get a better offer?
Sample angle: "Infosys has no bond — so what stops you from leaving in 6 months?"
Vary: Ask what their 2-year plan looks like if they join Infosys.

TRAP TOPIC: Legacy systems
Core test: Will they complain about boring work or stay professional?
Sample angle: "Many Infosys projects involve maintaining old COBOL or Java legacy code — how do you feel about that?"

TRAP TOPIC: Salary specificity
Core test: Do they know how to handle CTC negotiation professionally?
Sample angle: "Give me a specific number — what salary are you expecting?"
Vary: Ask how they arrived at that number.

TRAP TOPIC: Domain uncertainty
Core test: Flexibility and growth mindset.
Sample angle: "What if we put you in testing/QA instead of development — are you okay with that?"
""",
}
