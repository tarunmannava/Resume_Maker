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

% Experience / education: stacked lines parse cleanly in PDF-to-text
\\newcommand{\\resumeSubheading}[4]{%
  \\vspace{0pt}\\item
  \\textbf{#1} \\\\
  \\textit{\\small #2} \\\\
  \\small #3 -- #4
  \\vspace{2pt}
}

% Projects: title + tech stack
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
  Tampa, FL \\hspace{0.4em}\\resumeSep\\hspace{0.4em}+1 (656) 203-7074 \\hspace{0.4em}\\resumeSep\\hspace{0.4em}\\href{mailto:mannava.tarun34@gmail.com}{mannava.tarun34@gmail.com} \\hspace{0.4em}\\resumeSep\\hspace{0.4em}\\href{https://linkedin.com/in/tarunmannava}{LinkedIn} \\hspace{0.4em}\\resumeSep\\hspace{0.4em}\\href{https://github.com/tarunmannava}{GitHub}%
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
  \\textit{Software Engineer with 2+ years of experience building scalable Java and Spring Boot backend systems. Experienced in RESTful microservices, concurrent processing, distributed caching, secure authentication, and high-throughput data platforms using PostgreSQL, Redis, AWS, and modern software engineering practices.}
\\end{center}

\\vspace{-10pt}

%---------- SKILLS ----------
\\section{SKILLS}
\\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \\small{\\item{
    \\textbf{Backend:} Java, Spring Boot, Spring MVC, Spring Security, Spring Data JPA, Hibernate, REST APIs, Microservices \\\\[1pt]
    \\textbf{Concurrency:} CompletableFuture, ExecutorService \\\\[1pt]
    \\textbf{Databases:} PostgreSQL, MongoDB, SQL Server, Redis, jOOQ \\\\[1pt]
    \\textbf{Cloud \\& DevOps:} AWS (Cognito, S3), Docker, GitHub Actions, Linux \\\\[1pt]
    \\textbf{Testing:} JUnit, Cucumber \\\\[1pt]
    \\textbf{Frontend:} React, JavaScript, HTML, CSS
  }}
\\end{itemize}

%---------- EXPERIENCE ----------
\\section{EXPERIENCE}
\\resumeSubHeadingListStart

  \\resumeSubheading
    {Cognizant Technology Solutions}{Software Development Engineer}{Feb 2022}{Aug 2024}
  \\resumeItemListStart
    \\resumeItem{Developed \\textbf{Java 11}/\\textbf{Spring Boot} microservices for policy onboarding and validation (persisting client metadata in \\textbf{MongoDB}), contributing to a service on a distributed insurance platform handling 20K+ hourly transactions.}
    \\resumeItem{Enhanced asynchronous validation workflows built with \\textbf{CompletableFuture} and \\textbf{ExecutorService}, improving request latency through parallel task execution.}
    \\resumeItem{Implemented \\textbf{Redis}-backed caching strategies and cache warm-up mechanisms, reducing \\textbf{SQL Server} load and improving p95 API response latency by 30\\% during peak onboarding traffic.}
    \\resumeItem{Optimized complex queries for policy audit reporting using \\textbf{jOOQ} and SQL across \\textbf{PostgreSQL} and \\textbf{SQL Server}, eliminating N+1 query patterns and reducing database round trips.}
    \\resumeItem{Contributed to refactoring duplicate business logic across 8+ microservices into reusable Spring service-layer components with centralized exception handling.}
    \\resumeItem{Implemented \\textbf{Spring Security} OAuth2 integration with \\textbf{AWS Cognito} by adding new authorization features and securing REST endpoints with JWT-based authentication.}
    \\resumeItem{Developed \\textbf{JUnit} and \\textbf{Cucumber} test suites covering business-critical workflows, achieving 70\\% backend code coverage while reducing production regressions.}
  \\resumeItemListEnd

  \\resumeSubheading
    {University of South Florida}{Graduate Researcher, Software Engineer}{Jan 2025}{May 2026}
  \\resumeItemListStart
    \\resumeItem{Delivered a production web platform end to end, translating requirements from faculty and research stakeholders into 13 interactive modules built with \\textbf{React} and \\textbf{TypeScript}, serving 60+ students, instructors, and researchers at USF SHIELD Lab.}
    \\resumeItem{Developed a \\textbf{Python/Flask} REST API for AI assisted learning workflows, integrating \\textbf{Groq} and \\textbf{Gemini} with task based grading rubrics and response caching, supporting 60+ concurrent users with sub 2s response latency.}
    \\resumeItem{Integrated \\textbf{Supabase} (\\textbf{PostgreSQL}) for authentication, enrollment, progress tracking, and quiz persistence, supporting multi role access patterns across student, instructor, and researcher personas.}
    \\resumeItem{Delivered adaptive student exercises and instructor curriculum tools with \\textbf{React} role based routing and \\textbf{Flask} server side validation, covering 13 active learning modules across multiple course semesters.}
    \\resumeItem{Shipped 8+ major module updates on 2 week \\textbf{Agile} iteration cycles using \\textbf{Git} based workflows and code reviews, maintaining zero downtime during live classroom usage.}
  \\resumeItemListEnd

\\resumeSubHeadingListEnd

%---------- PROJECTS ----------
\\section{PROJECTS}
\\resumeSubHeadingListStart

  \\resumeProject{Java Issue Tracking and Team Workflow Management Application}{Java, Spring Boot, Spring Security, PostgreSQL, JUnit}
  \\resumeItemListStart
    \\resumeItem{Built a \\textbf{Java}/\\textbf{Spring Boot} backend exposing REST APIs with \\textbf{PostgreSQL} persistence through Spring Data JPA and Hibernate.}
    \\resumeItem{Designed normalized \\textbf{PostgreSQL} schemas with foreign key constraints and indexes supporting efficient filtering, pagination, and audit logging.}
    \\resumeItem{Designed and implemented a backend state machine to enforce issue-lifecycle transitions with validation rules and role-scoped access controls.}
    \\resumeItem{Achieved over 80\\% backend test coverage using \\textbf{JUnit} unit and integration tests validating CRUD operations, state transitions, and business logic.}
  \\resumeItemListEnd

\\resumeSubHeadingListEnd

%---------- EDUCATION ----------
\\section{EDUCATION}
\\resumeSubHeadingListStart
  \\resumeSubheading
    {University of South Florida, Tampa, United States}{Master of Science, Computer Science}{Aug 2024}{May 2026}
\\resumeSubHeadingListEnd

%---------- CERTIFICATIONS ----------
\\section{CERTIFICATIONS}
\\begin{itemize}[leftmargin=0in, label={}, itemsep=0pt, parsep=0pt, topsep=0pt, partopsep=0pt]
  \\small{\\item{
    \\textbf{AWS Certified Cloud Practitioner} -- Amazon, Nov 2023
  }}
\\end{itemize}

%-------------------------------------------
\\end{document}
`;
