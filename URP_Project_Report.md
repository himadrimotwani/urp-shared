# Fashion Supply Chain Simulation: URP Project Report

## Abstract

This project implements an interactive fashion supply chain simulation designed for educational use. The system allows students to act as buyers who negotiate contracts with an AI-supported supplier, place order quantities under uncertain demand, and observe the financial consequences of their decisions over multiple rounds. The application combines a Python/FastAPI backend, a browser-based JavaScript frontend, configurable economic parameters, demand-history-driven uncertainty, and data collection features for instructor review. The project demonstrates applied work in simulation modeling, backend system design, API development, frontend interaction design, and AI-assisted negotiation workflows.

## 1. Introduction

Supply chain decision-making often requires balancing risk, uncertainty, and incentives between multiple parties. In a fashion retail setting, buyers must decide how much inventory to order before demand is fully known. Ordering too little creates lost sales, while ordering too much creates unsold inventory and financial loss. Contract structures, such as buyback contracts, can redistribute this risk between buyer and supplier.

The URP project addresses this learning problem by creating a web-based simulation where students experience the operational and financial effects of contract negotiation and demand uncertainty. Instead of only studying formulas, students interact with a supplier, negotiate contract terms, place orders, and review detailed profit breakdowns. The project is intended to support classroom use, instructor experimentation, and student reflection.

## 2. Project Objectives

The main objectives of the project are:

- Build an interactive simulation for fashion supply chain contract negotiation.
- Allow students to negotiate wholesale price, buyback price, contract type, and contract length.
- Simulate round-by-round ordering decisions under uncertain demand.
- Provide transparent calculations for sales, returns, leftovers, buyer profit, and supplier profit.
- Support AI-assisted supplier negotiation using OpenAI or DeepSeek through OpenRouter.
- Provide instructor-facing controls for economic parameters, demand histories, and collected records.
- Maintain a modular structure so the simulation logic, API layer, and frontend interface can evolve independently.

## 3. System Overview

The application consists of three major layers:

1. A simulation engine in Python that models demand, order decisions, contract terms, and profit calculations.
2. A FastAPI backend that exposes game, negotiation, configuration, participant, and record endpoints.
3. A browser-based frontend that allows students and instructors to interact with the simulation.

The game follows a repeated cycle. A participant starts a session, negotiates a contract, places an order, observes realized demand and profit outcomes, and repeats this process until the game ends. When a contract expires, the student must negotiate another contract before continuing.

## 4. Backend Architecture

The backend is implemented using FastAPI. The main application entry point registers API routes, enables CORS, exposes health endpoints, and initializes AI provider status checks.

The backend is organized into route modules and service modules:

- `backend/app/routes/game.py` handles game creation, game state retrieval, order placement, early game termination, and summary generation.
- `backend/app/routes/negotiation.py` handles initial contract proposals, negotiation chat, and acceptance or rejection of draft agreements.
- `backend/app/routes/config.py` supports instructor configuration of economic parameters and negotiation settings.
- `backend/app/routes/participants.py` records participant information before gameplay begins.
- `backend/app/routes/records.py` exposes instructor-protected access to participant and round-level records.
- `backend/app/services/game_service.py` converts internal simulation objects into API response models.
- `backend/app/services/ai_service.py` manages AI negotiation chat generation, response cleaning, and contract term extraction.
- `backend/app/services/storage_service.py` stores participant and round records using append-only JSONL files and exports CSV data.
- `backend/app/services/demand_history_service.py` loads selectable demand-history scenarios.

The backend uses Pydantic schemas in `backend/app/schemas.py` to validate API inputs and structure API responses. This improves reliability by enforcing data types for contracts, game state, round output, configuration, and participant records.

## 5. Simulation Model

The simulation engine is implemented in `backend/simulation/core.py`. It defines data classes for economic parameters, contracts, game state, round inputs, round outputs, and round summaries.

The main contract currently modeled is a buyback contract. Under this contract, the buyer orders a quantity `Q`, demand realizes as `D`, and sales are calculated as:

```text
sales = min(Q, D)
unsold = max(Q - D, 0)
returns = unsold
leftovers = 0
```

For the buyer, revenue includes retail sales and buyback refunds from returned units. Costs include wholesale purchasing costs and return shipping costs. For the supplier, revenue includes wholesale revenue and salvage revenue from returned units. Costs include production cost, buyback cost, and return handling cost.

The buyer profit is calculated from:

```text
buyer profit =
    retail revenue
    + buyback refund
    - wholesale cost
    - return shipping cost
```

The supplier profit is calculated from:

```text
supplier profit =
    wholesale revenue
    + supplier salvage revenue
    - production cost
    - buyback cost
    - return handling cost
```

Each completed round updates cumulative buyer profit, cumulative supplier profit, total demand, total sales, total returns, total leftovers, and the list of round summaries. This makes it possible to generate a complete end-of-game report.

## 6. Demand Generation

The project supports demand generation from historical data. Demand histories are loaded from CSV files, including a default demand history and additional demand scenarios stored in `backend/data/demand_histories/`.

The application supports two demand-generation methods:

- Bootstrap sampling from historical demand values.
- Normal-distribution-based generation using historical demand statistics.

