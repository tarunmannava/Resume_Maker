PROJECTS = [
    {
        "id": 1,
        "name": "Project 1 - Production RAG-Based FAQ - Support System",
        "title": "Production-Grade Hybrid RAG Support Assistant with Evaluation Framework",
        "target_roles": ["AI Engineer", "Applied AI Engineer", "GenAI Engineer", "LLM Engineer"],
        "tech_stack": [
            "Python", "FastAPI", "LangChain", "LlamaIndex", "Pinecone", "pgvector",
            "Weaviate", "Elasticsearch", "OpenAI GPT-4", "BAAI/bge-large-en",
            "SentenceTransformers", "Langfuse", "Prometheus", "Grafana", "Docker",
            "Kubernetes", "GitHub Actions"
        ],
        "bullets": [
            "Built a hybrid RAG pipeline combining BM25 and dense vector retrieval with cross-encoder reranking, improving answer relevance by 37%.",
            "Developed automated LLM-as-judge evaluation pipelines using golden datasets, reducing hallucination rates by 34%.",
            "Designed scalable ingestion pipelines processing 500k+ semantic chunks with metadata-aware indexing.",
            "Implemented observability dashboards tracking retrieval precision, latency, token usage, and API costs, cutting mean time to detect retrieval regressions by 45%."
        ],
        "description": "Built a production-ready Retrieval-Augmented Generation (RAG) system with hybrid semantic and lexical retrieval."
    },
    {
        "id": 2,
        "name": "Project 2 - Autonomous Multi-Agent Research and Task Execution Platform",
        "title": "Autonomous Multi-Agent Research and Task Execution Platform",
        "target_roles": ["AI Agent Engineer", "Applied AI Engineer", "LLM Engineer", "AI Platform Engineer"],
        "tech_stack": [
            "Python", "FastAPI", "LangGraph", "CrewAI", "AutoGen", "PostgreSQL",
            "Redis", "OpenAI GPT-4", "Claude", "Gemini", "Docker", "Kubernetes",
            "LangSmith", "OpenTelemetry", "Prometheus"
        ],
        "bullets": [
            "Engineered a multi-agent orchestration framework enabling autonomous execution of complex research workflows, reducing end-to-end task completion time by 52% through parallel task decomposition.",
            "Implemented structured tool-calling interfaces using JSON schemas and dynamic routing, improving successful tool-call completion rates from 71% to 94%.",
            "Designed execution guardrails including retry policies, timeout controls, and step limits, reducing runaway tool loops by 90%.",
            "Built observability pipelines tracking token consumption, tool usage, latency, and execution traces, surfacing 95% of agent failures within 2 minutes of occurrence."
        ],
        "description": "Built an autonomous AI agent framework capable of executing complex workflows via tool calling, planning, and multi-agent systems."
    },
    {
        "id": 3,
        "name": "Project 3 - Prompt Management Registry & A-B Testing Platform",
        "title": "Centralized Prompt Registry and AI Experimentation Platform",
        "target_roles": ["AI Platform Engineer", "Backend AI Engineer", "Applied AI Engineer", "AI Infrastructure Engineer"],
        "tech_stack": [
            "Python", "FastAPI", "Pydantic", "Jinja2", "React", "Next.js",
            "PostgreSQL", "Redis", "OpenAI", "Gemini", "Claude", "Docker", "Kubernetes"
        ],
        "bullets": [
            "Developed a centralized prompt registry microservice supporting versioning, rollback, and dynamic rendering across 40+ production AI applications.",
            "Implemented real-time A/B experimentation infrastructure enabling safe rollout comparisons between OpenAI and Gemini models, improving winning-variant selection speed by 3x.",
            "Built observability dashboards tracking latency, token throughput, request cost, and generation quality, reducing mean time to detect anomalies by 40%.",
            "Designed dynamic traffic routing and canary deployment systems for production prompt experimentation, enabling zero-downtime rollouts across 12 prompt families."
        ],
        "description": "Built an internal AI experimentation and prompt versioning platform that supports dynamic model routing and A/B testing."
    },
    {
        "id": 4,
        "name": "Project 4 - End-to-End AI Infrastructure Deployment Platform",
        "title": "Scalable LLM Infrastructure and MLOps Deployment Platform",
        "target_roles": ["MLOps Engineer", "AI Infrastructure Engineer", "Platform Engineer", "DevOps Engineer"],
        "tech_stack": [
            "Docker", "Kubernetes", "Helm", "Terraform", "vLLM", "Ollama",
            "Hugging Face TGI", "GitHub Actions", "Prometheus", "Grafana", "AWS", "GCP"
        ],
        "bullets": [
            "Containerized and orchestrated open-source LLM inference services using Docker and Kubernetes with GPU autoscaling, supporting 10x traffic spikes without manual intervention.",
            "Implemented Infrastructure-as-Code using Terraform and automated deployments through GitHub Actions CI/CD pipelines, reducing environment provisioning time from 4 hours to 25 minutes.",
            "Integrated Prometheus and Grafana monitoring, achieving 99.9% uptime across production AI inference workloads.",
            "Optimized large-model inference pipelines using quantization and distributed serving strategies, increasing throughput by 2.4x while holding p95 latency under 800ms."
        ],
        "description": "Built an MLOps platform for deploying, scaling, and monitoring open-source LLMs using GPU orchestration and Kubernetes."
    },
    {
        "id": 5,
        "name": "Project 5 - Real-Time Fraud Detection Engine",
        "title": "Low-Latency Real-Time Fraud Detection System Using Classical Machine Learning",
        "target_roles": ["ML Engineer", "Applied ML Engineer", "Data Scientist", "Backend ML Engineer"],
        "tech_stack": [
            "Python", "Pandas", "NumPy", "Scikit-learn", "XGBoost", "LightGBM",
            "FastAPI", "Kafka", "Redis", "PostgreSQL", "Prometheus", "Grafana"
        ],
        "bullets": [
            "Trained and optimized an XGBoost-based fraud detection pipeline achieving 0.94 F1-score on highly imbalanced transaction datasets.",
            "Built a real-time inference service with Redis-backed feature caching, maintaining prediction latency below 30ms.",
            "Engineered behavioral anomaly features across 12M+ transaction records, improving fraud recall by 22% without increasing false positives.",
            "Developed monitoring and explainability workflows using SHAP analysis and drift detection, flagging 90% of feature drift incidents before model performance degraded."
        ],
        "description": "Built a low-latency real-time fraud detection engine processing transaction events on streaming infrastructure."
    },
    {
        "id": 6,
        "name": "Project 6 - Deep Learning Recommendation System",
        "title": "Two-Stage Deep Learning Recommendation and Semantic Retrieval System",
        "target_roles": ["Deep Learning Engineer", "ML Engineer", "Recommendation Systems Engineer", "Applied Scientist"],
        "tech_stack": [
            "PyTorch", "Transformers", "SentenceTransformers", "FAISS", "pgvector",
            "FastAPI", "PostgreSQL", "ONNX Runtime", "Quantization"
        ],
        "bullets": [
            "Built a two-stage recommendation architecture using PyTorch embeddings and FAISS retrieval, improving CTR by 18%.",
            "Trained dense representation models using contrastive learning on 8M+ interaction pairs, improving recall@10 by 24% for semantic retrieval.",
            "Optimized vector search pipelines using ONNX Runtime and ANN indexing, reducing retrieval latency below 15ms.",
            "Developed scalable embedding infrastructure supporting real-time personalized recommendations for 2M+ daily active users with sub-50ms end-to-end latency."
        ],
        "description": "Built a two-stage deep learning recommendation and semantic search system utilizing embeddings and vector indexes."
    },
    {
        "id": 7,
        "name": "Project 7 - Full-Stack Job Market Analytics Dashboard",
        "title": "Full-Stack Job Market Analytics Dashboard",
        "target_roles": ["Full Stack Engineer", "Backend Engineer", "Software Engineer"],
        "suitable_identities": ["backend_engineer", "frontend_engineer", "fullstack_engineer"],
        "tech_stack": [
            "React", "Next.js", "PostgreSQL", "Redis", "FastAPI", "Python", "Docker", "AWS"
        ],
        "bullets": [
            "Built a full-stack dashboard aggregating salary and remote job data from multiple public APIs, enabling engineers to filter by role, location, tech stack, and compensation.",
            "Designed a PostgreSQL schema for multi-column filtering across 50K+ records; implemented Redis caching to reduce average query latency from 800ms to under 80ms.",
            "Developed a FastAPI backend with scheduled ETL jobs to ingest and normalize disparate sources, paired with a Next.js frontend using server-side rendering for fast initial load.",
            "Containerized services with Docker and deployed on AWS with CI/CD; documented architecture and data model for maintainability.",
        ],
        "description": "Full-stack analytics web application with REST APIs, relational data modeling, caching, and cloud deployment.",
    },
    {
        "id": 8,
        "name": "Project 8 - Event-Driven News Aggregation API",
        "title": "Event-Driven Content Aggregation and Notification API",
        "target_roles": ["Backend Engineer", "Full Stack Engineer", "Software Engineer"],
        "suitable_identities": ["backend_engineer", "fullstack_engineer", "devops_engineer"],
        "tech_stack": [
            "Python", "FastAPI", "Kafka", "Redis", "React", "Docker", "AWS"
        ],
        "bullets": [
            "Built a scheduled ingestion service that aggregates industry news sources, normalizes articles, and exposes summaries through REST APIs and webhook delivery.",
            "Designed an async pipeline with Kafka for task queuing and Redis for deduplication and caching, ensuring each article is processed exactly once under rate limits.",
            "Implemented a FastAPI backend for configuring sources, topics, and schedules; delivered a React dashboard for digest history and operational visibility.",
            "Containerized with Docker and deployed on AWS; documented API contracts, error handling, and deployment runbooks.",
        ],
        "description": "Backend-focused event-driven pipeline with REST configuration APIs and a lightweight admin UI.",
    },
    {
        "id": 9,
        "name": "Project 9 - Secure Customer Onboarding REST API Platform",
        "title": "Secure Customer Onboarding and Authentication API Platform",
        "target_roles": ["Backend Engineer", "Software Engineer", "Java Developer"],
        "suitable_identities": ["backend_engineer", "fullstack_engineer"],
        "tech_stack": [
            "Java", "Spring Boot", "PostgreSQL", "Redis", "JUnit", "REST APIs", "Docker"
        ],
        "bullets": [
            "Developed Java/Spring Boot REST APIs for registration, validation, and authentication workflows supporting high-volume onboarding traffic with clean request/response contracts.",
            "Implemented business rules and input-validation services using OOP service abstractions and exception-handling patterns, reducing downstream processing errors by 18%.",
            "Leveraged Redis for session and token caching on authentication endpoints, improving p95 response times by 30% and lowering database load on hot read paths.",
            "Built JUnit test coverage on critical auth paths and standardized API error handling for reliable integration with web clients.",
        ],
        "description": "Production-style Java backend APIs with SQL persistence, caching, validation, and automated testing.",
    },
    {
        "id": 10,
        "name": "Project 10 - Java Issue Tracking and Team Workflow Management",
        "title": "Java Issue Tracking and Team Workflow Management Application",
        "target_roles": ["Java Developer", "Software Developer", "Backend Engineer", "Application Engineer"],
        "suitable_identities": ["backend_engineer", "fullstack_engineer"],
        "tech_stack": [
            "Java", "Spring Boot", "Spring MVC", "JSP/Servlets", "PostgreSQL", "JUnit", "Git"
        ],
        "bullets": [
            "Built a full-stack Java issue tracking application using Spring Boot, Spring MVC, JSP/Servlets, and PostgreSQL, supporting multi-role access control, issue lifecycle management, and audit history across teams.",
            "Designed normalized PostgreSQL tables for users, projects, issues, comments, and audit logs, enabling search, filtering, pagination, and reliable workflow state transitions.",
            "Implemented service-layer business rules, session-based authentication, and reusable validation flows with OOP abstractions, reducing duplicate controller logic across issue creation and assignment paths.",
            "Achieved 80%+ service-layer test coverage with JUnit and controller integration tests, validating CRUD flows, role-scoped access, and error handling across core application workflows.",
        ],
        "description": "Enterprise-style Java web application with Spring MVC, JSP/Servlets, PostgreSQL persistence, workflow state management, Git-based development, and JUnit testing.",
    },
]

