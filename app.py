# app.py
from cmath import acos
from flask import Flask, request, session, redirect, url_for, render_template, flash
import psycopg2  # pip install psycopg2
import psycopg2.extras
import re
from werkzeug.security import generate_password_hash, check_password_hash
import json
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length
from flask_wtf import FlaskForm

app = Flask(__name__)
app.secret_key = 'cairocoders-ednalan'

DB_HOST = "database-3.cruxh0msewub.us-east-2.rds.amazonaws.com"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "proyecto2bases"

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                        password=DB_PASS, host=DB_HOST)


@app.route('/')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
        account = cursor.fetchone()

        cursor.execute('SELECT * FROM perfiles WHERE email = %s',
                       [account['email']])
        perfiles = cursor.fetchall()

        if account['admin'] == 1:
            return redirect(url_for('home_admin'))

        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'], account=account, perfiles=perfiles)

    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/home_admin')
def home_admin():
    # Check if user is loggedin
    if 'loggedin' in session:

        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
        account = cursor.fetchone()

        # User is loggedin show them the home page
        return render_template('home_admin.html', username=session['username'], account=account)

    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    contador = 0

    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']

        # Check if account exists using MySQL
        cursor.execute(
            'SELECT * FROM cuentas WHERE username = %s', (username,))
        # Fetch one record and return result
        account = cursor.fetchone()

        if account:
            password_rs = account['password']
            # If account exists in cuentas table in out database
            if check_password_hash(password_rs, password):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']

                if account['admin'] == 1:
                    return redirect(url_for('home_admin'))
                else:
                    # Redirect to home page
                    return redirect(url_for('home'))

            else:
                # Account doesnt exist or username/password incorrect
                flash('Incorrect username/password')
                contador += 1
                mensaje = f"Lleva: {contador} intentos fallidos"
                flash(mensaje)
        else:
            # Account doesnt exist or username/password incorrect
            flash('Incorrect username/password')
            contador += 1
            mensaje = f"Lleva: {contador} intentos fallidos"
            flash(mensaje)

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        fullname = request.form['fullname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        tipocuenta = request.form['tipocuenta']
        admin = 0
        fecha_creacion = '2022-04-14'

        _hashed_password = generate_password_hash(password)

        # Check if account exists using MySQL
        cursor.execute(
            'SELECT * FROM cuentas WHERE username = %s', (username,))
        account = cursor.fetchone()
        print(account)
        # If account exists show error and validation checks
        if account:
            flash('La cuenta ya existe!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Dirección de correo invalida!')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('El usuario solo puede tener caracteres y números!')
        elif not username or not password or not email:
            flash('Por favor llene el formulario!')
        else:
            # Account doesnt exists and the form data is valid, now insert new account into cuentas table
            cursor.execute("INSERT INTO cuentas (fullname, username, password, email, tipocuenta, admin, fecha_creacion) VALUES (%s,%s,%s,%s,%s,%s, %s)",
                           (fullname, username, _hashed_password, email, tipocuenta, admin, fecha_creacion))
            conn.commit()
            flash('Te has registrado correctamente!')
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash('Por favor llene el formulario!')
    # Show registration form with message (if any)
    return render_template('register.html')


@app.route('/profile')
def profile():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check if user is loggedin
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/crear_perfil', methods=['GET', 'POST'])
# manda a pestaña para crear perfil
def crear_perfil():

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if account['tipocuenta'] == 'Premium':
        cursor.execute(
            'SELECT COUNT(*) FROM perfiles WHERE email = %s', [account['email']])
        contador = cursor.fetchone()

        if contador[0] < 8:
            if request.method == 'POST' and 'nombreperfil' in request.form:
                nombre_perfil = request.form['nombreperfil']
                email = account['email']
                fecha_ingreso = '2022-03-31'
                hora_ingreso = '05:49'

                # Account doesnt exists and the form data is valid, now insert new account into cuentas table
                cursor.execute("INSERT INTO perfiles (nombre_perfil, email, fecha_ingreso, hora_ingreso) VALUES (%s,%s,%s,%s)",
                               (nombre_perfil, email, fecha_ingreso, hora_ingreso))
                conn.commit()
                flash('Perfil creado con exito')
        else:
            if request.method == 'POST' and 'nombreperfil' in request.form:
                flash('Ya no se pueden crear mas perfiles')
    elif account['tipocuenta'] == 'Standard':
        cursor.execute(
            'SELECT COUNT(*) FROM perfiles WHERE email = %s', [account['email']])
        contador = cursor.fetchone()

        if contador[0] < 4:
            if request.method == 'POST' and 'nombreperfil' in request.form:
                nombre_perfil = request.form['nombreperfil']
                email = account['email']
                fecha_ingreso = '2022-03-31'
                hora_ingreso = '05:49'

                # Account doesnt exists and the form data is valid, now insert new account into cuentas table
                cursor.execute("INSERT INTO perfiles (nombre_perfil, email, fecha_ingreso, hora_ingreso) VALUES (%s,%s,%s,%s)",
                               (nombre_perfil, email, fecha_ingreso, hora_ingreso))
                conn.commit()
                flash('Perfil creado con exito')
        else:
            if request.method == 'POST' and 'nombreperfil' in request.form:
                flash('Ya no se pueden crear mas perfiles')
    else:
        cursor.execute(
            'SELECT COUNT(*) FROM perfiles WHERE email = %s', [account['email']])
        contador = cursor.fetchone()
        print('ResultCount = ', contador[0])
        if contador[0] < 1:
            if request.method == 'POST' and 'nombreperfil' in request.form:
                nombre_perfil = request.form['nombreperfil']
                email = account['email']
                fecha_ingreso = '2022-03-31'
                hora_ingreso = '05:49'

                # Account doesnt exists and the form data is valid, now insert new account into cuentas table
                cursor.execute("INSERT INTO perfiles (nombre_perfil, email, fecha_ingreso, hora_ingreso) VALUES (%s,%s,%s,%s)",
                               (nombre_perfil, email, fecha_ingreso, hora_ingreso))
                conn.commit()
                flash('Perfil creado con exito')
        else:
            if request.method == 'POST' and 'nombreperfil' in request.form:
                flash('Ya no se pueden crear mas perfiles')

    return render_template('crear_perfil.html', username=session['username'])


@app.route('/borrar_perfiles/<email>', methods=['GET', 'POST'])
def borrar_perfiles(email):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Mando a llamar Peliculas y series
    cursor.execute(
        'select *  from perfiles where email = %s', (email,))
    perfiles = cursor.fetchall()

    cursor.execute(
        'select *  from cuentas where email = %s', (email,))
    account = cursor.fetchone()
    email = account['email']
    return render_template('borrar_perfiles.html', perfiles=perfiles, email=email)


@app.route('/borrar_perfil/<email>/<name>/', methods=['GET', 'POST'])
def borrar_perfil(name, email):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        'DELETE FROM perfiles WHERE email=%s and nombre_perfil=%s', (email, name))
    conn.commit()
    flash("Perfil borrado con éxito")

    # Mando a llamar Peliculas y series
    cursor.execute(
        'select *  from perfiles where email = %s', (email,))
    perfiles = cursor.fetchall()

    cursor.execute(
        'select *  from cuentas where email = %s', (email,))
    account = cursor.fetchall()
    return render_template('borrar_perfiles.html', perfiles=perfiles, account=account)


