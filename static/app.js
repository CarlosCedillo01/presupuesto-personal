/**
 * app.js - Lógica del frontend para el Simulador de Presupuesto Personal
 */

// ============================================================
// State & Config
// ============================================================

const CATEGORIES_EXPENSE = [
    'Alimentación', 'Transporte', 'Entretenimiento', 'Educación',
    'Salud', 'Vivienda', 'Ropa', 'Servicios', 'Otro'
];

const CATEGORIES_INCOME = [
    'Salario', 'Freelance', 'Inversiones', 'Otro'
];

const CATEGORY_ICONS = {
    'Alimentación': '🍔', 'Transporte': '🚗', 'Entretenimiento': '🎬',
    'Educación': '📚', 'Salud': '🏥', 'Vivienda': '🏠', 'Ropa': '👕',
    'Servicios': '💡', 'Salario': '💼', 'Freelance': '💻',
    'Inversiones': '📈', 'Ahorro': '🏦', 'Otro': '📦'
};

const CHART_COLORS = [
    '#6366f1', '#8b5cf6', '#a78bfa', '#10b981', '#34d399',
    '#f59e0b', '#fbbf24', '#ef4444', '#f87171', '#3b82f6',
    '#60a5fa', '#ec4899'
];

let expensePieChart = null;
let budgetBarChart = null;
let incomePieChart = null;

// ============================================================
// Init
// ============================================================

document.addEventListener('DOMContentLoaded', async () => {
    // Verificar sesión activa antes de cargar la app
    try {
        const res = await fetch('/api/me');
        if (!res.ok) {
            window.location.href = '/login';
            return;
        }
        const me = await res.json();
        const headerUsername = document.getElementById('header-username');
        if (headerUsername) {
            headerUsername.textContent = `👤 ${me.username}`;
        }
    } catch {
        window.location.href = '/login';
        return;
    }

    // Botón cerrar sesión
    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
        btnLogout.addEventListener('click', async () => {
            await fetch('/api/logout', { method: 'POST' });
            window.location.href = '/login';
        });
    }

    initMonthSelector();
    initTabs();
    initForms();
    loadAllData();
});

function initMonthSelector() {
    const monthInput = document.getElementById('global-month');
    const monthDisplay = document.getElementById('month-display');
    const btnPrev = document.getElementById('btn-prev-month');
    const btnNext = document.getElementById('btn-next-month');
    const now = new Date();

    // Set initial value
    monthInput.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    updateMonthDisplay();

    btnPrev.addEventListener('click', () => changeMonth(-1));
    btnNext.addEventListener('click', () => changeMonth(1));
    monthInput.addEventListener('change', () => {
        updateMonthDisplay();
        loadAllData();
    });
}

function changeMonth(delta) {
    const monthInput = document.getElementById('global-month');
    const [year, month] = monthInput.value.split('-').map(Number);
    const d = new Date(year, month - 1 + delta, 1);
    monthInput.value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    updateMonthDisplay();
    loadAllData();
}

const MONTH_NAMES = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

function updateMonthDisplay() {
    const monthInput = document.getElementById('global-month');
    const monthDisplay = document.getElementById('month-display');
    const [year, month] = monthInput.value.split('-').map(Number);
    monthDisplay.textContent = `${MONTH_NAMES[month - 1]} ${year}`;
}

function getSelectedMonth() {
    return document.getElementById('global-month').value;
}

// ============================================================
// Tabs
// ============================================================

function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');

            // Refresh data when switching tabs
            if (btn.dataset.tab === 'resumen') loadSummaryData();
            if (btn.dataset.tab === 'reporte') loadReportData();
        });
    });
}

// ============================================================
// Forms
// ============================================================

