from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
import db
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

ADMIN_CODE = os.getenv('ADMIN_CODE', 'admin123')  # change via env

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Bitte melden Sie sich zuerst an.', 'warning')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        code = request.form.get('code')
        if code == ADMIN_CODE:
            session['admin_logged_in'] = True
            flash('Erfolgreich angemeldet.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Falscher Zugangscode.', 'danger')
    return render_template('admin_login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('Sie wurden abgemeldet.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin_dashboard.html')

@admin_bp.route('/students')
@login_required
def list_students():
    students = db.get_students(include_ill=True)
    return render_template('admin_students.html', students=students)

@admin_bp.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        class_group = request.form.get('class_group', '').strip()
        nummer = request.form.get('nummer', '').strip()
        ill = bool(request.form.get('ill'))
        if not name or not class_group or not nummer:
            flash('Alle Felder angegeben werden müssen.', 'danger')
            return redirect(url_for('admin.add_student'))
        try:
            db.add_student(name, class_group, nummer, ill)
            flash('Schüler erfolgreich hinzugefügt.', 'success')
            return redirect(url_for('admin.list_students'))
        except Exception as e:
            flash(f'Fehler beim Hinzufügen: {e}', 'danger')
    return render_template('admin_add_student.html')

@admin_bp.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = db.get_student_by_id(student_id)
    if not student:
        flash('Schüler nicht gefunden.', 'danger')
        return redirect(url_for('admin.list_students'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        class_group = request.form.get('class_group', '').strip()
        nummer = request.form.get('nummer', '').strip()
        ill = bool(request.form.get('ill'))
        if not name or not class_group or not nummer:
            flash('Alle Felder angegeben werden müssen.', 'danger')
            return redirect(url_for('admin.edit_student', student_id=student_id))
        try:
            db.update_student(student_id, name=name or None, class_group=class_group or None, nummer=nummer or None, ill=ill)
            flash('Schüler erfolgreich aktualisiert.', 'success')
            return redirect(url_for('admin.list_students'))
        except Exception as e:
            flash(f'Fehler beim Aktualisieren: {e}', 'danger')
    return render_template('admin_edit_student.html', student=student)

@admin_bp.route('/delete_student/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    try:
        db.delete_student(student_id)
        flash('Schüler erfolgreich gelöscht.', 'success')
    except Exception as e:
        flash(f'Fehler beim Löschen: {e}', 'danger')
    return redirect(url_for('admin.list_students'))

@admin_bp.route('/laeufe')
@login_required
def list_laeufe():
    laeufe = db.get_laeufe()
    return render_template('admin_laeufe.html', laeufe=laeufe)

@admin_bp.route('/start_lauf', methods=['GET', 'POST'])
@login_required
def start_lauf():
    if request.method == 'POST':
        class_group = request.form.get('class_group', '').strip()
        if not class_group:
            flash('Klasse/Gruppe erforderlich.', 'danger')
            return redirect(url_for('admin.start_lauf'))
        try:
            lauf_id = db.start_lauf(class_group)
            flash(f'Lauf für {class_group} gestartet (ID: {lauf_id}).', 'success')
            return redirect(url_for('admin.list_laeufe'))
        except Exception as e:
            flash(f'Fehler beim Starten des Laufs: {e}', 'danger')
    # Suggest class groups from students
    students = db.get_students()
    class_groups = sorted(set(s['class_group'] for s in students if s['class_group']))
    return render_template('admin_start_lauf.html', class_groups=class_groups)

@admin_bp.route('/end_lauf', methods=['POST'])
@login_required
def end_lauf():
    lauf_id = request.form.get('lauf_id')
    if not lauf_id:
        flash('Lauf-ID erforderlich.', 'danger')
        return redirect(url_for('admin.list_laeufe'))
    try:
        db.end_lauf(int(lauf_id))
        flash('Lauf beendet.', 'success')
    except Exception as e:
        flash(f'Fehler: {e}', 'danger')
    return redirect(url_for('admin.list_laeufe'))

@admin_bp.route('/measurements')
@login_required
def list_measurements():
    measurements = db.get_measurements(limit=100)
    return render_template('admin_measurements.html', measurements=measurements)

@admin_bp.route('/clear_measurements', methods=['POST'])
@login_required
def clear_measurements():
    try:
        db.clear_measurements()
        flash('Alle Messungen wurden gelöscht.', 'success')
    except Exception as e:
        flash(f'Fehler beim Löschen der Messungen: {e}', 'danger')
    return redirect(url_for('admin.list_measurements'))

# Optional JSON APIs for frontend use if needed
@admin_bp.route('/api/students')
@login_required
def api_students():
    return jsonify(db.get_students(include_ill=True))

@admin_bp.route('/api/measurements')
@login_required
def api_measurements():
    return jsonify(db.get_measurements())