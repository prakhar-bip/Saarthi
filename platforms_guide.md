# 📊 Sarthi - Observability & Monitoring Platforms Integration Guide

This guide contains configurations, setup instructions, and code templates to integrate Sarthi (FastAPI Backend + Next.js Frontend) with leading observability platforms.

---

## 1. New Relic (APM, Browser & Log Observability)
New Relic tracks agent bottlenecks, API latency, MongoDB slow queries, and frontend crashes.

### A. Backend Integration (FastAPI)

1. **Add Dependency:**
   Add `newrelic` to your `backend/requirements.txt`:
   ```text
   newrelic>=9.0.0
   ```

2. **Create Configuration File (`backend/newrelic.ini`):**
   Create a file named `newrelic.ini` in the `backend/` directory:
   ```ini
   [newrelic]
   license_key = YOUR_NEW_RELIC_LICENSE_KEY
   app_name = Sarthi-Backend-Prod
   monitor_mode = true
   log_file = stdout
   log_level = info
   ssl = true
   transaction_tracer.enabled = true
   transaction_tracer.transaction_threshold = apdex_f
   error_collector.enabled = true
   thread_profiler.enabled = true
   ```

3. **Initialize in Backend Startup (`backend/app/main.py`):**
   Place this snippet at the absolute top of `main.py` before any other imports:
   ```python
   import os
   import newrelic.agent

   # Load newrelic if config file exists
   if os.path.exists("newrelic.ini"):
       newrelic.agent.initialize("newrelic.ini")
       print("⚡ New Relic Agent Initialized successfully.")
   ```

4. **Environment Variables (Cloud Run / Local):**
   Add these to your environment configuration (`backend/env.yaml` or `.env`):
   ```bash
   NEW_RELIC_LICENSE_KEY=your_actual_license_key
   NEW_RELIC_APP_NAME="Sarthi-Backend"
   NEW_RELIC_LOG=stdout
   ```

---

### B. Frontend Integration (Next.js)

1. **Browser Snippet Setup (`frontend/src/app/layout.tsx`):**
   Copy the JavaScript snippet from your New Relic Browser Application dashboard and insert it using the Next.js `Script` component inside the root layout:

   ```tsx
   import Script from "next/script";

   export default function RootLayout({ children }) {
     return (
       <html lang="en">
         <head>
           {/* New Relic Browser Monitoring Agent */}
           <Script id="new-relic-browser" strategy="beforeInteractive">
             {`
               window.NREUM||(NREUM={});NREUM.info={beacon:"bam.nr-data.net",errorBeacon:"bam.nr-data.net",licenseKey:"YOUR_NR_BROWSER_KEY",applicationID:"YOUR_APP_ID",sa:1};
               // ... Paste the rest of the official New Relic JS Snippet here ...
             `}
           </Script>
         </head>
         <body>{children}</body>
       </html>
     );
   }
   ```

---

## 2. Alternate Platforms (For Future Use)

### A. Sentry (Error & Exception Tracking)
Excellent for capturing raw Python and React stack-traces.

* **Backend FastAPI Setup:**
  ```python
  import sentry_sdk
  from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

  sentry_sdk.init(
      dsn="YOUR_SENTRY_DSN",
      traces_sample_rate=1.0,
      profiles_sample_rate=1.0,
  )
  # FastAPI app initialized...
  # app = FastAPI()
  # app.add_middleware(SentryAsgiMiddleware)
  ```

* **Frontend Next.js Setup:**
  Install `@sentry/nextjs` and run:
  ```bash
  npx @sentry/wizard@latest -i nextjs
  ```

### B. Datadog (Infrastructure & APM Logs)
Best for containerized workloads and host-level metric aggregations.

* **Backend FastAPI Setup:**
  ```python
  from ddtrace import patch_all; patch_all() # Patches FastAPI, Motor, Redis
  ```
  Run using datadog wrapper:
  ```bash
  ddtrace-run uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```

---

## 3. Requestly (HTTP Interception, Redirects & API Mocking)
Requestly allows intercepting, modifying, and mocking HTTP requests/responses for local debugging and simulation.

### A. Key Sarthi Use Cases & Rules Setup

#### 1. Redirect Production Backend API to Localhost (Redirect Rule)
If you want to debug the Next.js UI hosted on Cloud Run (`https://sarthi-gtu3eysx6q-uc.a.run.app`) against your *local backend code* (`http://localhost:8000`), set up a **Redirect Rule** in the Requestly extension:
* **Rule Type:** Redirect Request
* **Source Trigger (If Request):** `URL Matches Regex` -> `https://sarthi-backend-gtu3eysx6q-uc.a.run.app/api/(.*)`
* **Destination (Redirect To):** `http://localhost:8000/api/$1`

*This forces the production browser client to send API calls to your local Uvicorn process.*

#### 2. Mocking Backend Responses (Mock Rule)
To test specific frontend UI behaviors (e.g., compile errors or custom lists) offline or without calling LLMs:
* **Rule Type:** Mock Response
* **Method:** `GET`
* **URL:** `Matches Regex` -> `.*/api/projects/suggestions.*`
* **Response Body (JSON):**
  ```json
  [
    {
      "name": "Custom Mocked SaaS App",
      "idea": "An app intercepted and served via Requestly for testing UI loading state.",
      "features": ["Feature A", "Feature B"],
      "tech_stack": "Next.js, FastAPI, MongoDB"
    }
  ]
  ```

#### 3. Simulating Network Latency / Delay (Delay Rule)
To test if Sarthi's progress spinner and WebSockets handle long generation delays gracefully without timeout:
* **Rule Type:** Delay Network Requests
* **URL:** `Matches Regex` -> `.*/api/projects/.*/compile`
* **Delay Value:** `15000` (15 seconds delay)

