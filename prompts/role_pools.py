"""Role-specific interview question pools — ~50% of technical/resume questions."""

from __future__ import annotations

# Frontend signup labels → internal ids
ROLE_LABEL_TO_ID: dict[str, str] = {
    "SDE / Backend": "sde_backend",
    "AI / Data Science": "ai_data_science",
    "VLSI / Embedded": "vlsi_embedded",
    "DevOps / Cloud": "devops_cloud",
}

TIMELINE_LABEL_TO_ID: dict[str, str] = {
    "Interview this week": "this_week",
    "Interview in 2–4 weeks": "two_to_four_weeks",
    "Interview in 1–3 months": "one_to_three_months",
    "Just exploring": "exploring",
}

VALID_TARGET_ROLES = frozenset(ROLE_LABEL_TO_ID.values())


def normalize_target_role(value: str | None) -> str | None:
    if not value or not str(value).strip():
        return None
    raw = str(value).strip()
    if raw in VALID_TARGET_ROLES:
        return raw
    if raw in ROLE_LABEL_TO_ID:
        return ROLE_LABEL_TO_ID[raw]
    lowered = raw.lower().replace(" ", "_").replace("/", "_")
    for rid in VALID_TARGET_ROLES:
        if rid in lowered or lowered in rid:
            return rid
    return None


def normalize_timeline(value: str | None) -> str | None:
    if not value or not str(value).strip():
        return None
    raw = str(value).strip()
    if raw in TIMELINE_LABEL_TO_ID.values():
        return raw
    return TIMELINE_LABEL_TO_ID.get(raw, raw.lower().replace(" ", "_")[:64])


