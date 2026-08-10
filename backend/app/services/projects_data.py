PROJECTS = [
    {
        "id": 1,
        "name": "Intelligent Codebase QA & Retrieval Assistant",
        "title": "Codebase QA & Retrieval Assistant",
        "target_roles": ["AI Engineer", "Applied AI Engineer", "LLM Engineer", "Backend Engineer", "Software Engineer"],
        "tech_stack": [
            "Python", "FastAPI", "AST Parsing", "Tree-Sitter", "PostgreSQL", "pgvector", "Ollama", "Docker"
        ],
        "bullets": [
            "Built a local QA assistant that traverses code repositories using AST and Tree-Sitter parsing to answer developer questions about the codebase.",
            "Chunked source code by classes, functions, and module dependencies to preserve full technical context during retrieval.",
            "Stored code embeddings and keyword indexes in PostgreSQL (pgvector) to support hybrid semantic and exact-match search.",
            "Retrieved relevant code snippets and fed them into local Ollama LLMs to generate grounded answers for complex architecture and logic questions.",
            "Implemented dependency tree traversal to trace function call hierarchies and variable usages across multi-file projects."
        ],
        "description": "A local QA assistant that traverses code repositories, indexes functions and classes in PostgreSQL with pgvector, and answers developer questions using RAG retrieval."
    },
    {
        "id": 2,
        "name": "Automated PR Documentation Agent with Dynamic Tool Calling",
        "title": "Automated PR Documentation Agent",
        "target_roles": ["AI Agent Engineer", "AI Engineer", "LLM Engineer", "Backend Engineer", "Software Engineer"],
        "tech_stack": [
            "Python", "FastAPI", "Pydantic", "Celery", "Redis", "PostgreSQL", "GitHub Webhooks", "Docker"
        ],
        "bullets": [
            "Built an automated PR documentation agent that listens to GitHub webhooks and executes targeted doc tools based on file diffs.",
            "Parsed PR code diffs (`unidiff`) to dynamically trigger specific tools for README updates, API schema docs, and database migration notes.",
            "Configured HMAC-SHA256 verified GitHub webhooks and an async Celery/Redis queue to process PR events in the background.",
            "Enforced strict Pydantic schemas on tool arguments and outputs to ensure generated doc updates remain valid before commenting on PRs.",
            "Persisted PR events, file diffs, and tool execution logs in PostgreSQL to support retries and track documentation updates."
        ],
        "description": "An automated PR documentation agent that processes merged GitHub pull requests and invokes targeted doc tools based on changed files."
    },
    {
        "id": 3,
        "name": "High-Throughput Financial Order Ledger",
        "title": "High-Throughput Financial Order Ledger & Event Gateway",
        "target_roles": ["Java Developer", "Java Backend Engineer", "Software Engineer"],
        "tech_stack": [
            "Java 21", "Spring Boot 3.3", "Apache Kafka", "Redis", "Redisson", "PostgreSQL", "Flyway", "Testcontainers", "JUnit 5"
        ],
        "bullets": [
            "Architected a Java 21 / Spring Boot 3.3 order processing ledger microservice utilizing Virtual Threads for concurrent request execution.",
            "Implemented Redisson distributed locking on account IDs to prevent race conditions and balance inconsistencies during concurrent transactions.",
            "Integrated Kafka event messaging using the Transactional Outbox Pattern to decouple HTTP request completion from downstream event dispatch.",
            "Executed load benchmarks using k6 to evaluate system throughput, p95/p99 latency, and Redis lock acquisition overhead under synthetic load."
        ],
        "description": "High-throughput Java 21 order processing service built with Spring Boot 3.3, Kafka messaging, Redisson distributed locking, and k6 load benchmarking."
    },
]