The demand history is copied into each game session so that selecting a demand scenario affects that session without globally changing other games. This design keeps game sessions isolated and reproducible at the session level.

## 7. Negotiation System

The negotiation system is one of the most important interactive parts of the project. Students first propose contract terms. The supplier evaluates the proposal and either accepts it or rejects it. If the proposal is rejected, the student can continue the negotiation through a chat interface.

The negotiation layer includes:

- Proposal validation against instructor-defined constraints.
- AI-assisted evaluation of contract terms.
- Fallback logic when no AI provider is configured.
- Chat history tracking during negotiation.
- Draft contract creation when agreement is detected.
- Negotiation history storage for final game summaries.

The AI service supports OpenAI and DeepSeek through OpenRouter. It also includes defensive parsing utilities for extracting contract terms from AI responses, including malformed or partially structured JSON. This is useful because model outputs can be inconsistent, especially when combining natural language and structured contract terms.

## 8. Frontend Design

The frontend is implemented using HTML, CSS, and JavaScript. The main frontend logic is in `frontend/main.js`, which manages global state, API calls, rendering, tab navigation, notifications, login flow, game actions, negotiation actions, configuration controls, and demand visualization.

The interface is divided into major sections:

- Student gameplay interface.
- Instructor configuration and monitoring interface.
- Debug/status interface.

The student workflow includes participant login, game start, contract negotiation, order placement, result review, and demand history visualization. The instructor workflow includes configuration of economic parameters and access to collected records.

The frontend communicates with the backend using JSON APIs. It uses a helper function to parse API responses, surface useful error messages, and update UI state after each action.

## 9. Data Collection and Instructor Features

The project includes lightweight data collection for classroom and research use. Participant records are stored when a student enters the game. Round-level records are logged after each order decision. These records include participant information, session ID, round number, order quantity, realized demand, sales, returns, leftovers, buyer profit, supplier profit, and contract terms.

Records are stored in JSONL format for append-only reliability and can be exported as CSV files. Instructor access to record summaries and CSV downloads is protected by an instructor access code loaded from the environment.

This design supports later analysis of student behavior, negotiation outcomes, ordering patterns, and performance across demand scenarios.

## 10. Configuration Management

The simulation uses JSON and CSV files for configuration. Economic parameters are stored in `backend/config/economic_params.json`, negotiation constraints are stored in `backend/config/negotiation_config.json`, and demand histories are stored in CSV files.

Configurable economic parameters include:

- Retail price.
- Buyer salvage value.
- Supplier salvage value.
- Supplier production cost.
- Buyer return shipping cost.
- Supplier return handling cost.

Configurable negotiation settings include:

- Available contract types.
- Minimum and maximum contract length.
- AI system prompt template.
- Example dialogue for negotiation behavior.

Externalizing these parameters allows instructors to create different teaching scenarios without changing code.

## 11. Technical Contributions

The project demonstrates several technical contributions:

- A modular simulation engine with explicit data classes and transparent financial calculations.
- A FastAPI backend with validated request and response schemas.
- AI-assisted negotiation with fallback behavior for non-AI operation.
- Session-based game state management.
- Configurable demand histories and economic parameters.
- Participant and round-level data logging.
- CSV export for instructor analysis.
- A browser frontend with game state rendering, notifications, charts, and multi-tab workflows.

The implementation also emphasizes explainability. Round outputs include detailed revenue and cost components, rather than only final profit values. This supports the educational goal of helping students understand why a decision produced a specific outcome.

## 12. Limitations

The current version has several limitations:

- Game sessions are stored in memory, so active sessions are not durable across server restarts.
- JSONL storage is simple and useful for prototypes, but a database would be better for production deployment.
- The simulation currently focuses mainly on buyback contracts.
- AI negotiation quality depends on API availability, model behavior, prompt quality, and response parsing.
- Authentication for instructor records is based on a shared access code rather than a full user management system.
- The frontend is implemented as a plain JavaScript application, which may become harder to maintain as the interface grows.

## 13. Future Work

Future development could improve the system in several directions:

- Add persistent database storage for sessions, participants, negotiations, and round outcomes.
- Support additional contract types such as revenue sharing or hybrid contracts.
- Add richer analytics for student decisions, negotiation efficiency, and profit comparisons.
- Improve AI prompt engineering and structured output enforcement.
- Add instructor dashboards for comparing students or sections.
- Add automated tests for simulation calculations and API behavior.
- Improve deployment configuration and production security.
- Add role-based authentication for instructors and students.

## 14. Conclusion

The URP Fashion Supply Chain Simulation is a full-stack educational tool that connects supply chain theory with interactive decision-making. It allows students to negotiate contracts, make ordering decisions under demand uncertainty, and observe how contract terms affect both buyer and supplier profits. Technically, the project integrates simulation modeling, API design, frontend development, AI-assisted negotiation, and data collection.

The project is valuable as both a teaching tool and a software engineering artifact. It shows the ability to translate a domain problem into a working computational system, design clear backend interfaces, implement transparent simulation logic, and build an interactive experience for end users. With further improvements in persistence, contract variety, testing, and analytics, the project could support broader classroom use and more detailed research into student decision-making behavior.
