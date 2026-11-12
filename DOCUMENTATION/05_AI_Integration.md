# 05. AI Grievance Assistant Integration

## CM KERALA – Chief Minister's Public Grievance Redressal Portal

---

## 1. Overview & Model Selection
The portal incorporates an AI Grievance Assistant powered by the Google Gemini API.  
- **Official Python SDK:** `google-genai` (Version &ge; 0.1.0)
- **Official Model:** `gemini-2.5-flash`
- **Environment Configuration:** API key stored strictly on the backend via `GEMINI_API_KEY` in `.env` (never exposed to frontend JavaScript).

---

## 2. AI Capabilities & Objectives
When a citizen enters a grievance narrative, the AI Grievance Assistant performs five key tasks:
1. **Semantic Text Analysis:** Evaluates the context, location, duration, and urgency of the public complaint.
2. **Department Recommendation:** Matches the problem with one of the participating Kerala government departments retrieved dynamically from MySQL (`departments` table).
3. **Category Suggestion:** Generates a concise category description (e.g., *Road Maintenance*, *Water Supply*, *Healthcare Services*).
4. **Priority Assessment:** Recommends a priority level (`Low`, `Medium`, or `High`) based on public health risk, safety hazard, or emergency severity.
5. **Executive Summary Generation:** Produces a 1-2 sentence executive briefing for the Chief Minister's Office review desk.
6. **Duplicate Case Detection:** Inspects existing recent complaints in the same district to flag potential duplicate submissions for human review.

---

## 3. Prompt Design & System Instructions
The integration uses structured prompting with system instructions and JSON mode (`response_mime_type="application/json"`):

### System Instruction:
```text
You are the AI Grievance Assistant for the Chief Minister's Public Grievance Redressal Portal, 
Government of Kerala. Analyze the citizen's complaint objectively. 
Return a strictly valid JSON object. Do not include markdown code blocks or extra text.

Available Kerala Government Departments:
- Public Works Department (PWD)
- Health & Family Welfare Department
- General Education Department
- Local Self Government Department (LSGD)
- Water Resources Department
- Electricity Department (KSEB)
- Revenue & Disaster Management
- Civil Supplies & Consumer Affairs

Recent existing cases in the area: [JSON list of recent grievances in the same district]
```

### Analysis Prompt:
```text
Analyze the following citizen grievance description:

District: {district}
Complaint Description:
"""{description}"""

Generate a valid JSON object with the following fields:
{
  "suggested_department": "Exact name of the most appropriate department from the available list",
  "suggested_category": "A concise 2-4 word category",
  "priority": "Low", "Medium", or "High",
  "summary": "A concise 1-2 sentence executive summary for the Chief Minister's Office review",
  "reason": "Clear explanation of why this department, category, and priority level were recommended",
  "possible_duplicate_warning": "Warning note if complaint appears similar to any recent existing cases, otherwise null"
}
```

---

## 4. Example AI Response (JSON)
```json
{
  "suggested_department": "Water Resources Department",
  "suggested_category": "Drinking Water Supply",
  "priority": "High",
  "summary": "Main transmission pipeline rupture near Mavoor junction causing potable water wastage and low pressure in 400 homes.",
  "reason": "Municipal water pipeline infrastructure and drinking water supply are under the direct jurisdiction of Kerala Water Authority (Water Resources Dept). High priority assigned due to public water disruption.",
  "possible_duplicate_warning": null
}
```

---

## 5. Human-in-the-Loop Safeguards & Limitations

### Crucial Safeguards:
1. **No Autonomous Official Decisions:** AI suggestions are purely advisory decision-support aids. AI does not autonomously assign departments or close grievances.
2. **Citizen Review Before Submission:** The citizen inspects the AI suggestions and can choose whether to click *"Apply Suggestions"* or manually select their preferred department and priority.
3. **CMO Administrative Authority:** The final department routing and priority assignment remain under the authority of authorized CMO administrators.
4. **Audit Trail Transparency:** The AI summary and recommendations are permanently stored in the `grievances` record, allowing administrators to audit what the AI suggested versus what was assigned.

---

## 6. Labeled Fallback Mechanism
As required by the assignment guidelines:
- If `GEMINI_API_KEY` is not configured, or if an unexpected network or API outage occurs, the system smoothly falls back to a transparent, clearly-labeled deterministic classifier.
- The UI explicitly displays:
  - When live AI is active: `<span class="badge bg-success">Google Gemini 2.5 Flash</span>`
  - When fallback is active: `<span class="badge bg-warning text-dark">Deterministic Classifier Fallback (GEMINI_API_KEY not configured)</span>`
- The system never pretends a keyword fallback is genuine AI.
