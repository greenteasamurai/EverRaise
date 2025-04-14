# EverRaise

## AI-Powered Business Communication Analytics Platform

EverRaise is an AI-powered platform designed to extract value from business communications (emails, chat, meetings, and documents) to generate automated reports, investor updates, and business insights. The platform saves 95%+ of the time spent manually compiling these reports while maintaining human oversight.

## Features

- **Automated Report Generation**
  - Investor Updates
  - Business Reviews
  - Knowledge Summaries

- **AI-Powered Processing**
  - RAG-Based LLM Pipeline
  - Dynamic Model Selection
  - Human-in-the-Loop Review

- **Integrations**
  - Communication Platforms (Gmail, Outlook, Slack, Teams)
  - Project Management (Jira, Asana, Notion)
  - Cloud Storage (Google Drive, Dropbox)
  - CRM & BI Tools (Salesforce, HubSpot, Tableau)

- **Enterprise-Grade Security**
  - Role-Based Access Control
  - End-to-End Encryption
  - Audit Logging & Compliance

## Project Structure

```
everraise/
├── backend/           # Python FastAPI backend
├── frontend/          # React TypeScript frontend
├── scripts/           # PowerShell scripts for starting and managing the application
├── docs/              # Documentation files
├── Archive/           # Archived files (obsolete or deprecated)
└── infrastructure/    # Docker and cloud deployment configs
```

## Getting Started

### Quick Start

The simplest way to start the application is using the main launcher script:

```powershell
.\run-everraise.ps1
```

This will display a menu with options to:
1. Start EverRaise (Backend and Frontend)
2. Start Backend Only
3. Start Frontend Only
4. Fix Common Issues
5. Run Tests

### Manual Setup

#### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Using Docker Compose

```bash
docker-compose up -d
```

## Documentation

Detailed documentation can be found in the `docs` directory:

- [Getting Started Guide](docs/START_HERE.md)
- [Running the Application](docs/RUNNING.md)
- [Testing Guide](docs/TESTING.md)

## Troubleshooting

If you encounter issues with the application:

1. Use the menu option "Fix Common Issues" in the main launcher
2. Check port conflicts (especially port 8000)
3. Review the database status
4. Check detailed logs in the backend/logs directory

## Security and Compliance

EverRaise is designed with security in mind:
- TLS 1.3 for in-transit encryption
- AES-256 for data at rest
- PII redaction before LLM processing
- RBAC for access control
- Audit logging for compliance

## License

Copyright © 2023 EverRaise. All rights reserved. 