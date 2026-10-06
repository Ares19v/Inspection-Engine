# Inspection Engine Guidelines

## Fast Startup Instructions
When asked to run or launch this project:
- Do NOT probe environments, run test imports, or do broad port discovery scans.
- The stack is configured with high-range random ports to guarantee zero conflict:
  - **Backend**: Port `38192` (`python -m uvicorn app.main:app --port 38192` inside `backend/`).
  - **Frontend**: Port `38193` (`npm run dev -- --port 38193` inside `frontend/`).
- Start both services immediately in the background or trigger `.\Run_Inspection_Engine.bat`.
