-- =============================================================================
-- CM KERALA – CHIEF MINISTER'S PUBLIC GRIEVANCE REDRESSAL PORTAL
-- Database Schema & Initial Data
-- Database: cm_kerala_portal
-- Compatible with MySQL 8.0+
-- =============================================================================

CREATE DATABASE IF NOT EXISTS cm_kerala_portal
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE cm_kerala_portal;

-- -----------------------------------------------------------------------------
-- 1. DEPARTMENTS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 2. USERS TABLE
-- Roles: 'citizen', 'admin' (CMO), 'officer' (Department Officer)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    mobile VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('citizen', 'admin', 'officer') NOT NULL DEFAULT 'citizen',
    department_id INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_department
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_users_role (role),
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 3. GRIEVANCES TABLE
-- Exact 5 Statuses: 'Submitted', 'Under Review', 'In Progress', 'Resolved', 'Reopened'
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS grievances (
    grievance_id INT AUTO_INCREMENT PRIMARY KEY,
    reference_number VARCHAR(32) NOT NULL UNIQUE,
    citizen_id INT NOT NULL,
    district VARCHAR(80) NOT NULL,
    category VARCHAR(100) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    priority ENUM('Low', 'Medium', 'High') NOT NULL DEFAULT 'Medium',
    status ENUM('Submitted', 'Under Review', 'In Progress', 'Resolved', 'Reopened') NOT NULL DEFAULT 'Submitted',
    assigned_department INT NULL,
    ai_summary TEXT NULL,
    ai_suggested_department VARCHAR(150) NULL,
    ai_suggested_category VARCHAR(100) NULL,
    ai_suggested_priority VARCHAR(20) NULL,
    cmo_remarks TEXT NULL,
    action_taken_report TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_grievances_citizen
        FOREIGN KEY (citizen_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_grievances_department
        FOREIGN KEY (assigned_department) REFERENCES departments(department_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_grievances_ref (reference_number),
    INDEX idx_grievances_status (status),
    INDEX idx_grievances_district (district),
    INDEX idx_grievances_category (category),
    INDEX idx_grievances_dept (assigned_department)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 4. GRIEVANCE HISTORY TABLE
-- Logs every transition with previous/new status, actor and remarks
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS grievance_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    grievance_id INT NOT NULL,
    previous_status VARCHAR(50) NULL,
    new_status VARCHAR(50) NOT NULL,
    changed_by INT NOT NULL,
    remarks TEXT,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_history_grievance
        FOREIGN KEY (grievance_id) REFERENCES grievances(grievance_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_history_user
        FOREIGN KEY (changed_by) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_history_grievance (grievance_id),
    INDEX idx_history_changed_at (changed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 5. DEPARTMENT ASSIGNMENTS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS department_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    grievance_id INT NOT NULL,
    department_id INT NOT NULL,
    officer_id INT NULL,
    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_assignments_grievance
        FOREIGN KEY (grievance_id) REFERENCES grievances(grievance_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_assignments_department
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_assignments_officer
        FOREIGN KEY (officer_id) REFERENCES users(user_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_assignments_grievance (grievance_id),
    INDEX idx_assignments_department (department_id),
    INDEX idx_assignments_officer (officer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 6. ATTACHMENTS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS attachments (
    attachment_id INT AUTO_INCREMENT PRIMARY KEY,
    grievance_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_attachments_grievance
        FOREIGN KEY (grievance_id) REFERENCES grievances(grievance_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_attachments_grievance (grievance_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 7. FEEDBACK TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    grievance_id INT NOT NULL,
    citizen_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comments TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_feedback_grievance
        FOREIGN KEY (grievance_id) REFERENCES grievances(grievance_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_feedback_citizen
        FOREIGN KEY (citizen_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_feedback_grievance (grievance_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- 8. CONTACT ENQUIRIES TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contact_enquiries (
    enquiry_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_enquiries_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- SAMPLE DEPARTMENTS SEED DATA
-- -----------------------------------------------------------------------------
INSERT INTO departments (department_id, department_name, description) VALUES
(1, 'Public Works Department (PWD)', 'Responsible for state highway maintenance, bridges, public roads, and structural safety.'),
(2, 'Health & Family Welfare Department', 'Oversees public healthcare institutions, hospitals, clinical quality, and public health welfare.'),
(3, 'General Education Department', 'Manages primary and secondary schooling, educational facilities, curriculum, and teacher staffing.'),
(4, 'Local Self Government Department (LSGD)', 'Administers Grama Panchayats, Municipalities, Corporations, waste management, and local sanitation.'),
(5, 'Water Resources Department', 'Supervises potable drinking water supply, Kerala Water Authority pipelines, and irrigation systems.'),
(6, 'Electricity Department (KSEB)', 'Governs power supply, transmission line maintenance, electrical hazards, and transformer upkeep.'),
(7, 'Revenue & Disaster Management', 'Handles land records, title deeds, village administration, tax collection, and natural disaster relief.'),
(8, 'Civil Supplies & Consumer Affairs', 'Administers the Public Distribution System (PDS), ration cards, and consumer protection services.')
ON DUPLICATE KEY UPDATE department_name=VALUES(department_name), description=VALUES(description);