function initForms() {
    // Transaction form
    document.getElementById('transaction-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            type: document.getElementById('tx-type').value,
            category: document.getElementById('tx-category').value,
            description: document.getElementById('tx-description').value,
            amount: parseFloat(document.getElementById('tx-amount').value),
            date: document.getElementById('tx-date').value
        };

        try {
            const res = await fetch('/api/transactions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!res.ok) throw new Error((await res.json()).error);
            showToast('Transacción registrada exitosamente', 'success');
            e.target.reset();
            // Reset date to today
            document.getElementById('tx-date').value = new Date().toISOString().split('T')[0];
            loadAllData();
        } catch (err) {
            showToast(`Error: ${err.message}`, 'error');
        }
    });

    // Set default date
    document.getElementById('tx-date').value = new Date().toISOString().split('T')[0];

    // Filtrar categorías según tipo de transacción
    const txType = document.getElementById('tx-type');
    txType.addEventListener('change', () => updateCategoryOptions(txType.value));
    updateCategoryOptions(txType.value); // carga inicial

    // Budget form
    document.getElementById('budget-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            category: document.getElementById('bg-category').value,
            monthly_limit: parseFloat(document.getElementById('bg-limit').value),
            month: getSelectedMonth()
        };

        try {
            const res = await fetch('/api/budgets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!res.ok) throw new Error((await res.json()).error);
            showToast('Presupuesto establecido', 'success');
            document.getElementById('bg-limit').value = '';
            loadAllData();
        } catch (err) {
            showToast(`Error: ${err.message}`, 'error');
        }
    });

    // Savings form
    document.getElementById('savings-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            name: document.getElementById('sv-name').value,
            target_amount: parseFloat(document.getElementById('sv-target').value),
            deadline: document.getElementById('sv-deadline').value || null
        };

        try {
            const res = await fetch('/api/savings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!res.ok) throw new Error((await res.json()).error);
            showToast('Meta de ahorro creada', 'success');
            e.target.reset();
            loadSavingsGoals();
        } catch (err) {
            showToast(`Error: ${err.message}`, 'error');
        }
    });

    // CSV Export
    document.getElementById('btn-export-csv').addEventListener('click', () => {
        const month = getSelectedMonth();
        window.open(`/api/export/csv?month=${month}`, '_blank');
        showToast('Exportando CSV...', 'info');
    });

    // Reset Data
    document.getElementById('btn-reset-data').addEventListener('click', () => resetData());
}

// ============================================================
// Data Loading
// ============================================================

async function loadAllData() {
    await Promise.all([
        loadTransactions(),
        loadAlerts(),
        loadSavingsGoals(),
        loadSummaryData(),
        loadReportData()
    ]);
}

async function loadTransactions() {
    const month = getSelectedMonth();
    try {
        const res = await fetch(`/api/transactions?month=${month}`);
        const transactions = await res.json();
        renderTransactions(transactions);
    } catch (err) {
        console.error('Error loading transactions:', err);
    }
}

async function loadAlerts() {
    const month = getSelectedMonth();
    try {
        const res = await fetch(`/api/alerts?month=${month}`);
        const alerts = await res.json();
        renderAlerts(alerts);
    } catch (err) {
        console.error('Error loading alerts:', err);
    }
}

async function loadSavingsGoals() {
    try {
        const res = await fetch('/api/savings');
        const goals = await res.json();
        renderSavingsGoals(goals);
    } catch (err) {
        console.error('Error loading savings goals:', err);
    }
}

async function loadSummaryData() {
    const month = getSelectedMonth();
    try {
        const res = await fetch(`/api/report?month=${month}`);
        const report = await res.json();
        renderKPIs(report);
        renderExpensePieChart(report.expense_by_category);
        renderBudgetBarChart(report.budget_comparison);
        renderBudgetProgress(report.budget_comparison);
    } catch (err) {
        console.error('Error loading summary:', err);
    }
}

async function loadReportData() {
    const month = getSelectedMonth();
    try {
        const res = await fetch(`/api/report?month=${month}`);
        const report = await res.json();
        renderReportSummary(report);
        renderIncomePieChart(report.income_by_category);
        renderRecommendations(report.recommendations);
    } catch (err) {
        console.error('Error loading report:', err);
    }
}

// ============================================================
// Render: Transactions
// ============================================================

