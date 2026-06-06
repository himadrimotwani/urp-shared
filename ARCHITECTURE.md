# Architecture Documentation

This document explains how the Fashion Supply Chain simulation works at the current state.

## 1. High-Level

### Purpose
This is an educational simulation where students play the role of a **buyer** in a fashion supply chain. They negotiate contracts with an AI-powered **supplier** and make ordering decisions across multiple rounds.

### Gameplay Loop
1. **Start Game**: Instructor/Student starts a new game session (specified number of rounds)
2. **Negotiate Contract**: Student proposes contract terms (wholesale price, buyback price, caps, length, contract type)
3. **AI Evaluation**: Supplier (AI) evaluates proposal and accepts/rejects

Accept -> Active contract
Reject -> Student enters chat to discuss

4. **Place Orders**: With an active contract, student places orders for each round
5. **Simulate Round**: App generates demand and calculates sales/returns/profits
6. **View Results**: Student sees round-by-round results and cumulative performance
7. **Repeat**: Continue until contract expires (negotiate new contract) or game ends

### Application Phases
The frontend tracks four distinct phases:
- **`no_game`**: No game session started yet
- **`needs_contract`**: Game started but no active contract (must negotiate)
- **`active_contract`**: Contract active, student can place orders
- **`game_over`**: Game ended (naturally or early termination)

### Period vs Round Distinction
**Period**: Demand timeline time unit, used for preloaded demand history.

**Round**: Demand timeline time unit, used for simulated demand.

**How it appears in code:**

Backend (`simulation/core.py`):
- `GameState.historical_demands`: List containing pre-game history + one demand per completed round
- `GameState.round_number`: Current round (1-indexed, increments after each order)
- `RoundSummary.round_index`: Round number for a completed round

Frontend (`main.js`):
- Calculates `initialHistoryLength = data.length - (currentState.round_number - 1)`
- Labels chart/table: "Period X" for historical data, "Round X" for game rounds
- Example: If `round_number = 3` and `historical_demands.length = 10`, then:
  - Periods 1-8 are historical
  - Round 1 = index 8, Round 2 = index 9

## 2. Project Structure and Responsibilities

### Backend Structure

#### `/backend/app/main.py`
- FastAPI application entry point
- Sets up CORS middleware
- Registers route modules (health, game, negotiation, config)
- Initializes AI clients and loads negotiation config on startup

#### `/backend/app/routes/`
**`game.py`**: Game lifecycle endpoints
- `POST /game/start`: Creates new game session with unique `session_id`
- `POST /game/state`: Returns current game state
- `POST /game/order`: Processes order, simulates round, updates state
- `GET /game/summary`: Returns end-of-game summary (only when game over)
- `POST /game/end-early`: Allows instructor to end game early

**`negotiation.py`**: Contract negotiation endpoints
- `POST /game/negotiate`: Handles initial contract proposal
- `POST /game/negotiate/chat`: Handles chat messages during negotiation
- `POST /game/negotiate/accept-counter`: Accepts/rejects draft contract from chat

**`config.py`**: Configuration management
- `GET /config/current`: Returns economic params and demand history summary
- `POST /config/update`: Updates economic params and/or demand history
- `GET /config/negotiation`: Returns negotiation configuration
- `POST /config/negotiation/update`: Updates negotiation constraints

**`health.py`**: Health check endpoint

#### `/backend/app/services/`
**`game_service.py`**: Data conversion and state checks
- `to_game_state_response()`: Converts `GameState` → `GameStateResponse` schema
- `to_contract_data()`: Converts `Contract` → `ContractData` schema
- `to_round_output_data()`: Converts `RoundOutput` → `RoundOutputData` schema
- `to_round_summary_data()`: Converts `RoundSummary` → `RoundSummaryData` schema
- `is_game_over()`: Checks if game ended
- `has_active_contract()`: Checks if contract has remaining rounds
- `build_config_state_response()`: Builds configuration response

**`negotiation_service.py`**: Contract evaluation logic
- `supplier_evaluate_contract()`: Evaluates proposal (accept/reject)
- `evaluate_proposal_with_ai()`: Uses AI to evaluate proposals
- `evaluate_proposal_simple_logic()`: Fallback when AI unavailable
- `generate_supplier_favored_counter()`: Creates counteroffer (not currently used in initial proposals)

**`ai_service.py`**: AI chat generation
- `generate_chat_response()`: Generates AI supplier responses in chat
- Detects agreement from student messages
- Extracts contract terms from AI JSON responses
- Creates draft contracts when agreement detected

**`ai_client.py`**: AI provider abstraction
- Initializes OpenAI and DeepSeek clients
- Determines active provider based on API keys
- Provides unified interface for AI calls

**`config_service.py`**: Configuration loading
- `load_negotiation_config()`: Loads negotiation config from JSON
- `reload_negotiation_config()`: Forces config reload

