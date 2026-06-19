# prompts/companies/zoho.py
ZOHO_CONFIG = {
    "company_id":       "zoho",
    "company_name":     "Zoho Corporation",
    "interviewer_name": "Anand Krishnan",
    "interviewer_role": "Senior Engineer and Interviewer",
    "style": "Highly technical. Zoho is a product company — they expect strong DSA, "
             "logical thinking, and original problem-solving. The toughest fresher "
             "interview in this list. Zoho values depth over breadth.",
    "culture": "Product-first, self-sufficient, deep technical ownership, no corporate politics.",
    "tech_focus": "DSA (sorting, searching, trees, graphs — verbal logic and pseudocode), "
                  "recursion, dynamic programming concepts, OOP depth, system thinking, "
                  "logical puzzles. Zoho may ask students to write pseudocode.",

    "verbal_technical_questions": """
DIFFICULTY: BASIC (rare at Zoho — only for clearly struggling candidates)
Topics to generate questions from:
- DSA: What is the time complexity of linear search vs binary search?
- DSA: Explain bubble sort step by step — why is it O(n²)?
- OOP: What are the four pillars of OOP? Give an original example for each.
- Recursion: What is recursion? Trace the execution of factorial(4) step by step.
- DSA: What is the difference between a stack and a queue? Implement one in pseudocode.

DIFFICULTY: INTERMEDIATE (standard Zoho fresher level)
Topics to generate questions from:
- DSA: How would you detect a cycle in a linked list? Explain Floyd's algorithm verbally.
- DSA: How would you find the second largest element in an array in one pass?
- DSA: Explain merge sort — why is it more efficient than bubble sort?
- DSA: What is a binary search tree? What is the time complexity of search, insert, delete?
- DSA: How would you check if a string is a palindrome without reversing it?
- Recursion: Write pseudocode for Fibonacci using memoization — explain why it is faster.
- OOP: What is the difference between composition and inheritance? When do you prefer each?
- Puzzles: You have 8 balls, one slightly heavier — how do you find it in 2 weighings?
- Logic: You have a 3-litre and a 5-litre jug — how do you measure exactly 4 litres?

DIFFICULTY: ADVANCED (for high performers, return sessions)
Topics to generate questions from:
- DSA: Explain quicksort — what is its worst case and how do you avoid it?
- DSA: What is a trie data structure? When would you use it over a hash map?
- DSA: Explain Dijkstra's algorithm conceptually — what problem does it solve?
- System: Design a simple URL shortener — walk me through your data structure choice.
- System: How would you design a system that finds duplicate images in a large database?
- DP: Explain the 0/1 knapsack problem — what makes it a dynamic programming problem?
- Puzzles: You have 12 balls, one is different weight — find it in 3 weighings (classic hard).
""",

    "behavioral_questions": """
BEHAVIORAL DIMENSION: Independent Learning
- Teaching yourself a technology with zero formal instruction
- Building something purely out of curiosity — not for any assignment
- Going 10 levels deeper into a topic than the syllabus required

BEHAVIORAL DIMENSION: Problem Solving Depth
- The hardest coding or logic problem you have ever solved — walk me through it
- A time you were completely stuck and how you eventually broke through
- Finding an elegant solution to a problem that had an obvious but inefficient answer

BEHAVIORAL DIMENSION: Product Thinking
- A software product or app you use daily — what would you improve and why?
- A feature you wished existed in a tool you use — could you build it?
- Identifying a gap in the market and thinking through how software could fill it

BEHAVIORAL DIMENSION: Work Ethic
- A project you were genuinely proud of — what made it excellent?
- Finishing something that most people would have given up on
- Staying with an unsolved problem for days or weeks until it clicked
""",

    "hr_round_questions": """
STANDARD HR TOPICS:
- Why Zoho specifically — name a Zoho product you have actually used.
- Product company vs service: What is the fundamental difference in day-to-day work?
- Long-term focus: Zoho engineers often spend 2-3 years on one product — are you okay with depth over breadth?
- Self-sufficiency: How do you work when there is no manager checking on you?
- Open source: Have you contributed to any open source project or built anything public?
- Learning: What technical book, course, or project are you working on right now?
""",

    "hr_trap_questions": """
TRAP TOPIC: Off-campus, no brand name degree
Core test: Self-confidence and merit mindset.
Sample angle: "Zoho largely hires through off-campus drives — you do not have a brand-name college. Why should we pick you over someone from a top NIT?"
Vary: Ask what specifically sets their skills apart from peers at better-ranked colleges.

TRAP TOPIC: Salary vs product
Core test: Genuine motivation.
Sample angle: "Zoho pays less than FAANG companies — what is your actual reason for choosing Zoho?"
Vary: Ask what they would do if they received a competing offer 40% higher.

TRAP TOPIC: Long tenure on one product
Core test: Patience and depth orientation.
Sample angle: "Zoho engineers work on the same product for years without switching roles — how do you feel about that level of focus?"
Vary: Ask what they would do if they felt bored with the same product after 18 months.

TRAP TOPIC: No formal management structure
Core test: Self-management capability.
Sample angle: "Zoho has very flat hierarchy — there is no hand-holding. How do you manage your own time and priorities without external pressure?"
""",
}