# Role-specific reframing for AI-leaning templates when shown to backend/fullstack recruiters
_PROJECT_2_FRAMING = {
    "ai_platform_engineer": {
        "title": "Autonomous Multi-Agent Code Refactoring Engine with LangGraph",
        "tech_stack": [
            "Python", "FastAPI", "LangGraph", "PostgreSQL", "Redis", "Docker"
        ],
        "bullets": [
            "Engineered a multi-agent orchestration state machine in LangGraph (Planner, Generator, Tester, Refiner) to automate python code refactoring and unit test generation.",
            "Defined strict Pydantic JSON Schema tool-calling interfaces with fallback handlers for tool argument parsing errors.",
            "Implemented execution safety controls including step depth limits (max 12 turns) and AST static analysis validation to prevent recursive agent execution loops.",
            "Persisted state machine steps in PostgreSQL with Redis caching, enabling execution resume after API timeout failures.",
        ],
    },
    "backend_engineer": {
        "title": "Distributed Workflow Execution Platform",
        "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
        "bullets": [
            "Engineered a distributed workflow execution service with task decomposition, reducing processing time for automated code refactoring.",
            "Implemented schema-validated REST interfaces and dynamic routing between worker services.",
            "Designed reliability guardrails with retry policies, timeouts, and step limits in production.",
            "Built monitoring for queue depth, API latency, and error rates.",
        ],
    },
    "fullstack_engineer": {
        "title": "Code Refactoring Collaboration Web Platform",
        "tech_stack": ["React", "TypeScript", "FastAPI", "PostgreSQL", "Redis", "Docker"],
        "bullets": [
            "Delivered a web platform for code task coordination with React/TypeScript UI and FastAPI backend services.",
            "Built REST APIs with validated contracts and role-aware routing between UI and backend workers.",
            "Added reliability controls (retries, timeouts, step limits) that reduced stuck workflows.",
            "Integrated operational dashboards for latency and error trends.",
        ],
    },
}

_PROJECT_3_FRAMING = {
    "ai_platform_engineer": {
        "title": "Prompt Versioning and Automated Evaluation Benchmark Service",
        "tech_stack": [
            "Python", "FastAPI", "PostgreSQL", "Redis", "Jinja2", "Docker"
        ],
        "bullets": PROJECTS[2]["bullets"] if len(PROJECTS) > 2 else [],
    },
    "backend_engineer": {
        "title": "Configuration Management API Service",
        "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
        "bullets": [
            "Developed a centralized configuration microservice supporting versioning and dynamic template rendering.",
            "Implemented release comparison tooling for testing configuration variants.",
            "Built observability dashboards tracking API latency and error rates.",
            "Designed canary routing for production release configurations.",
        ],
    },
    "fullstack_engineer": {
        "title": "Internal Admin Portal for Configuration Management",
        "tech_stack": ["React", "Next.js", "FastAPI", "PostgreSQL", "Redis", "Docker"],
        "bullets": [
            "Built an admin portal with React and FastAPI for managing versioned application settings.",
            "Shipped rollout comparison tooling for safe validation of configuration variants.",
            "Added dashboards for latency, throughput, and error tracking.",
            "Implemented canary deployment routing for zero-downtime configuration updates.",
        ],
    },
}

# Attach framing to project records (ids 2 and 3)
for _p in PROJECTS:
    if _p["id"] == 2:
        _p["framing"] = _PROJECT_2_FRAMING
        _p.setdefault("suitable_identities", ["ai_platform_engineer", "backend_engineer", "fullstack_engineer"])
    if _p["id"] == 3:
        _p["framing"] = _PROJECT_3_FRAMING
        _p.setdefault("suitable_identities", ["ai_platform_engineer", "backend_engineer", "fullstack_engineer", "devops_engineer"])
    if _p["id"] in (7, 8, 9, 10) and "suitable_identities" not in _p:
        _p["suitable_identities"] = ["backend_engineer", "fullstack_engineer"]
    if "suitable_identities" not in _p and _p["id"] <= 6:
        _p["suitable_identities"] = ["ai_platform_engineer", "ml_engineer"]
        if _p["id"] in (5,):
            _p["suitable_identities"] = ["ml_engineer", "backend_engineer"]
