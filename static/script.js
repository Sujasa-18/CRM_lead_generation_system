const API = "http://127.0.0.1:5000";

// --- Show message ---
function showMessage(text, type) {
    const msg = document.getElementById("message");
    msg.textContent = text;
    msg.className = `message ${type}`;
    msg.style.display = "block";
    setTimeout(() => { msg.style.display = "none"; }, 3000);
}

// --- Add Lead ---
async function addLead() {
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const phone = document.getElementById("phone").value;

    if (!name || !email || !phone) {
        showMessage("Please fill in all fields!", "error");
        return;
    }

    try {
        const response = await fetch(`${API}/add-lead`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, phone })
        });

        const data = await response.json();
        if (response.ok) {
            showMessage(data.message, "success");
            document.getElementById("name").value = "";
            document.getElementById("email").value = "";
            document.getElementById("phone").value = "";
            viewLeads();
        } else {
            showMessage(data.message, "error");
        }
    } catch (err) {
        showMessage("Network error!", "error");
        console.error(err);
    }
}

// --- View Leads ---
async function viewLeads() {
    try {
        const response = await fetch(`${API}/view-leads`);
        const data = await response.json();
        renderStats(data.leads);
        renderCharts(data.leads);
        renderTable(data.leads);
    } catch (err) {
        showMessage("Failed to load leads!", "error");
        console.error(err);
    }
}

// --- Render Stats ---
function renderStats(leads) {
    document.getElementById("totalLeads").textContent = leads.length;
    document.getElementById("newLeads").textContent = leads.filter(l => l.status === "New").length;
    document.getElementById("contactedLeads").textContent = leads.filter(l => l.status === "Contacted").length;
    document.getElementById("convertedLeads").textContent = leads.filter(l => l.status === "Converted").length;
}

// --- Chart instances ---
let statusChartInstance = null;
let categoryChartInstance = null;
let churnChartInstance = null;
let priorityChartInstance = null;
let featureChartInstance = null;