ROLE_POOLS: dict[str, dict] = {
    "sde_backend": {
        "label": "SDE / Backend",
        "technical": """
ROLE-SPECIFIC TECHNICAL THEMES (SDE / Backend — use ~50% of technical questions from here):
- Arrays, strings, hash maps: two-pointer, sliding window, frequency counting (verbal — no IDE)
- Linked lists, stacks, queues: reversal, cycle detection, monotonic stack use-cases
- Trees & graphs: BFS/DFS intuition, shortest path concepts, tree traversals
- Time/space complexity: Big-O for their stated approach; trade-offs between sorting vs hashing
- OOP & design basics: encapsulation, inheritance vs composition, SOLID at a fresher level
- DBMS: indexing, normalisation, JOIN types, when to use SQL vs NoSQL
- OS: processes vs threads, deadlock, mutex/semaphore, context switching
- Concurrency: race conditions, thread safety, producer-consumer pattern verbally
- System design lite: design URL shortener, rate limiter, chat at a 0–2 YOE level
- API design: REST verbs, idempotency, pagination, error handling
- Backend stack: explain a REST API they built; auth (JWT/session), middleware
- Debugging: how they'd trace a 500 error or memory leak in a project
""",
        "behavioral": """
ROLE-SPECIFIC BEHAVIORAL (SDE / Backend):
- Debugging a critical production bug under time pressure
- Disagreeing with a senior on a technical approach — how they handled it
- Optimising slow API/database query in a college or internship project
- Learning a new framework/language quickly for a deadline
""",
        "resume": """
ROLE-SPECIFIC RESUME PROBES (SDE / Backend):
- Deep-dive one backend/API project: endpoints, DB schema, bottlenecks
- Ask about Git workflow, code review, unit testing if mentioned on resume
- If they list DSA platforms — pick one problem type they solved and ask approach
""",
    },
    "ai_data_science": {
        "label": "AI / Data Science",
        "technical": """
ROLE-SPECIFIC TECHNICAL THEMES (AI / Data Science — ~50% of technical questions):
- ML fundamentals: bias-variance, overfitting, train/val/test split, cross-validation
- Supervised vs unsupervised; classification vs regression with Indian industry examples
- Linear & logistic regression intuition; when NOT to use them
- Decision trees, random forests, gradient boosting — trade-offs verbally
- Evaluation metrics: accuracy vs F1 vs AUC-ROC; imbalanced datasets
- Feature engineering: scaling, encoding categoricals, handling missing data
- Neural networks basics: layers, activation, backprop intuition (no heavy math)
- CNN vs RNN vs Transformers — when each applies (vision, NLP, sequences)
- NLP: tokenisation, embeddings, fine-tuning vs prompt engineering for LLMs
- MLOps lite: model versioning, monitoring drift, batch vs online inference
- Python data stack: pandas, numpy, sklearn — practical problem solving
- SQL for analytics: window functions, aggregations, joins for feature extraction
- Statistics: mean vs median, p-value intuition, correlation vs causation
- Projects: explain end-to-end ML pipeline they built; data collection to deployment
- GenAI: RAG, vector DBs, hallucination mitigation at conceptual level
""",
        "behavioral": """
ROLE-SPECIFIC BEHAVIORAL (AI / Data Science):
- Presenting model results to non-technical stakeholders
- Handling a model that performed well offline but failed in production
- Ethical concerns with data (privacy, bias) in a project
- Self-learning path into ML/AI — courses, Kaggle, research papers
""",
        "resume": """
ROLE-SPECIFIC RESUME PROBES (AI / Data Science):
- Walk through one ML project: problem, dataset, model choice, metrics, outcome
- Ask about datasets used — size, cleaning, label quality
- If Kaggle/competition mentioned — what they learned, not just rank
""",
    },
    "vlsi_embedded": {
        "label": "VLSI / Embedded",
        "technical": """
ROLE-SPECIFIC TECHNICAL THEMES (VLSI / Embedded — ~50% of technical questions):
- Digital logic: gates, multiplexers, flip-flops, counters, FSM design
- Verilog/VHDL basics: module, always blocks, blocking vs non-blocking assignments
- Clock domains, metastability, synchronisers — conceptual
- CMOS fundamentals: pull-up/down, power consumption, propagation delay
- Memory: SRAM vs DRAM, cache hierarchy basics
- Microcontrollers: timers, interrupts, GPIO, UART/SPI/I2C protocols
- Embedded C: pointers, volatile, bit manipulation, memory-mapped I/O
- RTOS basics: tasks, scheduling, semaphores in embedded context
- PCB/hardware awareness: reading schematics if on resume
- Testing: simulation vs synthesis, testbenches, corner cases
- Low-level debugging: oscilloscope/logic analyser use-cases verbally
- Power optimisation in battery-powered devices
- Automotive/IoT embedded scenarios common in Indian placements
""",
        "behavioral": """
ROLE-SPECIFIC BEHAVIORAL (VLSI / Embedded):
- Hardware-software co-design challenge in a college project
- Working with incomplete specs from a client or professor
- Attention to detail — catching a timing bug before tape-out / demo
""",
        "resume": """
ROLE-SPECIFIC RESUME PROBES (VLSI / Embedded):
- FPGA/Verilog project: architecture, modules, simulation results
- Embedded project: sensors, MCU choice, communication protocol used
""",
    },
    "devops_cloud": {
        "label": "DevOps / Cloud",
        "technical": """
ROLE-SPECIFIC TECHNICAL THEMES (DevOps / Cloud — ~50% of technical questions):
- Linux: file permissions, processes, cron, systemd, common troubleshooting commands
- Networking: TCP vs UDP, DNS, HTTP/HTTPS, load balancers, firewalls
- Shell scripting: automating deploy/logs backup; error handling in bash
- Git & CI/CD: branch strategies, pipeline stages, rollback strategy
- Docker: images vs containers, Dockerfile best practices, multi-stage builds
- Kubernetes lite: pods, services, deployments, scaling, ConfigMaps/Secrets
- Cloud (AWS/GCP/Azure): EC2/VM, S3/blob storage, IAM basics, VPC concept
- IaC: Terraform/CloudFormation purpose — idempotency, state files
- Monitoring: metrics vs logs vs traces; Prometheus/Grafana/CloudWatch concepts
- Incident response: on-call, postmortem, SLI/SLO/SLA at fresher level
- Security: secrets management, least privilege, container scanning
- High availability: multi-AZ, health checks, blue-green vs canary deploy
- Database ops: backups, replication, connection pooling
- Cost optimisation in cloud for student/side projects
""",
        "behavioral": """
ROLE-SPECIFIC BEHAVIORAL (DevOps / Cloud):
- Handling a failed deployment on demo/deadline day
- Automating a manual process that saved team time
- Explaining an outage to management — communication under pressure
""",
        "resume": """
ROLE-SPECIFIC RESUME PROBES (DevOps / Cloud):
- CI/CD pipeline they built: tools, stages, how they tested it
- Cloud project: services used, architecture diagram verbally, cost/security choices
""",
    },
}


def get_role_pool(target_role: str | None) -> dict | None:
    key = normalize_target_role(target_role)
    if not key:
        return None
    return ROLE_POOLS.get(key)


def build_role_prompt_block(target_role: str | None) -> str:
    """Inject ~50% role-specific question guidance into Gemini system prompt."""
    pool = get_role_pool(target_role)
    if not pool:
        return ""

    return f"""
=== CANDIDATE TARGET ROLE: {pool['label']} ===
This student signed up for {pool['label']} placement preparation.
QUESTION MIX RULE (CRITICAL):
- In TECHNICAL phase: roughly HALF your questions should draw from ROLE-SPECIFIC
  themes below; the other half from the company's general technical pool.
- In RESUME phase: prioritise ROLE-SPECIFIC resume probes when relevant.
- In BEHAVIORAL phase: include at least one ROLE-SPECIFIC behavioral theme.
- Never ignore their role — a DevOps candidate should not get only DSA graph theory.
- Still generate FRESH questions every session — themes are inspiration, not a script.

{pool.get('technical', '')}
{pool.get('behavioral', '')}
{pool.get('resume', '')}
"""
