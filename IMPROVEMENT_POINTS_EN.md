# Improvement Points for the Hackathon Documents

## Executive Summary

The current documents are useful as an internal planning base, but they are not yet strong enough to function as a convincing final hackathon submission. The project direction is promising, but the scope remains too broad and the product definition is still unclear. At this stage, the materials read more like brainstorming notes than a focused, implementable solution.

The main issue is that the current documents describe a broad set of agricultural information services instead of a clear, user-centered product with a concrete workflow, target user, and risk-aware AI behavior. To maximize evaluation scores, the project should be narrowed into a specific use case that is easy to demo and clearly connected to the hackathon criteria.

---

## 1. Current Documents Are Too Broad

The current ideation document attempts to cover several major areas at once:
- weather-based task guidance
- crop growth recommendations
- price trend information
- subsidy matching
- pest and disease risk alerts

This makes the product feel like a general agricultural dashboard rather than a focused application. In a hackathon setting, a broad feature set lowers clarity and makes implementation riskier within a limited time window.

### Recommended Improvement

Reduce the project scope to one primary user flow, such as:
- a beginner farmer checking "what should I do this week?"
- a farmer comparing crop task priorities based on local weather and growth stage
- a mobile-first advisory assistant for key crop management tasks

The app should focus on one core workflow and keep the rest as optional features or future expansions.

---

## 2. The Target User Is Still Too General

The current description mentions "beginner farmers" in general, but does not specify a concrete user profile. A stronger product definition needs a more precise target, such as:
- 1- to 2-year small-scale farmers in Cheongdo
- beginners growing a specific crop, such as chili, cabbage, or fruit trees
- farmers managing limited land and uncertain crop schedules

Without a specific target user, it is difficult to prove real value and to justify product design decisions.

### Recommended Improvement

Define a narrow persona such as:
"A small-scale beginner farmer in Cheongdo who wants a simple weekly guide for what to do in the field, without needing to search multiple sources of weather, crop, and local government information."

This persona should guide all design and implementation choices.

---

## 3. The Product Is Not Yet Concretely Defined

The current documents describe ideas and features, but they do not yet describe a complete user journey. A clearer product definition should explain:
- who the user is
- what problem they face
- what they do in the app
- what they see on the first screen
- how the AI assistant supports them
- what the app does not claim or guarantee

At the moment, the project is still at the idea stage rather than the product stage.

### Recommended Improvement

Add a short product story such as:
"A farmer opens the app, selects crop type and growth stage, reviews the weekly task list powered by local weather and crop guidance, asks a question about what to do next, and receives a recommendation with sources and uncertainty warnings."

This makes the solution much easier to understand and demo.

---

## 4. The AI Strategy Needs to Be More Specific

The current materials mention Copilot SDK and Microsoft Agent Framework, but the actual implementation logic is still too abstract. For evaluation, it is not enough to simply say that the app uses AI. The documentation should clearly explain:
- how the user question is routed
- what tools the agent uses
- how data is retrieved
- how results are summarized
- how uncertainty is handled

### Recommended Improvement

Explain the agent pipeline in concrete terms:
1. User asks a question such as "What should I do this week?"
2. The app identifies crop type and growth stage
3. The agent fetches weather and crop guidance data
4. Optional tools retrieve price or subsidy data
5. The agent combines relevant evidence and returns a recommendation with source links and caveats
6. If data is missing or uncertain, the app explicitly states that the information is incomplete

This is much more convincing than saying the app uses a generic AI assistant.

---

## 5. The Documents Still Read Like Internal Notes, Not Submission-Ready Materials

The material is understandable, but it still lacks the structure of a high-quality hackathon submission. A strong submission should clearly separate:
- problem definition
- target user
- product experience
- feature prioritization
- technical architecture
- evaluation relevance

The current structure mixes planning notes with product ideas, which weakens the pitch.

### Recommended Improvement

Restructure the documents into:
- agent.md: internal working guide and rules
- ideation.md: product concept and strategic direction
- PRD.md: problem, user, features, and success criteria
- TRD.md: architecture, tools, deployment, and technical design