# Role-specific reframing for AI-leaning templates when shown to backend/fullstack recruiters
_PROJECT_2_FRAMING = {
    "ai_platform_engineer": {
        "title": "Autonomous Multi-Agent Research and Task Execution Platform",
        "tech_stack": [
            "Python", "FastAPI", "LangGraph", "PostgreSQL", "Redis", "Docker", "Kubernetes",
            "OpenTelemetry", "Prometheus",
        ],
        "bullets": [
            "Engineered a multi-agent orchestration framework enabling autonomous execution of complex research workflows, reducing end-to-end task completion time by 52% through parallel task decomposition.",
            "Implemented structured tool-calling interfaces using JSON schemas and dynamic routing, improving successful tool-call completion rates from 71% to 94%.",
            "Designed execution guardrails including retry policies, timeout controls, and step limits, reducing runaway tool loops by 90%.",
            "Built observability pipelines tracking token consumption, tool usage, latency, and execution traces, surfacing 95% of agent failures within 2 minutes of occurrence.",
        ],
    },
    "backend_engineer": {
        "title": "Distributed Backend Workflow Execution Platform",
        "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "REST APIs"],
        "bullets": [
            "Engineered a distributed workflow execution service with parallel job decomposition, reducing end-to-end processing time by 52% for research automation workloads.",
            "Implemented schema-validated REST interfaces and dynamic routing between worker services, improving successful request completion rates from 71% to 94%.",
            "Designed reliability guardrails with retry policies, timeouts, and step limits, reducing runaway processing loops by 90% in production.",
            "Built monitoring for queue depth, API latency, and error rates, surfacing 95% of failures within 2 minutes for on-call response.",
        ],
    },
    "fullstack_engineer": {
        "title": "Research Collaboration Web Platform",
        "tech_stack": ["React", "TypeScript", "FastAPI", "PostgreSQL", "Redis", "Docker"],
        "bullets": [
            "Delivered a web platform for research task coordination with React/TypeScript UI and FastAPI backend services, cutting end-to-end workflow time by 52%.",
            "Built REST APIs with validated contracts and role-aware routing between UI and backend workers, improving successful operations from 71% to 94%.",
            "Added reliability controls (retries, timeouts, step limits) that reduced stuck workflows by 90% during peak classroom usage.",
            "Integrated operational dashboards for latency and error trends, enabling instructors to monitor 60+ concurrent users with sub-2s page interactions.",
        ],
    },
}

