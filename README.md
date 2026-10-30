# 🚀 AdaptiveClass AI — Adaptive Learning for College Classrooms

> **Core Philosophy**: *AI augments the teacher; it does not replace the teacher.*

AdaptiveClass AI is an AI-powered adaptive learning platform designed for college engineering classrooms (50–100+ students). It analyzes student performance at both individual and classroom levels, isolates acute concept gaps, equips professors with actionable instructional interventions, and provides students with dynamically personalized adaptive practice.

---

## 🌟 The Problem We Solve

In typical university engineering courses (e.g. 80 students in Data Structures), a professor receives an opaque class average like **64%**.

That single aggregate score cannot answer:
- *Which specific concepts are difficult for the majority of students?*
- *Which students are falling behind in recursion specifically?*
- *Who has mastered the curriculum and is ready for advanced algorithms?*
- *What targeted revision should the teacher conduct before next week's exam?*

### The AdaptiveClass AI Difference:
Instead of "Class Average: 64%", AdaptiveClass AI shows:
- **Arrays**: 82.0% ✓ (Strong)
- **Linked Lists**: 64.0% (Moderate)
- **Trees**: 41.0% ⚠ (Needs Attention)
- **Recursion**: 35.0% 🔴 (**Critical Gap** — 23 students below the 40% support threshold)
- **Graphs**: 58.0% (Needs Attention)
- **Sorting**: 75.0% ✓ (Proficient)

And gives the professor immediate, data-grounded recommendations:
> *"Recursion is currently the largest classroom learning gap at 35.0% class mastery. 23 students scored below the academic support threshold. Suggested action: Conduct a targeted recursion revision session covering base cases and stack behavior before introducing tree traversals."*

---

## ⚡ The "Wow" Demo (The Closed Feedback Loop)

1. **Step 1 (Teacher View)**:
   - Login as **Prof. Vikram Sen** (`teacher@demo.com`).
   - Observe **Recursion at 35.0%** flagged with a **Critical Gap** alert.
   - See **23 students** needing support in the prominent **AI Classroom Insight** card.
   - Inspect **Aarav Sharma** in the *Students Needing Attention* table with **28% mastery** and a declining quiz trend (72% ➔ 64% ➔ 48%).

2. **Step 2 (Student View)**:
   - 1-click switch to **Aarav Sharma** (`student@demo.com`).
   - View personalized dashboard: **Recursion (28%)** flagged under *Needs Practice*.
   - See targeted practice recommendation: *"Recursion Fundamentals & Stack Tracing — ~15 min"*.

3. **Step 3 (Adaptive Practice)**:
   - Click **Start Adaptive Practice**.
   - Question 1 begins at **Beginner** difficulty (Base case purpose).
   - Answering correctly dynamically escalates the next question to **Intermediate**!
   - Answering incorrectly reinforces with supportive foundational problems.

4. **Step 4 (Dynamic Recalculation & Loop Closure)**:
   - Submit practice with 80% accuracy.
   - Aarav's new mastery is calculated dynamically from PostgreSQL:
     $$\text{New Mastery} = \text{round}(28.0 \times 0.35 + 80.0 \times 0.65) = 61.8\% \quad (+33.8\% \text{ gain})$$
   - Click **"View Updated Teacher Dashboard"**.
   - Teacher Dashboard re-queries PostgreSQL live:
     - **Class Recursion Average**: rose from **35.0% to 35.4%**!
     - **Students Needing Support**: dropped from **23 to 22**!

5. **Step 5 (Reset Demo Anytime)**:
   - Click **"Reset Demo"** in the top navigation bar to restore all 80 students, initial attempts, and baseline metrics instantly.

---

## 🛠️ Tech Stack & Architecture

- **Frontend**: React 19, Vite, TypeScript, Tailwind CSS, Lucide Icons
- **Backend**: FastAPI (Python 3.13), Pydantic v2, SQLAlchemy 2.0
- **Database**: PostgreSQL 17 (`psycopg[binary]`)
- **AI & Analytics**:
  - **Gemini 2.5 Flash**: Natural language instructional summaries (optional with `GEMINI_API_KEY`)
  - **Autonomous Rule-Based Fallback Engine**: Deterministic analytics engine operating with zero latency and 100% reliability offline or without API keys.

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL 17

