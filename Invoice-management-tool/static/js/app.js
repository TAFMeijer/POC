/**
 * Invoice Management Tool — Frontend Logic
 *
 * Handles:
 *  - Loading client dropdown from API
 *  - Fetching appointments from Google Calendar via backend
 *  - Rendering editable Handsontable grid
 *  - Auto-calculating amounts (duration × hourly rate)
 *  - Generating PDF invoice via backend
 */

// ── State ───────────────────────────────────────────────────────────
let hot = null;              // Handsontable instance
let currentClient = null;    // Full client object from API
let currentClientName = "";  // Selected client name

// ── DOM Elements ────────────────────────────────────────────────────
const clientSelect   = document.getElementById("client-select");
const startDateInput = document.getElementById("start-date");
const endDateInput   = document.getElementById("end-date");
const fetchBtn       = document.getElementById("fetch-btn");
const generateBtn    = document.getElementById("generate-btn");
const generateCorrectionBtn = document.getElementById("generate-correction-btn");
const openTrackerBtn = document.getElementById("open-tracker-btn");
const statusMsg      = document.getElementById("status-message");
const tableSection   = document.getElementById("table-section");
const tableContainer = document.getElementById("appointments-table");
const tableClientName = document.getElementById("table-client-name");
const rowCount       = document.getElementById("row-count");
const totalAmount    = document.getElementById("total-amount");
const downloadSection = document.getElementById("download-section");
const downloadFilename = document.getElementById("download-filename");
const downloadLink   = document.getElementById("download-link");

// ── Initialisation ──────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    loadClients();
    setupEventListeners();
    setDefaultDates();
});

function setDefaultDates() {
    // Default: first day of current month → today
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    startDateInput.value = formatDateISO(firstDay);
    endDateInput.value = formatDateISO(today);
}

function formatDateISO(date) {
    return date.toISOString().split("T")[0];
}

function setupEventListeners() {
    clientSelect.addEventListener("change", onClientChange);
    startDateInput.addEventListener("change", validateForm);
    endDateInput.addEventListener("change", validateForm);
    fetchBtn.addEventListener("click", fetchAppointments);
    generateBtn.addEventListener("click", () => generateInvoice(false));
    generateCorrectionBtn.addEventListener("click", () => generateInvoice(true));
    openTrackerBtn.addEventListener("click", openTracker);
}

function validateForm() {
    let valid = false;
    if (currentClient && currentClient.billing_type === "pack") {
        valid = clientSelect.value && startDateInput.value;
    } else {
        valid = clientSelect.value && startDateInput.value && endDateInput.value;
    }
    fetchBtn.disabled = !valid;
}

// ── Status Messages ─────────────────────────────────────────────────
function showStatus(message, type = "info") {
    statusMsg.textContent = message;
    statusMsg.className = `status-message ${type}`;
    statusMsg.classList.remove("hidden");
}

function hideStatus() {
    statusMsg.classList.add("hidden");
}

async function onClientChange() {
    const clientName = clientSelect.value;
    if (!clientName) {
        currentClient = null;
        currentClientName = "";
        validateForm();
        tableSection.classList.add("hidden");
        generateCorrectionBtn.classList.add("hidden");
        return;
    }
    
    try {
        const resp = await fetch(`/api/client/${clientName}`);
        const data = await resp.json();
        
        if (data.error) {
            showStatus(data.error, "error");
            return;
        }
        
        currentClient = data.client;
        currentClientName = currentClient.name;
        
        // Reset correction button when changing clients
        generateCorrectionBtn.classList.add("hidden");
        
        if (currentClient.billing_type === "pack") {
            // Pack mode: hide end date, change text
            startDateInput.previousElementSibling.textContent = "Date du pack";
            startDateInput.parentElement.classList.remove("hidden");
            endDateInput.parentElement.classList.add("hidden");
            
            fetchBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg> Générer la ligne';
            fetchBtn.parentElement.classList.remove("hidden");
            
            tableSection.classList.add("hidden"); 
            showStatus("Mode Pack activé. Sélectionnez la date et cliquez sur Générer.", "success");
            validateForm();
        } else {
            // Standard calendar mode
            startDateInput.previousElementSibling.textContent = "Date de début";
            startDateInput.parentElement.classList.remove("hidden");
            endDateInput.parentElement.classList.remove("hidden");
            
            fetchBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg> Rechercher';
            fetchBtn.parentElement.classList.remove("hidden");
            
            tableSection.classList.add("hidden"); 
            hideStatus();
            validateForm();
        }
    } catch (e) {
        console.error("onClientChange error:", e);
    }
}