**`state.py`**: Session storage
- `SESSIONS`: Global dictionary mapping `session_id` → `GameState`
- In-memory storage (not persisted to database)

#### `/backend/app/schemas.py`
Pydantic models defining API request/response shapes:
- **Configuration**: `EconomicParamsData`, `HistorySummary`, `ConfigStateResponse`, `NegotiationConfigData`
- **Game State**: `GameStateResponse`, `GameStartRequest`, `GameStartResponse`
- **Contracts**: `ContractData`
- **Rounds**: `RoundOutputData`, `RoundSummaryData`
- **Negotiation**: `NegotiateRequest`, `NegotiateResponse`, `NegotiationChatRequest`, `NegotiationChatResponse`, `AcceptCounterRequest`, `AcceptCounterResponse`, `NegotiationHistory`
- **Orders**: `OrderRequest`, `OrderResponse`
- **Summary**: `GameSummary`

#### `/backend/simulation/core.py`
Core simulation logic:
- **Data Classes**: `EconomicParams`, `Contract`, `GameState`, `RoundInput`, `RoundOutput`, `RoundSummary`
- **Configuration**: `load_economic_params_from_json()`, `load_demand_history_from_csv()`, `reload_defaults()`
- **Simulation**: `simulate_round()` (calculates one round), `simulate_game_round()` (generates demand + simulates)
- **Demand Generation**: `generate_demand()` (bootstrap or normal distribution)

### Frontend Structure

#### `/frontend/index.html`
- HTML structure with tabs (Student, Instructor, Debug)
- Forms for negotiation, ordering, configuration
- UI elements: phase banner, contract summary, demand chart, round results

#### `/frontend/main.js`
Single-file frontend application:
- **Global State**: `sessionId`, `currentState` (latest `GameStateResponse`)
- **UI Initialization**: Tab switching, dropdowns, notifications
- **Rendering**: Demand chart (Chart.js), demand table, round results, contract summary, phase UI
- **API Helpers**: `fetchJsonWithDetail()` (handles errors, parses JSON)
- **Game Control**: Start game, end early, fetch summary
- **Negotiation**: Submit proposal, chat, accept/reject counteroffers
- **Ordering**: Place orders, display round results
- **Configuration**: Load/update economic params, demand history, negotiation config

#### `/frontend/style.css`
Styling for UI components

### Configuration Files

#### `/backend/config/economic_params.json`
Economic parameters:
```json
{
  "retail_price": 50.0,
  "buyer_salvage_value": 3.0,
  "supplier_salvage_value": 12.0,
  "supplier_cost": 12.0,
  "return_shipping_buyer": 1.0,
  "return_handling_supplier": 0.5
}
```

#### `/backend/config/negotiation_config.json`
Negotiation constraints:
- `contract_types_available`: Allowed contract types
- `length_min`, `length_max`: Contract length range
- `cap_type_allowed`: "fraction", "unit", or "both"
- `cap_value_min`, `cap_value_max`: Cap value ranges
- `revenue_share_min`, `revenue_share_max`: Revenue share ranges
- `system_prompt_template`: AI prompt template with placeholders

#### `/backend/data/D_hist.csv`
Historical demand data (one value per row, first column)

## 3. Frontend ↔ Backend Communication

### API Helper
Frontend uses `fetchJsonWithDetail()` function:
- Wraps `fetch()` API
- Reads response as text first (can only read body once)
- Extracts error details from JSON if request fails
- Throws errors with HTTP status and detail message
- Returns parsed JSON on success

### Request/Response Flow

**Example: Starting a Game**
```javascript
// Frontend (main.js)
const data = await fetchJsonWithDetail(`${BASE_URL}/game/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rounds: 50, demand_method: "bootstrap" })
});

// Backend (routes/game.py)
@router.post("/game/start", response_model=GameStartResponse)
def start_game(request: GameStartRequest) -> GameStartResponse:
    session_id = str(uuid4())
    state = GameState(...)
    SESSIONS[session_id] = state
    return GameStartResponse(state=to_game_state_response(session_id, state))