This separation will improve readability, focus, and final submission quality.

---

## 6. The Scope Should Be Reduced to a Realistic MVP

The current idea includes too many functional elements at once. A better hackathon approach is to define a realistic MVP with a clear value proposition and an easy demonstration flow.

### Recommended Improvement

Prioritize the following MVP:
- select crop and growth stage
- view this week's recommended work items
- read reasoning with source and date metadata
- ask a natural-language question about crop tasks
- see uncertainty and data limitations clearly

Then add optional secondary features like:
- price trend view
- subsidy recommendation
- disease risk alerts

Only after the core flow works well.

---

## 7. Trust and Safety Are Not Strong Enough

The project mentions AI recommendations and public data, but the documents do not yet sufficiently discuss reliability and responsible usage. This is especially important in agriculture, where incorrect advice may lead to real-world mistakes.

### Recommended Improvement

Add explicit reliability rules such as:
- never present a recommendation as a definitive crop treatment or yield guarantee
- show the source of each recommendation
- include the data timestamp
- indicate when information is not verified or not available
- clearly distinguish between advice and factual evidence
- avoid making claims beyond supported evidence

This is essential for both trustworthiness and hackathon evaluation.

---

## 8. The Business and User Value Need to Be More Explicit

The ideas are directionally good, but the value proposition is still not strong enough. The product should answer clearly: why does this matter to the user, and what productivity improvement does it create?

### Recommended Improvement

Write a short value statement such as:
"The app helps beginner farmers reduce the time spent searching across weather, crop guidance, and local information sources by providing one clear weekly action plan based on their crop and location."

This connects the app to a concrete productivity gain, which matches the evaluation criteria.

---

## 9. The Evaluation Criteria Should Be Reflected More Directly

The documents broadly mention the evaluation categories, but they do not clearly tie each feature to the actual scoring rubric. This should be addressed in the ideation or PRD stage.

### Recommended Improvement

Map each major feature to the relevant evaluation dimension:
- Copilot SDK + Agent Framework usage -> core AI integration
- workflow clarity -> UX and user value
- real data and source transparency -> trust and reliability
- Azure deployment -> cloud integration
- public demo without login -> usability and judging feasibility

This would show that the project is designed for the actual judging rubric, not just for general usefulness.

---

## 10. The Documents Need a Stronger Final Product Positioning

At the moment, the project is still described as a collection of useful ideas. To be persuasive, the project should have a strong product positioning statement.

### Recommended Improvement

Use a positioning sentence like:
"A mobile-first AI farming assistant for beginner farmers in Cheongdo that turns scattered weather, crop, subsidy, and market information into a single weekly action plan with transparent evidence and safe recommendations."

This is more crisp, concrete, and submission-ready than listing multiple vague features.

---

## Suggested Next Actions

1. Narrow the product to one main user flow and one main problem.
2. Define a concrete farmer persona and local crop scenario.
3. Rewrite the ideation document as a focused product concept, not a feature dump.
4. Prepare PRD.md with problem, user journey, MVP scope, and success criteria.
5. Prepare TRD.md with agent architecture, tool orchestration, Azure architecture, and risk handling.
6. Keep the internal agent.md as a working note, but separate it from the public submission material.
7. Ensure all claims are evidence-based and traceable to sources.

---

## Final Recommendation

The project has a promising direction, but the current documents need to become narrower, clearer, and more product-oriented. The best next step is to keep the broad research and rules in agent.md, while converting ideation.md into a more precise problem-solution statement focused on one believable, implementable AI agriculture assistant use case.

Once that is done, the content will be much closer to a strong hackathon submission and will be easier to evolve into PRD.md and TRD.md.

---

## NEWLY ADDED: Additional Improvement Points for the Revised ideation.md

The revised ideation.md successfully narrows the scope to "이번 주 농사" (weekly farm tasks) and establishes clearer boundaries on MVP scope and data reliability. However, several new issues have emerged that require attention before the next phase:

### 1. The "Weekly" Timeframe Is Not Precisely Defined