### 1. Database Setup
A dedicated PostgreSQL cluster script is provided in `scripts/`:
```cmd
# Initialize and start dedicated PostgreSQL instance on port 5433
d:\Zinnovatio 4.0\scripts\setup_pg.bat
d:\Zinnovatio 4.0\scripts\start_pg.bat
```
*(Or use any existing PostgreSQL instance and set `DATABASE_URL` in `backend/.env`)*

### 2. Backend Setup
```powershell
cd "d:\Zinnovatio 4.0\backend"

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies (already installed in .venv)
pip install -r requirements.txt

# Run automated tests verifying PostgreSQL seed calibration & APIs
python -m pytest -v tests/

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at `http://127.0.0.1:8000/docs`.

### Staff login and dataset analysis API

`GET /api/auth/captcha` creates a five-minute, single-use arithmetic captcha. New
staff clients submit its `captcha_id` and answer with `login_id`, `password`, and
receive a JWT from `POST /api/auth/login`. The seeded mentor account is
`mentor@demo.com` / `password`; the existing teacher demo account remains
`teacher@demo.com` / `password`.

Staff clients send the JWT as `Authorization: Bearer <token>`. Teachers and
mentors upload datasets only; there is no marks-entry workflow. Supported formats
are `.xlsx`, `.xlsm`, `.csv`, and `.json`. Each row must contain:

```text
roll_number, name, subject, class, marks, max_marks, topic, assessment, date
```

Dataset endpoints:

- `POST /api/datasets/upload` validates and stores a dataset.
- `GET /api/datasets` lists datasets owned by the current teacher or all datasets
  for a mentor.
- `GET /api/datasets/{dataset_id}/rows` returns normalized rows.
- `POST /api/datasets/{dataset_id}/analysis` generates teacher dashboard analysis
  using Gemini when `GEMINI_API_KEY` is configured, with a deterministic fallback
  for local development.
- `GET /api/datasets/{dataset_id}/analysis` returns saved analyses.

The analysis includes class/subject summaries, topic gaps, at-risk students,
performance trends, and recommendations. Direct `/api/marks` endpoints are not
registered in the new workflow.

Student AI endpoints require a student JWT:

- `POST /api/student-ai/chat`
- `POST /api/student-ai/quiz`
- `POST /api/student-ai/learning-plan`
- `GET /api/student-ai/resources?topic=...&difficulty=...`
- `POST /api/student-ai/attempts` records quiz score and question-level results.
- `GET /api/student-ai/report` lets a student view their activity report.
- `GET /api/student-ai/reports/{student_id}` lets an authorized teacher or mentor
  view the student's AI activity report.

These endpoints use the student's roll number to connect uploaded performance
rows to AI-generated learning interactions. Every AI request stores the student's
message, topic, difficulty, AI response, model, and timestamp. Quiz attempts are
stored separately with scores and result details. The report analyzes the stored
conversation and attempts and includes topics discussed, quiz performance,
learning signals, and suggested teacher actions.

### 3. Frontend Setup
```cmd
cd "d:\Zinnovatio 4.0\frontend"
npm install
npm run dev -- --port 5173
```
Open `http://localhost:5173` in your browser.

---

## 🔑 Demo Accounts

Quick 1-click switchers are built into the top navigation bar:

| Role | Email | Password | Persona & Key Scenario |
|---|---|---|---|
| **Teacher** | `teacher@demo.com` | `password` | **Prof. Vikram Sen**: Oversees 80 students, views concept gaps, and assigns revisions |
| **Student** | `student@demo.com` | `password` | **Aarav Sharma**: Needs attention in Recursion (starts at 28.0%, takes adaptive quiz) |
| **Advanced** | `advanced@demo.com` | `password` | **Priya Patel**: High performer (92.0% overall), receives enrichment challenges |

---

## 🛡️ Teacher Agency Principle

Every AI-generated insight strictly includes the standard disclaimer:
> *"AI-generated insights are recommendations. Teachers remain in control of instructional decisions."*

The system never dictates high-stakes academic judgments or labels students negatively; it highlights academic support needs grounded in measured concept data.
