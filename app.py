"""
app.py - Servidor Flask para el Simulador de Presupuesto Personal.
"""

from flask import Flask, request, jsonify, send_from_directory, Response
import database as db
import csv
import io
from datetime import date

app = Flask(__name__, static_folder='static', static_url_path='')


# ============================================================
# Servir frontend
# ============================================================

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


# ============================================================
# API - Transacciones
# ============================================================

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    month = request.args.get('month')
    transactions = db.get_transactions(user_id=1, month=month)
    return jsonify(transactions)

"""Punto de enlace (Endpoint) que traduce datos de SQL a JSON.
    1. Consulta las transacciones en la base de datos SQL.
    2. Convierte el resultado a formato JSON para el frontend. """

@app.route('/api/transactions', methods=['POST'])
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
        user_id=1,
        t_type=data['type'],
        category=data['category'],
        description=data.get('description', ''),
        amount=amount,
        t_date=data['date']
    )
    return jsonify({'id': tid, 'message': 'Transacción registrada'}), 201


@app.route('/api/transactions/<int:tid>', methods=['DELETE'])
def delete_transaction(tid):
    db.delete_transaction(tid, user_id=1)
    return jsonify({'message': 'Transacción eliminada'})


# ============================================================
# API - Presupuestos
# ============================================================

@app.route('/api/budgets', methods=['GET'])
def get_budgets():
    month = request.args.get('month')
    budgets = db.get_budgets(user_id=1, month=month)
    return jsonify(budgets)


@app.route('/api/budgets', methods=['POST'])
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
        user_id=1,
        category=data['category'],
        monthly_limit=limit,
        month=data['month']
    )
    return jsonify({'id': bid, 'message': 'Presupuesto guardado'}), 201


@app.route('/api/budgets/<int:bid>', methods=['PUT'])
def update_budget(bid):
    data = request.get_json()
    if 'monthly_limit' not in data:
        return jsonify({'error': 'Campo requerido: monthly_limit'}), 400
    db.update_budget(bid, float(data['monthly_limit']), user_id=1)
    return jsonify({'message': 'Presupuesto actualizado'})


@app.route('/api/budgets/<int:bid>', methods=['DELETE'])
def delete_budget(bid):
    db.delete_budget(bid, user_id=1)
    return jsonify({'message': 'Presupuesto eliminado'})


# ============================================================
# API - Alertas
# ============================================================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    month = request.args.get('month')
    alerts = db.get_alerts(user_id=1, month=month)
    return jsonify(alerts)


# ============================================================
# API - Reporte
# ============================================================

@app.route('/api/report', methods=['GET'])
def get_report():
    month = request.args.get('month')
    report = db.get_report(user_id=1, month=month)
    return jsonify(report)


# ============================================================
# API - Metas de Ahorro
# ============================================================

@app.route('/api/savings', methods=['GET'])
def get_savings():
    goals = db.get_savings_goals(user_id=1)
    # Agregar proyección a cada meta
    for g in goals:
        g['projection'] = _calculate_projection(g)
    return jsonify(goals)


@app.route('/api/savings', methods=['POST'])
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
        user_id=1,
        name=data['name'],
        target_amount=target,
        deadline=data.get('deadline')
    )
    return jsonify({'id': gid, 'message': 'Meta de ahorro creada'}), 201


@app.route('/api/savings/<int:gid>/deposit', methods=['POST'])
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

    db.deposit_to_goal(gid, amount, user_id=1)
    return jsonify({'message': 'Depósito realizado'})


@app.route('/api/savings/<int:gid>', methods=['DELETE'])
def delete_savings_goal(gid):
    db.delete_savings_goal(gid, user_id=1)
    return jsonify({'message': 'Meta eliminada'})


# ============================================================
# API - Exportar CSV
# ============================================================

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    month = request.args.get('month')
    transactions = db.get_transactions(user_id=1, month=month)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Tipo', 'Categoría', 'Descripción', 'Monto', 'Fecha'])

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
