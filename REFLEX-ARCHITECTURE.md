# REFLEX-ARCHITECTURE: I2I-Native Notebook

## The Problem with LangGraph Hooks
Hooks intercept an existing workflow after the fact. They're bolted on, not native. A true A2A system should use the **vessel protocol as the orchestration layer**, not as an afterthought.

## The Solution: Notebook as Vessel Endpoint

Instead of hooking into LangGraph:
```
Bottle arrives → Hook intercepts + modifies LangGraph → Result
```

Make the notebook an I2I endpoint:
```
Vessel [incoming] → Notebook Flask/FastAPI → Vessel [outgoing]
                           ↕
                    LangGraph (internal impl)
```

## Architecture

### Incoming Flow
```
I2I Vessel/harbor/incoming/
  └─ bottle.json  →  Notebook A2A router
                        ├─ type: research → ask.py
                        ├─ type: transform → transformation.py
                        ├─ type: podcast → podcast_commands.py
                        └─ type: status → return notebook config
```

Each bottle type maps DIRECTLY to a notebook capability. No hooks. The router IS the A2A layer.

### Background Vessel Poller
```
[Background Task] ↔ I2I Vessel/incoming/
     │
     ├─ Reads new bottles every N seconds
     ├─ Routes to appropriate handler
     ├─ Joins any completed results back
     └─ Writes response to Vessel/outgoing/
```

### CORTEX Discovery
```
GET /.well-known/cortex.json  →  Lists all bottle types this notebook processes
                               →  Other agents discover: "notebook-1 can do research/transform/podcast"
                               →  They send bottles accordingly
```

## Implementation (Phase 1)

### Files to Create

1. **open_notebook/i2i/router.py** — I2I endpoint router
   - Maps bottle types to handlers
   - Handles bottle envelope parsing/validation
   - Returns ACK/NACK responses

2. **open_notebook/i2i/poller.py** — Background vessel poller
   - Async task that checks I2I vessel/incoming/
   - Routes to handlers, writes results to outgoing/
   - Configurable poll interval

3. **open_notebook/i2i/handlers.py** — Bottle type handlers
   - `handle_research(bottle)` → calls ask.py
   - `handle_transform(bottle)` → calls transformation.py  
   - `handle_podcast(bottle)` → calls podcast code
   - `handle_status(bottle)` → returns notebook status

4. **open_notebook/i2i/__init__.py** — Package initialization
   - Start background poller on FastAPI startup
   - Register I2I routes
   - Register CORTEX discovery endpoint

5. **CORTEX.json** — Capability manifest

### What Changes in Existing Code

| File | Change |
|------|--------|
| `run_api.py` | Mount i2i router, start background poller via lifespan |
| `open_notebook/graphs/ask.py` | NO CHANGES — called by handler, not hooked |
| `open_notebook/graphs/transformation.py` | NO CHANGES — called by handler, not hooked |

Zero LangGraph modifications. The A2A layer sits ABOVE the graph layer.

## Comparison

| Aspect | Hook Approach | Vessel-Native Approach |
|--------|--------------|----------------------|
| LangGraph changes | 2 files modified | 0 files modified |
| A2A separation | Mixed with business logic | Cleanly separated |
| Bottle handling | Implicit via hooks | Explicit via router |
| Debugging | Hard (hidden in hook chain) | Easy (router logs every bottle) |
| Testing | Integration-heavy | Unit-testable router |
| Add new capability | New hook point | New route handler |
| Offline resilience | Fragile | Vessel stores bottles |