```

**Response Parsing and State Updates**
- Frontend stores `sessionId` and `currentState` from responses
- Calls `renderGameState()` after each API call to update UI
- `renderGameState()` updates: phase banner, contract summary, demand chart, round results, section visibility

### Error Handling
- Frontend catches errors in try/catch blocks
- Displays error messages in notification system
- Shows errors in output elements (e.g., `negotiate-output`, `order-output`)
- Backend returns HTTP status codes (400, 404, 500) with detail messages

### Debug Logging
- Frontend logs raw JSON responses to debug output elements
- Backend prints errors to console (e.g., AI API failures)
- Game state JSON displayed in debug tab

## 4. Schema and Data Model Layer

### Role of Schemas
Pydantic models (`app/schemas.py`) serve multiple purposes:
- **API Validation**: FastAPI automatically validates request/response data
- **Type Safety**: Enforces data types and structure
- **Documentation**: FastAPI generates OpenAPI docs from schemas
- **Serialization**: Automatic JSON serialization/deserialization

### Internal vs API Models

**Internal Models** (`simulation/core.py`):
- `Contract`: Dataclass with contract terms
- `GameState`: Complete game state with lists, aggregates
- `RoundOutput`: Detailed round results
- `RoundSummary`: Per-round summary for logging

**API Models** (`app/schemas.py`):
- `ContractData`: API-safe contract representation
- `GameStateResponse`: API-safe game state
- `RoundOutputData`: API-safe round results
- `RoundSummaryData`: API-safe round summary

**Conversion Functions** (`app/services/game_service.py`):
- `to_contract_data()`: `Contract` → `ContractData`
- `to_game_state_response()`: `GameState` → `GameStateResponse`
- `to_round_output_data()`: `RoundOutput` → `RoundOutputData`
- `to_round_summary_data()`: `RoundSummary` → `RoundSummaryData`

### Key Data Models

#### Game/Session State
```json
{
  "session_id": "uuid-string",
  "round_number": 3,
  "total_rounds": 50,
  "contract": { /* ContractData */ },
  "cumulative_buyer_profit": 1250.50,
  "cumulative_supplier_profit": 890.25,
  "game_over": false,
  "demand_method": "bootstrap",
  "historical_demands": [450, 520, 480, 600, 550, 530, 490, 510, 495],
  "rounds": [ /* RoundSummaryData[] */ ]
}
```

#### Contracts
```json
{
  "wholesale_price": 25.0,
  "buyback_price": 12.0,
  "cap_type": "fraction",
  "cap_value": 0.5,
  "length": 5,
  "remaining_rounds": 3,
  "contract_type": "buyback",
  "revenue_share": 0.0
}
```

#### Per-Round Outputs
```json
{
  "order_quantity": 100,
  "realized_demand": 95,
  "sales": 95,
  "unsold": 5,
  "returns": 2,
  "leftovers": 3,
  "buyer_revenue": 4750.0,
  "buyer_cost": 2500.0,
  "buyer_profit": 2250.0,
  "supplier_revenue": 2500.0,
  "supplier_cost": 1200.0,
  "supplier_profit": 1300.0,
  "retail_revenue": 4750.0,
  "salvage_revenue_buyer": 9.0,
  "buyback_refund_buyer": 24.0,
  "wholesale_cost_buyer": 2500.0,
  "return_shipping_cost_buyer": 2.0,
  "revenue_share_payment_buyer": 0.0,
  "wholesale_revenue_supplier": 2500.0,
  "salvage_revenue_supplier": 24.0,
  "production_cost_supplier": 1200.0,
  "buyback_cost_supplier": 24.0,
  "return_handling_cost_supplier": 1.0,
  "revenue_share_revenue_supplier": 0.0
}
```

#### Per-Round Summaries
```json
{
  "round_index": 1,
  "order_quantity": 100,
  "realized_demand": 95,
  "buyer_revenue": 4750.0,
  "buyer_cost": 2500.0,
  "buyer_profit": 2250.0,
  "supplier_revenue": 2500.0,
  "supplier_cost": 1200.0,
  "supplier_profit": 1300.0,
  "wholesale_price": 25.0,
  "buyback_price": 12.0,
  "cap_type": "fraction",
  "cap_value": 0.5,
  "contract_length": 5,
  "remaining_rounds": 4,
  "contract_type": "buyback",
  "revenue_share": 0.0
}
```

#### Game-Level Summary
```json
{
  "session_id": "uuid-string",
  "total_rounds_played": 10,
  "total_demand": 950,
  "total_sales": 920,
  "total_returns": 50,
  "total_leftovers": 30,
  "cumulative_buyer_profit": 12500.0,
  "cumulative_supplier_profit": 8900.0,
  "average_demand": 95.0,
  "fill_rate": 0.968,
  "return_rate": 0.054,
  "leftover_rate": 0.032,
  "historical_demands": [ /* all demands */ ],
  "rounds": [ /* RoundSummaryData[] */ ],
  "negotiation_history": [ /* NegotiationHistory[] */ ]
}
```

## 5. Simulation Run: Overview and Technical Breakdown

### A) Conceptual Flow

1. **Game Initialization**
   - Instructor/student starts game with rounds and demand method
   - System creates new `GameState` with empty contract
   - Loads demand history from CSV
   - Generates unique `session_id`

2. **Contract Negotiation**
   - Student proposes contract terms
   - AI evaluates proposal (accept/reject)
   - If rejected, student enters chat to discuss
   - Chat may produce draft contract
   - Student accepts/rejects draft
   - Contract becomes active

3. **Ordering Rounds**
   - Student places order (Q) for current round
   - System generates demand (D) using bootstrap or normal distribution
   - Simulation calculates: sales, returns, leftovers, profits
   - Contract `remaining_rounds` decrements
   - Round summary saved to history
   - Cumulative profits updated

4. **Contract Expiration**
   - When `remaining_rounds` reaches 0, contract expires
   - Student must negotiate new contract to continue

5. **Game End**
   - Game ends when `round_number > total_rounds` or instructor ends early
   - Summary generated with all statistics and history

### B) Technical Sequence

#### Starting a Game

**Backend Functions:**
- `routes/game.py::start_game()`:
  - Validates `demand_method`
  - Creates UUID `session_id`
  - Creates empty `Contract` (length=0, remaining_rounds=0)
  - Loads `DEFAULT_HISTORY` (per-session copy)
  - Creates `GameState` with `round_number=1`, empty profits, empty negotiation state
  - Stores in `SESSIONS[session_id]`
  - Returns `GameStartResponse` with converted state

**State Mutations:**
- New entry in `SESSIONS` dictionary
- `GameState` initialized with default values

**Frontend Reaction:**
- Stores `sessionId` and `currentState`
- Calls `renderGameState()` to update UI
- Phase changes to `needs_contract`
- Negotiation section becomes visible

#### Negotiating a Contract

**Backend Functions:**
- `routes/negotiation.py::negotiate()`:
  - Validates session exists, game not over, no active contract
  - Saves previous negotiation to history (if exists)
  - Clears negotiation state (chat history, draft contract)
  - Validates proposal against negotiation config
  - Builds `Contract` from proposal
  - Calls `negotiation_service.py::supplier_evaluate_contract()`
  - If accepted: makes contract active, saves to history, clears negotiation state
  - If rejected: adds rejection message to chat history

- `negotiation_service.py::supplier_evaluate_contract()`:
  - Validates contract structure (buyback < wholesale)
  - Calls `evaluate_proposal_with_ai()` or `evaluate_proposal_simple_logic()`

- `negotiation_service.py::evaluate_proposal_with_ai()`:
  - Builds evaluation prompt with proposal, supplier constraints, demand context
  - Calls AI (OpenAI or DeepSeek)
  - Parses AI response (DECISION: accept/reject, MESSAGE: ...)
  - Returns (decision, message, None)

**State Mutations:**
- If accepted: `state.contract` updated, `remaining_rounds` set to `length`
- If rejected: `state.negotiation_chat_history` updated with rejection message
- `state.negotiation_history` updated with negotiation record

**Frontend Reaction:**
- If accepted: Phase changes to `active_contract`, order section becomes visible
- If rejected: Chat section becomes visible, proposal form hidden

#### Negotiation Chat

**Backend Functions:**
- `routes/negotiation.py::negotiation_chat()`:
  - Adds student message to `state.negotiation_chat_history`
  - Calls `ai_service.py::generate_chat_response()`
  - Adds AI response to chat history
  - If draft contract detected, stores in `state.negotiation_draft_contract`

- `ai_service.py::generate_chat_response()`:
  - Builds system prompt from template with game context
  - Checks if student message indicates agreement
  - Sends conversation to AI (last 10 messages)
  - Parses JSON response: `{"response": "...", "contract": {...}, "negotiation_complete": true/false}`
  - Creates `Contract` from JSON if present
  - Validates and clamps contract values to config ranges

**State Mutations:**
- `state.negotiation_chat_history` updated with student and supplier messages
- `state.negotiation_draft_contract` updated if agreement detected

**Frontend Reaction:**
- Displays chat messages in chat UI
- If draft contract present, shows counteroffer section with accept/reject buttons

#### Accepting/Rejecting Counteroffer

**Backend Functions:**
- `routes/negotiation.py::accept_counter()`:
  - If accepting: makes draft contract active, saves negotiation to history, clears negotiation state
  - If rejecting: clears draft contract, adds rejection message to chat history

**State Mutations:**
- If accepting: `state.contract` updated, `remaining_rounds` set, negotiation state cleared
- If rejecting: `state.negotiation_draft_contract` cleared, chat history updated

**Frontend Reaction:**
- If accepting: Phase changes to `active_contract`, chat/offer sections hidden
- If rejecting: Chat continues, offer section hidden

#### Placing an Order

**Backend Functions:**
- `routes/game.py::place_order()`:
  - Validates session exists, game not over, active contract exists
  - Calls `simulation/core.py::simulate_game_round()`

- `simulation/core.py::simulate_game_round()`:
  - Calls `generate_demand()` to get realized demand (D)
  - Appends D to `state.historical_demands`
  - Creates `RoundInput(order_quantity=Q, realized_demand=D)`
  - Calls `simulate_round(state.contract, round_input)`
  - Updates cumulative profits
  - Updates aggregate statistics (total_demand, total_sales, etc.)
  - Creates `RoundSummary` and appends to `state.round_summaries`
  - Increments `state.round_number`

- `simulation/core.py::simulate_round()`:
  - Calculates sales = min(Q, D)
  - Calculates unsold = max(Q - D, 0)
  - Based on contract type (buyback/revenue_sharing/hybrid):
    - Calculates returns based on cap constraints
    - Calculates leftovers
    - Calculates all revenue/cost components
    - Calculates profits
  - Decrements `contract.remaining_rounds`
  - Returns `RoundOutput`

**State Mutations:**
- `state.historical_demands` appended with new demand
- `state.cumulative_buyer_profit` and `state.cumulative_supplier_profit` updated
- `state.total_demand`, `state.total_sales`, `state.total_returns`, `state.total_leftovers` updated
- `state.round_summaries` appended with new summary
- `state.round_number` incremented
- `state.contract.remaining_rounds` decremented

**Frontend Reaction:**
- Displays round results in round result card
- Updates demand chart and table
- Updates cumulative profits display
- If contract expired, phase changes to `needs_contract`
- If game over, fetches and displays summary

#### Demand History Evolution

- **Initial**: `historical_demands` contains pre-game history from CSV
- **During Game**: Each round appends one demand value
- **Formula**: `initialHistoryLength = historical_demands.length - (round_number - 1)`
- **Example**: If 7 historical periods and 3 rounds completed:
  - `historical_demands.length = 10` (7 historical + 3 game)
  - `round_number = 4` (next round)
  - `initialHistoryLength = 10 - 3 = 7` (first 7 are historical)

#### Period and Round Increments

- **Periods**: Always increment as demand values are added to `historical_demands`
- **Rounds**: `round_number` starts at 1, increments after each order
- **After Round 1**: `round_number = 2`, meaning Round 1 is complete
- **Round Index**: `round_index = round_number - 1` (for display)

#### Contract Persistence

- **Active Contract**: Stored in `state.contract`
- **Remaining Rounds**: `contract.remaining_rounds` decrements each order
- **Expiration**: When `remaining_rounds = 0`, contract expires
- **New Contract**: Must negotiate new contract to continue ordering
- **Contract History**: Each `RoundSummary` includes contract details at time of round

## 6. Negotiation System Design

The negotiation system uses a multi-step flow that allows students to negotiate contracts through conversation with an AI supplier. The system is designed to be educational, helping students understand contract terms and negotiation dynamics.

### Flow Diagram

```
1. Student Submits Initial Proposal
   ↓
