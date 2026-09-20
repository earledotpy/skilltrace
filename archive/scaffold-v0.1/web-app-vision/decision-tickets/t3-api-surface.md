# Decision Ticket T3: Engine API Surface

**Title:** Define the API surface the new web app must consume from the skilltrace engine

**Description:**
The new mobile‑first web app will need to consume mechanics from the skilltrace engine. Define the minimal API surface that the interface layer must implement on top of the engine core.

**Engine mechanics that the interface must be able to query or act upon:**

1. **Node state queries**
   - `GET /nodes/{id}` — returns node state (locked/available/active/passed/mastered)
   - `GET /available` — returns all nodes currently available to start

2. **Eligibility checks**
   - `POST /eligibility/pass/{id}` — returns whether node X can be passed right now
   - `POST /eligibility/master/{id}` — returns whether node X can be mastered right now

3. **Evidence submission**
   - `POST /evidence/submit/{id}` — submits evidence for node X against spec Y
   - Returns acceptance result (accepted/rejected/superseded)

4. **Node state transitions**
   - `POST /nodes/{id}/start` — moves node from available to active
   - `POST /nodes/{id}/pass` — asserts pass on a node (engine‑side)
   - `POST /nodes/{id}/master` — asserts mastery on a passed node

5. **Graph structure queries**
   - `GET /nodes/{id}/prereqs` — returns prerequisites of node X
   - `GET /nodes/{id}/unlocks` — returns nodes that X unlocks
   - `GET /graph/overview` — returns overview of the full graph (81 nodes, 124 edges)

6. **Progress retrieval**
   - `GET /progress/{id}` — returns current state for node X
   - `GET /progress/available` — returns all nodes available to start

7. **Resource listing**
   - `GET /resources/{id}` — returns resources supporting node X
   - `GET /resources/verified` — returns all verified resources

8. **Event retrieval**
   - `GET /events/{id}` — returns events for node X (audit trail)

**Decision Needed:** Finalize the API surface specification (endpoints, methods, request/response formats). This will define what the web app developers need to implement.

**Dependencies:**
- T1 (interface type — determines which engine mechanics are exposed via which protocol)
- T2 (original research elements — some may require additional API endpoints)
- Synthesis research document (this file — provides context on what the engine already does)

**Labels:** decision, api, priority-high