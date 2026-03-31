"""
database.py - Módulo de gestión de base de datos SQLite
para el Simulador de Presupuesto Personal.
"""

import sqlite3
import os
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "budget.db")


def get_connection():
    """Obtiene una conexión a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Inicializa las tablas y carga datos demo si es necesario."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS credentials (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('ingreso', 'gasto')),
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL CHECK(amount > 0),
            date TEXT NOT NULL,
            hidden INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL CHECK(monthly_limit > 0),
            month TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, category, month)
        );

        CREATE TABLE IF NOT EXISTS savings_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            target_amount REAL NOT NULL CHECK(target_amount > 0),
            current_amount REAL NOT NULL DEFAULT 0,
            deadline TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)

    # Usuarios predefinidos: (id, nombre, username, contraseña)
    PREDEFINED_USERS = [
        (1, 'Usuario 01', 'usuario01', 'finanzas2026'),
        (2, 'Usuario 02', 'usuario02', 'express2026'),
        (3, 'Usuario 03', 'usuario03', 'ahorro2026'),
        (4, 'Usuario 04', 'usuario04', 'balance2026'),
        (5, 'Usuario 05', 'usuario05', 'gastos2026'),
        (6, 'Usuario 06', 'usuario06', 'ingreso2026'),
        (7, 'Usuario 07', 'usuario07', 'meta2026'),
        (8, 'Usuario 08', 'usuario08', 'cuenta2026'),
        (9, 'Usuario 09', 'usuario09', 'dinero2026'),
        (10, 'Usuario 10', 'usuario10', 'budget2026'),
    ]

    for uid, name, username, password in PREDEFINED_USERS:
        user = cur.execute("SELECT id FROM users WHERE id = ?", (uid,)).fetchone()
        if not user:
            cur.execute("INSERT INTO users (id, name) VALUES (?, ?)", (uid, name))
            cur.execute(
                "INSERT INTO credentials (user_id, username, password_hash) VALUES (?, ?, ?)",
                (uid, username, generate_password_hash(password))
            )
            if uid == 1:
                _load_demo_data(cur)
        else:
            # Asegurar que existan las credenciales aunque ya existiera el usuario
            cred = cur.execute("SELECT user_id FROM credentials WHERE user_id = ?", (uid,)).fetchone()
            if not cred:
                cur.execute(
                    "INSERT INTO credentials (user_id, username, password_hash) VALUES (?, ?, ?)",
                    (uid, username, generate_password_hash(password))
                )

    conn.commit()
    conn.close()


def _load_demo_data(cur):
    """Carga datos de demostración para el perfil invitado."""
    today = date.today()
    month = today.strftime("%Y-%m")

    # Transacciones de ejemplo
    demo_transactions = [
        (1, 'ingreso', 'Salario', 'Salario quincenal', 15000.00, f"{month}-01"),
        (1, 'ingreso', 'Freelance', 'Proyecto diseño web', 3500.00, f"{month}-05"),
        (1, 'gasto', 'Alimentación', 'Supermercado semanal', 1200.00, f"{month}-02"),
        (1, 'gasto', 'Transporte', 'Gasolina', 800.00, f"{month}-03"),
        (1, 'gasto', 'Entretenimiento', 'Streaming y cine', 450.00, f"{month}-04"),
        (1, 'gasto', 'Educación', 'Curso en línea', 600.00, f"{month}-06"),
        (1, 'gasto', 'Servicios', 'Luz, agua, internet', 1800.00, f"{month}-07"),
        (1, 'gasto', 'Salud', 'Consulta médica', 500.00, f"{month}-08"),
        (1, 'gasto', 'Alimentación', 'Restaurante', 350.00, f"{month}-10"),
        (1, 'gasto', 'Ropa', 'Zapatos nuevos', 900.00, f"{month}-12"),
        (1, 'gasto', 'Transporte', 'Uber', 250.00, f"{month}-14"),
    ]

    cur.executemany(
        "INSERT INTO transactions (user_id, type, category, description, amount, date) VALUES (?, ?, ?, ?, ?, ?)",
        demo_transactions
    )

    # Presupuestos de ejemplo
    demo_budgets = [
        (1, 'Alimentación', 2000.00, month),
        (1, 'Transporte', 1500.00, month),
        (1, 'Entretenimiento', 500.00, month),
        (1, 'Educación', 1000.00, month),
        (1, 'Servicios', 2000.00, month),
        (1, 'Salud', 800.00, month),
        (1, 'Ropa', 600.00, month),
    ]

    cur.executemany(
        "INSERT INTO budgets (user_id, category, monthly_limit, month) VALUES (?, ?, ?, ?)",
        demo_budgets
    )

    # Metas de ahorro de ejemplo
    cur.execute(
        "INSERT INTO savings_goals (user_id, name, target_amount, current_amount, deadline, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (1, 'Laptop Nueva', 20000.00, 5500.00, f"{today.year}-{today.month + 4:02d}-01" if today.month <= 8 else f"{today.year + 1}-{(today.month + 4 - 12):02d}-01", today.isoformat())
    )
    cur.execute(
        "INSERT INTO savings_goals (user_id, name, target_amount, current_amount, deadline, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (1, 'Televisión 55"', 12000.00, 3000.00, f"{today.year}-{today.month + 6:02d}-01" if today.month <= 6 else f"{today.year + 1}-{(today.month + 6 - 12):02d}-01", today.isoformat())
    )


# ============================================================
# CRUD Transacciones
# ============================================================

def get_transactions(user_id=1, month=None):
    conn = get_connection()
    if month:
        rows = conn.execute(
            "SELECT * FROM transactions WHERE user_id = ? AND date LIKE ? AND hidden = 0 ORDER BY date DESC",
            (user_id, f"{month}%")
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM transactions WHERE user_id = ? AND hidden = 0 ORDER BY date DESC",
            (user_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_transaction(user_id, t_type, category, description, amount, t_date):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO transactions (user_id, type, category, description, amount, date) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, t_type, category, description, amount, t_date)
    )
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    return tid


def delete_transaction(tid, user_id=1):
    """Oculta la transacción de la lista pero la mantiene para reportes."""
    conn = get_connection()
    conn.execute("UPDATE transactions SET hidden = 1 WHERE id = ? AND user_id = ?", (tid, user_id))
    conn.commit()
    conn.close()


# ============================================================
# CRUD Presupuestos
# ============================================================

def get_budgets(user_id=1, month=None):
    conn = get_connection()
    if month:
        rows = conn.execute(
            "SELECT * FROM budgets WHERE user_id = ? AND month = ?",
            (user_id, month)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM budgets WHERE user_id = ?", (user_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_budget(user_id, category, monthly_limit, month):
    conn = get_connection()
    cur = conn.execute(
        "INSERT OR REPLACE INTO budgets (user_id, category, monthly_limit, month) VALUES (?, ?, ?, ?)",
        (user_id, category, monthly_limit, month)
    )
    conn.commit()
    bid = cur.lastrowid
    conn.close()
    return bid


def update_budget(bid, monthly_limit, user_id=1):
    conn = get_connection()
    conn.execute(
        "UPDATE budgets SET monthly_limit = ? WHERE id = ? AND user_id = ?",
        (monthly_limit, bid, user_id)
    )
    conn.commit()
    conn.close()


def delete_budget(bid, user_id=1):
    conn = get_connection()
    conn.execute("DELETE FROM budgets WHERE id = ? AND user_id = ?", (bid, user_id))
    conn.commit()
    conn.close()


# ============================================================
# CRUD Metas de Ahorro
# ============================================================

def get_savings_goals(user_id=1):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM savings_goals WHERE user_id = ? ORDER BY deadline", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_savings_goal(user_id, name, target_amount, deadline):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO savings_goals (user_id, name, target_amount, current_amount, deadline, created_at) VALUES (?, ?, ?, 0, ?, ?)",
        (user_id, name, target_amount, deadline, date.today().isoformat())
    )
    conn.commit()
    gid = cur.lastrowid
    conn.close()
    return gid


def deposit_to_goal(goal_id, amount, user_id=1):
    conn = get_connection()
    # Obtener el nombre de la meta para la descripción
    goal = conn.execute(
        "SELECT name FROM savings_goals WHERE id = ? AND user_id = ?",
        (goal_id, user_id)
    ).fetchone()
    goal_name = goal['name'] if goal else 'Meta de ahorro'

    # Actualizar monto de la meta
    conn.execute(
        "UPDATE savings_goals SET current_amount = current_amount + ? WHERE id = ? AND user_id = ?",
        (amount, goal_id, user_id)
    )

    # Registrar como gasto en transacciones
    conn.execute(
        "INSERT INTO transactions (user_id, type, category, description, amount, date) VALUES (?, 'gasto', 'Ahorro', ?, ?, ?)",
        (user_id, f'Caja de Ahorro: {goal_name}', amount, date.today().isoformat())
    )

    conn.commit()
    conn.close()


def withdraw_from_goal(goal_id, amount, user_id=1):
    """Retira dinero de una meta de ahorro y lo devuelve al balance."""
    conn = get_connection()
    goal = conn.execute(
        "SELECT name, current_amount FROM savings_goals WHERE id = ? AND user_id = ?",
        (goal_id, user_id)
    ).fetchone()

    if not goal:
        conn.close()
        return False, 'Meta no encontrada'

    if amount > goal['current_amount']:
        conn.close()
        return False, f'No puedes retirar más de ${goal["current_amount"]:.2f}'

    goal_name = goal['name']

    # Reducir monto de la meta
    conn.execute(
        "UPDATE savings_goals SET current_amount = current_amount - ? WHERE id = ? AND user_id = ?",
        (amount, goal_id, user_id)
    )

    # Registrar como ingreso (devolver al balance)
    conn.execute(
        "INSERT INTO transactions (user_id, type, category, description, amount, date) VALUES (?, 'ingreso', 'Ahorro', ?, ?, ?)",
        (user_id, f'Retiro de Caja de Ahorro: {goal_name}', amount, date.today().isoformat())
    )

    conn.commit()
    conn.close()
    return True, 'Retiro realizado'


def delete_savings_goal(goal_id, user_id=1):
    conn = get_connection()
    # Verificar si la meta tiene dinero acumulado
    goal = conn.execute(
        "SELECT name, current_amount FROM savings_goals WHERE id = ? AND user_id = ?",
        (goal_id, user_id)
    ).fetchone()

    if goal and goal['current_amount'] > 0:
        # Devolver el dinero al balance como ingreso
        conn.execute(
            "INSERT INTO transactions (user_id, type, category, description, amount, date) VALUES (?, 'ingreso', 'Ahorro', ?, ?, ?)",
            (user_id, f'Devolución por cierre de meta: {goal["name"]}', goal['current_amount'], date.today().isoformat())
        )

    conn.execute("DELETE FROM savings_goals WHERE id = ? AND user_id = ?", (goal_id, user_id))
    conn.commit()
    conn.close()


# ============================================================
# Autenticación
# ============================================================

def verify_credentials(username, password):
    """Verifica usuario y contraseña. Retorna el user_id si son válidos, None si no."""
    conn = get_connection()
    row = conn.execute(
        """SELECT c.user_id, c.password_hash
           FROM credentials c
           WHERE c.username = ?""",
        (username,)
    ).fetchone()
    conn.close()
    if row and check_password_hash(row['password_hash'], password):
        return row['user_id']
    return None


# ============================================================
# Reset de datos
# ============================================================

def reset_user_data(user_id=1):
    """Elimina todas las transacciones, presupuestos y metas de ahorro del usuario."""
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM budgets WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM savings_goals WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ============================================================
# Alertas y Reportes
# ============================================================

def get_alerts(user_id=1, month=None):
    """Obtener alertas de categorías que exceden su presupuesto."""
    if not month:
        month = date.today().strftime("%Y-%m")
    conn = get_connection()
    rows = conn.execute("""
        SELECT b.category, b.monthly_limit,
               COALESCE(SUM(t.amount), 0) as total_spent
        FROM budgets b
        LEFT JOIN transactions t
            ON t.user_id = b.user_id
            AND t.category = b.category
            AND t.type = 'gasto'
            AND t.date LIKE ?
        WHERE b.user_id = ? AND b.month = ?
        GROUP BY b.category, b.monthly_limit
        HAVING total_spent > b.monthly_limit
    """, (f"{month}%", user_id, month)).fetchall()
    conn.close()

    alerts = []
    for r in rows:
        exceeded = r['total_spent'] - r['monthly_limit']
        pct = (r['total_spent'] / r['monthly_limit']) * 100
        alerts.append({
            'category': r['category'],
            'monthly_limit': r['monthly_limit'],
            'total_spent': r['total_spent'],
            'exceeded_by': round(exceeded, 2),
            'percentage': round(pct, 1)
        })
    return alerts


def get_report(user_id=1, month=None):
    """Generar reporte resumen con recomendaciones."""
    if not month:
        month = date.today().strftime("%Y-%m")

    conn = get_connection()

    # Totales de ingresos y gastos
    income = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND type = 'ingreso' AND date LIKE ?",
        (user_id, f"{month}%")
    ).fetchone()['total']

    expenses = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = ? AND type = 'gasto' AND date LIKE ?",
        (user_id, f"{month}%")
    ).fetchone()['total']

    # Gastos por categoría
    expense_rows = conn.execute(
        "SELECT category, SUM(amount) as total FROM transactions WHERE user_id = ? AND type = 'gasto' AND date LIKE ? GROUP BY category ORDER BY total DESC",
        (user_id, f"{month}%")
    ).fetchall()
    expense_by_category = [dict(r) for r in expense_rows]

    # Ingresos por categoría
    income_rows = conn.execute(
        "SELECT category, SUM(amount) as total FROM transactions WHERE user_id = ? AND type = 'ingreso' AND date LIKE ? GROUP BY category ORDER BY total DESC",
        (user_id, f"{month}%")
    ).fetchall()
    income_by_category = [dict(r) for r in income_rows]

    # Presupuestos vs gastos reales
    budget_rows = conn.execute("""
        SELECT b.category, b.monthly_limit,
               COALESCE(SUM(t.amount), 0) as total_spent
        FROM budgets b
        LEFT JOIN transactions t
            ON t.user_id = b.user_id
            AND t.category = b.category
            AND t.type = 'gasto'
            AND t.date LIKE ?
        WHERE b.user_id = ? AND b.month = ?
        GROUP BY b.category, b.monthly_limit
    """, (f"{month}%", user_id, month)).fetchall()
    budget_comparison = [dict(r) for r in budget_rows]

    conn.close()

    balance = income - expenses
    savings_rate = (balance / income * 100) if income > 0 else 0

    # Generar recomendaciones
    recommendations = _generate_recommendations(
        income, expenses, balance, savings_rate,
        expense_by_category, budget_comparison
    )

    return {
        'month': month,
        'total_income': round(income, 2),
        'total_expenses': round(expenses, 2),
        'balance': round(balance, 2),
        'savings_rate': round(savings_rate, 1),
        'expense_by_category': expense_by_category,
        'income_by_category': income_by_category,
        'budget_comparison': budget_comparison,
        'recommendations': recommendations
    }


def _generate_recommendations(income, expenses, balance, savings_rate, expense_by_cat, budget_comp):
    """Genera recomendaciones inteligentes basadas en los datos."""
    recs = []

    # Recomendación sobre balance
    if balance < 0:
        recs.append({
            'type': 'danger',
            'icon': '🚨',
            'title': 'Balance negativo',
            'text': f'Tus gastos superan tus ingresos por ${abs(balance):,.2f}. Es urgente reducir gastos o buscar fuentes de ingreso adicionales.'
        })
    elif savings_rate < 10:
        recs.append({
            'type': 'warning',
            'icon': '⚠️',
            'title': 'Tasa de ahorro baja',
            'text': f'Tu tasa de ahorro es de solo {savings_rate:.1f}%. Se recomienda ahorrar al menos un 20% de tus ingresos.'
        })
    elif savings_rate >= 20:
        recs.append({
            'type': 'success',
            'icon': '✅',
            'title': '¡Excelente tasa de ahorro!',
            'text': f'Estás ahorrando {savings_rate:.1f}% de tus ingresos. ¡Sigue así!'
        })

    # Recomendaciones por categorías excedidas
    for b in budget_comp:
        if b['total_spent'] > b['monthly_limit']:
            pct_over = ((b['total_spent'] - b['monthly_limit']) / b['monthly_limit']) * 100
            recs.append({
                'type': 'warning',
                'icon': '📊',
                'title': f'{b["category"]} excedido',
                'text': f'Excediste tu presupuesto de {b["category"]} en {pct_over:.0f}% (${b["total_spent"] - b["monthly_limit"]:,.2f} de más). Considera ajustar tus gastos o aumentar el límite.'
            })

    # Categoría con mayor gasto
    if expense_by_cat:
        top = expense_by_cat[0]
        pct_of_total = (top['total'] / expenses * 100) if expenses > 0 else 0
        if pct_of_total > 40:
            recs.append({
                'type': 'info',
                'icon': '💡',
                'title': 'Gasto concentrado',
                'text': f'El {pct_of_total:.0f}% de tus gastos se concentra en "{top["category"]}". Diversificar podría darte más control.'
            })

    # Regla 50/30/20
    if income > 0:
        needs_pct = 0
        wants_pct = 0
        needs_cats = ['Alimentación', 'Vivienda', 'Servicios', 'Salud', 'Transporte']
        wants_cats = ['Entretenimiento', 'Ropa']
        for ec in expense_by_cat:
            pct = (ec['total'] / income * 100)
            if ec['category'] in needs_cats:
                needs_pct += pct
            elif ec['category'] in wants_cats:
                wants_pct += pct

        if needs_pct > 50:
            recs.append({
                'type': 'info',
                'icon': '📐',
                'title': 'Regla 50/30/20',
                'text': f'Tus gastos necesarios representan {needs_pct:.0f}% de tus ingresos (recomendado: máx 50%). Revisa si puedes optimizar servicios o transporte.'
            })

    if not recs:
        recs.append({
            'type': 'success',
            'icon': '🎉',
            'title': '¡Todo en orden!',
            'text': 'Tus finanzas se ven bien. Sigue manteniendo el control de tus gastos.'
        })

    return recs