// ── Load Clients ────────────────────────────────────────────────────
async function loadClients() {
    try {
        const resp = await fetch("/api/clients");
        const data = await resp.json();

        if (data.error) {
            showStatus(`Erreur: ${data.error}`, "error");
            return;
        }

        data.clients.forEach(name => {
            const opt = document.createElement("option");
            opt.value = name;
            opt.textContent = name;
            clientSelect.appendChild(opt);
        });
    } catch (err) {
        showStatus("Impossible de charger la liste des clients.", "error");
        console.error("loadClients error:", err);
    }
}

// ── Fetch Appointments ──────────────────────────────────────────────
async function fetchAppointments() {
    if (currentClient && currentClient.billing_type === "pack") {
        return generatePackLine();
    }

    const clientName = clientSelect.value;
    const startDate  = startDateInput.value;
    const endDate    = endDateInput.value;

    if (!clientName || !startDate || !endDate) return;

    fetchBtn.classList.add("loading");
    showStatus("Recherche des rendez-vous en cours…", "info");
    downloadSection.classList.add("hidden");

    try {
        const resp = await fetch("/api/appointments", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                client: clientName,
                start_date: startDate,
                end_date: endDate,
            }),
        });

        const data = await resp.json();

        if (data.error) {
            showStatus(`Erreur: ${data.error}`, "error");
            return;
        }

        currentClient = data.client;
        currentClientName = clientName;

        if (data.appointments.length === 0) {
            showStatus("Aucun rendez-vous trouvé pour cette période.", "info");
            tableSection.classList.add("hidden");
            return;
        }

        showStatus(`${data.appointments.length} rendez-vous trouvé(s).`, "success");
        renderTable(data.appointments);

    } catch (err) {
        showStatus("Erreur de connexion au serveur.", "error");
        console.error("fetchAppointments error:", err);
    } finally {
        fetchBtn.classList.remove("loading");
    }
}

function generatePackLine() {
    const startDate = startDateInput.value;
    if (!startDate || !currentClient) return;

    // Parse the ISO date to DD/MM/YYYY
    const parts = startDate.split("-"); // YYYY-MM-DD
    const frDate = `${parts[2]}/${parts[1]}/${parts[0]}`;
    
    let description = currentClient.pack_description_template || "Pack de XX heures <br/>A partir du DD/MM/YYYY";
    description = description.replace("DD/MM/YYYY", frDate);
    
    const hours = currentClient.pack_hours || 1;
    
    const mockAppts = [{
        date: description,
        day: "",
        duration_display: String(hours) + ":00",
        duration_hours: hours,
        hourly_rate: currentClient.hourly_rate,
        amount: hours * currentClient.hourly_rate
    }];
    
    downloadSection.classList.add("hidden");
    showStatus("Ligne de facturation Pack générée.", "success");
    renderTable(mockAppts);
}

// ── Render Handsontable ─────────────────────────────────────────────
function renderTable(appointments) {
    tableSection.classList.remove("hidden");
    tableClientName.textContent = currentClientName;

    // Prepare data: max 10 rows
    const rows = appointments.slice(0, 10).map(apt => [
        apt.date, // Serves as 'Date' or 'Prestation'
        apt.day || "",
        apt.duration_display,
        parseFloat(apt.hourly_rate).toFixed(2),
        parseFloat(apt.amount).toFixed(2),
    ]);

    rowCount.textContent = `${rows.length} ligne${rows.length > 1 ? "s" : ""}`;

    // Destroy previous instance
    if (hot) {
        hot.destroy();
        hot = null;
    }

    const isPack = currentClient && currentClient.billing_type === "pack";
    const headers = isPack 
        ? ["Prestation", "Détail (Opt)", "Heures", "Tarif Horaire (€)", "Total (€)"]
        : ["Date", "Jour", "Heures", "Tarif Horaire (€)", "Total (€)"];

    hot = new Handsontable(tableContainer, {
        data: rows,
        colHeaders: headers,
        columns: [
            { type: "text", width: 120 },      // Date / Prestation
            { type: "text", width: 100, readOnly: !isPack }, // Day (auto from date) OR Detail if Pack
            { type: "text", width: 90 },        // Duration
            { type: "numeric", numericFormat: { pattern: "0.00" }, width: 130 },
            { type: "numeric", numericFormat: { pattern: "0.00" }, width: 110, readOnly: true },
        ],
        rowHeaders: false,
        stretchH: "all",
        licenseKey: "non-commercial-and-evaluation",
        height: "auto",
        autoColumnSize: false,
        className: "htCenter",
        afterChange: onCellChange,
    });

    updateTotal();
}

// ── Cell Change Handler ─────────────────────────────────────────────
function onCellChange(changes, source) {
    if (source === "loadData" || !changes) return;

    changes.forEach(([row, col]) => {
        // col 2 = duration, col 3 = hourly rate → recalc col 4 (amount)
        if (col === 2 || col === 3) {
            recalcRow(row);
        }
        // col 0 = date → update day (col 1)
        if (col === 0) {
            updateDayFromDate(row);
        }
    });

    updateTotal();
}