@app.route('/cambiocuenta', methods=['GET', 'POST'])
def cambiocuenta():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    if 'tipocuenta' in request.form:
        # Check tipo de cuenta
        tipocuenta = request.form['tipocuenta']

        cursor.execute('UPDATE cuentas SET tipocuenta = %s WHERE username  = %s',
                       (tipocuenta, session['username']))
        conn.commit()
        flash('Tipo de Cuenta Actualizada')

    # rediregir a cambio cuenta
    return render_template('cambiocuenta.html', account=account)

# Pagina de home de perfiles


@app.route('/homep/<name>')
def homep(name):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()
    tipocuenta = account['tipocuenta']
    email = account['email']

    cursor.execute(
        'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
    perfil = cursor.fetchone()

    # Mando a llamar Peliculas y series
    cursor.execute(
        'select distinct serie_pelicula,imagen,link_repro from serie_peliculas')
    series_peliculas = cursor.fetchall()

    cursor.execute(
        'select * from anuncios')
    anuncios = cursor.fetchall()

    # Buscar contenido similar
    cursor.execute(
        'select distinct serie_pelicula,imagen,link_repro from serie_peliculas')
    recomendaciones = cursor.fetchall()

    # update de perfil a activo
    cursor.execute(
        'UPDATE perfiles SET activo = 1 WHERE nombre_perfil = (%s) AND email = (%s)', (name, email))
    conn.commit()

    # Mandar a pagina de inicio del perfil
    return render_template('homep.html', account=account, perfil=perfil, series_peliculas=series_peliculas, anuncios=anuncios, tipocuenta=tipocuenta, recomendaciones=recomendaciones)


@app.route('/regresar_home/<name>')
def regresar_home(name):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()
    email = account['email']

    # update de perfil a inactivo
    cursor.execute(
        'UPDATE perfiles SET activo = 0 WHERE nombre_perfil = (%s) AND email = (%s)', (name, email))
    conn.commit()

    cursor.execute('SELECT * FROM perfiles WHERE email = %s',
                   [account['email']])
    perfiles = cursor.fetchall()

    # User is loggedin show them the home page
    return render_template('home.html', username=session['username'], account=account, perfiles=perfiles)


@app.route('/mylist/<name>')
def mylist(name):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    cursor.execute(
        'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
    perfil = cursor.fetchone()

    cursor.execute(
        'select * from serie_peliculas sp natural join favoritos f where nombre_perfil = (%s)', (name,))
    serie_pelicula = cursor.fetchall()

    cursor.execute(
        'select * from anuncios')
    anuncios = cursor.fetchall()

    # Mandar a pagina de inicio del perfil
    # , vistos=vistos
    return render_template('mylist.html', account=account, perfil=perfil, serie_pelicula=serie_pelicula, anuncios=anuncios)


@app.route('/agregar_pos', methods=['POST', 'GET'])
def agregar_pos():

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == 'POST' and 'nombre' in request.form and 'imagen' in request.form and 'link' in request.form and 'director' in request.form:
        pelicula_serie = request.form['nombre']
        imagen = request.form['imagen']
        link = request.form['link']
        director = request.form['director']
        categoria = request.form['categoria']
        premios = request.form['premios']
        estreno = request.form['estreno']
        duracion = request.form['duracion']

        # Account doesnt exists and the form data is valid, now insert new account into cuentas table
        cursor.execute("INSERT INTO serie_peliculas (serie_pelicula, imagen, link_repro, director, categoria, premios, estreno, duracion) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                       (pelicula_serie, imagen, link, director, categoria, premios, estreno, duracion))
        conn.commit()
        flash('Serie/Película creada con éxito')

    # Mandar a pagina para agregar series o peliculas
    return render_template('agregar_pos.html')


@app.route('/agregar_actores/<string:nombrepos>/<string:nombreac>', methods=['POST'])
def agregar_actores(nombrepos, nombreac):

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    nombrepos = json.loads(nombrepos)
    nombreac = json.loads(nombreac)

    # Account doesnt exists and the form data is valid, now insert new account into cuentas table
    cursor.execute("INSERT INTO actores (serie_pelicula, nombre_actor) VALUES (%s,%s)",
                   (nombrepos, nombreac))
    conn.commit()

    return ('/')


@app.route('/premodificar_pos/', methods=['GET', 'POST'])
def premodificar_pos():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Mando a llamar Peliculas y series
    cursor.execute(
        'select distinct serie_pelicula,imagen,link_repro from serie_peliculas')
    series_peliculas = cursor.fetchall()

    # Mandar a pagina para agregar series o peliculas
    return render_template('premodificar_pos.html', series_peliculas=series_peliculas)


@app.route('/modificaruno/<nombrepos>', methods=['POST', 'GET'])
def modificaruno(nombrepos):
    print(nombrepos)
    return render_template('modificaruno.html', nombrepos=nombrepos)


@app.route('/modificar_pos/<nombrepos>', methods=['POST', 'GET'])
def modificar_pos(nombrepos):
    nombrepos = nombrepos
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == 'POST' and 'nombre' in request.form and 'imagen' in request.form and 'link' in request.form and 'director' in request.form:
        pelicula_serie = request.form['nombre']
        imagen = request.form['imagen']
        link = request.form['link']
        director = request.form['director']
        categoria = request.form['categoria']
        premios = request.form['premios']
        estreno = request.form['estreno']
        duracion = request.form['duracion']

        # Account doesnt exists and the form data is valid, now insert new account into cuentas table
        cursor.execute("UPDATE serie_peliculas SET serie_pelicula = %s, imagen = %s, link_repro = %s, director = %s, categoria = %s, premios = %s, estreno = %s, duracion = %s WHERE serie_pelicula = %s",
                       (pelicula_serie, imagen, link, director, categoria, premios, estreno, duracion, nombrepos))
        # UPDATE weather SET temp_lo = temp_lo+1, temp_hi = temp_lo+15, prcp = DEFAULT WHERE city = 'San Francisco'
        conn.commit()
        flash('Serie/Película actualizada con exito')
    return render_template('modificar_pos.html',  nombrepos=nombrepos)


@app.route('/modificar_actores/<nombrepos>', methods=['POST', 'GET'])
def modificar_actores(nombrepos):
    nombrepos = nombrepos
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Mando a llamar Peliculas y series
    cursor.execute(
        'select * from actores where serie_pelicula = %s', (nombrepos,))
    actores = cursor.fetchall()
    print(nombrepos)
    print(actores)

    if request.method == 'POST' and 'nombrea' in request.form and 'nombren' in request.form:
        nombreantiguo = request.form['nombrea']
        nombrenuevo = request.form['nombren']

        # Account doesnt exists and the form data is valid, now insert new account into cuentas table
        cursor.execute("UPDATE actores SET nombre_actor = %s WHERE nombre_actor= %s AND serie_pelicula = %s",
                       (nombrenuevo, nombreantiguo, nombrepos))
        # UPDATE weather SET temp_lo = temp_lo+1, temp_hi = temp_lo+15, prcp = DEFAULT WHERE city = 'San Francisco'
        conn.commit()
        flash('Serie/Película actualizada con exito')

    return render_template('modificar_actores.html',  nombrepos=nombrepos, actores=actores)


@app.route('/borrar_pos', methods=['GET', 'POST'])
def borrar_pos():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Mando a llamar Peliculas y series
    cursor.execute(
        'select *  from serie_peliculas')
    series_peliculas = cursor.fetchall()

    # Mandar a pagina para borrar series o peliculas
    return render_template('borrar_pos.html', series_peliculas=series_peliculas)


@app.route('/borrar_ps/<name>/', methods=['GET', 'POST'])
def borrar_ps(name):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        'DELETE FROM serie_peliculas WHERE serie_pelicula=%s', (name,))
    conn.commit()
    flash("Serie o Pelicula borrada con éxito")

    # Mando a llamar Peliculas y series
    # Mando a llamar Peliculas y series
    cursor.execute(
        'select *  from serie_peliculas')
    series_peliculas = cursor.fetchall()
    return render_template('borrar_pos.html', series_peliculas=series_peliculas)


@app.route('/modificar_usuarios/', methods=['GET', 'POST'])
def modificar_usuarios():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Mando a llamar Peliculas y series
    cursor.execute(
        'select *  from cuentas')
    usuarios = cursor.fetchall()
    return render_template('modificar_usuarios.html', usuarios=usuarios)


@app.route('/modificar_usuario/<usuario>', methods=['GET', 'POST'])
def modificar_usuario(usuario):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    usuario = usuario

    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.form and 'email' in request.form:
            # Create variables for easy access
            fullname = request.form['fullname']
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            tipocuenta = request.form['tipocuenta']
            admin = 0
            fecha_creacion = request.form['fechacreacion']

            _hashed_password = generate_password_hash(password)

            if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                flash('Dirección de correo invalida!')
            elif not re.match(r'[A-Za-z0-9]+', username):
                flash('El usuario solo puede tener caracteres y números!')
            elif not username or not password or not email:
                flash('Por favor llene el formulario!')
            else:
                cursor.execute("UPDATE cuentas SET fullname = %s, username = %s, password = %s, email = %s, tipocuenta = %s, admin = %s, fecha_creacion = %s WHERE username = %s",
                               (fullname, username, _hashed_password, email, tipocuenta, admin, fecha_creacion, usuario))
                conn.commit()
                flash('Has modificado correctamente!')
        elif request.method == 'POST':
            # Form is empty... (no POST data)
            flash('Por favor llene el formulario!')
        # Show registration form with message (if any)
    return render_template('modificar_usuario.html', usuario=usuario)


@app.route('/borrar_usuarios/', methods=['GET', 'POST'])
def borrar_usuarios():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Mando a llamar Peliculas y series
    cursor.execute(
        'select *  from cuentas')
    usuarios = cursor.fetchall()
    return render_template('borrar_usuarios.html', usuarios=usuarios)


@app.route('/borrar_usuario/<usuario>', methods=['GET', 'POST'])
def borrar_usuario(usuario):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        'SELECT email FROM cuentas WHERE username=%s', (usuario,))
    email = cursor.fetchone()
    correo = email['email']
    # borrar todo a llamar Peliculas y series
    cursor.execute(
        'DELETE FROM cuentas WHERE username=%s', (usuario,))
    cursor.execute(
        'DELETE FROM perfiles WHERE email=%s', (correo,))
    cursor.execute(
        'DELETE FROM contenido WHERE correo_cuenta=%s', (correo,))
    cursor.execute(
        'DELETE FROM favoritos WHERE correo_cuenta=%s', (correo,))
    cursor.execute(
        'DELETE FROM sugerencias WHERE correo_cuenta=%s', (correo,))
    conn.commit()
    flash("Usuario desactivado con éxito")
    return render_template('borrar_usuarios.html')


@app.route('/agregar_anunciante', methods=['POST', 'GET'])
def agregar_anunciante():

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if request.method == 'POST' and 'nombrean' in request.form and 'correo' in request.form and 'telefono' in request.form:
        nombre_anunciante = request.form['nombrean']
        correo_contacto = request.form['correo']
        telefono = request.form['telefono']

        # Account doesnt exists and the form data is valid, now insert new account into cuentas table
        cursor.execute("INSERT INTO anunciantes (nombre_anunciante, correo_contacto, telefono) VALUES (%s,%s,%s)",
                       (nombre_anunciante, correo_contacto, telefono))
        conn.commit()
        flash('Anunciante creado con éxito')

    # Mandar a pagina para agregar series o peliculas
    return render_template('agregar_anunciante.html')


@app.route('/borrar_anunciantes/', methods=['GET', 'POST'])
def borrar_anunciantes():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Mando a llamar a anunciantes y anuncios
    cursor.execute(
        'select *  from anunciantes')
    anunciantes = cursor.fetchall()

    cursor.execute(
        'select *  from anuncios')
    anuncios = cursor.fetchall()
    return render_template('borrar_anunciantes.html', anunciantes=anunciantes, anuncios=anuncios)


@app.route('/borrar_anunciante/<anunciante>', methods=['GET', 'POST'])
def borrar_anunciante(anunciante):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Mando a eliminar a anunciantes y anuncios con el nombre del anunciante
    cursor.execute(
        'DELETE FROM anunciantes WHERE nombre_anunciante=%s', (anunciante,))
    cursor.execute(
        'DELETE FROM anuncios WHERE anunciante=%s', (anunciante,))
    conn.commit()
    flash("Anunciante borrado con éxito")
    return render_template('borrar_anunciantes.html')


@app.route('/agregar_anuncio', methods=['POST', 'GET'])
def agregar_anuncio():

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute(
        'select *  from anunciantes')
    anunciantes = cursor.fetchall()

    if request.method == 'POST' and 'nombrean' in request.form and 'link' in request.form and 'anunciante' in request.form:
        nombre_anuncio = request.form['nombrean']
        link = request.form['link']
        anunciante = request.form['anunciante']

        # Account doesnt exists and the form data is valid, now insert new account into cuentas table
        cursor.execute("INSERT INTO anuncios (nombre_anuncio, link_anuncio, anunciante) VALUES (%s,%s,%s)",
                       (nombre_anuncio, link, anunciante))
        conn.commit()
        flash('Anuncio creado con éxito')

    # Mandar a pagina para agregar series o peliculas
    return render_template('agregar_anuncio.html', anunciantes=anunciantes)


@app.route('/modificar_anuncios/', methods=['GET', 'POST'])
def modificar_anuncios():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Mando a llamar a anunciantes y anuncios
    cursor.execute(
        'select *  from anunciantes')
    anunciantes = cursor.fetchall()
    cursor.execute(
        'select *  from anuncios')
    anuncios = cursor.fetchall()
    return render_template('modificar_anuncios.html', anuncios=anuncios, anunciantes=anunciantes)


@app.route('/modificar_anuncio/<anuncio>', methods=['GET', 'POST'])
def modificar_anuncio(anuncio):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    anuncio = anuncio

    cursor.execute(
        'select *  from anunciantes')
    anunciantes = cursor.fetchall()
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST':
        if request.method == 'POST' and 'nombrean' in request.form and 'link' in request.form and 'anunciante' in request.form:
            nombre_anuncio = request.form['nombrean']
            link = request.form['link']
            anunciante = request.form['anunciante']

            cursor.execute("UPDATE anuncios SET nombre_anuncio = %s, link_anuncio = %s, anunciante = %s WHERE nombre_anuncio = %s",
                           (nombre_anuncio, link, anunciante, anuncio))
            conn.commit()
            flash('Has modificado el anuncio correctamente!')
        elif request.method == 'POST':
            # Form is empty... (no POST data)
            flash('Por favor llene el formulario!')
        # Show registration form with message (if any)
    return render_template('modificar_anuncio.html', anuncio=anuncio, anunciantes=anunciantes)


@app.route('/borrar_anuncios/', methods=['GET', 'POST'])
def borrar_anuncios():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Mando a llamar a anunciantes y anuncios
    cursor.execute(
        'select *  from anunciantes')
    anunciantes = cursor.fetchall()

    cursor.execute(
        'select *  from anuncios')
    anuncios = cursor.fetchall()
    return render_template('borrar_anuncios.html', anunciantes=anunciantes, anuncios=anuncios)


@app.route('/borrar_anuncio/<anuncio>', methods=['GET', 'POST'])
def borrar_anuncio(anuncio):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute(
        'DELETE FROM anuncios WHERE nombre_anuncio=%s', (anuncio,))
    conn.commit()
    flash("Anuncio borrado con éxito")
    return render_template('borrar_anunciantes.html')


@app.route('/favoritos/<name>/<sp>/<cuenta>')
def favoritos(sp, name, cuenta):

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute(
        'SELECT * FROM favoritos WHERE nombre_perfil = (%s)', (name,))
    favoritos = cursor.fetchone()

    cursor.execute(
        'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
    perfil = cursor.fetchone()

    cursor.execute(
        'select CAST(COUNT(*) AS BIT) FROM favoritos WHERE serie_pelicula  = (%s) and nombre_perfil = (%s)', (sp, name,))
    contador = cursor.fetchone()

    contador = contador['count']

    if contador == '0':
        cursor.execute(
            'insert into favoritos (serie_pelicula,nombre_perfil,correo_cuenta) values (%s,%s,%s)', (sp, name, cuenta))
        conn.commit()

        print('Agregado')
    else:
        print('Ya esta agregado')

    cursor.execute(
        'select * from serie_peliculas sp natural join favoritos f where nombre_perfil = (%s)', (name,))
    serie_pelicula = cursor.fetchall()

    cursor.execute(
        'select * from anuncios')
    anuncios = cursor.fetchall()

    return render_template('mylist.html', perfil=perfil, serie_pelicula=serie_pelicula, anuncios=anuncios)


@app.route('/borrar_favoritos/<sp>/<name>')
def borrar_favoritos(sp, name):

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute(
        'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
    perfil = cursor.fetchone()

    cursor.execute(
        'DELETE FROM favoritos WHERE serie_pelicula= (%s)', (sp,))
    conn.commit()
    flash('Serie / Película borrada con exito')

    cursor.execute(
        'select * from serie_peliculas sp natural join favoritos f where nombre_perfil = (%s)', (name,))
    serie_pelicula = cursor.fetchall()

    return render_template('mylist.html', perfil=perfil, serie_pelicula=serie_pelicula)


@app.route('/watched/<name>')
def watched(name):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    cursor.execute(
        'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
    perfil = cursor.fetchone()

    cursor.execute(
        'select * from serie_peliculas sp natural join contenido where nombre_perfil = (%s)', (name,))
    serie_pelicula = cursor.fetchall()

    cursor.execute(
        'select * from anuncios')
    anuncios = cursor.fetchall()

    # Mandar a pagina de inicio del perfil
    # , vistos=vistos
    return render_template('watched.html', account=account, perfil=perfil, serie_pelicula=serie_pelicula, anuncios=anuncios)


@app.route('/vistos/<name>/<sp>/<cuenta>', methods=['GET', 'POST'])
def vistos(sp, name, cuenta):

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    cursor.execute(
        'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
    perfil = cursor.fetchone()

    cursor.execute(
        'select * from anuncios')
    anuncios = cursor.fetchall()

    cursor.execute(
        'select CAST(COUNT(*) AS BIT) FROM contenido c WHERE serie_pelicula  = (%s) and nombre_perfil = (%s) and correo_cuenta = (%s)', (sp, name, cuenta,))
    contador = cursor.fetchone()

    contador = contador['count']

    if contador == '0':
        cursor.execute(
            'insert into contenido (serie_pelicula,nombre_perfil,correo_cuenta) values (%s,%s,%s)', (sp, name, cuenta))
        conn.commit()

        cursor.execute(
            'DELETE FROM viendo WHERE serie_pelicula= (%s)', (sp,))
        conn.commit()

        print('Agregado')
    else:
        print('Ya esta agregado')

        cursor.execute(
            'DELETE FROM viendo WHERE serie_pelicula= (%s)', (sp,))
        conn.commit()

    cursor.execute(
        'select * from serie_peliculas sp natural join contenido c where nombre_perfil = (%s)', (name,))
    serie_pelicula = cursor.fetchall()

    cursor.execute(
        'select link_repro from serie_peliculas sp natural join contenido c where serie_pelicula = (%s) and nombre_perfil = (%s)', (sp, name,))
    link = cursor.fetchone()

    cursor.execute(
        'select * from anuncios')
    anuncios = cursor.fetchall()

    link = link['link_repro']
    print(link)

    return render_template('watched.html', account=account, perfil=perfil, serie_pelicula=serie_pelicula, anuncios=anuncios)


@app.route('/viendo/<name>/<sp>/<cuenta>', methods=['GET', 'POST'])
def viendo(sp, name, cuenta):

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute(
        'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
    perfil = cursor.fetchone()

    cursor.execute(
        'select CAST(COUNT(*) AS BIT) FROM viendo WHERE serie_pelicula  = (%s) and nombre_perfil = (%s)and cuenta = (%s)', (sp, name, cuenta,))
    contador = cursor.fetchone()

    contador = contador['count']

    if contador == '0':
        cursor.execute(
            'insert into viendo (serie_pelicula,nombre_perfil,cuenta) values (%s,%s,%s)', (sp, name, cuenta))
        conn.commit()

        print('Agregado')
    else:
        print('Ya esta agregado')

    cursor.execute(
        'select * from serie_peliculas sp natural join viendo where nombre_perfil = (%s)', (name,))
    serie_pelicula = cursor.fetchall()

    cursor.execute(
        'select link_repro from serie_peliculas sp natural join viendo where serie_pelicula = (%s) and nombre_perfil = (%s)', (sp, name,))
    link = cursor.fetchone()

    link = link['link_repro']
    print(link)

    return redirect(link, code=302)


@app.route('/watching/<name>')
def watching(name):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    cursor.execute(
        'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
    perfil = cursor.fetchone()

    cursor.execute(
        'select * from serie_peliculas sp natural join viendo where nombre_perfil = (%s)', (name,))
    serie_pelicula = cursor.fetchall()

    cursor.execute(
        'select * from anuncios')
    anuncios = cursor.fetchall()

    # Mandar a pagina de inicio del perfil
    # , vistos=vistos
    return render_template('viendo.html', account=account, perfil=perfil, serie_pelicula=serie_pelicula, anuncios=anuncios)

# Pasarse datos con el navbar
# Pass Stuff To Navbar


@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

# Form del buscar


class SearchForm(FlaskForm):
    searched = StringField("Searched", validators=[DataRequired()])
    submit = SubmitField("Submit")

# Funcion de buscar


@app.route('/search/<name>', methods=["POST"])
def search(name):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    form = SearchForm()
    #posts = Post.query
    if form.validate_on_submit():

        # Obtener la data enviada
        post = form.searched.data

        search = "%{}%".format(post)

        cursor.execute(
            'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
        perfil = cursor.fetchone()

        # Query a la base de datos
        # pelicula o serie
        cursor.execute(
            'select serie_pelicula,imagen,link_repro from serie_peliculas where serie_pelicula like %s', (search,))
        posts = cursor.fetchall()

        # director
        cursor.execute(
            'select serie_pelicula,imagen,link_repro from serie_peliculas where director like %s', (search,))
        director = cursor.fetchall()

        # actor
        cursor.execute(
            'select serie_pelicula,imagen,link_repro from actores natural join serie_peliculas where nombre_actor like  %s', (search,))
        actor = cursor.fetchall()

        # categoria
        # director
        cursor.execute(
            'select serie_pelicula,imagen,link_repro from serie_peliculas where categoria like %s', (search,))
        categoria = cursor.fetchall()

        return render_template("search.html",
                               form=form,
                               searched=post,
                               posts=posts,
                               actores=actor,
                               directores=director,
                               categorias=categoria,
                               perfil=perfil)


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)
