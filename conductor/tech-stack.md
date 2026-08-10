# Technology Stack: Resume Maker

## Core Stack
- **Backend Framework**: Python 3.10+ with FastAPI, Uvicorn, Pydantic v2
- **Frontend Framework**: React 18, Vite, TypeScript, Tailwind CSS, Lucide React
- **AI / LLM Integration**:
  - Google Gemini API (`google-genai`)
  - OpenAI API (`openai`) / OpenRouter API
  - Embeddings: `text-embedding-3-small` (with lexical tf-idf/word-overlap fallback)
- **Document Processing**:
  - LaTeX compilation via local `pdflatex` / `xelatex` CLI
  - Regex-based LaTeX parser, sanitizer, & brace balancing
  - `python-docx` for Word document handling

## Testing & Quality Control
- **Backend Testing**: `pytest`
- **Build Tools**: Node.js / `npm` for frontend, `pip` for backend