function renderTransactions(transactions) {
    const container = document.getElementById('transactions-list');

    if (transactions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <p>No hay transacciones registradas este mes</p>
            </div>`;
        return;
    }

    container.innerHTML = transactions.map(tx => {
        const icon = CATEGORY_ICONS[tx.category] || '📦';
        const isIncome = tx.type === 'ingreso';
        const sign = isIncome ? '+' : '-';
        const typeClass = isIncome ? 'income' : 'expense';

        return `
            <div class="tx-item" data-id="${tx.id}">
                <div class="tx-info">
                    <div class="tx-icon ${typeClass}">${icon}</div>
                    <div class="tx-details">
                        <h4>${tx.description || tx.category}</h4>
                        <p>${tx.category}</p>
                    </div>
                </div>
                <div class="tx-right">
                    <span class="tx-date">${formatDate(tx.date)}</span>
                    <span class="tx-amount ${typeClass}">${sign}$${formatNumber(tx.amount)}</span>
                    <button class="btn btn-sm btn-danger" onclick="deleteTransaction(${tx.id})" title="Eliminar">✕</button>
                </div>
            </div>`;
    }).join('');
}

// ============================================================
// Render: Alerts
// ============================================================

function renderAlerts(alerts) {
    const banner = document.getElementById('alerts-banner');

    if (alerts.length === 0) {
        banner.classList.add('hidden');
        banner.innerHTML = '';
        return;
    }

    banner.classList.remove('hidden');
    banner.innerHTML = alerts.map(a => `
        <div class="alert-item">
            <span class="alert-icon">🚨</span>
            <span><strong>${a.category}</strong> excedido: gastaste <strong>$${formatNumber(a.total_spent)}</strong> de <strong>$${formatNumber(a.monthly_limit)}</strong> (${a.percentage}%)</span>
        </div>
    `).join('');
}

// ============================================================
// Render: KPIs
// ============================================================

function renderKPIs(report) {
    document.getElementById('kpi-income-value').textContent = `$${formatNumber(report.total_income)}`;
    document.getElementById('kpi-expense-value').textContent = `$${formatNumber(report.total_expenses)}`;
    document.getElementById('kpi-balance-value').textContent = `$${formatNumber(report.balance)}`;
    document.getElementById('kpi-savings-value').textContent = `${report.savings_rate}%`;

    // Color-code balance
    const balanceEl = document.getElementById('kpi-balance-value');
    balanceEl.style.color = report.balance >= 0 ? 'var(--info)' : 'var(--danger)';
}

// ============================================================
// Render: Charts
// ============================================================

function renderExpensePieChart(expenseByCategory) {
    const ctx = document.getElementById('expense-pie-chart').getContext('2d');

    if (expensePieChart) expensePieChart.destroy();

    if (!expenseByCategory || expenseByCategory.length === 0) {
        expensePieChart = null;
        return;
    }

    expensePieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: expenseByCategory.map(e => e.category),
            datasets: [{
                data: expenseByCategory.map(e => e.total),
                backgroundColor: CHART_COLORS.slice(0, expenseByCategory.length),
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#94a3b8',
                        padding: 14,
                        font: { family: "'Inter', sans-serif", size: 12 },
                        usePointStyle: true,
                        pointStyleWidth: 10
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleFont: { family: "'Inter', sans-serif" },
                    bodyFont: { family: "'Inter', sans-serif" },
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: (ctx) => ` $${formatNumber(ctx.raw)}`
                    }
                }
            },
            cutout: '60%'
        }
    });
}

function renderBudgetBarChart(budgetComparison) {
    const ctx = document.getElementById('budget-bar-chart').getContext('2d');

    if (budgetBarChart) budgetBarChart.destroy();

    if (!budgetComparison || budgetComparison.length === 0) {
        budgetBarChart = null;
        return;
    }

    budgetBarChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: budgetComparison.map(b => b.category),
            datasets: [
                {
                    label: 'Presupuesto',
                    data: budgetComparison.map(b => b.monthly_limit),
                    backgroundColor: 'rgba(99, 102, 241, 0.6)',
                    borderColor: '#6366f1',
                    borderWidth: 1,
                    borderRadius: 6,
                    barPercentage: 0.7
                },
                {
                    label: 'Gasto Real',
                    data: budgetComparison.map(b => b.total_spent),
                    backgroundColor: budgetComparison.map(b =>
                        b.total_spent > b.monthly_limit
                            ? 'rgba(239, 68, 68, 0.6)'
                            : 'rgba(16, 185, 129, 0.6)'
                    ),
                    borderColor: budgetComparison.map(b =>
                        b.total_spent > b.monthly_limit ? '#ef4444' : '#10b981'
                    ),
                    borderWidth: 1,
                    borderRadius: 6,
                    barPercentage: 0.7
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#94a3b8',
                        font: { family: "'Inter', sans-serif", size: 12 },
                        usePointStyle: true,
                        pointStyleWidth: 10,
                        padding: 14
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleFont: { family: "'Inter', sans-serif" },
                    bodyFont: { family: "'Inter', sans-serif" },
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: (ctx) => ` ${ctx.dataset.label}: $${formatNumber(ctx.raw)}`
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#64748b', font: { family: "'Inter', sans-serif", size: 11 } },
                    grid: { color: 'rgba(255,255,255,0.04)' }
                },
                y: {
                    ticks: {
                        color: '#64748b',
                        font: { family: "'Inter', sans-serif", size: 11 },
                        callback: v => `$${formatNumber(v)}`
                    },
                    grid: { color: 'rgba(255,255,255,0.04)' }
                }
            }
        }
    });
}

function renderIncomePieChart(incomeByCategory) {
    const ctx = document.getElementById('income-pie-chart').getContext('2d');

    if (incomePieChart) incomePieChart.destroy();

    if (!incomeByCategory || incomeByCategory.length === 0) {
        incomePieChart = null;
        return;
    }

    incomePieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: incomeByCategory.map(e => e.category),
            datasets: [{
                data: incomeByCategory.map(e => e.total),
                backgroundColor: ['#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#6366f1', '#8b5cf6'],
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#94a3b8',
                        padding: 14,
                        font: { family: "'Inter', sans-serif", size: 12 },
                        usePointStyle: true,
                        pointStyleWidth: 10
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleFont: { family: "'Inter', sans-serif" },
                    bodyFont: { family: "'Inter', sans-serif" },
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: (ctx) => ` $${formatNumber(ctx.raw)}`
                    }
                }
            },
            cutout: '60%'
        }
    });
}

// ============================================================
// Render: Budget Progress
// ============================================================

function renderBudgetProgress(budgetComparison) {
    const container = document.getElementById('budget-progress-list');

    if (!budgetComparison || budgetComparison.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🎯</div>
                <p>No hay presupuestos establecidos para este mes</p>
            </div>`;
        return;
    }

    container.innerHTML = budgetComparison.map(b => {
        const pct = Math.min((b.total_spent / b.monthly_limit) * 100, 100);
        const actualPct = (b.total_spent / b.monthly_limit) * 100;
        let statusClass = 'ok';
        let statusText = `${actualPct.toFixed(0)}% utilizado`;

        if (actualPct > 100) {
            statusClass = 'danger';
            statusText = `⚠️ Excedido por $${formatNumber(b.total_spent - b.monthly_limit)} (${actualPct.toFixed(0)}%)`;
        } else if (actualPct > 75) {
            statusClass = 'warning';
            statusText = `⚡ ${actualPct.toFixed(0)}% utilizado - ¡Precaución!`;
        }

        return `
            <div class="budget-progress-item">
                <div class="budget-progress-header">
                    <h4>${CATEGORY_ICONS[b.category] || '📦'} ${b.category}</h4>
                    <span class="budget-progress-amounts">$${formatNumber(b.total_spent)} / $${formatNumber(b.monthly_limit)}</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill ${statusClass}" style="width: ${pct}%"></div>
                </div>
                <div class="budget-status ${statusClass}">${statusText}</div>
            </div>`;
    }).join('');
}

