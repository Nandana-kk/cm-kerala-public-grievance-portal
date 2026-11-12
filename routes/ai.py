"""
AI Integration Route using Google Gemini API (Official Python SDK: google-genai).
Analyzes citizen grievance descriptions, suggests departments, categories, priority,
generates CMO summaries, and detects potential duplicates.
"""

import json
import logging
from flask import Blueprint, request, jsonify, session
from config import Config
from database import query_db

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")
logger = logging.getLogger(__name__)


def get_available_departments():
    """Retrieve list of active departments from MySQL."""
    try:
        rows = query_db("SELECT department_name FROM departments ORDER BY department_name")
        return [r["department_name"] for r in rows]
    except Exception as e:
        logger.error(f"Error fetching departments for AI: {e}")
        return [
            "Public Works Department (PWD)",
            "Health & Family Welfare Department",
            "General Education Department",
            "Local Self Government Department (LSGD)",
            "Water Resources Department",
            "Electricity Department (KSEB)",
            "Revenue & Disaster Management",
            "Civil Supplies & Consumer Affairs"
        ]


def get_recent_grievances_summary(district=None):
    """Retrieve recent grievances in the same district to detect potential duplicates."""
    try:
        if district:
            rows = query_db(
                "SELECT reference_number, subject, category FROM grievances WHERE district = %s ORDER BY created_at DESC LIMIT 5",
                (district,)
            )
        else:
            rows = query_db(
                "SELECT reference_number, subject, category FROM grievances ORDER BY created_at DESC LIMIT 5"
            )
        return [{"ref": r["reference_number"], "subject": r["subject"], "category": r["category"]} for r in rows]
    except Exception as e:
        logger.error(f"Error fetching recent grievances: {e}")
        return []


def analyze_with_gemini(description, district=""):
    """
    Call Google Gemini API using official google-genai Python SDK.
    Returns a dictionary of analysis or raises an exception.
    """
    from google import genai
    from google.genai import types

    api_key = Config.GEMINI_API_KEY.strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured in backend environment variables (.env).")

    client = genai.Client(api_key=api_key)
    departments = get_available_departments()
    dept_list_str = "\n".join([f"- {d}" for d in departments])
    recent_cases = get_recent_grievances_summary(district)
    recent_cases_str = json.dumps(recent_cases) if recent_cases else "None"

    system_instruction = (
        "You are the AI Grievance Assistant for the Chief Minister's Public Grievance Redressal Portal, "
        "Government of Kerala. Analyze the citizen's complaint objectively. "
        "Return a strictly valid JSON object. Do not include markdown code blocks or extra text.\n\n"
        "Available Kerala Government Departments:\n"
        f"{dept_list_str}\n\n"
        f"Recent existing cases in the area: {recent_cases_str}"
    )

    prompt = f"""
Analyze the following citizen grievance description:

District: {district or 'Not specified'}
Complaint Description:
\"\"\"{description}\"\"\"

Generate a valid JSON object with the following fields:
{{
  "suggested_department": "Exact name of the most appropriate department from the available list",
  "suggested_category": "A concise 2-4 word category (e.g., Road Maintenance, Water Supply, Hospital Staffing, Waste Management, Electricity Outage, Land Mutation)",
  "priority": "Low", "Medium", or "High" (Assess based on urgency, public safety, or emergency hazard),
  "summary": "A concise 1-2 sentence executive summary for the Chief Minister's Office review",
  "reason": "Clear explanation of why this department, category, and priority level were recommended",
  "possible_duplicate_warning": "Warning note if complaint appears similar to any recent existing cases, otherwise null"
}}
"""

    model_name = Config.GEMINI_MODEL or "gemini-2.5-flash"
    
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.2
        )
    )

    response_text = response.text.strip()
    result = json.loads(response_text)
    return result