2. Supplier Evaluates (AI)
   ├─→ ACCEPT → Contract Active (Game continues)
   ├─→ REJECT → Chat opens (Student can discuss)
   └─→ (No counter on initial proposal)
   
3. Student Enters Chat
   ↓
4. AI Responds in Chat
   ├─→ May detect agreement → Creates draft contract
   └─→ Continues conversation
   
5. Draft Contract Created (from chat)
   ↓
6. Student Accepts/Rejects Counter
   ├─→ ACCEPT → Contract Active
   └─→ REJECT → Chat continues
```

### Step-by-Step Breakdown

#### Step 1: Initial Proposal (`POST /game/negotiate`)

**What happens:**
1. Student submits a contract proposal with all terms (wholesale, buyback, length, cap, etc.)
2. System validates proposal against negotiation config:
   - Contract type must be in `contract_types_available`
   - Length must be between `length_min` and `length_max`
   - Cap type must match `cap_type_allowed`
   - Cap value must be between `cap_value_min` and `cap_value_max`
   - Revenue share must be between `revenue_share_min` and `revenue_share_max` (if applicable)
3. Basic validation: buyback price < wholesale price
4. **Contract type is locked** - stored in `state.initial_contract_type` and cannot be changed
5. Previous negotiation history is saved (if exists)
6. New negotiation state is initialized (chat history cleared, start time recorded)

**Supplier Evaluation:**
- Calls `supplier_evaluate_contract()` which uses AI to evaluate
- AI can only return **"accept"** or **"reject"** - NO counteroffers on initial proposal
- This is intentional: counteroffers only come after conversation
- Builds prompt with proposal, supplier constraints (cost, salvage), demand history

**Possible Outcomes:**

**A. ACCEPT:**
- Contract becomes active immediately (`state.contract` updated, `remaining_rounds` set to `length`)
- Negotiation history saved with "accept" decision
- Negotiation state cleared
- Student can now place orders
- Phase changes to `active_contract`, order section becomes visible

**B. REJECT:**
- Rejection message added to chat history
- Chat interface opens for student
- Negotiation continues (student can discuss terms)
- Phase remains `needs_contract`, chat section becomes visible, proposal form hidden

**C. (No Counter):**
- Counteroffers are NOT provided on initial proposals
- This forces students to engage in conversation to negotiate

#### Step 2: Negotiation Chat (`POST /game/negotiate/chat`)

**Purpose:**
- Allows student and AI supplier to discuss terms
- Educational: helps student understand contract mechanics
- No contract is activated directly from chat messages

**How it works:**
1. Student sends a message
2. Message added to `state.negotiation_chat_history`
3. AI generates response using `generate_chat_response()`
4. AI response added to chat history
5. System checks if agreement was reached

**AI Response Generation:**
- Uses full chat history for context (last 10 messages sent to AI to stay within token limits)
- Has access to game state (demand history, current round, etc.)
- Knows the fixed contract type (cannot be changed)
- System prompt includes: economic params, demand statistics, game progress, negotiation constraints
- Can detect when student agrees to terms

**Agreement Detection:**
The system uses multiple methods to detect agreement:

1. **JSON Contract in AI Response** (Priority 1)
   - AI provides `CONTRACT_JSON: {...}` block or JSON in response
   - Most reliable method
   - Extracted and validated immediately
   - AI returns: `{"response": "...", "contract": {...}, "negotiation_complete": true}`

2. **Explicit Agreement Check**
   - If student uses agreement phrases ("sounds good", "lock in", "yes", "deal", etc.)
   - System asks AI explicitly: "Has the student agreed to finalize?"
   - AI responds with JSON if yes

3. **Pattern-Based Extraction** (Fallback)
   - Extracts terms from conversation using regex
   - Looks for prices, lengths, cap values in recent messages
   - Less reliable but handles edge cases

**Draft Contract Creation:**
- When agreement is detected, a draft contract is created
- Stored in `state.negotiation_draft_contract`
- Available for student to accept/reject
- Terms are validated and clamped against negotiation config ranges
- Contract type cannot be changed (fixed from initial proposal)
- Frontend displays counteroffer section with accept/reject buttons

**Counteroffer Structure:**
```json
{
  "wholesale_price": 25.0,
  "buyback_price": 12.0,
  "contract_length": 5,
  "cap_type": "fraction",
  "cap_value": 0.5,
  "contract_type": "buyback",
  "revenue_share": 0.0
}
```

#### Step 3: Accept/Reject Counter (`POST /game/negotiate/accept-counter`)

**When it's used:**
- Student has a draft contract available (from chat)
- Student clicks "Accept Counter" or "Reject Counter"

**If ACCEPTED:**
- Draft contract becomes active (`state.contract`)
- Contract's `remaining_rounds` set to `length`
- Negotiation history saved with "accept" decision
- Negotiation state cleared
- Student can now place orders
- Phase changes to `active_contract`, chat/offer sections hidden

**If REJECTED:**
- Draft contract cleared
- Chat history preserved
- Negotiation can continue
- Chat continues, offer section hidden

### Key Data Structures

**GameState Fields:**
- `negotiation_chat_history`: List of chat messages `[{role: "student"/"supplier", content: "..."}]`
- `negotiation_draft_contract`: Contract object (if agreement reached in chat)
- `initial_contract_type`: Contract type from initial proposal (FIXED, cannot change)
- `negotiation_history`: List of completed negotiation sessions
- `_current_negotiation_start_time`: Timestamp when current negotiation started

**Contract Validation:**
- Length must be within `length_min` and `length_max` (from config)
- Cap value must be within `cap_value_min` and `cap_value_max`
- Revenue share must be within `revenue_share_min` and `revenue_share_max`
- Contract type must be in `contract_types_available`
- Cap type must match `cap_type_allowed` setting

### Important Design Decisions

1. **No Counters on Initial Proposals**
   - Forces students to engage in conversation
   - More educational: teaches negotiation through discussion
   - Counters only emerge from chat discussions

2. **Contract Type is Fixed**
   - Once initial proposal sets contract type, it cannot change
   - Prevents confusion and maintains negotiation focus
   - Stored in `initial_contract_type` and enforced throughout

3. **Multiple Agreement Detection Methods**
   - JSON from AI (most reliable)
   - Explicit AI check (when agreement likely)
   - Pattern extraction (fallback)
   - Ensures agreements are captured even if AI doesn't provide JSON

4. **Negotiation History Preservation**
   - All negotiations are saved to `negotiation_history`
   - Includes chat messages, final decision, contract terms, timestamps
   - Available in game summary for analysis

5. **Draft Contracts**
   - Created when agreement detected in chat
   - Stored but not active until student accepts
   - Allows student to review before committing

### Example Flow

1. **Student proposes:** Buyback contract, $18 wholesale, $10 buyback, 5 rounds
2. **AI evaluates:** Rejects (wholesale too low)
3. **Chat opens:** Student asks "What would you suggest?"
4. **AI responds:** "I'd suggest $25 wholesale, $12 buyback, 5 rounds..."
5. **Student says:** "Sounds good"
6. **System detects agreement:** Creates draft contract
7. **Draft shown:** Student sees counteroffer with accept/reject buttons
8. **Student accepts:** Contract becomes active, game continues

### API Endpoints and Request/Response Examples

**Initial Proposal Request:**
```json
POST /game/negotiate
{
  "session_id": "uuid",
  "wholesale_price": 20.0,
  "buyback_price": 10.0,
  "cap_type": "fraction",
  "cap_value": 0.5,
  "length": 5,
  "contract_type": "buyback",
  "revenue_share": 0.0
}
```

**Initial Proposal Response:**
```json
{
  "state": { /* GameStateResponse */ },
  "ai_message": "The wholesale price is too low for me to operate profitably.",
  "decision": "reject",
  "counter_contract": null
}
```

**Chat Request:**
```json
POST /game/negotiate/chat
{
  "session_id": "uuid",
  "message": "How about $25 wholesale with $12 buyback?"
}
```

**Chat Response:**
```json
{
  "supplier_message": "That sounds more reasonable. Let me think...",
  "negotiation_draft_contract": null
}
```

**Chat Response with Agreement:**
```json
{
  "supplier_message": "Great! Let's lock in these terms: $25 wholesale, $12 buyback, 5 rounds.",
  "negotiation_draft_contract": {
    "wholesale_price": 25.0,
    "buyback_price": 12.0,
    "cap_type": "fraction",
    "cap_value": 0.5,
    "length": 5,
    "remaining_rounds": 5,
    "contract_type": "buyback",
    "revenue_share": 0.0
  }
}
```

**Accept Counteroffer Request:**
```json
POST /game/negotiate/accept-counter
{
  "session_id": "uuid",
  "accept": true
}
```

**Accept Counteroffer Response:**
```json
{
  "state": { /* GameStateResponse with active contract */ }
}
```

**Frontend Interpretation:**
- Checks `decision` field to determine next step
- If `reject`: Shows chat section, hides proposal form
- If `accept`: Hides negotiation section, shows order section
- If `negotiation_draft_contract` present: Shows counteroffer section with accept/reject buttons
- Updates phase UI based on contract status

### Configuration

Negotiation behavior is controlled by `config/negotiation_config.json`:
- `contract_types_available`: Allowed contract types
- `length_min`, `length_max`: Contract length range
- `cap_type_allowed`: "fraction", "unit", or "both"
- `cap_value_min`, `cap_value_max`: Cap value ranges
- `revenue_share_min`, `revenue_share_max`: Revenue share ranges
- `system_prompt_template`: AI prompt template with placeholders

## 7. Model Selection and Fallback Logic

### Model Selection

**AI Provider Selection** (`app/services/ai_client.py`):
- Checks for `OPENAI_API_KEY` environment variable
- If present, uses OpenAI (`gpt-4o-mini`)
- Otherwise checks for `OPENROUTER_API_KEY`
- If present, uses DeepSeek via OpenRouter
- Active provider stored in `ai_provider` variable

**Model Configuration:**
- OpenAI: `gpt-4o-mini` (cost-effective model)
- DeepSeek: Tries multiple models in order:
  1. `deepseek/deepseek-r1-0528:free` (free model)
  2. `deepseek/deepseek-chat:free` (fallback free model)
  3. `deepseek/deepseek-chat` (paid model)

### Fallback Logic

**Proposal Evaluation Fallback:**
- If AI unavailable or fails: `evaluate_proposal_simple_logic()` used
- Simple logic:
  - Calculates minimum acceptable wholesale price (cost + margin)
  - Rejects if wholesale too low
  - Rejects if buyback too high relative to wholesale
  - Accepts if terms reasonable

**Chat Response Fallback:**
- If AI unavailable: Returns generic message: "I'm open to discussing contract terms. What would you like to adjust?"
- If AI fails: Returns one of several fallback messages (rotated based on message count)
- If JSON parsing fails: Returns: "I'm having trouble processing that. Could you rephrase your proposal?"

**Model Fallback Chain (DeepSeek):**
- Tries `deepseek/deepseek-r1-0528:free` first
- If model not found (404) or error: tries `deepseek/deepseek-chat:free`
- If that fails: tries `deepseek/deepseek-chat`
- If all fail: raises error, triggers fallback response

### Preserved Baseline Logic

**Simple Evaluation Logic:**
- `evaluate_proposal_simple_logic()` in `negotiation_service.py`
- Used when AI unavailable or fails
- Provides basic validation to ensure game continues
- Not used when AI is working (AI always preferred)

**No Legacy Functions:**
- All functions are actively used
- No temporary or legacy code identified
- Fallback logic is intentional, not legacy

## 8. Educational Design Intent

### Transparency of Contract Mechanics

**How it's achieved:**
- **Detailed Round Outputs**: `RoundOutputData` includes all revenue/cost components
  - Buyer: retail_revenue, salvage_revenue_buyer, buyback_refund_buyer, wholesale_cost_buyer, return_shipping_cost_buyer, revenue_share_payment_buyer
  - Supplier: wholesale_revenue_supplier, salvage_revenue_supplier, production_cost_supplier, buyback_cost_supplier, return_handling_cost_supplier, revenue_share_revenue_supplier
- **Contract Summary Display**: Frontend shows all contract terms (type, prices, caps, length, remaining rounds)
- **Round-by-Round History**: Students can see how each decision affected profits
- **Game Summary**: End-of-game summary shows aggregate statistics and all rounds

**Code locations:**
- `simulation/core.py::simulate_round()`: Calculates all components explicitly
- `frontend/main.js::renderRoundResultCard()`: Displays detailed breakdown
- `frontend/main.js::updateContractSummary()`: Shows contract terms

### Iterative Negotiation

**How it's achieved:**
- **Initial Proposal → Rejection → Chat → Counteroffer → Accept/Reject → Continue**
- Chat allows back-and-forth discussion before committing
- Draft contracts can be rejected to continue negotiation
- Multiple negotiation attempts allowed (each saved to history)

**Code locations:**
- `routes/negotiation.py::negotiate()`: Handles initial proposals
- `routes/negotiation.py::negotiation_chat()`: Handles chat messages
- `routes/negotiation.py::accept_counter()`: Handles accept/reject of counteroffers
- `ai_service.py::generate_chat_response()`: Generates conversational responses

### Clear Separation of Historical Context vs Decision Rounds

**How it's achieved:**
- **Period vs Round Labels**: Frontend labels historical data as "Period X", game data as "Round X"
- **Demand History**: `historical_demands` clearly separates pre-game history from game-generated demand
- **Initial History Length Calculation**: `initialHistoryLength = data.length - (round_number - 1)`

**Code locations:**
- `frontend/main.js::renderDemandChart()`: Creates labels distinguishing periods from rounds
- `frontend/main.js::renderDemandTable()`: Labels table rows as Period or Round
- `simulation/core.py::simulate_game_round()`: Appends new demand to `historical_demands`

### Phase-Aware UI Behavior

**How it's achieved:**
- **Phase Computation**: `computePhase()` determines current phase based on game state
- **Phase-Based UI Updates**: `updatePhaseUI()` enables/disables buttons, updates banner text
- **Section Visibility**: `updateSectionVisibility()` shows/hides sections based on phase
- **Button Tooltips**: Explain why buttons are disabled

**Phases:**
- `no_game`: No game started
- `needs_contract`: Game started, no active contract
- `active_contract`: Contract active, can place orders
- `game_over`: Game ended

**Code locations:**
- `frontend/main.js::computePhase()`: Determines phase
- `frontend/main.js::updatePhaseUI()`: Updates UI based on phase
- `frontend/main.js::updateSectionVisibility()`: Controls section visibility

### Contract Mechanics

**Buyback Contracts:**
- Buyer orders Q units at wholesale price w
- Demand D occurs
- Sales = min(Q, D)
- Unsold = max(Q - D, 0)
- Returns = min(unsold, cap) where cap = φ * Q (fraction) or B_max (unit)
- Leftovers = unsold - returns
- Buyer profit = (p * sales) + (v_B * leftovers) + (b * returns) - (w * Q) - (c_ret * returns)
- Supplier profit = (w * Q) + (v_S * returns) - (c * Q) - (b * returns) - (h * returns)

**Revenue Sharing Contracts:**
- No returns
- Revenue share: Supplier receives share * (p * sales)
- Buyer profit = (p * sales) - (share * p * sales) + (v_B * leftovers) - (w * Q)
- Supplier profit = (w * Q) + (share * p * sales) - (c * Q)

**Hybrid Contracts:**
- Combines buyback and revenue sharing
- Returns calculated with cap constraints
- Revenue share applied to sales
- Both mechanisms active simultaneously

**Code locations:**
- `simulation/core.py::simulate_round()`: Implements all contract type calculations

### Design Choices
- **No Counteroffers on Initial Proposals**: Encourages conversation before committing
- **Chat-Based Negotiation**: More natural, educational interaction
- **Detailed Profit Breakdowns**: Transparency helps students understand mechanics
- **Phase-Aware UI**: Clear guidance on what actions are available
- **Period vs Round Distinction**: Helps students understand historical context vs decisions

---

**Note on AI Assistance**: AI assistance was used during development to generate boilerplate, suggest patterns, fill knowledge gaps, code reformatting/reorganization and documentation, while final design and integration decisions remained developer-driven.

**THIS FILE WAS GENERATED WITH AI, BUT REVIEWED**