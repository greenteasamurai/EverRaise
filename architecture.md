# Application Architecture Design

This document outlines a proposed architecture for the EverRaise application, focusing on smooth integrations, scalability, ease of iteration, and problem isolation.

## Core Architectural Principles

1.  **Modularity & Separation of Concerns:** Break the application into distinct layers/components (API, Services, Data Access, Integrations, Tasks) with well-defined responsibilities.
2.  **Asynchronous Processing:** Utilize asynchronous operations (FastAPI, Task Queues) for I/O-bound tasks (external APIs, LLMs, DB operations) to enhance responsiveness and throughput.
3.  **Clear Interfaces & Contracts:** Define data structures and API contracts clearly using Pydantic schemas for consistency and predictability.
4.  **Stateless API Layer:** Keep the main API layer stateless for horizontal scaling. State managed via tokens/database sessions passed via dependencies.
5.  **Configuration-Driven:** Externalize configuration (DB URLs, API keys, model names) via environment variables and Pydantic settings (`.env`).

## Proposed Architecture Components

```mermaid
graph LR
    subgraph Frontend
        WebApp[React/TypeScript UI]
    end

    subgraph Backend (FastAPI Application)
        API[API Layer (FastAPI Routers)]
        Auth[Auth Service (JWT/OAuth)]
        Service[Service Layer (Business Logic)]
        DAL[Data Access Layer (CRUD/SQLAlchemy)]
        Integration[Integration Layer]
    end

    subgraph Infrastructure
        DB[(PostgreSQL w/ PGVector)]
        Queue[(Task Queue: RQ)]
        Broker[(Broker: Redis)]
        LLM[External LLM Service]
        ExtAPI1[External API 1 (Gmail)]
        ExtAPI2[External API 2 (Slack...)]
    end

    WebApp --> API
    API --> Auth
    API --> Service

    Service --> DAL
    Service --> Integration
    Service --> Queue

    DAL --> DB

    Integration --> LLM
    Integration --> ExtAPI1
    Integration --> ExtAPI2
    Integration --> DB # For PGVector

    Queue --> Broker
    Worker[RQ Workers] --> Broker
    Worker --> Service # Workers execute business logic via Service layer
    Worker --> Integration # Workers interact with external systems

```

## Component Breakdown

1.  **Frontend (React/TypeScript):**
    *   Handles user interaction, displays data/status.
    *   Communicates with Backend API via REST.
    *   Uses component libraries (e.g., shadcn/ui) and styling (e.g., Tailwind CSS).

2.  **Backend (FastAPI Application):**
    *   **API Layer (Routers):** Defines endpoints, handles request validation (Pydantic), manages request/response flow, calls Service Layer. Uses FastAPI Dependency Injection.
    *   **Auth Service:** Manages user authentication (JWT) and potentially OAuth flows. Verifies permissions.
    *   **Service Layer:** Contains core business logic (report generation orchestration, user management). Calls DAL for data persistence, Integration Layer for external interactions, and enqueues background tasks using RQ.
    *   **Data Access Layer (DAL) / CRUD:** Abstracts database interactions (CRUD operations) using SQLAlchemy against PostgreSQL. Includes logic for interacting with PGVector if applicable within data models or specific DAL functions.
    *   **Integration Layer:** Modules for interacting with external services:
        *   *LLM Service:* Abstracts calls to LLM APIs.
        *   *Data Source Connectors (Gmail, etc.):* Fetch data from external APIs.
        *   *Embedding Service:* Handles embedding generation (potentially calling an external model API or using a local library) before data is stored/queried via PGVector in the DAL.

3.  **Infrastructure:**
    *   **PostgreSQL Database:** Stores relational data (users, organizations, report metadata, etc.) and vector embeddings using the **PGVector** extension.
    *   **Task Queue (RQ):** Manages background tasks using **Redis** as the broker.
    *   **Redis:** Acts as the message broker for RQ.
    *   **RQ Workers:** Python processes that consume tasks from the Redis queue. Scale independently.
    *   **External Services:** LLM APIs, Google APIs, Slack APIs, etc.

## Alignment with Goals

*   **Smooth Integrations:** Dedicated `Integration Layer` isolates external interactions. Configuration externalized via `.env`.
*   **Scalability:** Stateless API layer, independently scalable RQ Workers, asynchronous processing.
*   **Easy Iteration:** Separation of concerns allows independent development. Pydantic schemas enforce contracts.
*   **Problem Isolation:** Modularity aids debugging. Logs from specific layers (Workers, Integration modules) help pinpoint issues. Testability enhanced by distinct layers.

## Technology Stack Choices (Simplest & Interoperable Focus)

*   **Vector Storage:** **PGVector** (PostgreSQL Extension). Leverages the existing primary database, simplifying the stack and operations compared to a separate dedicated vector database, while being sufficient for many use cases.
*   **Task Queue:** **RQ (Redis Queue)**. Offers a simpler setup and management experience compared to Celery for robust background tasks, using the widely adopted and performant Redis as a broker. FastAPI `BackgroundTasks` remain an option only for trivial, non-critical, fire-and-forget operations.

## Technology Stack Considerations

*   **Vector DB:** Evaluate PGVector for simplicity vs. dedicated Vector DBs/Services for performance at scale.
*   **Task Queue:** Compare Celery vs. alternatives like Dramatiq, RQ, or Cloud-Native queues based on required features (persistence, monitoring, retries), complexity tolerance, and existing infrastructure (e.g., Redis usage). 