// --- Render Charts ---
async function renderCharts(leads) { 

    // ── 1. Lead Status Pie Chart ───────────────────────────────────
    const statusCounts = {
        "New": leads.filter(l => l.status === "New").length,
        "Contacted": leads.filter(l => l.status === "Contacted").length,
        "Converted": leads.filter(l => l.status === "Converted").length,
        "Lost": leads.filter(l => l.status === "Lost").length
    };

    if (statusChartInstance) statusChartInstance.destroy();
    statusChartInstance = new Chart(document.getElementById("statusChart"), {
        type: "pie",
        data: {
            labels: Object.keys(statusCounts),
            datasets: [{
                data: Object.values(statusCounts),
                backgroundColor: ["#2E75B6", "#00B0F0", "#1E6B3C", "#C00000"]
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: "bottom" } }
        }
    });

    // ── 2. Category Bar Chart ──────────────────────────────────────
    const categoryCounts = {
        "Hot": leads.filter(l => l.lead_category === "Hot").length,
        "Warm": leads.filter(l => l.lead_category === "Warm").length,
        "Cold": leads.filter(l => l.lead_category === "Cold").length
    };

    if (categoryChartInstance) categoryChartInstance.destroy();
    categoryChartInstance = new Chart(document.getElementById("categoryChart"), {
        type: "bar",
        data: {
            labels: Object.keys(categoryCounts),
            datasets: [{
                label: "Leads",
                data: Object.values(categoryCounts),
                backgroundColor: ["#C00000", "#FF8C00", "#2E75B6"]
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });

    // ── 3. Churn Risk Bar Chart ────────────────────────────────────
    const churnCounts = {
        "High": leads.filter(l => l.churn_risk === "High").length,
        "Medium": leads.filter(l => l.churn_risk === "Medium").length,
        "Low": leads.filter(l => l.churn_risk === "Low").length
    };

    if (churnChartInstance) churnChartInstance.destroy();
    churnChartInstance = new Chart(document.getElementById("churnChart"), {
        type: "bar",
        data: {
            labels: Object.keys(churnCounts),
            datasets: [{
                label: "Leads",
                data: Object.values(churnCounts),
                backgroundColor: ["#C00000", "#FF8C00", "#1E6B3C"]
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });

    // ── 4. Priority Bar Chart ──────────────────────────────────────
    const priorityCounts = {
        "P1 Urgent": leads.filter(l => l.priority && l.priority.includes("1")).length,
        "P2 Follow Up": leads.filter(l => l.priority && l.priority.includes("2")).length,
        "P3 Nurture": leads.filter(l => l.priority && l.priority.includes("3")).length,
        "P4 Monitor": leads.filter(l => l.priority && l.priority.includes("4")).length,
        "P5 No Action": leads.filter(l => l.priority && l.priority.includes("5")).length
    };

    if (priorityChartInstance) priorityChartInstance.destroy();
    priorityChartInstance = new Chart(document.getElementById("priorityChart"), {
        type: "bar",
        data: {
            labels: Object.keys(priorityCounts),
            datasets: [{
                label: "Leads",
                data: Object.values(priorityCounts),
                backgroundColor: ["#C00000", "#FF8C00", "#FFD700", "#2E75B6", "#A0A0A0"]
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });

    // ── 5. Feature Importance Chart ───────────────────────────────
    const fiResponse = await fetch(`${API}/feature-importance`);
    const fiData = await fiResponse.json();

    if (featureChartInstance) featureChartInstance.destroy();
    featureChartInstance = new Chart(document.getElementById("featureChart"), {
        type: "bar",
        data: {
            labels: fiData.features,
            datasets: [{
                label: "Importance",
                data: fiData.importance,
                backgroundColor: "#2E75B6"
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true } }
        }
    });
}

// --- Render Table ---
function renderTable(leads) {
    const tbody = document.getElementById("leadsBody");
    tbody.innerHTML = "";

    leads.forEach(lead => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${lead.id}</td>
            <td>${lead.name}</td>
            <td>${lead.email}</td>
            <td>${lead.phone}</td>
            <td>
                <select class="status-dropdown">
                    <option value="New">New</option>
                    <option value="Contacted">Contacted</option>
                    <option value="Converted">Converted</option>
                    <option value="Lost">Lost</option>
                </select>
            </td>
            <td><span class="notes-text">${lead.notes || '—'}</span></td>
            <td>${lead.follow_up_date || '—'}</td>
            <td>${lead.lead_category ? `<span style="color:white; background:${lead.lead_category==='Hot'?'red':lead.lead_category==='Warm'?'orange':'steelblue'}; padding:2px 10px; border-radius:12px">${lead.lead_category}</span>` : '—'}</td>
            <td>${lead.lead_score ? `${lead.lead_score}%` : '—'}</td>
            <td>${lead.churn_risk || '—'}</td>
            <td style="white-space: nowrap">${lead.priority || '—'}</td>
            <td>
                <button class="edit-btn">✏️ Edit</button>
                <button class="delete-btn">🗑 Delete</button>
            </td>
        `;

        row.querySelector(".status-dropdown").value = lead.status || "New";
        row.querySelector(".status-dropdown").addEventListener("change", (e) => updateStatus(lead.id, e.target.value));
        row.querySelector(".edit-btn").addEventListener("click", () => openModal(lead));
        row.querySelector(".delete-btn").addEventListener("click", () => deleteLead(lead.id));

        tbody.appendChild(row);
    });
}

// --- Search Leads ---
async function searchLeads() {
    const query = document.getElementById("searchInput").value;
    let url = `${API}/search-leads?q=${encodeURIComponent(query)}`;

    const categories = ["Hot", "Warm", "Cold"];
    const priorities = ["Urgent", "Follow Up", "Nurture", "Monitor", "No Action"];

    if (categories.some(c => c.toLowerCase() === query.toLowerCase())) {
        url = `${API}/search-leads?category=${encodeURIComponent(query)}`;
    } else if (priorities.some(p => query.toLowerCase().includes(p.toLowerCase()))) {
        url = `${API}/search-leads?priority=${encodeURIComponent(query)}`;
    }

    try {
        const response = await fetch(url);
        const data = await response.json();
        renderTable(data.leads);
    } catch (err) {
        showMessage("Search failed!", "error");
        console.error(err);
    }
}

// --- Update Status ---
async function updateStatus(id, status) {
    try {
        const response = await fetch(`${API}/update-lead/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status })
        });
        const data = await response.json();
        showMessage(data.message, "success");
        viewLeads();
    } catch (err) {
        showMessage("Failed to update status!", "error");
        console.error(err);
    }
}

// --- Open Edit Modal ---
function openModal(lead) {
    document.getElementById("editId").value = lead.id;
    document.getElementById("editName").value = lead.name;
    document.getElementById("editEmail").value = lead.email;
    document.getElementById("editPhone").value = lead.phone;
    document.getElementById("editNotes").value = lead.notes || '';
    document.getElementById("editFollowUp").value = lead.follow_up_date || '';
    document.getElementById("modalOverlay").classList.add("active");
}

// --- Close Modal ---
function closeModal() {
    document.getElementById("modalOverlay").classList.remove("active");
}

// --- Save Edited Lead ---
async function saveLead() {
    const id = document.getElementById("editId").value;
    const name = document.getElementById("editName").value;
    const email = document.getElementById("editEmail").value;
    const phone = document.getElementById("editPhone").value;
    const notes = document.getElementById("editNotes").value;
    const follow_up_date = document.getElementById("editFollowUp").value;

    try {
        const response = await fetch(`${API}/update-lead/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, phone, notes, follow_up_date })
        });
        const data = await response.json();
        showMessage(data.message, "success");
        closeModal();
        viewLeads();
    } catch (err) {
        showMessage("Failed to save lead!", "error");
        console.error(err);
    }
}

// --- Delete Lead ---
async function deleteLead(id) {
    try {
        const response = await fetch(`${API}/delete-lead/${id}`, {
            method: "DELETE"
        });
        const data = await response.json();
        showMessage(data.message, "success");
        viewLeads();
    } catch (err) {
        showMessage("Failed to delete lead!", "error");
        console.error(err);
    }
}

// --- Run ML Segmentation ---
async function runSegmentation() {
    try {
        const response = await fetch(`${API}/run-segmentation`, {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        const data = await response.json();
        if (response.ok) {
            showMessage(data.message, "success");
            viewLeads();
        } else {
            showMessage(data.error, "error");
        }
    } catch (err) {
        showMessage("Segmentation failed!", "error");
        console.error(err);
    }
}

// --- Run Lead Scoring ---
async function runLeadScoring() {
    try {
        const response = await fetch(`${API}/run-lead-scoring`, {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        const data = await response.json();
        if (response.ok) {
            showMessage(data.message, "success");
            viewLeads();
        } else {
            showMessage(data.error, "error");
        }
    } catch (err) {
        showMessage("Lead scoring failed!", "error");
        console.error(err);
    }
}

// --- Initialize page ---
viewLeads();