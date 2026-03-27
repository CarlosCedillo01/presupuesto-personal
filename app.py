"""
app.py - Servidor Flask para el Simulador de Presupuesto Personal.
"""

from flask import Flask, request, jsonify, send_from_directory, Response, session, redirect, url_for
import database as db
import csv
import io
from datetime import date
from functools import wraps

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = 'finanzas-express-secret-2024-xK9mP#'


# ============================================================
# Auth helpers
# ============================================================

def require_login(f):
    """Decorador que protege endpoints: requiere sesión activa."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'No autorizado. Inicia sesión.'}), 401
        return f(*args, **kwargs)
    return decorated


def current_user_id():
    return session.get('user_id')


# ============================================================
# Servir frontend
# ============================================================

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    return send_from_directory('static', 'index.html')


@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect('/')
    return send_from_directory('static', 'login.html')


# ============================================================
# API - Autenticación
# ============================================================

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'error': 'Usuario y contraseña son requeridos'}), 400

    user_id = db.verify_credentials(username, password)
    if user_id is None:
        return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401

    session['user_id'] = user_id
    session['username'] = username
    return jsonify({'message': 'Sesión iniciada', 'username': username}), 200


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'message': 'Sesión cerrada'}), 200


@app.route('/api/me', methods=['GET'])
def api_me():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    return jsonify({'user_id': session['user_id'], 'username': session['username']}), 200


# ============================================================
# API - Transacciones
# ============================================================

@app.route('/api/transactions', methods=['GET'])
@require_login
def get_transactions():
    month = request.args.get('month')
    transactions = db.get_transactions(user_id=current_user_id(), month=month)
    return jsonify(transactions)


@app.route('/api/transactions', methods=['POST'])
@require_login
def add_transaction():
    data = request.get_json()
    required = ['type', 'category', 'amount', 'date']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Campo requerido: {field}'}), 400

    if data['type'] not in ('ingreso', 'gasto'):
        return jsonify({'error': 'El tipo debe ser "ingreso" o "gasto"'}), 400

    try:
        amount = float(data['amount'])
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'El monto debe ser un número positivo'}), 400

    tid = db.add_transaction(
        user_id=current_user_id(),
        t_type=data['type'],
        category=data['category'],
        description=data.get('description', ''),
        amount=amount,
        t_date=data['date']
    )
    return jsonify({'id': tid, 'message': 'Transacción registrada'}), 201


@app.route('/api/transactions/<int:tid>', methods=['DELETE'])
@require_login
def delete_transaction(tid):
    db.delete_transaction(tid, user_id=current_user_id())
    return jsonify({'message': 'Transacción eliminada'})


@app.route('/api/reset', methods=['POST'])
@require_login
def reset_data():
    """Borra todas las transacciones, presupuestos y metas de ahorro del usuario."""
    db.reset_user_data(user_id=current_user_id())
    return jsonify({'message': 'Datos reiniciados exitosamente'})


# ============================================================
# API - Presupuestos
# ============================================================

@app.route('/api/budgets', methods=['GET'])
@require_login
def get_budgets():
    month = request.args.get('month')
    budgets = db.get_budgets(user_id=current_user_id(), month=month)
    return jsonify(budgets)


@app.route('/api/budgets', methods=['POST'])
@require_login
def add_budget():
    data = request.get_json()
    required = ['category', 'monthly_limit', 'month']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Campo requerido: {field}'}), 400

    try:
        limit = float(data['monthly_limit'])
        if limit <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'El límite debe ser un número positivo'}), 400

    bid = db.add_budget(
        user_id=current_user_id(),
        category=data['category'],
        monthly_limit=limit,
        month=data['month']
    )
    return jsonify({'id': bid, 'message': 'Presupuesto guardado'}), 201


@app.route('/api/budgets/<int:bid>', methods=['PUT'])
@require_login
def update_budget(bid):
    data = request.get_json()
    if 'monthly_limit' not in data:
        return jsonify({'error': 'Campo requerido: monthly_limit'}), 400
    db.update_budget(bid, float(data['monthly_limit']), user_id=current_user_id())
    return jsonify({'message': 'Presupuesto actualizado'})


@app.route('/api/budgets/<int:bid>', methods=['DELETE'])
@require_login
def delete_budget(bid):
    db.delete_budget(bid, user_id=current_user_id())
    return jsonify({'message': 'Presupuesto eliminado'})


# ============================================================
# API - Alertas
# ============================================================

@app.route('/api/alerts', methods=['GET'])
@require_login
def get_alerts():
    month = request.args.get('month')
    alerts = db.get_alerts(user_id=current_user_id(), month=month)
    return jsonify(alerts)


# ============================================================
# API - Reporte
# ============================================================

@app.route('/api/report', methods=['GET'])
@require_login
def get_report():
    month = request.args.get('month')
    report = db.get_report(user_id=current_user_id(), month=month)
    return jsonify(report)


# ============================================================
# API - Metas de Ahorro
# ============================================================

@app.route('/api/savings', methods=['GET'])
@require_login
def get_savings():
    goals = db.get_savings_goals(user_id=current_user_id())
    for g in goals:
        g['projection'] = _calculate_projection(g)
    return jsonify(goals)


@app.route('/api/savings', methods=['POST'])
@require_login
def add_savings_goal():
    data = request.get_json()
    required = ['name', 'target_amount']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Campo requerido: {field}'}), 400

    try:
        target = float(data['target_amount'])
        if target <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'El monto objetivo debe ser un número positivo'}), 400

    gid = db.add_savings_goal(
        user_id=current_user_id(),
        name=data['name'],
        target_amount=target,
        deadline=data.get('deadline')
    )
    return jsonify({'id': gid, 'message': 'Meta de ahorro creada'}), 201


@app.route('/api/savings/<int:gid>/deposit', methods=['POST'])
@require_login
def deposit_to_goal(gid):
    data = request.get_json()
    if 'amount' not in data:
        return jsonify({'error': 'Campo requerido: amount'}), 400

    try:
        amount = float(data['amount'])
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'El monto debe ser un número positivo'}), 400

    db.deposit_to_goal(gid, amount, user_id=current_user_id())
    return jsonify({'message': 'Depósito realizado'})


@app.route('/api/savings/<int:gid>/withdraw', methods=['POST'])
@require_login
def withdraw_from_goal(gid):
    data = request.get_json()
    if 'amount' not in data:
        return jsonify({'error': 'Campo requerido: amount'}), 400

    try:
        amount = float(data['amount'])
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'El monto debe ser un número positivo'}), 400

    success, message = db.withdraw_from_goal(gid, amount, user_id=current_user_id())
    if not success:
        return jsonify({'error': message}), 400
    return jsonify({'message': message})


@app.route('/api/savings/<int:gid>', methods=['DELETE'])
@require_login
def delete_savings_goal(gid):
    db.delete_savings_goal(gid, user_id=current_user_id())
    return jsonify({'message': 'Meta eliminada'})


# ============================================================
# API - Exportar CSV
# ============================================================

@app.route('/api/export/csv', methods=['GET'])
@require_login
def export_csv():
    month = request.args.get('month')
    transactions = db.get_transactions(user_id=current_user_id(), month=month)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Tipo', 'Categoria', 'Descripcion', 'Monto', 'Fecha'])

    for t in transactions:
        writer.writerow([t['id'], t['type'], t['category'], t['description'], t['amount'], t['date']])

    csv_data = output.getvalue()
    output.close()

    month_label = month if month else 'todos'
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=transacciones_{month_label}.csv'}
    )


# ============================================================
# Helpers
# ============================================================

def _calculate_projection(goal):
    """Calcula la proyección de cuándo se alcanzará la meta de ahorro."""
    from datetime import datetime

    remaining = goal['target_amount'] - goal['current_amount']
    if remaining <= 0:
        return {'status': 'completed', 'message': '¡Meta alcanzada!', 'percentage': 100}

    percentage = (goal['current_amount'] / goal['target_amount']) * 100

    created = datetime.fromisoformat(goal['created_at'])
    days_elapsed = (datetime.now() - created).days or 1
    daily_rate = goal['current_amount'] / days_elapsed

    projection = {
        'percentage': round(percentage, 1),
        'remaining': round(remaining, 2),
        'daily_rate': round(daily_rate, 2),
        'status': 'in_progress'
    }

    if daily_rate > 0:
        days_needed = remaining / daily_rate
        projected_date = datetime.now().date().__class__.fromordinal(
            datetime.now().date().toordinal() + int(days_needed)
        )
        projection['estimated_date'] = projected_date.isoformat()
        projection['days_remaining'] = int(days_needed)

        if goal['deadline']:
            deadline = datetime.fromisoformat(goal['deadline']).date()
            if projected_date > deadline:
                monthly_needed = remaining / max((deadline - datetime.now().date()).days / 30, 1)
                projection['status'] = 'behind'
                projection['message'] = f'A este ritmo no alcanzarás la meta a tiempo. Necesitas ahorrar ${monthly_needed:,.2f}/mes.'
            else:
                projection['message'] = f'Vas bien. A este ritmo alcanzarás la meta el {projected_date.strftime("%d/%m/%Y")}.'
        else:
            projection['message'] = f'A este ritmo alcanzarás la meta en {int(days_needed)} días ({projected_date.strftime("%d/%m/%Y")}).'
    else:
        projection['message'] = 'Aún no hay depósitos. ¡Comienza a ahorrar!'
        projection['status'] = 'no_deposits'

    return projection


# ============================================================
# Inicialización
# ============================================================

if __name__ == '__main__':
    db.init_db()
    print("🚀 Servidor iniciado en http://localhost:5000")
    app.run(debug=True, port=5000)
