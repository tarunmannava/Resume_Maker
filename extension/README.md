# HiringCafe Capture Extension for Resume Maker

This lightweight Chrome Extension (Manifest V3) captures job listings and descriptions from your active HiringCafe search tab and securely sends them to your local Resume Maker SQLite database (`backend/storage/jobs.db`).

---

## 🚀 Setup Instructions (1 Minute)

1. Open Google Chrome.
2. In the URL bar, go to:
   ```text
   chrome://extensions
   ```
3. Enable **Developer mode** toggle in the top right corner.
4. Click the **Load unpacked** button in the top left.
5. Select the folder:
   ```text
   D:\Projects\Resume Maker\extension
   ```
6. The extension **"HiringCafe Job Queue Capture"** is now installed! Pin it to your Chrome toolbar for quick access.

---

## 🎯 How to Use

1. **Start Resume Maker**:
   - Make sure your FastAPI backend is running on `http://localhost:8000`:
     ```powershell
     cd "D:\Projects\Resume Maker\backend"
     uvicorn app.main:app --reload --port 8000
     ```
   - Start your frontend:
     ```powershell
     cd "D:\Projects\Resume Maker\frontend"
     npm run dev
     ```

2. **Open HiringCafe**:
   - Go to `https://hiringcafe.com/` and log in.
   - Run your desired job search (e.g. "Software Engineer", remote, YOE filters, etc.).

3. **Capture Jobs**:
   - Click the **HiringCafe Job Queue Capture** extension icon in your Chrome toolbar.
   - Click **"Capture This Page"**.
   - The extension will:
     - Read the jobs directly from the tab's page data.
     - Check your backend for existing jobs to avoid duplicate fetching.
     - Fetch the job descriptions sequentially with human-like delays (2–4s) to avoid rate limits.
     - Send the full job batch to your Resume Maker backend.

4. **Review & Apply in Resume Maker**:
   - Switch to the Resume Maker web UI (`http://localhost:5173`).
   - Click the **"🎯 Job Radar & Queue"** tab.
   - The background worker will automatically:
     - **Screen** each role against your USF CS MS background and tech stack (Python, Java, .NET, Node, AI/ML).
     - **Rewrite** matching jobs with tailored LaTeX and compile an authentic DOCX resume.
     - **Flag** ineligible jobs (e.g., C++/embedded/hardware, US Citizen security clearance required, staff/principal roles).
   - Click **Download DOCX** to get your tailored resume, click **Apply Link →** to submit, or click **Studio →** to edit further in the manual studio!
