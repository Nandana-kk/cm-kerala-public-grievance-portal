/**
 * CM KERALA – CHIEF MINISTER'S PUBLIC GRIEVANCE REDRESSAL PORTAL
 * Frontend JavaScript: AI Assistant, Chart.js Visualization, Form Validations
 */

document.addEventListener("DOMContentLoaded", function () {
    // -------------------------------------------------------------------------
    // 1. AI GRIEVANCE ASSISTANT (Citizen Submission Page)
    // -------------------------------------------------------------------------
    const analyzeBtn = document.getElementById("btn-analyze-ai");
    const descInput = document.getElementById("description");
    const districtInput = document.getElementById("district");
    const aiContainer = document.getElementById("ai-analysis-container");
    const aiSpinner = document.getElementById("ai-spinner");
    const aiResults = document.getElementById("ai-results");
    const aiError = document.getElementById("ai-error");

    if (analyzeBtn && descInput) {
        analyzeBtn.addEventListener("click", function () {
            const description = descInput.value.trim();
            const district = districtInput ? districtInput.value.trim() : "";

            if (!description || description.length < 15) {
                alert("Please type at least 15 characters in the description box before requesting AI analysis.");
                descInput.focus();
                return;
            }

            // Show loading state
            if (aiContainer) aiContainer.classList.remove("d-none");
            if (aiSpinner) aiSpinner.classList.remove("d-none");
            if (aiResults) aiResults.classList.add("d-none");
            if (aiError) aiError.classList.add("d-none");
            analyzeBtn.disabled = true;
            analyzeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Analyzing with Gemini AI...';

            fetch("/api/ai/analyze-grievance", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    description: description,
                    district: district
                })
            })
            .then(response => response.json())
            .then(data => {
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = '<i class="bi bi-robot me-1"></i> Re-Analyze with AI';
                if (aiSpinner) aiSpinner.classList.add("d-none");

                if (data.success && data.analysis) {
                    const an = data.analysis;
                    if (aiResults) aiResults.classList.remove("d-none");

                    // Populate UI
                    document.getElementById("ai-suggested-dept").textContent = an.suggested_department || "Not determined";
                    document.getElementById("ai-suggested-cat").textContent = an.suggested_category || "General";
                    document.getElementById("ai-suggested-priority").textContent = an.priority || "Medium";
                    document.getElementById("ai-summary-text").textContent = an.summary || "Summary generated.";
                    document.getElementById("ai-reason-text").textContent = an.reason || "Recommendation based on complaint text analysis.";
                    
                    const sourceTag = document.getElementById("ai-source-badge");
                    if (sourceTag) {
                        sourceTag.textContent = data.ai_source || "AI Assistant";
                        if (data.is_live_ai) {
                            sourceTag.className = "badge bg-success";
                        } else {
                            sourceTag.className = "badge bg-warning text-dark";
                        }
                    }

                    // Duplicate warning alert
                    const dupAlert = document.getElementById("ai-duplicate-warning");
                    if (dupAlert) {
                        if (an.possible_duplicate_warning) {
                            dupAlert.textContent = "Duplicate Alert: " + an.possible_duplicate_warning;
                            dupAlert.classList.remove("d-none");
                        } else {
                            dupAlert.classList.add("d-none");
                        }
                    }

                    // Set hidden form fields for submission
                    const hSummary = document.getElementById("hidden_ai_summary");
                    const hDept = document.getElementById("hidden_ai_dept");
                    const hCat = document.getElementById("hidden_ai_cat");
                    const hPri = document.getElementById("hidden_ai_priority");

                    if (hSummary) hSummary.value = an.summary || "";
                    if (hDept) hDept.value = an.suggested_department || "";
                    if (hCat) hCat.value = an.suggested_category || "";
                    if (hPri) hPri.value = an.priority || "Medium";

                    // Handle "Apply Suggestions" button
                    const applyBtn = document.getElementById("btn-apply-ai");
                    if (applyBtn) {
                        applyBtn.onclick = function () {
                            // Apply priority
                            const priSelect = document.getElementById("priority");
                            if (priSelect && an.priority) {
                                priSelect.value = an.priority;
                            }
                            // Apply category
                            const catSelect = document.getElementById("category");
                            if (catSelect && an.suggested_category) {
                                for (let opt of catSelect.options) {
                                    if (opt.text.toLowerCase().includes(an.suggested_category.toLowerCase())) {
                                        catSelect.value = opt.value;
                                        break;
                                    }
                                }
                            }
                            // Apply department
                            const deptSelect = document.getElementById("department_id");
                            if (deptSelect && an.suggested_department) {
                                for (let opt of deptSelect.options) {
                                    if (opt.text.toLowerCase().includes(an.suggested_department.toLowerCase())) {
                                        deptSelect.value = opt.value;
                                        break;
                                    }
                                }
                            }
                            alert("AI suggestions applied to the form!");
                        };
                    }
                } else {
                    if (aiError) {
                        aiError.textContent = data.error || "Unable to complete AI analysis.";
                        aiError.classList.remove("d-none");
                    }
                }
            })
            .catch(err => {
                analyzeBtn.disabled = false;
                analyzeBtn.innerHTML = '<i class="bi bi-robot me-1"></i> Analyze with AI Assistant';
                if (aiSpinner) aiSpinner.classList.add("d-none");
                if (aiError) {
                    aiError.textContent = "Network or server error while contacting AI Assistant: " + err.message;
                    aiError.classList.remove("d-none");
                }
            });
        });
    }

    // -------------------------------------------------------------------------
    // 2. CHART.JS VISUALIZATION (CMO Admin Dashboard)
    // -------------------------------------------------------------------------
    const statusChartCanvas = document.getElementById("chart-status");
    const districtChartCanvas = document.getElementById("chart-district");
    const deptChartCanvas = document.getElementById("chart-department");

    if (statusChartCanvas || districtChartCanvas || deptChartCanvas) {
        fetch("/admin/api/chart-stats")
            .then(res => res.json())
            .then(chartData => {
                // Status Chart (Doughnut)
                if (statusChartCanvas && chartData.status) {
                    new Chart(statusChartCanvas, {
                        type: "doughnut",
                        data: {
                            labels: chartData.status.labels,
                            datasets: [{
                                data: chartData.status.data,
                                backgroundColor: [
                                    "#2563eb", // Submitted - Blue
                                    "#d97706", // Under Review - Amber
                                    "#0891b2", // In Progress - Cyan
                                    "#16a34a", // Resolved - Green
                                    "#9333ea"  // Reopened - Purple
                                ],
                                borderWidth: 2,
                                borderColor: "#ffffff"
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                legend: { position: "bottom" }
                            }
                        }
                    });
                }

                // District Chart (Bar)
                if (districtChartCanvas && chartData.districts) {
                    new Chart(districtChartCanvas, {
                        type: "bar",
                        data: {
                            labels: chartData.districts.labels,
                            datasets: [{
                                label: "Grievances Count",
                                data: chartData.districts.data,
                                backgroundColor: "#0d5c3a",
                                borderRadius: 4
                            }]
                        },
                        options: {
                            responsive: true,
                            scales: {
                                y: { beginAtZero: true, ticks: { precision: 0 } }
                            },
                            plugins: {
                                legend: { display: false }
                            }
                        }
                    });
                }

                // Department Chart (Horizontal Bar)
                if (deptChartCanvas && chartData.departments) {
                    new Chart(deptChartCanvas, {
                        type: "bar",
                        data: {
                            labels: chartData.departments.labels.map(l => l.length > 25 ? l.substring(0, 25) + "..." : l),
                            datasets: [{
                                label: "Complaints Forwarded",
                                data: chartData.departments.data,
                                backgroundColor: "#13293d",
                                borderRadius: 4
                            }]
                        },
                        options: {
                            indexAxis: 'y',
                            responsive: true,
                            scales: {
                                x: { beginAtZero: true, ticks: { precision: 0 } }
                            },
                            plugins: {
                                legend: { display: false }
                            }
                        }
                    });
                }
            })
            .catch(err => {
                console.warn("Could not load chart data: ", err);
            });
    }

    // -------------------------------------------------------------------------
    // 3. AUTO-DISMISS ALERTS AFTER 5 SECONDS
    // -------------------------------------------------------------------------
    const alerts = document.querySelectorAll(".alert:not(.alert-permanent)");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 6000);
    });
});
