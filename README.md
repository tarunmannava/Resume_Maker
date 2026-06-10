# Resume Rewriter

An ATS-focused LaTeX resume rewriting app with a FastAPI backend and React frontend.

## MVP Features

- Analyze job descriptions for technical keywords.
- Extract readable text from LaTeX resumes.
- Score resume/job keyword alignment.
- Classify exact, transferable, missing, and unsupported keywords.
- Guard against high-risk substitutions such as C/C++ when the resume only supports Python/Java.
- Rewrite LaTeX resumes with Gemini or OpenAI when an API key is configured.
- Paste a job description and LaTeX resume in the frontend.
- View rewritten LaTeX, match score, missing keywords, and high-risk substitutions.
- Compile rewritten LaTeX locally into PDF files using MiKTeX/latexmk.

## Backend Setup

1. Create a virtual environment.
2. Install dependencies:

   `pip install -r backend/requirements.txt`

3. Copy environment template:

   `copy backend\.env.example backend\.env`

4. Add your Gemini or OpenAI API key to `backend/.env` if you want AI rewriting.

5. Run the API from the project root:

   `python -m uvicorn backend.app.main:app --reload`

6. Open API docs:

   `http://localhost:8000/docs`

## Frontend Setup

1. Install frontend dependencies:

   `npm install --prefix frontend`

2. Start the frontend dev server:

   `npm run dev --prefix frontend`

3. Open the frontend:

   `http://localhost:5173`

The frontend calls the backend at `http://localhost:8000` by default. You can override this by copying `frontend/.env.example` to `frontend/.env` and changing `VITE_API_BASE_URL`.

## Local PDF Generation

The app compiles LaTeX locally using MiKTeX/latexmk. Generated files are stored under:

`backend/storage/generated/Name_Company_Role/`

Filenames use this format with no timestamp:

`Name_Company_Role.pdf`

Generating again for the same name/company/role overwrites the previous local files.

## API Endpoints

- `GET /api/health`
- `POST /api/analyze-job`
- `POST /api/analyze-resume`
- `POST /api/score`
- `POST /api/compile`
- `GET /api/files/{folder}/{filename}`
- `POST /api/rewrite`
- `POST /api/rewrite-and-compile`

## Rewrite Modes

- `strict`: only use directly supported skills.
- `transferable`: use target job language through defensible transferable concepts.
- `user_verified`: use confirmed skills more directly.
- `aggressive`: maximize ATS alignment, while still treating high-risk substitutions carefully.

## Substitution Guardrail

The system treats `C`, `C++`, embedded systems, pointers, memory management, Kubernetes, and Terraform as high-risk direct substitutions. If a job requires C/C++ but the resume only shows Java/Python, the API emphasizes OOP, algorithms, data structures, performance, concurrency, and systems concepts instead of falsely claiming C/C++ experience.
