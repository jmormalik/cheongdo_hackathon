# PRD Improvement Recommendations

This document reviews the root-level `PRD.md` and identifies what should still be improved before final submission. The root PRD is already much stronger than the earlier working draft because it includes clearer scope boundaries, evidence-based requirements, and explicit risk/validation language. The remaining improvements below focus on final submission quality, not broad rework.

---

## 1. What is already strong

The current root PRD already does a good job in the following areas:

- Clear P0/P1 separation
- Evidence-based guidance requirement
- Explicit rejection of fabricated or unsupported recommendations
- Data status transparency for demo and real-data cases
- Good focus on public Azure access and no-login use
- Realistic expectation that source verification is required before claiming a crop or dataset is supported

These are well-aligned with hackathon scoring and reduce the chance of a vague or over-claimed submission.

---

## 2. Main remaining improvements

### 2.1 Make SDK/Framework usage more operationally explicit

The PRD states that GitHub Copilot SDK and Microsoft Agent Framework must be used, but it would be stronger if it included a short implementation contract for the live request path.

Recommended addition:

- user question arrives in backend
- framework chooses the relevant tool
- tool executes against verified agricultural data or local retrieval layer
- tool returns structured results with status and source metadata
- SDK generates the final answer grounded in those results
- UI renders the answer plus source links and timestamps

This should be kept short, because the root PRD is already strategic rather than implementation-detailed.

### 2.2 Clarify the difference between demo fixtures and real data

The PRD already states that unverified crops must use fixture data with clear labeling, which is good. The improvement is to make the boundary even more explicit:

- fixture data may be used only for development and demonstration
- fixture data must never appear as a final recommendation from verified sources
- the UI must show the same label every time: `Demo example data — not real-time information`
- fixture use must be clearly isolated from the actual source-backed flow

This reduces risk of misinterpretation by judges.

### 2.3 Strengthen the acceptance criteria for tool calls

The current requirement says the tool call and model response should happen, but the acceptance guidance can be sharper.

Suggested wording:

> The final deployed app must show a real tool invocation path in the live request flow, not a mock or hard-coded response. The response must include evidence metadata and must fail visibly when no valid evidence exists.

This is a key validation condition and reduces the chance of an empty or superficial demo.

### 2.4 Add a concrete fallback policy for data and model failures

The PRD already says failures must be shown clearly, but it could be improved by explicitly defining the fallback states.

Recommended states:

- success
- partial success
- no relevant data
- stale or expired data
- unsupported crop/stage/region
- tool failure
- model failure

For each state, the UI should show a clear action: retry, switch crop, narrow range, or acknowledge that no valid advice is available.

### 2.5 Clarify how streaming is handled

The PRD mentions streaming as a validation gate, which is appropriate. The remaining improvement is to specify that streaming is optional only when the selected SDK/model supports it.

Recommended wording:

> If streaming is supported by the selected SDK/model combination, partial results may be shown during generation, but they must not be presented as final guidance. If streaming is unsupported, the app must use a normal loading state and final response only.

This keeps the PRD truthful without overcommitting.

---

## 3. Improvements to specific sections

### Section 1: Overview

The overview is already solid, but it could be tightened by emphasizing the product is a decision-support assistant, not a general agricultural advisor.

Suggested addition:

- It helps users decide what to check this week.
- It explains why the task matters and what source supports it.
- It does not replace expert advice, diagnose diseases, or promise yield outcomes.

### Section 4: Goals and success measurement

This section is already good, but it would benefit from a stronger note that no performance claims should be made without measured evidence.

Suggested addition:

> Productivity claims must be treated as hypotheses until a real user test is performed. Until then, the product may report usability and workflow clarity, but must not claim time savings or productivity gains without data.

### Section 6: Functional requirements

The functional requirements are strong overall. The remaining improvement is to sharpen the verification phrase in FR-004 and FR-005.

Suggested revision:

- `FR-004`: responses must be grounded in actual tool output and source metadata
- `FR-005`: failure states must be visible and understandable to the user, not hidden behind generic errors

### Section 8: Release and evaluation

This is a very good section. It could be slightly improved by explicitly adding a final deployment check:

> verify the public Azure URL directly in a fresh browser session, confirm no login is required, confirm the app opens without any special configuration, and confirm that the public URL matches the allowed domain format.

This makes the gate more operational and less abstract.

---

## 4. Recommended additions

These are small but valuable additions to the root PRD and should be kept brief.

### 4.1 Short architecture note

A 5-7 line architecture note is enough:

- frontend collects user inputs
- backend routes requests to agent tools
- agent framework orchestrates tool usage
- Copilot SDK handles model generation grounded in tool output
- UI displays evidence and failure state

This makes the document easier for judges and reviewers to understand.

### 4.2 Short source-verification checklist

Add a checklist after the data gate:

- official source URL confirmed
- source date or update cadence confirmed
- stage coverage confirmed
- region applicability confirmed
- terms of use reviewed
- sample output checked in a live call

This reduces the chance of local assumptions being mistaken for verified evidence.

### 4.3 Short stream/fallback rule

Add one sentence under the technical gate:

> The app must not claim streaming support unless it is verified in the selected SDK/model environment. If unsupported, the app must use a standard loading state and final answer mode.

This keeps the PRD honest and aligned with real deployment validation.

---

## 5. Items to keep as-is

The following parts should not be changed unless there is a critical timing issue:

- P0/P1 scoping
- rejection of unsupported or invented advice
- requirement for public no-login access
- requirement for visible evidence metadata
- no-claim policy for performance improvements without testing
- use of fixture data only with explicit labeling

These are well-justified and already in the right direction.

---

## 6. Final recommendation

The root PRD is already close to a strong final submission document. The best next step is not a major rewrite, but a limited polish:

1. add a short live request-flow note for SDK + Agent Framework
2. tighten acceptance wording for real tool invocation and fallback states
3. clarify streaming fallback policy
4. add a final Azure public-access verification gate
5. keep all performance claims explicitly provisional until user testing is complete

This gives the PRD more submission readiness without overcomplicating it or adding speculative features.

---

## 7. Suggested final priority order

Priority 1 (must do):
- real tool invocation requirement
- explicit fallback and failure states
- Azure public URL verification condition

Priority 2 (should do):
- short architecture note
- source verification checklist
- streaming fallback rule

Priority 3 (optional polish):
- wording adjustments to reduce ambiguity
- final consistency pass for terminology

This keeps the PRD strong without drifting into unnecessary implementation detail.

---

## 8. Additional gaps discovered in full PRD review

After systematic review of the complete root PRD (lines 100-235), the following additional clarifications would strengthen the submission:

### 8.1 Fixture data labeling placement and prominence

The PRD correctly requires fixture data to be labeled "Demo example data — not real-time information", but does not specify **where** the label appears or how visibly. 

Recommended addition:

- The label must appear **above the recommendation cards**, not in footnotes or collapsed sections
- The label must use distinct visual styling (color, size, icon) so it is impossible to miss
- The label must appear on **every screen that uses fixture data**, including the weekly checklist and any pop-overs or details
- A single disclaimer buried in settings is not sufficient

This reduces risk that judges will interpret demo fixtures as real verified data.

### 8.2 Unverified crop handling strategy

The PRD lists five candidate crops (감, 단감, 미나리, 복숭아, 포도) but only the first has been "chosen" per the decisions table. The remaining four are "not verified".

Recommended clarification:

- Until a crop is verified (source URL confirmed, sample data retrieved, terms reviewed), it must not appear as a selectable option in the production app UI
- It may appear in a separate "Demo crops" section with a clear visual boundary (e.g., a "Demo" badge or grayed-out state)
- Or, only the verified crop should be selectable, and other crops should be in "coming soon" state
- This prevents users from confusing unverified fixtures with production data

The PRD currently defers this decision (see Q-001) but does not specify the UI boundary. Adding this clarification would strengthen the submission's credibility.

### 8.3 Tool error taxonomy and retry logic

FR-004 and FR-005 require clear failure messages, but the PRD does not enumerate which errors are user-recoverable vs. terminal.

Recommended taxonomy:

- **Transient (retry recommended):** tool timeout, network error, API rate limit, temporary data source outage
- **User-recoverable (change input):** unsupported crop/stage/region combination, source data doesn't cover the selected range
- **Terminal (acknowledge):** model service unavailable, tool no longer exists, data source permanently discontinued

For each category, the UI should show:
- the error code or category name
- a user-friendly message explaining why it happened
- the recommended next action (retry, change inputs, acknowledge and continue with partial data)

This reduces ambiguity about what judges should expect when errors occur.

### 8.4 Evidence-grounding feedback loop for model responses

FR-004 requires that all advice be grounded in tool output, but the PRD does not specify how the UI should **show the grounding** to the user.

Recommended pattern:

- User asks: "What should I check this week for persimmons?"
- Agent framework selects tool: `get_weekly_tasks(crop="persimmon", stage="X", date_range=...)`
- Tool returns: structured list with source URL, source date, and task description
- Model generates: "Based on the tasks for persimmons in their [stage name] at [week date range], you should [task 1], [task 2]..."
- UI renders:
  - the model's summary text
  - clickable source links inline next to each piece of advice
  - a "View sources" button that expands to show tool output (source URL, date, stage applicability)