_PROJECT_3_FRAMING = {
    "ai_platform_engineer": {
        "title": "Centralized Prompt Registry and AI Experimentation Platform",
        "tech_stack": [
            "Python", "FastAPI", "React", "Next.js", "PostgreSQL", "Redis", "Docker", "Kubernetes"
        ],
        "bullets": PROJECTS[2]["bullets"] if len(PROJECTS) > 2 else [],
    },
    "backend_engineer": {
        "title": "Configuration and Release Management API for Application Settings",
        "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "REST APIs"],
        "bullets": [
            "Developed a centralized configuration microservice supporting versioning, rollback, and dynamic rendering across 40+ production applications.",
            "Implemented safe rollout comparisons and feature-flag style experiments, improving release validation speed by 3x without downtime.",
            "Built observability dashboards tracking API latency, throughput, and error rates, reducing mean time to detect anomalies by 40%.",
            "Designed canary routing for production releases, enabling zero-downtime updates across 12 configuration families.",
        ],
    },
    "fullstack_engineer": {
        "title": "Internal Admin Portal for Feature Configuration and Rollouts",
        "tech_stack": ["React", "Next.js", "FastAPI", "PostgreSQL", "Redis", "Docker"],
        "bullets": [
            "Built an admin portal with React/Next.js and FastAPI for managing versioned application settings across 40+ production apps.",
            "Shipped A/B style rollout tooling for safe comparison of configuration variants, improving release confidence and speed by 3x.",
            "Added dashboards for latency, throughput, and error tracking, cutting anomaly detection time by 40%.",
            "Implemented canary deployment routing for zero-downtime configuration updates across 12 product areas.",
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
    if _p["id"] in (7, 8, 9) and "suitable_identities" not in _p:
        pass  # already set
    if "suitable_identities" not in _p and _p["id"] <= 6:
        _p["suitable_identities"] = ["ai_platform_engineer", "ml_engineer"]
        if _p["id"] in (5,):
            _p["suitable_identities"] = ["ml_engineer", "backend_engineer"]
