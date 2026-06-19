# prompts/companies/hcl.py
HCLTEC_CONFIG = {
    "company_id":       "hcl",
    "company_name":     "HCLTech",
    "interviewer_name": "Suresh Menon",
    "interviewer_role": "Technical Recruitment Manager",
    "style": "Conversational, less structured than TCS. HCL focuses on infrastructure, "
             "cloud, and networking. Relatively accessible fresher interview.",
    "culture": "Employees first, clients second. Known for work-life balance in India.",
    "tech_focus": "Networking (OSI model, protocols, IP addressing), cloud fundamentals "
                  "(IaaS/PaaS/SaaS, AWS/Azure basics), Linux basics, OOP, scripting.",

    "verbal_technical_questions": """
DIFFICULTY: BASIC
Topics to generate questions from:
- Networking: Name the 7 layers of the OSI model — what does each layer do?
- Networking: What is the difference between TCP and UDP? Which is reliable and why?
- Networking: What is an IP address? What is a subnet mask?
- Cloud: What is cloud computing? Name three benefits of using it.
- Linux: Name 5 basic Linux commands and explain what each does.
- OOP: Explain encapsulation — why would you hide data inside a class?
- Basics: What is the difference between RAM and storage (HDD/SSD)?
- Networking: What is a MAC address? How is it different from an IP address?

DIFFICULTY: INTERMEDIATE
Topics to generate questions from:
- Networking: What is DNS? Trace a DNS lookup from browser to server step by step.
- Networking: What is the difference between a router and a switch?
- Networking: What is NAT (Network Address Translation) and why is it used?
- Cloud: Explain the difference between public cloud, private cloud, and hybrid cloud.
- Cloud: What is a virtual machine? How is it different from a container?
- Linux: What does the chmod command do? Explain file permission numbers.
- Scripting: What is a shell script? Give an example of when you would write one.
- Security: What is a firewall? What is the difference between stateful and stateless?

DIFFICULTY: ADVANCED
Topics to generate questions from:
- Cloud: What is Kubernetes? What problem does container orchestration solve?
- Networking: What is BGP? Where is it used?
- Security: What is a VPN? How does it create a secure tunnel?
- DevOps: What is CI/CD? Explain the pipeline from code commit to deployment.
""",

    "behavioral_questions": """
BEHAVIORAL DIMENSION: Technical Troubleshooting
- A time you debugged a problem that took much longer than expected
- Fixing something that broke right before a deadline
- Solving a problem with limited resources or documentation

BEHAVIORAL DIMENSION: Learning on the Job
- Teaching yourself a skill specifically for a project need
- A time you had to figure something out with no one to ask
- Following up on something you did not understand until you fully got it

BEHAVIORAL DIMENSION: Teamwork
- Coordinating with team members who had conflicting schedules
- A situation where you had to depend on someone unreliable
- Helping a peer who was stuck on a technical problem

BEHAVIORAL DIMENSION: Adaptability
- Switching from one project approach to a completely different one mid-way
- Working in a domain that was new to you — what you did to get up to speed
""",

    "hr_round_questions": """
STANDARD HR TOPICS:
- Why HCLTech specifically vs TCS or Infosys?
- Infrastructure interest: Are you genuinely interested in networking/cloud domains?
- International work: Are you open to working with global clients across time zones?
- Staying updated: What cloud certification or networking course have you looked into?
- Work-life: What does a healthy work environment mean to you?
- Career goal: Where do you want to be in 3 years within the infrastructure/cloud space?
""",

    "hr_trap_questions": """
TRAP TOPIC: Lower starting CTC
Core test: Realistic expectations and flexibility.
Sample angle: "HCL's fresher package is slightly lower than TCS — does that concern you?"
Vary: Ask what factors beyond salary matter to them.

TRAP TOPIC: Infrastructure vs development
Core test: Genuine interest or just a backup offer?
Sample angle: "This role is primarily infrastructure support, not software development — are you truly okay with that?"

TRAP TOPIC: Location posting
Core test: Flexibility.
Sample angle: "HCL may post you to a smaller city like Nagpur or Coimbatore — is that acceptable?"
""",
}
