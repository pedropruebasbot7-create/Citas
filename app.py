
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3, os
import secrets
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'umbra-beauty-secret-2026')
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'beauty.db')


def repair_corrupted_db():
    if not os.path.exists(DB_PATH):
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('PRAGMA quick_check').fetchone()
        conn.close()
        return
    except sqlite3.DatabaseError:
        pass

    try:
        os.remove(DB_PATH)
    except FileNotFoundError:
        pass


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA quick_check').fetchone()
        return conn
    except sqlite3.DatabaseError:
        repair_corrupted_db()
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def init_db():
    repair_corrupted_db()
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS servicios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        categoria TEXT NOT NULL,
        duracion INTEGER NOT NULL,
        precio REAL NOT NULL,
        descripcion TEXT,
        imagen TEXT,
        activo INTEGER DEFAULT 1
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        categoria TEXT NOT NULL,
        precio REAL NOT NULL,
        stock INTEGER DEFAULT 20,
        descripcion TEXT,
        imagen TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS citas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_nombre TEXT NOT NULL,
        cliente_telefono TEXT NOT NULL,
        cliente_email TEXT,
        servicio_id INTEGER,
        fecha TEXT NOT NULL,
        hora TEXT NOT NULL,
        estado TEXT DEFAULT 'pendiente',
        notas TEXT,
        creado TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(servicio_id) REFERENCES servicios(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_nombre TEXT NOT NULL,
        cliente_email TEXT,
        cliente_telefono TEXT,
        direccion TEXT,
        total REAL NOT NULL,
        estado TEXT DEFAULT 'pendiente',
        fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS pedido_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        producto_id INTEGER,
        cantidad INTEGER,
        precio_unitario REAL,
        FOREIGN KEY(pedido_id) REFERENCES pedidos(id),
        FOREIGN KEY(producto_id) REFERENCES productos(id)
    )''')
    conn.commit()

    if c.execute('SELECT COUNT(*) FROM servicios').fetchone()[0] == 0:
        servicios = [
            ('Pesta\u00f1as Cl\u00e1sicas', 'pesta\u00f1as', 90, 450, 'Mirada natural y elegante, pelo a pelo. Duraci\u00f3n 3-4 semanas.', 'https://images.unsplash.com/photo-1515688594390-b649af70d282?w=600'),
            ('Pesta\u00f1as Volumen Ruso', 'pesta\u00f1as', 120, 650, 'Volumen extremo, mirada de impacto. Ideal para eventos.', 'https://images.unsplash.com/photo-1526045478515-99145907023c?w=600'),
            ('U\u00f1as Acr\u00edlicas', 'u\u00f1as', 90, 380, 'Esculturales, con dise\u00f1o a tu gusto. Incluye gelish.', 'https://images.unsplash.com/photo-1604654894610-df63bc536371?w=600'),
            ('Gelish & Manicure Spa', 'u\u00f1as', 60, 250, 'Cuidado completo + color semipermanente que dura 21 d\u00edas.', 'https://images.unsplash.com/photo-1519014816548-bf5fe059798b?w=600'),
            ('Dise\u00f1o de Cejas HD', 'cejas', 45, 280, 'Depilaci\u00f3n, mapeo y pigmentaci\u00f3n temporal perfecta.', 'https://images.unsplash.com/photo-1570172619644-dfd03ed1350b?w=600'),
            ('Laminado de Cejas', 'cejas', 60, 350, 'Cejas peinadas, definidas y con efecto planchado.', 'https://images.unsplash.com/photo-1583001809873-a128495da465?w=600'),
            ('Acripie Spa de Lujo', 'acripie', 75, 400, 'Pedicure con acr\u00edlico + exfoliaci\u00f3n + masaje relajante.', 'https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?w=600'),
            ('Keratina Brasile\u00f1a', 'keratina', 150, 900, 'Alisado y reparaci\u00f3n profunda, cabello sin frizz 3 meses.', 'https://images.unsplash.com/photo-1560869713-7d0a29430803?w=600'),
            ('Botox Capilar', 'keratina', 90, 550, 'Brillo, hidrataci\u00f3n y fuerza para cabello maltratado.', 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=600'),
        ]
        c.executemany('INSERT INTO servicios (nombre,categoria,duracion,precio,descripcion,imagen) VALUES (?,?,?,?,?,?)', servicios)

    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db()
    servicios = conn.execute('SELECT * FROM servicios WHERE activo=1').fetchall()
    productos = conn.execute('SELECT * FROM productos LIMIT 8').fetchall()
    conn.close()
    return render_template('index.html', servicios=servicios, productos=productos)

@app.route('/agendar', methods=['GET','POST'])
def agendar():
    conn = get_db()
    servicios = conn.execute('SELECT * FROM servicios WHERE activo=1').fetchall()
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        conn.execute('INSERT INTO citas (cliente_nombre, cliente_telefono, cliente_email, servicio_id, fecha, hora, notas) VALUES (?,?,?,?,?,?,?)',
                     (data.get('cliente_nombre'), data.get('cliente_telefono'), data.get('cliente_email'), data.get('servicio_id'), data.get('fecha'), data.get('hora'), data.get('notas')))
        conn.commit()
        conn.close()
        if request.is_json:
            return jsonify({'ok': True, 'msg': 'Cita agendada con exito'})
        return redirect(url_for('historial'))
    conn.close()
    return render_template('agendar.html', servicios=servicios)

@app.route('/tienda')
def tienda():
    conn = get_db()
    productos = conn.execute('SELECT * FROM productos').fetchall()
    conn.close()
    return render_template('tienda.html', productos=productos)

@app.route('/historial')
def historial():
    conn = get_db()
    citas = conn.execute('''SELECT c.*, s.nombre as servicio_nombre, s.precio FROM citas c LEFT JOIN servicios s ON s.id=c.servicio_id ORDER BY c.fecha DESC, c.hora DESC''').fetchall()
    pedidos = conn.execute('SELECT * FROM pedidos ORDER BY fecha_creacion DESC').fetchall()
    conn.close()
    return render_template('historial.html', citas=citas, pedidos=pedidos)

@app.route('/api/citas', methods=['GET','POST'])
def api_citas():
    conn = get_db()
    if request.method == 'POST':
        d = request.get_json()
        conn.execute('INSERT INTO citas (cliente_nombre, cliente_telefono, cliente_email, servicio_id, fecha, hora, notas) VALUES (?,?,?,?,?,?,?)',
                     (d['cliente_nombre'], d['cliente_telefono'], d.get('cliente_email'), d['servicio_id'], d['fecha'], d['hora'], d.get('notas','')))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})
    citas = conn.execute('SELECT c.*, s.nombre as servicio FROM citas c LEFT JOIN servicios s ON s.id=c.servicio_id ORDER BY c.id DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in citas])

@app.route('/api/citas/<int:id>', methods=['PUT','DELETE'])
def api_cita_detail(id):
    conn = get_db()
    if request.method == 'PUT':
        d = request.get_json()
        conn.execute('UPDATE citas SET estado=? WHERE id=?', (d.get('estado'), id))
        conn.commit()
    else:
        conn.execute('DELETE FROM citas WHERE id=?', (id,))
        conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/productos')
def api_productos():
    conn = get_db()
    productos = conn.execute('SELECT * FROM productos').fetchall()
    conn.close()
    return jsonify([dict(r) for r in productos])

@app.route('/api/productos/<int:id>', methods=['PUT','DELETE','POST'])
def api_producto_detail(id):
    conn = get_db()
    if request.method == 'DELETE':
        conn.execute('DELETE FROM productos WHERE id=?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})
    d = request.get_json()
    if id == 0:
        conn.execute('INSERT INTO productos (nombre,categoria,precio,stock,descripcion,imagen) VALUES (?,?,?,?,?,?)',
                     (d['nombre'], d['categoria'], d['precio'], d['stock'], d['descripcion'], d.get('imagen','')))
        conn.commit()
    else:
        conn.execute('UPDATE productos SET nombre=?, categoria=?, precio=?, stock=?, descripcion=?, imagen=? WHERE id=?',
                     (d['nombre'], d['categoria'], d['precio'], d['stock'], d['descripcion'], d.get('imagen',''), id))
        conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/images', methods=['POST'])
def api_image_upload():
    if not session.get('admin'):
        return jsonify({'error': 'Inicia sesión para subir imágenes.'}), 401

    image = request.files.get('image')
    if image is None or not image.filename:
        return jsonify({'error': 'Selecciona una imagen.'}), 400

    extension = os.path.splitext(image.filename)[1].lower()
    signatures = {
        '.jpg': lambda data: data.startswith(b'\xff\xd8\xff'),
        '.jpeg': lambda data: data.startswith(b'\xff\xd8\xff'),
        '.png': lambda data: data.startswith(b'\x89PNG\r\n\x1a\n'),
        '.gif': lambda data: data.startswith((b'GIF87a', b'GIF89a')),
        '.webp': lambda data: len(data) >= 12 and data[:4] == b'RIFF' and data[8:12] == b'WEBP',
    }
    if extension not in signatures:
        return jsonify({'error': 'Usa una imagen JPG, PNG, GIF o WEBP.'}), 400

    image_data = image.stream.read(5 * 1024 * 1024 + 1)
    if len(image_data) > 5 * 1024 * 1024:
        return jsonify({'error': 'La imagen debe pesar 5 MB o menos.'}), 413
    if not signatures[extension](image_data):
        return jsonify({'error': 'El archivo no coincide con el formato de imagen seleccionado.'}), 400

    filename = f'{uuid.uuid4().hex}{extension}'
    upload_dir = os.path.join(app.static_folder, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    with open(os.path.join(upload_dir, filename), 'wb') as uploaded_file:
        uploaded_file.write(image_data)

    return jsonify({'url': url_for('static', filename=f'uploads/{filename}')})

@app.route('/api/servicios', methods=['GET','POST'])
def api_servicios():
    conn = get_db()
    if request.method == 'POST':
        d = request.get_json()
        if d.get('id') == 0:
            conn.execute('INSERT INTO servicios (nombre,categoria,duracion,precio,descripcion,imagen) VALUES (?,?,?,?,?,?)',
                         (d['nombre'], d['categoria'], d['duracion'], d['precio'], d['descripcion'], d.get('imagen','')))
        else:
            conn.execute('UPDATE servicios SET nombre=?, categoria=?, duracion=?, precio=?, descripcion=?, imagen=? WHERE id=?',
                         (d['nombre'], d['categoria'], d['duracion'], d['precio'], d['descripcion'], d.get('imagen',''), d['id']))
        conn.commit()
    servicios = conn.execute('SELECT * FROM servicios').fetchall()
    conn.close()
    return jsonify([dict(r) for r in servicios])

@app.route('/api/servicios/<int:id>', methods=['DELETE'])
def api_servicio_delete(id):
    conn = get_db()
    conn.execute('DELETE FROM servicios WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/pedidos', methods=['GET','POST'])
def api_pedidos():
    conn = get_db()
    if request.method == 'POST':
        d = request.get_json()
        cur = conn.cursor()
        cur.execute('INSERT INTO pedidos (cliente_nombre, cliente_email, cliente_telefono, direccion, total, estado) VALUES (?,?,?,?,?,?)',
                    (d['cliente_nombre'], d.get('cliente_email'), d.get('cliente_telefono'), d.get('direccion',''), d['total'], 'pendiente'))
        pedido_id = cur.lastrowid
        for item in d.get('items', []):
            cur.execute('INSERT INTO pedido_items (pedido_id, producto_id, cantidad, precio_unitario) VALUES (?,?,?,?)',
                        (pedido_id, item['id'], item['cantidad'], item['precio']))
        conn.commit()
        conn.close()
        return jsonify({'ok': True, 'pedido_id': pedido_id})
    pedidos = conn.execute('SELECT * FROM pedidos ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in pedidos])

@app.route('/api/pedidos/<int:id>', methods=['PUT'])
def api_pedido_update(id):
    d = request.get_json()
    conn = get_db()
    conn.execute('UPDATE pedidos SET estado=? WHERE id=?', (d.get('estado'), id))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/admin')
def admin():
    if not session.get('admin'):
        first = secrets.randbelow(9) + 1
        second = secrets.randbelow(9) + 1
        session['admin_sum_answer'] = first + second
        return render_template('admin_login.html', first=first, second=second)
    conn = get_db()
    stats = {
        'citas': conn.execute('SELECT COUNT(*) FROM citas').fetchone()[0],
        'pendientes': conn.execute("SELECT COUNT(*) FROM citas WHERE estado='pendiente'").fetchone()[0],
        'productos': conn.execute('SELECT COUNT(*) FROM productos').fetchone()[0],
        'pedidos': conn.execute('SELECT COUNT(*) FROM pedidos').fetchone()[0],
        'ingresos': conn.execute('SELECT SUM(total) FROM pedidos WHERE estado!="cancelado"').fetchone()[0] or 0
    }
    conn.close()
    return render_template('admin.html', stats=stats)

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json(silent=True) or {}
    expected = session.get('admin_sum_answer')
    if expected is not None and str(data.get('answer', '')).strip() == str(expected):
        session['admin'] = True
        session.pop('admin_sum_answer', None)
        return jsonify({'ok': True})

    first = secrets.randbelow(9) + 1
    second = secrets.randbelow(9) + 1
    session['admin_sum_answer'] = first + second
    return jsonify({'ok': False, 'first': first, 'second': second, 'msg': 'La suma es incorrecta.'}), 401

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    session.pop('admin_sum_answer', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