function recalcRow(row) {
    const durationStr = hot.getDataAtCell(row, 2);
    const rateStr = hot.getDataAtCell(row, 3);

    const durationHours = parseDuration(durationStr);
    const rate = parseFloat(rateStr) || 0;
    const amount = (durationHours * rate).toFixed(2);

    hot.setDataAtCell(row, 4, amount, "internal");
}

function parseDuration(str) {
    if (!str) return 0;
    str = String(str).trim();

    // Format "H:MM" or "HH:MM"
    if (str.includes(":")) {
        const parts = str.split(":");
        const h = parseInt(parts[0], 10) || 0;
        const m = parseInt(parts[1], 10) || 0;
        return h + m / 60;
    }

    // Decimal format "1.50"
    return parseFloat(str) || 0;
}

function updateDayFromDate(row) {
    if (currentClient && currentClient.billing_type === "pack") return;

    const dateStr = hot.getDataAtCell(row, 0);
    if (!dateStr) return;

    // Parse DD-MM-YYYY
    const parts = dateStr.split("-");
    if (parts.length !== 3) return;

    const d = new Date(parts[2], parts[1] - 1, parts[0]);
    if (isNaN(d.getTime())) return;

    const days = ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"];
    hot.setDataAtCell(row, 1, days[d.getDay()], "internal");
}

function updateTotal() {
    if (!hot) return;

    let sum = 0;
    const rowCount_ = hot.countRows();
    for (let i = 0; i < rowCount_; i++) {
        const val = parseFloat(hot.getDataAtCell(i, 4)) || 0;
        sum += val;
    }

    totalAmount.textContent = `€ ${sum.toFixed(2)}`;
}

// ── Generate Invoice ────────────────────────────────────────────────
async function generateInvoice(isCorrection = false) {
    if (!hot || !currentClientName) return;

    const btn = isCorrection ? generateCorrectionBtn : generateBtn;
    btn.classList.add("loading");
    showStatus(isCorrection ? "Correction de la facture en cours…" : "Génération de la facture en cours…", "info");

    // Collect table data
    const appointments = [];
    const rowCount_ = hot.countRows();

    for (let i = 0; i < rowCount_; i++) {
        const date = hot.getDataAtCell(i, 0);
        const duration = hot.getDataAtCell(i, 2);
        const rate = parseFloat(hot.getDataAtCell(i, 3)) || 0;
        const amount = parseFloat(hot.getDataAtCell(i, 4)) || 0;

        if (!date) continue;

        let description = "";
        if (currentClient && currentClient.billing_type === "pack") {
            description = date; // In pack mode, column 0 is raw description
            const detailOpt = hot.getDataAtCell(i, 1);
            if (detailOpt) description += ` - ${detailOpt}`;
        }

        appointments.push({
            date: date,
            description: description,
            duration_display: duration,
            duration_hours: parseDuration(duration),
            hourly_rate: rate,
            amount: amount,
        });
    }

    if (appointments.length === 0) {
        showStatus("Aucune ligne à facturer.", "error");
        btn.classList.remove("loading");
        return;
    }

    try {
        const resp = await fetch("/api/generate-invoice", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                client_name: currentClientName,
                appointments: appointments,
                is_correction: isCorrection,
            }),
        });

        const data = await resp.json();

        if (data.error) {
            showStatus(`Erreur: ${data.error}`, "error");
            return;
        }

        // Show download section
        showStatus("Facture générée avec succès!", "success");
        downloadFilename.textContent = data.filename;
        downloadLink.href = data.download_url;
        downloadSection.classList.remove("hidden");
        
        // Show correction button for subsequent fixes
        generateCorrectionBtn.classList.remove("hidden");

        // Smooth scroll to download
        downloadSection.scrollIntoView({ behavior: "smooth", block: "center" });

    } catch (err) {
        showStatus("Erreur lors de la génération de la facture.", "error");
        console.error("generateInvoice error:", err);
    } finally {
        btn.classList.remove("loading");
    }
}

// ── Open Tracker ────────────────────────────────────────────────────
async function openTracker() {
    if (!currentClientName) return;

    openTrackerBtn.classList.add("loading");
    try {
        const resp = await fetch("/api/open-tracker", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ client_name: currentClientName }),
        });
        const data = await resp.json();
        
        if (data.error) {
            showStatus(`Excel: ${data.error}`, "info"); // Show as info if file just doesn't exist yet
        }
    } catch (err) {
        showStatus("Erreur d'ouverture du fichier Excel.", "error");
        console.error("openTracker error:", err);
    } finally {
        openTrackerBtn.classList.remove("loading");
    }
}