This ensures judges can verify that the grounding actually happened and wasn't fabricated.

### 8.5 Week boundary logic and timezone handling

FR-002 specifies that the app displays the current week "Monday 00:00 to Sunday 23:59 in Asia/Seoul timezone", but does not specify **how the boundary is computed**.

Recommended clarification:

- The app must always use the current date in Asia/Seoul timezone (not server time or browser local time)
- "Current week" is the ISO week containing today's date in that timezone
- If the date rolls over during a user session (e.g., midnight), the app should refresh the display
- Weekly data queries must use the same timezone for consistency
- If a data source uses a different timezone or date format, the app must document the conversion and include the original source timestamp in the UI

This prevents issues where judges in a different timezone see different week ranges than expected.

### 8.6 Model hallucination guardrails and evidence validation

FR-004 requires that the model not fabricate sources, but the PRD does not specify **how the backend validates** model responses before returning them to the UI.

Recommended requirement:

- Before returning a model-generated response to the UI, the backend must:
  1. Parse the response to extract claimed source URLs and dates
  2. Cross-check each URL/date pair against the actual tool output
  3. If a claimed source does not appear in tool output, log the discrepancy and either remove the claim or append a visible caveat
  4. Never return a response that contains sources the tool did not provide
- The response must include a machine-readable `evidence_chain` that maps each piece of advice to its source tool output

This is a strong guardrail against model hallucination and gives judges confidence in the grounding.

### 8.7 Azure domain validation and deployment readiness

NFR-005 requires public Azure access, but does not specify what domain patterns are allowed.

Recommended explicit constraint:

- Only these Azure domain patterns are permitted:
  - `*.azurewebsites.net` (App Service)
  - `*.azurecontainerapps.io` (Container Apps)
  - `*.azurestaticapps.net` (Static Web Apps)
- Custom domains, Azure CDN endpoints, or non-Azure domains will disqualify the submission
- The deployment URL must be verified at submission time to confirm it is publicly accessible and matches one of the allowed patterns
- A URL like `my-app-2026.azurewebsites.net/app` is acceptable; `my-company.com` or `my-app.azure-edge.net` is not

This removes ambiguity and prevents last-minute deployment surprises.

### 8.8 Data freshness and source currency policy

FR-002 and FR-005 require that stale data be flagged, but the PRD does not define **what "stale" means** for each data type.

Recommended guidance:

- **Seasonal crop guidance:** source date must be within the current growing season (or the most recent prior season if off-season)
- **Weekly weather data:** source must be updated within the last 6 hours for reliability, or 24 hours for warning-only use (marked as "last updated [date]")
- **Region-specific data:** if the source date predates changes to regional agricultural policy or variety recommendations, it must be flagged as outdated
- If a source is older than one growing season, the app must not use it without explicit user confirmation that they want historical reference data

This clarifies when data should be considered unreliable and sets judges' expectations for what data freshness looks like.

### 8.9 Integration acceptance criteria with live flow traceability

Section 8's acceptance criteria state that "real tool invocation and model response" must be verifiable, but does not specify **how judges verify this**.

Recommended verification method:

- The app must provide a "Request Flow" diagnostic view (hidden or developer-only) that shows:
  - timestamp of user request
  - tool name and input parameters sent to Agent Framework
  - tool output received (raw structured data)
  - model input and generation parameters
  - model output token usage
  - final UI rendering
- OR, at minimum, the browser's Network tab must show real HTTP requests to the tool endpoint and model endpoint (not mocked, not cached)
- A judge should be able to open the browser DevTools, make a request, and see the actual tool and model calls in real time

This gives judges a clear way to audit the integration.

### 8.10 Contingency for partial feature delivery

The PRD does not explicitly address the scenario where, by submission deadline, one or more P0 features cannot be verified.

Recommended contingency wording:

- If data source verification (Q-002) is incomplete by deadline, the app may ship with fixture data only, provided all recommendations are labeled "Demo example data" and no real sources are claimed
- If streaming support (streaming fallback rule) cannot be verified, the app must ship with standard loading state and final-answer mode, and must not claim streaming support in the summary
- If one of the five crops cannot be verified, that crop must be removed from the selectable list and marked "coming soon" or "demo only"
- A contingency note should be included in the submission summary explaining which features were deferred and why

This shows the judges that the team prioritized credibility over feature count, which aligns with the PRD's values.