// ============================================================
// Render: Savings Goals
// ============================================================

function renderSavingsGoals(goals) {
    const container = document.getElementById('savings-goals-list');

    if (goals.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🏦</div>
                <p>No hay metas de ahorro</p>
            </div>`;
        return;
    }

    container.innerHTML = goals.map(g => {
        const pct = Math.min((g.current_amount / g.target_amount) * 100, 100);
        const proj = g.projection || {};
        let projClass = '';
        if (proj.status === 'behind') projClass = 'behind';
        if (proj.status === 'completed') projClass = 'completed';

        const deadlineStr = g.deadline ? `📅 ${formatDate(g.deadline)}` : 'Sin fecha límite';

        return `
            <div class="savings-goal-card">
                <div class="savings-goal-header">
                    <h4>🎯 ${g.name}</h4>
                    <span class="goal-deadline">${deadlineStr}</span>
                </div>
                <div class="savings-goal-amounts">
                    <span class="current">$${formatNumber(g.current_amount)}</span>
                    <span class="target">de $${formatNumber(g.target_amount)}</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill ${pct >= 100 ? 'ok' : pct > 50 ? 'warning' : 'ok'}" style="width: ${pct}%"></div>
                </div>
                <div class="savings-goal-projection ${projClass}">
                    ${proj.message || 'Calculando proyección...'}
                </div>
                <div class="savings-goal-actions">
                    <input type="number" class="deposit-input" id="deposit-${g.id}" placeholder="Monto" min="1" step="0.01">
                    <button class="btn btn-sm btn-deposit" onclick="depositToGoal(${g.id})">💵 Depositar</button>
                    <button class="btn btn-sm btn-withdraw" onclick="withdrawFromGoal(${g.id})">💸 Retirar</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteSavingsGoal(${g.id})">✕</button>
                </div>
            </div>`;
    }).join('');
}

// ============================================================
// Render: Report
// ============================================================

function renderReportSummary(report) {
    const container = document.getElementById('report-summary-table');

    let rows = '';

    // Expenses by category
    if (report.expense_by_category.length > 0) {
        rows += report.expense_by_category.map(e => `
            <tr>
                <td>${CATEGORY_ICONS[e.category] || '📦'} ${e.category}</td>
                <td style="color: var(--danger);">-$${formatNumber(e.total)}</td>
                <td>${report.total_expenses > 0 ? ((e.total / report.total_expenses) * 100).toFixed(1) : 0}%</td>
            </tr>`).join('');
    }

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Concepto</th>
                    <th>Monto</th>
                    <th>% del Total</th>
                </tr>
            </thead>
            <tbody>
                <tr class="report-total">
                    <td>💵 Total Ingresos</td>
                    <td style="color: var(--success);">+$${formatNumber(report.total_income)}</td>
                    <td>—</td>
                </tr>
                ${rows}
                <tr class="report-total">
                    <td>📉 Total Gastos</td>
                    <td style="color: var(--danger);">-$${formatNumber(report.total_expenses)}</td>
                    <td>100%</td>
                </tr>
                <tr class="report-total">
                    <td>💰 Balance</td>
                    <td style="color: ${report.balance >= 0 ? 'var(--info)' : 'var(--danger)'};">
                        ${report.balance >= 0 ? '+' : ''}$${formatNumber(report.balance)}
                    </td>
                    <td>Ahorro: ${report.savings_rate}%</td>
                </tr>
            </tbody>
        </table>`;
}

function renderRecommendations(recommendations) {
    const container = document.getElementById('recommendations-list');

    if (!recommendations || recommendations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">💡</div>
                <p>No hay recomendaciones disponibles</p>
            </div>`;
        return;
    }

    container.innerHTML = recommendations.map(r => `
        <div class="rec-item ${r.type}">
            <div class="rec-icon">${r.icon}</div>
            <div class="rec-content">
                <h4>${r.title}</h4>
                <p>${r.text}</p>
            </div>
        </div>`).join('');
}

// ============================================================
// Actions
// ============================================================

async function resetData() {
    if (!confirm('⚠️ ¿Estás seguro de que quieres borrar TODOS los movimientos?\n\nEsto eliminará todas las transacciones, presupuestos y metas de ahorro.\nEsta acción no se puede deshacer.')) return;

    try {
        const res = await fetch('/api/reset', { method: 'POST' });
        if (!res.ok) throw new Error((await res.json()).error);
        showToast('Todos los datos han sido reiniciados', 'success');
        loadAllData();
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

async function deleteTransaction(id) {
    if (!confirm('¿Eliminar esta transacción?')) return;
    try {
        await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
        showToast('Transacción eliminada', 'info');
        loadAllData();
    } catch (err) {
        showToast('Error al eliminar', 'error');
    }
}

async function depositToGoal(goalId) {
    const input = document.getElementById(`deposit-${goalId}`);
    const amount = parseFloat(input.value);

    if (!amount || amount <= 0) {
        showToast('Ingresa un monto válido', 'error');
        return;
    }

    try {
        const res = await fetch(`/api/savings/${goalId}/deposit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount })
        });
        if (!res.ok) throw new Error((await res.json()).error);
        showToast(`Depósito de $${formatNumber(amount)} realizado`, 'success');
        input.value = '';
        loadAllData();
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