The concept centers on "this week's tasks," but the document does not clarify what defines "this week" or how updates are triggered.

**Issues:**
- Is "this week" the current calendar week (Mon-Sun)?
- Does the app show Monday-Sunday or seven days from today?
- How often does the task list refresh (daily, on open)?
- How does the app handle the boundary between "this week's" old data and next week's upcoming tasks?

**Recommended Improvement:**
- Define "this week" precisely: "the 7-day period starting from today (Monday if today is Monday, Tuesday if today is Tuesday, etc.)"
- Specify refresh logic: "tasks are recalculated on app open and hourly if left open"
- Show a clear date range on the UI (e.g., "Nov 3 - Nov 9") so users understand what period is being displayed

### 2. The Specific Crop Is Still Undecided

The document correctly states that the crop must be chosen after verifying data availability, but this leaves the demo in a precarious state.

**Issues:**
- Without a specific crop, TRD.md cannot be written (no concrete data source examples)
- The demo cannot be prepared until the crop is confirmed
- Testing the agent's tool orchestration requires real (or realistic mock) crop data
- The team cannot validate Copilot SDK and Agent Framework integration without knowing what tools will be needed

**Recommended Improvement:**
- Identify 2-3 candidate crops immediately (e.g., chili, cabbage, persimmon—common Cheongdo crops)
- For each candidate, document:
  - A reliable public source for crop stage guidance (with URL, terms of use, update frequency)
  - A weather data source usable for that crop region (API, access method, refresh cycle)
  - Any known data quality or availability constraints
- Complete this "crop research" by the next planning meeting so TRD.md can be started
- If no suitable crop data is found, simplify to a generic/mock crop for the hackathon demo and note this as a limitation in the submission

### 3. The Agent's Tool Set and Orchestration Logic Is Still Too Vague

The document mentions "weather tool" and "crop guidance tool," but does not specify their actual input/output contracts or orchestration rules.

**Issues:**
- "Tool selection" (step 2 of the agent flow) is not concrete—what criteria drive the choice?
- Input validation is not described—what happens if the user asks about an unsupported crop?
- Error handling is not clear—what does the agent return if weather data is unavailable?
- Response structure is not defined—how should the model format its output for the frontend?

**Recommended Improvement:**
- Define each tool's interface:
  - **Tool: FetchCropTasks**
    - Input: `{ crop: string, stage: string, region: string }`
    - Output: `{ tasks: [{name, reason, stage, source_url, source_date}], error: string | null }`
  - **Tool: FetchWeather**
    - Input: `{ region: string, days: number }`
    - Output: `{ forecast: [{date, temp_min, temp_max, rain_prob}], source, updated_at, error: string | null }`
- Define the agent's routing logic as a decision tree:
  - If crop not supported → return user-friendly error with supported crops
  - If weather unavailable but crop data exists → show crop tasks with weather caveat
  - If both unavailable → prompt user to re-check inputs
- Specify the model's response format (JSON, markdown, HTML) and how the frontend consumes it

### 4. The Demo Data and UI Flow Are Not Yet Designed

The document describes user actions but not the actual screens, buttons, or data presentation.

**Issues:**
- What does the crop/stage selection look like? Dropdowns, search, radio buttons?
- How are the task cards laid out? Cards, list, timeline?
- Where does the uncertainty caveat appear? On each card, in a separate section, as a tooltip?
- How is the question/answer interface presented? Chat bubble, input field + modal, side panel?
- What happens on an empty state (no tasks for this week)?

**Recommended Improvement:**
- Create a wireframe or screenshot mockup for each screen:
  - Landing / crop selection
  - Weekly task list
  - Task detail / source view
  - Q&A interface
  - Empty state, error state, loading state
- Define the data structure for task cards (title, reason, source link, date, caution)
- Specify where uncertainty or missing data is displayed (e.g., "Data not available as of Nov 3")

### 5. The "Completion Gate" Table Is Ambitious but Not Backed by Timeline

The document correctly requires validation of crop data, weather sources, Copilot SDK, Agent Framework, and Azure deployment before shipping.

