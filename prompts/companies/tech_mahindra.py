# prompts/companies/tech_mahindra.py
TECH_MAHINDRA_CONFIG = {
    "company_id":       "tech_mahindra",
    "company_name":     "Tech Mahindra",
    "interviewer_name": "Vikram Gupta",
    "interviewer_role": "Talent Acquisition Specialist",
    "style": "Conversational, moderately formal. Strong telecom background — "
             "networking knowledge genuinely valued. Less strict than TCS.",
    "culture": "Connected world, connected experiences. Diverse and global mindset.",
    "tech_focus": "Networking (OSI, protocols, 5G basics), telecom fundamentals, "
                  "OOP, SQL, basic Python or shell scripting.",

    "verbal_technical_questions": """
DIFFICULTY: BASIC
Topics to generate questions from:
- Networking: Explain the OSI model — what happens at each layer?
- Networking: What is the difference between a router and a switch?
- Telecom: What is 5G? How does it differ from 4G in terms of speed and use cases?
- Networking: What is a MAC address and how does it differ from an IP address?
- OOP: What is encapsulation? Give an example from a telecom application.
- Basics: What is VoIP? Give a real-world example of where it is used.
- Networking: What is a firewall? What does it protect against?
- Scripting: What is the purpose of a shell script? Give one example use case.

DIFFICULTY: INTERMEDIATE
Topics to generate questions from:
- Networking: What is the difference between synchronous and asynchronous communication?
- Networking: What is NAT and why is it needed in home/office networks?
- Telecom: What is LTE (Long Term Evolution)? How does it relate to 4G?
- Networking: Explain the three-way TCP handshake step by step.
- Linux: What is the difference between a process and a daemon in Linux?
- Networking: What is DHCP and what problem does it solve?
- Security: What is a VPN? How does it create a private tunnel over a public network?
- Protocols: What is the difference between FTP and SFTP?

DIFFICULTY: ADVANCED
Topics to generate questions from:
- Telecom: What is network slicing in 5G? Why is it important for enterprise use?
- Networking: Explain BGP (Border Gateway Protocol) at a conceptual level.
- Cloud: What is edge computing? How does it relate to 5G deployment?
- Security: What is a man-in-the-middle attack? How do SSL certificates prevent it?
""",

    "behavioral_questions": """
BEHAVIORAL DIMENSION: Technical Communication
- Explaining a complex networking concept to a non-technical teammate
- Documenting something so well that someone else could follow it without your help
- A technical presentation that did not go as planned — what you learned

BEHAVIORAL DIMENSION: Problem Solving Under Constraints
- Solving a technical problem with limited internet access or resources
- A time when the standard approach failed and you had to invent a solution
- Fixing something that had no documentation or tutorial available

BEHAVIORAL DIMENSION: Adaptability
- Working in a domain that was completely unfamiliar when the project started
- Switching from one technology to another mid-project
- A change in project direction that required relearning something

BEHAVIORAL DIMENSION: Initiative
- Starting something that improved your project without being asked
- Noticing a gap in the team's knowledge and filling it voluntarily
""",

    "hr_round_questions": """
STANDARD HR TOPICS:
- Why Tech Mahindra specifically — what do you know about their telecom focus?
- Domain interest: Are you genuinely interested in 5G, networking, or telecom?
- Global mindset: Are you open to international client postings?
- Industry trends: What is one 5G or telecom development you have been following?
- Work style: What kind of problems do you enjoy solving most?
""",

    "hr_trap_questions": """
TRAP TOPIC: Telecom domain interest
Core test: Genuine interest vs fallback offer.
Sample angle: "Tech Mahindra is heavily telecom-focused — are you genuinely interested in that domain or is this just a backup offer?"
Vary: Ask them to name a specific Tech Mahindra telecom project or client.

TRAP TOPIC: CTC vs domain
Core test: What matters more — money or work type?
Sample angle: "A service company focused on telecom may have a slower CTC growth vs product companies — does that concern you?"

TRAP TOPIC: Bench period
Core test: Self-motivation.
Sample angle: "Tech Mahindra may have a 2-3 month onboarding/bench period before your first project — how would you stay productive?"
""",
}
