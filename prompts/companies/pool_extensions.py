"""
Extra question topic pools appended to every company config at runtime.
Gemini uses these as themes — never verbatim scripts.
"""

POOL_EXTENSIONS: dict[str, dict[str, str]] = {
    "tcs": {
        "verbal_technical_questions": """
EXTRA TCS TECHNICAL THEMES:
- Explain how you would debug a production issue when logs are incomplete.
- Verbal walkthrough: design a simple student attendance system (tables + queries).
- Difference between REST and SOAP — when would TCS clients care?
- What is CI/CD? How would it help a large delivery team?
- Explain multithreading vs multiprocessing in a client-server app.
""",
        "behavioral_questions": """
EXTRA TCS BEHAVIORAL THEMES:
- Adapting when a senior rejected your approach in a college project.
- Learning TCS values (integrity, excellence) through a real campus example.
- Handling a teammate who missed deadlines during fest or hackathon season.
""",
        "hr_round_questions": """
EXTRA TCS HR THEMES:
- Two-year commitment: why TCS training model needs patience from freshers.
- Willingness for rotational learning across domains in first 18 months.
- How do you stay updated when assigned to a legacy technology stack?
""",
    },
    "infosys": {
        "verbal_technical_questions": """
EXTRA INFOSYS TECHNICAL THEMES:
- Explain MVC architecture using a project you built.
- What is an ER diagram? Design entities for a library management system.
- Difference between stack overflow and heap memory — practical impact.
- How does HTTPS handshake work at a high level?
- Explain agile ceremonies: sprint planning, retro, daily standup.
""",
        "behavioral_questions": """
EXTRA INFOSYS BEHAVIORAL THEMES:
- Following a strict process when you preferred a faster shortcut.
- Teaching a concept you just learned to a junior in your batch.
- Recovering after performing poorly in a campus mock interview.
""",
        "hr_round_questions": """
EXTRA INFOSYS HR THEMES:
- Mysore/global education campus — what do you expect from training?
- Comfort with client-facing communication in English.
- Long-term learning plan inside a large structured organization.
""",
    },
    "wipro": {
        "verbal_technical_questions": """
EXTRA WIPRO TECHNICAL THEMES:
- Explain exception handling — checked vs unchecked with examples.
- What is load balancing? Why do client projects need it?
- Describe how you would optimize a slow SQL query verbally.
- Difference between monolith and modular codebase in college projects.
- Basics of containerization — what problem does Docker solve?
""",
        "behavioral_questions": """
EXTRA WIPRO BEHAVIORAL THEMES:
- Staying positive during repetitive debugging work.
- Collaborating with someone whose communication style clashed with yours.
- Taking feedback from a client or professor and improving visibly.
""",
        "hr_round_questions": """
EXTRA WIPRO HR THEMES:
- Shift flexibility for US/UK clients — realistic expectations.
- Spirit of Wipro: give an example of earning client trust.
- Growth path from fresher to team lead — what skills will you build first?
""",
    },
    "hcl": {
        "verbal_technical_questions": """
EXTRA HCL TECHNICAL THEMES:
- Troubleshooting steps when a web API returns 500 errors.
- Explain ORM — benefits and drawbacks with a project example.
- What is caching? Where would you add cache in a web app?
- Verbal design: URL shortener data model and read/write flow.
- Difference between authentication and authorization with examples.
""",
        "behavioral_questions": """
EXTRA HCL BEHAVIORAL THEMES:
- Learning on the job when documentation was poor.
- Supporting a teammate who was struggling technically.
- Owning a bug that reached demo day — what you did next.
""",
        "hr_round_questions": """
EXTRA HCL HR THEMES:
- Mode 1/2/3 services mindset — willingness to learn business context.
- Relocation across HCL delivery centers in India.
- Salary vs learning trade-off in first two years of career.
""",
    },
    "accenture": {
        "verbal_technical_questions": """
EXTRA ACCENTURE TECHNICAL THEMES:
- Explain cloud migration risks for a legacy on-prem app.
- What is technical debt? How did you manage it in a project?
- Describe microservice communication: sync API vs message queue.
- Consulting angle: how would you gather requirements from a vague client ask?
- Explain Big-O for a feature you implemented in a college app.
""",
        "behavioral_questions": """
EXTRA ACCENTURE BEHAVIORAL THEMES:
- Working under ambiguous requirements — how you created clarity.
- Presenting to stakeholders with different technical levels.
- Multitasking during placement season — prioritization framework you used.
""",
        "hr_round_questions": """
EXTRA ACCENTURE HR THEMES:
- Global career interest — travel or international projects.
- Why consulting mindset fits your strengths.
- Handling rejection or failure in a competitive hiring process.
""",
    },
    "cognizant": {
        "verbal_technical_questions": """
EXTRA COGNIZANT TECHNICAL THEMES:
- Explain SDLC with an example from your internship or project.
- What is regression testing? When must it run before release?
- Describe session management in web applications.
- Difference between SQL and NoSQL — pick one for a chat app and justify.
- How would you explain APIs to a business analyst on day one?
""",
        "behavioral_questions": """
EXTRA COGNIZANT BEHAVIORAL THEMES:
- Balancing quality vs speed when deadline was immovable.
- Observing team dynamics and improving collaboration.
- Accountability when your module broke integration testing.
""",
        "hr_round_questions": """
EXTRA COGNIZANT HR THEMES:
- Digital engineering interest vs pure maintenance work.
- Willingness to upskill every 6–12 months in client stack.
- Cognizant culture: learning agility with a concrete example.
""",
    },
    "tech_mahindra": {
        "verbal_technical_questions": """
EXTRA TECH MAHINDRA TECHNICAL THEMES:
- Explain latency vs bandwidth — why both matter in telecom apps.
- What is SNMP? Why do network operations teams use it?
- Describe how 4G/5G handoff might affect a mobile app user experience.
- Scripting automation: one task you would automate on a Linux server.
- Difference between circuit switching and packet switching — simple analogy.
""",
        "behavioral_questions": """
EXTRA TECH MAHINDRA BEHAVIORAL THEMES:
- Explaining a networking lab experiment to a non-tech friend.
- Adapting when project scope shifted from software to telecom domain.
- Initiative: improving team documentation or lab setup without being asked.
""",
        "hr_round_questions": """
EXTRA TECH MAHINDRA HR THEMES:
- Genuine interest in connected-world / telecom digital projects.
- Openness to global client exposure and travel if required.
- How you would use bench or training time to build telecom fundamentals.
""",
    },
    "zoho": {
        "verbal_technical_questions": """
EXTRA ZOHO TECHNICAL THEMES:
- Find duplicate elements in an array — multiple approaches and complexities.
- Explain graph BFS vs DFS with a real routing or social-network analogy.
- Design a rate limiter for an API — verbal logic only.
- How would you test edge cases for a form validation module?
- Optimize search in sorted rotated array — walk through intuition.
""",
        "behavioral_questions": """
EXTRA ZOHO BEHAVIORAL THEMES:
- Building a side project users actually used — metrics of success.
- Pushing back on a mediocre solution to reach an elegant one.
- Self-learning path that proves depth (book, course, open source).
""",
        "hr_round_questions": """
EXTRA ZOHO HR THEMES:
- Name a Zoho product weakness you would fix and how.
- Comfort with long-term ownership of one product surface area.
- Why product company engineering culture fits you better than services.
""",
    },
}


def merge_pool_extensions(config: dict) -> dict:
    """Append shared extra pools onto a company config (in-place safe copy)."""
    company_id = (config.get("company_id") or "").lower()
    extra = POOL_EXTENSIONS.get(company_id, {})
    if not extra:
        return config
    merged = dict(config)
    for key, block in extra.items():
        if block.strip():
            merged[key] = (merged.get(key) or "").rstrip() + "\n" + block.strip()
    return merged
