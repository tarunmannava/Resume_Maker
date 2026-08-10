export const sampleResume = `%-------------------------
% Tarun Mannava - Resume in LaTeX
%-------------------------

\\documentclass[a4paper,10pt]{article}

\\usepackage[T1]{fontenc}
\\usepackage[utf8]{inputenc}
\\usepackage{latexsym}
\\usepackage[empty]{fullpage}
\\usepackage{titlesec}
\\usepackage{marvosym}
\\usepackage[usenames,dvipsnames]{color}
\\usepackage{verbatim}
\\usepackage{enumitem}
\\usepackage[hidelinks]{hyperref}
\\usepackage{fancyhdr}
\\usepackage[english]{babel}
\\usepackage{tabularx}
\\usepackage{mathptmx}
\\usepackage{geometry}
\\usepackage{setspace}

% Standardized thin margins to maximize space safely
\\geometry{
  a4paper,
  top=0.35in,
  bottom=0.35in,
  left=0.4in,
  right=0.4in
}

\\setstretch{1.0}

\\pagestyle{fancy}
\\fancyhf{}
\\fancyfoot{}
\\renewcommand{\\headrulewidth}{0pt}
\\renewcommand{\\footrulewidth}{0pt}

\\urlstyle{same}
\\raggedbottom
\\raggedright
\\setlength{\\tabcolsep}{0in}

% Further reduced section gap (pulled up higher, tighter below the rule)
\\titleformat{\\section}{
  \\vspace{-10pt}\\scshape\\raggedright\\large
}{}{0em}{}[\\color{black}\\titlerule \\vspace{-7pt}]

\\newcommand{\\resumeItem}[1]{
  \\item\\small{#1}
}

\\usepackage{anyfontsize}
\\renewcommand{\\normalsize}{\\fontsize{10.5}{12.6}\\selectfont}
\\renewcommand{\\small}{\\fontsize{10.5}{12.6}\\selectfont}
\\normalsize

\\newcommand{\\resumeSep}{\\textbullet}

% Experience / education: stacked lines parse cleanly in PDF to text
\\newcommand{\\resumeSubheading}[4]{%
  \\vspace{0pt}\\item
  \\textbf{#1} \\\\
  \\textit{\\small #2} \\\\
  \\small #3 -- #4
  \\vspace{2pt}
}

% Projects: title + tech stack only (no date range; not relevant for projects)
\\newcommand{\\resumeProject}[2]{%
  \\vspace{0pt}\\item[]
  \\textbf{#1} \\\\
  \\small\\textit{#2}
  \\vspace{2pt}
}

\\newcommand{\\resumeItemListStart}{%
  \\begin{itemize}[leftmargin=0.15in, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt, label={$\\bullet$}]%
}
\\newcommand{\\resumeItemListEnd}{\\end{itemize}\\vspace{2pt}}

\\newcommand{\\resumeHeadingContact}{%
  Tampa, FL \\hspace{0.4em}\\resumeSep\\hspace{0.4em}+1 (656) 203 7074 \\hspace{0.4em}\\resumeSep\\hspace{0.4em}\\href{mailto:mannava.tarun34@gmail.com}{mannava.tarun34@gmail.com} \\hspace{0.4em}\\resumeSep\\hspace{0.4em}\\href{https://linkedin.com/in/tarunmannava}{LinkedIn} \\hspace{0.4em}\\resumeSep\\hspace{0.4em}\\href{https://github.com/tarunmannava}{GitHub}%
}

\\newcommand{\\resumeSubHeadingListStart}{\\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]}
\\newcommand{\\resumeSubHeadingListEnd}{\\end{itemize}}

%-------------------------------------------
\\begin{document}

%---------- HEADING ----------
\\begin{center}
  {\\Huge \\textbf{Tarun Mannava}} \\\\[4pt]
  \\small
  \\resumeHeadingContact \\\\[4pt]
  \\textit{Software Engineer with 2+ years of experience building scalable Java and Spring Boot backend systems. Experienced in RESTful microservices, concurrent processing, distributed caching, secure authentication, and high-throughput data platforms using PostgreSQL, Redis, Docker, and AWS.}
\\end{center}

\\vspace{-10pt}

%---------- EDUCATION ----------
\\section{EDUCATION}
\\resumeSubHeadingListStart
  \\resumeSubheading
    {University of South Florida, Tampa, United States}{Master of Science, Computer Science}{Aug 2024}{May 2026}
\\resumeSubHeadingListEnd

%---------- EXPERIENCE ----------
\\section{EXPERIENCE}
\\resumeSubHeadingListStart

  \\resumeSubheading
    {University of South Florida}{Graduate Researcher, Full Stack AI Platform}{Jan 2025}{May 2026}
  \\resumeItemListStart
    \\resumeItem{Built and deployed an AI powered learning platform with 13 interactive modules, serving 60+ daily active students and instructors at USF SHIELD Lab.}
    \\resumeItem{Developed React and TypeScript frontends for student exercises and instructor tools, supporting adaptive learning workflows.}
    \\resumeItem{Built Node.js backend services integrating LLMs via Groq API, maintaining sub 2s response latency for 60+ concurrent classroom users.}
    \\resumeItem{Designed PostgreSQL schemas and role based access control (RBAC) models for authentication, enrollment, and learning analytics.}
    \\resumeItem{Designed shared TypeScript interfaces and Zod validation schemas, reducing API integration defects by 30\\% and eliminating manual contract synchronization.}
    \\resumeItem{Shipped 8 production releases with zero downtime by implementing backward compatible database migrations and API schemas.}
  \\resumeItemListEnd

  \\resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \\resumeItemListStart
    \\resumeItem{Developed Java 11 Spring Boot microservices exposing REST APIs for policy validation, persisting client metadata in MongoDB and supporting a distributed insurance platform processing 20K+ hourly transactions.}
    \\resumeItem{Enhanced asynchronous validation workflows using CompletableFuture and ExecutorService, improving latency through parallel task execution.}
    \\resumeItem{Implemented Redis backed caching and cache warm up mechanisms, reducing SQL Server load and improving p95 response latency by 30\\% during peak traffic.}
    \\resumeItem{Optimized complex reporting queries using jOOQ and SQL across PostgreSQL and SQL Server, eliminating N+1 patterns and database round trips.}
    \\resumeItem{Refactored duplicate logic across 8+ microservices into reusable Spring service components with centralized exception handling.}
    \\resumeItem{Secured REST endpoints with JWT based authentication using Spring Security OAuth2 and AWS Cognito.}
    \\resumeItem{Developed JUnit and Cucumber test suites covering critical workflows, achieving 70\\% backend code coverage.}
  \\resumeItemListEnd

\\resumeSubHeadingListEnd

%---------- PROJECTS ----------
\\section{PROJECTS}
\\resumeSubHeadingListStart

  \\resumeProject{Scalable LLM Infrastructure for Student Facing AI Tutoring}{Docker, Kubernetes, Terraform, vLLM, Prometheus}
  \\resumeItemListStart
    \\resumeItem{Built a self hosted inference platform for classroom scale AI tutoring (60+ concurrent users), containerizing vLLM on Kubernetes with GPU autoscaling}
    \\resumeItem{Provisioned staging clusters with Terraform and automated deployments via GitHub Actions, reducing setup time from 4 hours to under 30 minutes}
    \\resumeItem{Integrated Prometheus and Grafana alerting on GPU utilization and throughput, resolving bottlenecks to improve p95 latency by 35\\%}
  \\resumeItemListEnd

  \\resumeProject{Centralized Prompt Registry for AI Assisted Learning Modules}{Python, FastAPI, React, PostgreSQL, Redis}
  \\resumeItemListStart
    \\resumeItem{Developed a prompt registry microservice with version history and dynamic rendering for 13+ learning modules}
    \\resumeItem{Implemented A/B testing comparing OpenAI and Gemini variants, accelerating prompt selection cycles by 3x}
    \\resumeItem{Implemented Grafana dashboards tracking latency and token costs, reducing regression detection time by 40\\%}
    \\resumeItem{Designed staged rollouts for zero downtime prompt updates, decoupling prompt changes from application releases}
  \\resumeItemListEnd

\\resumeSubHeadingListEnd

%---------- SKILLS ----------
\\section{SKILLS}
\\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \\small{\\item{
    \\textbf{Languages:} Java, Python, TypeScript, SQL, JavaScript \\\\[1pt]
    \\textbf{Backend:} Java, Spring Boot, Spring MVC, Spring Security, Spring Data JPA, Hibernate, REST APIs, Microservices, Node.js, Express.js, FastAPI \\\\[1pt]
    \\textbf{Concurrency:} CompletableFuture, ExecutorService \\\\[1pt]
    \\textbf{Databases \\& Caching:} PostgreSQL, MongoDB, SQL Server, Redis, jOOQ \\\\[1pt]
    \\textbf{Cloud \\& DevOps:} AWS (Cognito, S3), Kubernetes, Terraform, Docker, Git, GitHub Actions, Jenkins, Linux \\\\[1pt]
    \\textbf{Build Tools:} Maven, Gradle \\\\[1pt]
    \\textbf{AI \\& Observability:} LLM Integration, LangChain, Prometheus, Grafana \\\\[1pt]
    \\textbf{Testing:} JUnit, Cucumber, Jest, Cypress \\\\[1pt]
    \\textbf{Frontend:} React, Next.js, HTML, CSS
  }}
\\end{itemize}

%---------- CERTIFICATIONS ----------
\\section{CERTIFICATIONS}
\\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \\small{\\item{
    \\textbf{AWS Certified Cloud Practitioner} - Amazon, Nov 2023
  }}
\\end{itemize}

%-------------------------------------------
\\end{document}
`;

export const sampleJob = `Required: Python, Django, PostgreSQL, REST APIs, AWS.
Preferred: React or Angular, Docker, CI/CD.
We value backend engineers who can build scalable services and collaborate across teams.`;