**Issues:**
- No timeline is given for these validations
- No owner is assigned (who checks Copilot SDK? Who verifies weather API access?)
- No fallback if a validation fails (e.g., if Copilot SDK doesn't work in the deployment environment)
- No plan B if a crop's data source becomes unavailable during development

**Recommended Improvement:**
- Add a timeline to the gate table:
  | Target | Validation | Owner | Deadline | Fallback |
  |---|---|---|---|---|
  | Crop data | Verify public source for 1 chosen crop | [Name] | [Date] | Use mock data for demo |
  | Weather API | Test access and refresh rate | [Name] | [Date] | Use hardcoded weather |
  | Copilot SDK | Confirm model call in [language] | [Name] | [Date] | Use direct API call instead |
  | Agent Framework | Test tool orchestration with mocks | [Name] | [Date] | Implement sequential tool calls |
  | Azure deploy | Confirm login-free public path | [Name] | [Date] | Deploy to free tier temporarily |

### 6. Error Handling and Edge Cases Are Underspecified

The document mentions reliability principles but does not define concrete error cases and responses.

**Issues:**
- What if the crop stage is entered incorrectly? Does the app suggest stages, or show an error?
- What if the weather data is 48 hours old? Is a task recommendation still shown, or deferred?
- What if the agent times out? Does the frontend wait indefinitely, or show a timeout message?
- What if a tool returns contradictory results (e.g., crop stage is "seedling" but weather is for harvest season)?

**Recommended Improvement:**
- Add an "Error Handling" section to TRD.md with specific cases:
  - Invalid crop input → "We don't have data for [crop]. Try: [list]"
  - Outdated data → "Latest data: Nov 1 (2 days old). Recommendations may not reflect current conditions."
  - Tool timeout (>5s) → "Weather service is slow. Showing task list without weather context."
  - Agent error → "Unable to answer. Try again or contact support."
  - Empty result → "No specific tasks for this stage and weather this week. Check [link] for general guidance."

### 7. The MVP Feature Set Is Clear, but the User Value Is Still Aspirational

The document claims the app "reduces time spent searching," but this is not yet proven.

**Issues:**
- No baseline measurement (how long do farmers currently spend searching?)
- No success metric (how long should the app's process take?)
- No test plan to validate the claim during the hackathon

**Recommended Improvement:**
- During user testing or team walkthrough, measure and record:
  - Time from "open app" to "see first task"
  - Time from "read task" to "understand reason + source"
  - Time from "ask question" to "see answer + uncertainty caveat"
- Compare to a baseline (e.g., searching weather + crop guide manually)
- Include a sentence in PRD.md: "Success criterion: MVP reduces task identification time from [X mins] to [Y mins]" or "MVP is faster or equally fast compared to baseline approach"

### 8. The Product Positioning Could Be Stronger

The one-line intro is good, but it does not yet highlight the differentiator.

**Current:**
"青도에서 처음 농사를 짓는 소규모 농가가 작물과 생육 단계를 선택하면, 확인된 재배 자료와 지역 날씨를 바탕으로 이번 주 점검할 일을 근거와 함께 보여주는 모바일 우선 웹 앱."

**Improved positioning (to emphasize trust and evidence):**
"For beginner farmers in Cheongdo, a mobile-first app that consolidates this week's farm tasks in one screen with transparent sources and dates—no guessing, no searching across multiple websites, no unverified advice."

This emphasizes **trust (sources, dates)**, **simplicity (one screen, no searching)**, and **responsibility (no unverified advice)** — three evaluation criteria.

---

## Summary of Newly Added Points

The revised ideation.md is much stronger in scope and responsibility. The remaining gaps are primarily:
1. **Operational** (crop choice, tool definitions, error handling)
2. **UI/UX** (screen design, data presentation)
3. **Timeline** (who validates what, by when)
4. **Measurement** (how to prove time savings)

These are all workable within the hackathon timeframe, but they must be addressed in the PRD.md and TRD.md phases. The next step is not to improve ideation.md further, but to move forward with concrete crop research and architectural work.