async function deleteSavingsGoal(goalId) {
    if (!confirm('¿Eliminar esta meta de ahorro?')) return;
    try {
        await fetch(`/api/savings/${goalId}`, { method: 'DELETE' });
        showToast('Meta eliminada', 'info');
        loadSavingsGoals();
    } catch (err) {
        showToast('Error al eliminar', 'error');
    }
}

async function withdrawFromGoal(goalId) {
    const input = document.getElementById(`deposit-${goalId}`);
    const amount = parseFloat(input.value);

    if (!amount || amount <= 0) {
        showToast('Ingresa un monto válido para retirar', 'error');
        return;
    }

    try {
        const res = await fetch(`/api/savings/${goalId}/withdraw`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        showToast(`Retiro de $${formatNumber(amount)} realizado`, 'success');
        input.value = '';
        loadAllData();
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

// ============================================================
// Category Filtering
// ============================================================

function updateCategoryOptions(type) {
    const select = document.getElementById('tx-category');
    const categories = type === 'ingreso' ? CATEGORIES_INCOME : CATEGORIES_EXPENSE;
    select.innerHTML = categories.map(cat => {
        const icon = CATEGORY_ICONS[cat] || '📦';
        return `<option value="${cat}">${icon} ${cat}</option>`;
    }).join('');
}

// ============================================================
// Utilities
// ============================================================

function formatNumber(n) {
    return Number(n).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' });
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span> ${message}`;
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3500);
}
