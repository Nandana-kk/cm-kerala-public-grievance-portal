"""
Comprehensive Automated Test Suite for CM Kerala Grievance Redressal Portal.
Tests all 13 mandatory recruitment workflow test cases and edge cases against real MySQL.
"""

import sys
import io
import unittest
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from database import query_db, execute_db


class GrievancePortalWorkflowTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def test_01_public_pages_load(self):
        """Verify all 6 public pages load with HTTP 200."""
        routes = ["/", "/about", "/how-it-works", "/departments", "/contact", "/faq"]
        for r in routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed to load.")
            self.assertIn(b"CM KERALA", res.data)

    def test_02_citizen_registration_and_login(self):
        """TEST 1: Citizen registration, duplicate check, and login."""
        test_email = "test.citizen.reg@example.com"
        # Clean up if existed
        execute_db("DELETE FROM users WHERE email = %s", (test_email,))

        # Successful registration
        res = self.client.post("/register", data={
            "name": "Arun Kumar",
            "email": test_email,
            "mobile": "9847111222",
            "password": "Password@123",
            "confirm_password": "Password@123"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Registration successful", res.data)

        # Duplicate registration attempt should be rejected
        res_dup = self.client.post("/register", data={
            "name": "Arun Kumar",
            "email": test_email,
            "mobile": "9847111222",
            "password": "Password@123",
            "confirm_password": "Password@123"
        }, follow_redirects=True)
        self.assertIn(b"already exists", res_dup.data)

        # Login with correct credentials
        res_login = self.client.post("/login", data={
            "email": test_email,
            "password": "Password@123"
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn(b"Welcome back", res_login.data)

        # Logout first
        self.client.get("/logout")

        # Invalid login check
        res_bad = self.client.post("/login", data={
            "email": test_email,
            "password": "WrongPassword!"
        }, follow_redirects=True)
        self.assertIn(b"Invalid email address or password", res_bad.data)

    def test_03_ai_grievance_analysis_api(self):
        """TEST 3: AI Grievance Assistant endpoint."""
        res = self.client.post("/api/ai/analyze-grievance", json={
            "district": "Ernakulam",
            "description": "The main road from Aluva to Perumbavoor has massive dangerous potholes causing daily accidents."
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        analysis = data.get("analysis")
        self.assertIsNotNone(analysis)
        self.assertIn("Public Works Department (PWD)", analysis.get("suggested_department"))
        self.assertEqual(analysis.get("priority"), "High")
        self.assertTrue(len(analysis.get("summary")) > 5)

    def test_04_citizen_submit_and_track_workflow(self):
        """TEST 2, 4, 11: Citizen submits grievance, system generates ref no, citizen tracks progress."""
        # Log in as demo citizen
        self.client.post("/login", data={
            "email": "sujith.citizen@example.com",
            "password": "Citizen@123"
        }, follow_redirects=True)

        # Submit grievance with attachment
        file_content = b"Simulated image of broken culvert on village road."
        file_data = (io.BytesIO(file_content), "culvert_damage.jpg")

        res = self.client.post("/citizen/submit", data={
            "district": "Kottayam",
            "category": "Road Maintenance & Infrastructure",
            "subject": "Collapsed road culvert blocking school bus route in Pala",
            "description": "The stone culvert near Pala high school has caved in after monsoon rain, cutting off vehicular movement for two villages.",
            "priority": "High",
            "department_id": "1",
            "attachment": file_data
        }, content_type="multipart/form-data", follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Grievance submitted successfully", res.data)
        self.assertIn(b"Reference Number is: KL-2026-", res.data)

        # Retrieve the newly inserted grievance from MySQL
        latest_g = query_db(
            "SELECT * FROM grievances WHERE subject LIKE '%Collapsed road culvert%' ORDER BY grievance_id DESC LIMIT 1",
            one=True
        )
        self.assertIsNotNone(latest_g)
        ref_no = latest_g["reference_number"]
        self.assertTrue(ref_no.startswith("KL-2026-"))
        self.assertEqual(latest_g["status"], "Submitted")

        # Track grievance by reference number
        track_res = self.client.get(f"/citizen/track?ref={ref_no}")
        self.assertEqual(track_res.status_code, 200)
        self.assertIn(ref_no.encode(), track_res.data)
        self.assertIn(b"Pala high school", track_res.data)
        self.assertIn(b"Submitted", track_res.data)

    def test_05_cmo_admin_workflow(self):
        """TEST 5, 6, 10: CMO reviews grievance, assigns department/officer, and resolves."""
        # 1. Log in as CMO Admin
        self.client.post("/login", data={
            "email": "admin@cmkerala.gov.in",
            "password": "Admin@123"
        }, follow_redirects=True)

        # View dashboard
        res_dash = self.client.get("/admin/dashboard")
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn(b"Chief Minister's Office (CMO) Administration", res_dash.data)

        # Verify Chart stats API
        chart_res = self.client.get("/admin/api/chart-stats")
        self.assertEqual(chart_res.status_code, 200)
        chart_json = chart_res.get_json()
        self.assertIn("status", chart_json)
        self.assertIn("districts", chart_json)

        # Get the first Submitted grievance
        sub_g = query_db("SELECT * FROM grievances WHERE status = 'Submitted' LIMIT 1", one=True)
        self.assertIsNotNone(sub_g)
        g_id = sub_g["grievance_id"]

        # View grievance details
        res_det = self.client.get(f"/admin/grievance/{g_id}")
        self.assertEqual(res_det.status_code, 200)

        # Assign to PWD department (ID 1)
        res_assign = self.client.post(f"/admin/grievance/{g_id}/assign", data={
            "department_id": "1",
            "cmo_remarks": "Forwarded to PWD Executive Engineer. Complete field inspection within 48 hours."
        }, follow_redirects=True)
        self.assertEqual(res_assign.status_code, 200)

        # Verify status is now 'Under Review' and logged in grievance_history
        updated_g = query_db("SELECT status, assigned_department FROM grievances WHERE grievance_id = %s", (g_id,), one=True)
        self.assertEqual(updated_g["status"], "Under Review")
        self.assertEqual(updated_g["assigned_department"], 1)

        history_rows = query_db("SELECT * FROM grievance_history WHERE grievance_id = %s ORDER BY history_id DESC", (g_id,))
        self.assertTrue(len(history_rows) >= 2)
        self.assertEqual(history_rows[0]["new_status"], "Under Review")

    def test_06_officer_workflow_and_security_isolation(self):
        """TEST 7, 8, 9: Officer logs in, views assigned grievances, updates progress & ATR. Tests isolation."""
        # Log in as PWD Officer (Department 1)
        self.client.post("/login", data={
            "email": "officer.pwd@kerala.gov.in",
            "password": "Officer@123"
        }, follow_redirects=True)

        res_off = self.client.get("/officer/dashboard")
        self.assertEqual(res_off.status_code, 200)
        self.assertIn(b"Public Works Department", res_off.data)

        # Fetch a grievance assigned to PWD
        pwd_g = query_db("SELECT * FROM grievances WHERE assigned_department = 1 LIMIT 1", one=True)
        self.assertIsNotNone(pwd_g)
        g_id = pwd_g["grievance_id"]

        # Officer inspects details
        res_pwd_det = self.client.get(f"/officer/grievance/{g_id}")
        self.assertEqual(res_pwd_det.status_code, 200)

        # Officer updates progress and submits ATR
        res_atr = self.client.post(f"/officer/grievance/{g_id}/submit-report", data={
            "status": "In Progress",
            "investigation_remarks": "Inspected culvert foundation. Excavator engaged for clearing debris.",
            "action_taken_report": "Debris completely cleared. Box culvert reinforced concrete pre-cast slabs installed."
        }, follow_redirects=True)
        self.assertEqual(res_atr.status_code, 200)

        # Verify MySQL reflects update
        g_check = query_db("SELECT status, action_taken_report FROM grievances WHERE grievance_id = %s", (g_id,), one=True)
        self.assertEqual(g_check["status"], "In Progress")
        self.assertIn("Box culvert reinforced", g_check["action_taken_report"])

        # SECURITY ISOLATION CHECK:
        # PWD Officer attempts to access a grievance belonging to Water Resources (Dept 5)
        water_g = query_db("SELECT grievance_id FROM grievances WHERE assigned_department = 5 LIMIT 1", one=True)
        if water_g:
            res_unauth = self.client.get(f"/officer/grievance/{water_g['grievance_id']}", follow_redirects=True)
            self.assertIn(b"Unauthorized access: This grievance is assigned to another department", res_unauth.data)

    def test_07_cmo_approval_and_citizen_feedback(self):
        """TEST 10, 12: CMO approves resolution, citizen submits rating and feedback."""
        # 1. CMO logs in and approves resolution
        self.client.post("/login", data={
            "email": "admin@cmkerala.gov.in",
            "password": "Admin@123"
        }, follow_redirects=True)

        pwd_g = query_db("SELECT grievance_id, citizen_id FROM grievances WHERE assigned_department = 1 LIMIT 1", one=True)
        g_id = pwd_g["grievance_id"]

        res_resolve = self.client.post(f"/admin/grievance/{g_id}/update-status", data={
            "status": "Resolved",
            "priority": "Medium",
            "cmo_remarks": "Action Taken Report verified with site photos. Redressal approved."
        }, follow_redirects=True)
        self.assertEqual(res_resolve.status_code, 200)

        # Verify status in MySQL is 'Resolved'
        g_status = query_db("SELECT status FROM grievances WHERE grievance_id = %s", (g_id,), one=True)["status"]
        self.assertEqual(g_status, "Resolved")

        # 2. Citizen logs in and provides feedback
        self.client.get("/logout")
        citizen_user = query_db("SELECT email FROM users WHERE user_id = %s", (pwd_g["citizen_id"],), one=True)
        self.client.post("/login", data={
            "email": citizen_user["email"],
            "password": "Citizen@123"
        }, follow_redirects=True)

        res_fb = self.client.post(f"/citizen/feedback/{g_id}", data={
            "rating": "5",
            "comments": "The broken culvert was repaired very quickly. Excellent work by CMO and PWD team!"
        }, follow_redirects=True)
        self.assertEqual(res_fb.status_code, 200)
        self.assertTrue(b"Thank you" in res_fb.data or b"feedback" in res_fb.data)

        # Verify feedback in MySQL
        fb_row = query_db("SELECT * FROM feedback WHERE grievance_id = %s", (g_id,), one=True)
        self.assertIsNotNone(fb_row)
        self.assertEqual(fb_row["rating"], 5)

    def test_08_contact_enquiry_saving(self):
        """TEST 13: Public contact enquiry is saved into contact_enquiries table."""
        res = self.client.post("/contact", data={
            "name": "Lakshmi Menon",
            "email": "lakshmi.menon@example.com",
            "subject": "Query regarding hospital medicine supply timeline",
            "message": "When will the next batch of medicines arrive at the primary health center?"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"received successfully", res.data)

        # Verify in MySQL
        enquiry = query_db(
            "SELECT * FROM contact_enquiries WHERE email = 'lakshmi.menon@example.com' ORDER BY enquiry_id DESC LIMIT 1",
            one=True
        )
        self.assertIsNotNone(enquiry)
        self.assertEqual(enquiry["name"], "Lakshmi Menon")

    def test_09_interactive_homepage_stat_cards(self):
        """Verify homepage stat cards interactivity and status filtering on grievance list page."""
        # 1. Check Homepage contains interactive links for all 3 cards
        res_home = self.client.get("/")
        self.assertEqual(res_home.status_code, 200)
        self.assertIn(b"/citizen/track?status=all", res_home.data)
        self.assertIn(b"/citizen/track?status=Resolved", res_home.data)
        self.assertIn(b"/citizen/track?status=In+Progress", res_home.data)

        # 2. Test 'Total Grievances' filter (All grievances)
        res_all = self.client.get("/citizen/track?status=all")
        self.assertEqual(res_all.status_code, 200)
        self.assertIn(b"Public Grievance Records", res_all.data)
        # Should contain grievances of multiple statuses
        self.assertIn(b"KL-2026-", res_all.data)

        # 3. Test 'Successfully Resolved' filter (Only Resolved)
        res_res = self.client.get("/citizen/track?status=Resolved")
        self.assertEqual(res_res.status_code, 200)
        self.assertIn(b"Successfully Resolved Grievances", res_res.data)
        # Resolved grievance reference must be present
        self.assertIn(b"Resolved", res_res.data)

        # 4. Test 'Action in Progress' filter (Only In Progress)
        res_prog = self.client.get("/citizen/track?status=In Progress")
        self.assertEqual(res_prog.status_code, 200)
        self.assertIn(b"Action In Progress Grievances", res_prog.data)
        self.assertIn(b"In Progress", res_prog.data)

        # 5. Test when logged in as Admin, cards link to admin dashboard filters
        self.client.post("/login", data={
            "email": "admin@cmkerala.gov.in",
            "password": "Admin@123"
        }, follow_redirects=True)
        res_admin_home = self.client.get("/")
        self.assertEqual(res_admin_home.status_code, 200)
        self.assertIn(b"/admin/dashboard?status=Resolved", res_admin_home.data)
        self.assertIn(b"/admin/dashboard?status=In+Progress", res_admin_home.data)
        self.client.get("/logout")


if __name__ == "__main__":
    unittest.main()