def rule_based_fallback(description, district=""):
    """
    Transparent, clearly-labeled fallback classifier used ONLY when
    Gemini API key is not configured or network/quota error occurs.
    """
    desc_lower = description.lower()
    
    # Priority determination
    priority = "Medium"
    if any(k in desc_lower for k in ["urgent", "danger", "accident", "emergency", "fire", "death", "collapse", "severe", "critical", "burst"]):
        priority = "High"
    elif any(k in desc_lower for k in ["routine", "suggestion", "query", "minor"]):
        priority = "Low"

    # Department and category mapping
    if any(k in desc_lower for k in ["road", "pothole", "bridge", "tarring", "highway", "drainage", "construction"]):
        dept = "Public Works Department (PWD)"
        cat = "Road Maintenance & Infrastructure"
        reason = "Keywords related to roads, potholes, bridges, or highways correspond to PWD jurisdiction."
    elif any(k in desc_lower for k in ["hospital", "doctor", "medicine", "health", "clinic", "pharmacy", "nurse", "patient"]):
        dept = "Health & Family Welfare Department"
        cat = "Healthcare Services & Medicines"
        reason = "Keywords related to healthcare facilities, doctors, or medicine shortages correspond to Health Dept."
    elif any(k in desc_lower for k in ["school", "teacher", "education", "student", "class", "syllabus", "mid-day"]):
        dept = "General Education Department"
        cat = "Educational Institutions"
        reason = "Keywords related to schools, teaching, and education infrastructure correspond to General Education."
    elif any(k in desc_lower for k in ["water", "kwa", "pipe", "drinking water", "leak", "pipeline", "tap"]):
        dept = "Water Resources Department"
        cat = "Drinking Water Supply"
        reason = "Keywords related to water pipelines, drinking water supply, or leaks correspond to Water Resources Dept."
    elif any(k in desc_lower for k in ["electricity", "power", "kseb", "voltage", "current", "transformer", "wire", "pole"]):
        dept = "Electricity Department (KSEB)"
        cat = "Power Supply & Electrical Infrastructure"
        reason = "Keywords related to electricity supply, transformers, and voltage fluctuations correspond to KSEB."
    elif any(k in desc_lower for k in ["garbage", "waste", "panchayat", "municipality", "cleaning", "drain", "sewage", "street light"]):
        dept = "Local Self Government Department (LSGD)"
        cat = "Sanitation & Local Civic Amenities"
        reason = "Keywords related to local civic amenities, waste disposal, and panchayat administration correspond to LSGD."
    elif any(k in desc_lower for k in ["land", "patta", "deed", "revenue", "village office", "certificate", "tax"]):
        dept = "Revenue & Disaster Management"
        cat = "Land Records & Revenue Services"
        reason = "Keywords related to land titles, revenue offices, and certificates correspond to Revenue Dept."
    elif any(k in desc_lower for k in ["ration", "rice", "food", "dealer", "pds", "card", "grocery"]):
        dept = "Civil Supplies & Consumer Affairs"
        cat = "Public Distribution & Ration Cards"
        reason = "Keywords related to ration cards, food distribution, and fair price shops correspond to Civil Supplies."
    else:
        dept = "Local Self Government Department (LSGD)"
        cat = "General Public Grievance"
        reason = "Assigned to Local Self Government as primary local administration authority."

    # First sentence as summary
    first_sentence = description.strip().split(".")[0]
    summary = (first_sentence[:150] + "...") if len(first_sentence) > 150 else first_sentence

    return {
        "suggested_department": dept,
        "suggested_category": cat,
        "priority": priority,
        "summary": summary,
        "reason": reason,
        "possible_duplicate_warning": None
    }


@ai_bp.route("/analyze-grievance", methods=["POST"])
def analyze_grievance():
    """
    API endpoint: /api/ai/analyze-grievance
    Analyzes grievance text submitted via POST JSON.
    """
    data = request.get_json() or {}
    description = data.get("description", "").strip()
    district = data.get("district", "").strip()

    if not description:
        return jsonify({"error": "Description text is required for AI analysis."}), 400

    if len(description) < 15:
        return jsonify({"error": "Please provide at least 15 characters describing your grievance for accurate AI analysis."}), 400

    # Attempt genuine Gemini API integration
    try:
        if Config.GEMINI_API_KEY.strip():
            result = analyze_with_gemini(description, district)
            return jsonify({
                "success": True,
                "is_live_ai": True,
                "ai_source": f"Google Gemini API ({Config.GEMINI_MODEL})",
                "analysis": result
            })
        else:
            # Fallback when API key is not configured in .env
            fallback_result = rule_based_fallback(description, district)
            return jsonify({
                "success": True,
                "is_live_ai": False,
                "ai_source": "Deterministic Classifier Fallback (GEMINI_API_KEY not configured in .env)",
                "note": "To enable real-time Gemini LLM inference, configure a valid GEMINI_API_KEY in the .env file.",
                "analysis": fallback_result
            })
    except Exception as e:
        logger.warning(f"Gemini API invocation encountered an issue: {e}")
        # Return fallback with clear error message as required by guidelines
        fallback_result = rule_based_fallback(description, district)
        return jsonify({
            "success": True,
            "is_live_ai": False,
            "ai_source": "Deterministic Classifier Fallback (Gemini API unavailable)",
            "api_error": str(e),
            "note": "The system smoothly fell back to standard categorization rules to ensure uninterrupted portal operation.",
            "analysis": fallback_result
        })
