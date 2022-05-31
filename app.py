# app.py
from cmath import acos
from itertools import count
from flask import Flask, g,  request, session, redirect, url_for, render_template, flash
import psycopg2  # pip install psycopg2
import psycopg2.extras
import re
from werkzeug.security import generate_password_hash, check_password_hash
import json
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length
from flask_wtf import FlaskForm
from datetime import datetime
import datetime

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

                # Borra los intentos con ese nombre de usuario
                cursor.execute("TRUNCATE TABLE intentos")
                conn.commit()

                if account['admin'] == 1:
                    return redirect(url_for('home_admin'))
                else:
                    # Redirect to home page
                    return redirect(url_for('home'))

            else:
                # Account doesnt exist or username/password incorrect
                flash('Incorrect username/password')
                # Inserta el intento fallido
                cursor.execute(
                    "INSERT INTO intentos (usuario, fallos) VALUES (%s,%s)", ('usuario1', '1',))
                conn.commit()
                # cuenta cuantos intentos fallidos van
                cursor.execute(
                    'select count(*) from intentos where usuario =%s ', ('usuario1',))
                contador = cursor.fetchone()
                # Muestra el mensaje
                mensaje = f"Lleva: {contador} intentos fallidos"
                flash(mensaje)
                contadort = contador['count']
                if contadort >= 5:
                    return render_template('intentos.html')

        else:
            # Account doesnt exist or username/password incorrect
            flash('Incorrect username/password')
            # Inserta el intento fallido
            cursor.execute(
                "INSERT INTO intentos (usuario, fallos) VALUES (%s,%s)", ('usuario1', '1',))
            conn.commit()
            # cuenta cuantos intentos fallidos van
            cursor.execute(
                'select count(*) from intentos where usuario =%s ', ('usuario1',))
            contador = cursor.fetchone()
            # Muestra el mensaje
            mensaje = f"Lleva: {contador} intentos fallidos"
            flash(mensaje)
            contadort = contador['count']
            if contadort >= 5:
                return render_template('intentos.html')

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
        fecha_creacion = datetime.date.today()

        _hashed_password = generate_password_hash(password)

        # Check if account exists using MySQL
        cursor.execute(
            'SELECT * FROM cuentas WHERE username = %s', (username,))
        account = cursor.fetchone()

        cursor.execute('''create or replace function crear_cuenta()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Creacion Cuenta", datetime.datetime.now()))
        conn.commit()

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

    email = account['email']

    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if account['tipocuenta'] == 'Premium':
        cursor.execute(
            'SELECT COUNT(*) FROM perfiles WHERE email = %s', [account['email']])
        contador = cursor.fetchone()

        if contador[0] < 8:
            if request.method == 'POST' and 'nombreperfil' in request.form:
                nombre_perfil = request.form['nombreperfil']
                email = account['email']

                # Account doesnt exists and the form data is valid, now insert new account into cuentas table
                cursor.execute("INSERT INTO perfiles (nombre_perfil, email) VALUES (%s,%s)",
                               (nombre_perfil, email))
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

                # Account doesnt exists and the form data is valid, now insert new account into cuentas table
                cursor.execute("INSERT INTO perfiles (nombre_perfil, email) VALUES (%s,%s)",
                               (nombre_perfil, email))
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

                # Account doesnt exists and the form data is valid, now insert new account into cuentas table
                cursor.execute("INSERT INTO perfiles (nombre_perfil, email) VALUES (%s,%s)",
                               (nombre_perfil, email))
                conn.commit()
                flash('Perfil creado con exito')
        else:
            if request.method == 'POST' and 'nombreperfil' in request.form:
                flash('Ya no se pueden crear mas perfiles')

    cursor.execute('''create or replace function nuevo_perfil()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Crear Perfil", datetime.datetime.now()))
    conn.commit()

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

    cursor.execute('''create or replace function borrar_perfil()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Borrar Perfil", datetime.datetime.now()))
    conn.commit()

    return render_template('borrar_perfiles.html', perfiles=perfiles, account=account)


@app.route('/cambiocuenta', methods=['GET', 'POST'])
def cambiocuenta():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    email = account['email']

    if 'tipocuenta' in request.form:
        # Check tipo de cuenta
        tipocuenta = request.form['tipocuenta']

        cursor.execute('UPDATE cuentas SET tipocuenta = %s WHERE username  = %s',
                       (tipocuenta, session['username']))
        conn.commit()
        flash('Tipo de Cuenta Actualizada')

    cursor.execute('''create or replace function update_cuenta()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Update Cuenta", datetime.datetime.now()))
    conn.commit()

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
        'select * from serie_peliculas s where categoria = (select s.categoria from contenido c natural join serie_peliculas s where c.nombre_perfil = %s and c.correo_cuenta = %s order by id desc limit 1)', (name, email,))
    recomendaciones = cursor.fetchall()

    # ingresar la hora y fech que entro al perfil
    now = datetime.datetime.now()
    hora = now.strftime("%H:%M:%S")
    fecha = datetime.date.today()
    cursor.execute(
        'insert into horas_uso(email, nombre_perfil, fecha_ingreso,hora_ingreso) values(%s,%s,%s,%s)', (email, name, fecha, hora))

    # update de perfil a activo
    cursor.execute(
        'UPDATE perfiles SET activo = 1 WHERE nombre_perfil = (%s) AND email = (%s)', (name, email))
    conn.commit()

    cursor.execute('''create or replace function update_perfil()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Update Perfil", datetime.datetime.now()))
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

    cursor.execute('''create or replace function update_perfil()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Update Perfil", datetime.datetime.now()))
    conn.commit()
    # User is loggedin show them the home page
    return render_template('home.html', username=session['username'], account=account, perfiles=perfiles)


@app.route('/mylist/<name>')
def mylist(name):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()
    tipocuenta = account['tipocuenta']

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
    return render_template('mylist.html', account=account, perfil=perfil, serie_pelicula=serie_pelicula, anuncios=anuncios, tipocuenta=tipocuenta)


@app.route('/agregar_pos', methods=['POST', 'GET'])
def agregar_pos():

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    email = account['email']

    cursor.execute('''create or replace function agregar_serie_pelicula()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Agregar Serie_Pelicula", datetime.datetime.now()))
    conn.commit()

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

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    email = account['email']

    cursor.execute('''create or replace function agregar_actor()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Agregar Actor", datetime.datetime.now()))
    conn.commit()

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

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    email = account['email']

    cursor.execute('''create or replace function update_serie_pelicula()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Update Serie_Pelicula", datetime.datetime.now()))
    conn.commit()

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

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    email = account['email']

    cursor.execute('''create or replace function update_actor()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Update Actor", datetime.datetime.now()))
    conn.commit()

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

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    email = account['email']

    cursor.execute('''create or replace function delete_serie_pelicula()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Delete Serie_Pelicula", datetime.datetime.now()))
    conn.commit()

    cursor.execute('''create or replace function delete_actor()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Delete Actor", datetime.datetime.now()))
    conn.commit()

    cursor.execute(
        'DELETE FROM serie_peliculas WHERE serie_pelicula=%s', (name,))
    cursor.execute(
        'DELETE FROM actores WHERE serie_pelicula=%s', (name,))
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

            cursor.execute('''create or replace function update_cuenta()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Update Cuenta", datetime.datetime.now()))
            conn.commit()

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

    cursor.execute('''create or replace function borrar_cuenta()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (correo, "Borrar Cuenta", datetime.datetime.now()))
    conn.commit()

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
    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    email = account['email']

    cursor.execute('''create or replace function agregar_anunciante()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Agregar anunciante", datetime.datetime.now()))
    conn.commit()

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
    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    email = account['email']

    cursor.execute('''create or replace function delete_anunciante()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Delete anunciante", datetime.datetime.now()))
    conn.commit()

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

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    email = account['email']

    cursor.execute('''create or replace function agregar_anuncio()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Agregar Anuncio", datetime.datetime.now()))
    conn.commit()

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

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    email = account['email']

    cursor.execute('''create or replace function update_anuncio()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Update Anuncio", datetime.datetime.now()))
    conn.commit()
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

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    email = account['email']

    cursor.execute('''create or replace function delete_anuncio()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email, "Delete Anuncio", datetime.datetime.now()))
    conn.commit()

    cursor.execute(
        'DELETE FROM anuncios WHERE nombre_anuncio=%s', (anuncio,))
    conn.commit()
    flash("Anuncio borrado con éxito")
    return render_template('borrar_anunciantes.html')


@app.route('/favoritos/<name>/<sp>/<cuenta>')
def favoritos(sp, name, cuenta):

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()
    tipocuenta = account['tipocuenta']

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

    return render_template('mylist.html', perfil=perfil, serie_pelicula=serie_pelicula, anuncios=anuncios, tipocuenta=tipocuenta)


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
    tipocuenta = account['tipocuenta']

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
    return render_template('watched.html', account=account, perfil=perfil, serie_pelicula=serie_pelicula, anuncios=anuncios, tipocuenta=tipocuenta)


@app.route('/vistos/<name>/<sp>/<cuenta>', methods=['GET', 'POST'])
def vistos(sp, name, cuenta):

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()
    tipocuenta = account['tipocuenta']

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
            'insert into contenido (serie_pelicula,nombre_perfil,correo_cuenta,fecha_terminado) values (%s,%s,%s,%s)', (sp, name, cuenta, datetime.datetime.now(),))
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

    return render_template('watched.html', account=account, perfil=perfil, serie_pelicula=serie_pelicula, anuncios=anuncios, tipocuenta=tipocuenta)


@app.route('/viendo/<name>/<sp>/<cuenta>', methods=['GET', 'POST'])
def viendo(sp, name, cuenta):

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()
    tipocuenta = account['tipocuenta']

    cursor.execute(
        'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
    perfil = cursor.fetchone()

    cursor.execute(
        'select CAST(COUNT(*) AS BIT) FROM viendo WHERE serie_pelicula  = (%s) and nombre_perfil = (%s)and cuenta = (%s)', (sp, name, cuenta,))
    contador = cursor.fetchone()

    contador = contador['count']

    if contador == '0':
        cursor.execute(
            'insert into viendo (serie_pelicula,nombre_perfil,cuenta,fecha_comienzo) values (%s,%s,%s,%s)', (sp, name, cuenta,datetime.datetime.now(),))
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

    return redirect(link, code=302)


@app.route('/watching/<name>')
def watching(name):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()
    tipocuenta = account['tipocuenta']

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
    return render_template('viendo.html', account=account, perfil=perfil, serie_pelicula=serie_pelicula, anuncios=anuncios, tipocuenta=tipocuenta)

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

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()
    tipocuenta = account['tipocuenta']

    form = SearchForm()

    cursor.execute(
        'select * from anuncios')
    anuncios = cursor.fetchall()
    #posts = Post.query
    if form.validate_on_submit():

        # Obtener la data enviada
        post = form.searched.data

        # inserta lo buscado en una nueva tabla
        cursor.execute(
            'INSERT INTO historial (busqueda) VALUES (%s)', (post,))

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

        conn.commit()

        return render_template("search.html", form=form, searched=post, posts=posts, actores=actor, directores=director, categorias=categoria, perfil=perfil, anuncios=anuncios, tipocuenta=tipocuenta)


@app.route('/prequery1/', methods=["POST", "GET"])
def prequery1():
    return render_template("prequery1.html")


@app.route('/query1/', methods=["POST", "GET"])
def query1():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    fecha1 = request.form['fechain']
    fecha2 = request.form['fechafi']
    # top generos vistos en rango de fechas
    cursor.execute('select serie_peliculas.categoria as categoria, count(*) as cantidad_por_genero from contenido natural join serie_peliculas where date(fecha_terminado) between %s and %s group by serie_peliculas.categoria order by cantidad_por_genero  desc limit 10', (fecha1, fecha2))
    categorias = cursor.fetchall()
    # minutos consumidos
    cursor.execute('select sum(duracion) as total_mins_consumidos from contenido natural join serie_peliculas where date(fecha_terminado) between %s and %s', (fecha1, fecha2))
    minutos = cursor.fetchone()
    return render_template("query1.html", categorias=categorias, minutos=minutos)


@app.route('/prequery2/', methods=["POST", "GET"])
def prequery2():
    return render_template("prequery2.html")


@app.route('/query2/', methods=["POST", "GET"])
def query2():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    fecha1 = request.form['fechain']
    fecha2 = request.form['fechafi']
    # top generos vistos en rango de fechas por tipo de cuenta
    cursor.execute('select serie_peliculas.categoria as categoria, count(*) as cantidad_por_categoria from contenido join cuentas on cuentas.email = contenido.correo_cuenta natural join serie_peliculas where tipocuenta = %s and date(fecha_terminado) between %s and %s group by serie_peliculas.categoria order by cantidad_por_categoria desc limit 10', ('Gratis', fecha1, fecha2))
    gratis = cursor.fetchall()
    cursor.execute('select serie_peliculas.categoria as categoria, count(*) as cantidad_por_categoria from contenido join cuentas on cuentas.email = contenido.correo_cuenta natural join serie_peliculas where tipocuenta = %s and date(fecha_terminado) between %s and %s group by serie_peliculas.categoria order by cantidad_por_categoria desc limit 10', ('Standard', fecha1, fecha2))
    standard = cursor.fetchall()
    cursor.execute('select serie_peliculas.categoria as categoria, count(*) as cantidad_por_categoria from contenido join cuentas on cuentas.email = contenido.correo_cuenta natural join serie_peliculas where tipocuenta = %s and date(fecha_terminado) between %s and %s group by serie_peliculas.categoria order by cantidad_por_categoria desc limit 10', ('Premium', fecha1, fecha2))
    premium = cursor.fetchall()
    return render_template("query2.html", gratis=gratis, standard=standard, premium=premium)


@app.route('/query3/', methods=["POST", "GET"])
def query3():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # top 10 directores
    cursor.execute(
        'select actores.nombre_actor as nombre_actor, count(serie_peliculas.serie_pelicula) as conteo_apariciones from contenido join cuentas on cuentas.email = contenido.correo_cuenta natural join serie_peliculas inner join actores on serie_peliculas.serie_pelicula = actores.serie_pelicula where cuentas.tipocuenta = %s or cuentas.tipocuenta = %s group by actores.nombre_actor, serie_peliculas.serie_pelicula order by conteo_apariciones desc limit 10', ('Standard', 'Premium'))
    actores = cursor.fetchall()
    # top 10 actores
    cursor.execute(
        'select serie_peliculas.director as nombre_director, count(serie_peliculas.serie_pelicula) as conteo_apariciones from contenido join cuentas on cuentas.email = contenido.correo_cuenta natural join serie_peliculas where cuentas.tipocuenta = %s or cuentas.tipocuenta = %s group by serie_peliculas.director, serie_peliculas.serie_pelicula order by conteo_apariciones desc limit 10', ('Standard', 'Premium'))
    directores = cursor.fetchall()
    return render_template("query3.html", directores=directores, actores=actores)


@app.route('/query4/', methods=["POST", "GET"])
def query4():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # total de cuentas avanzadas creadas en 6 meses anteriores
    cursor.execute(
        'select * from cuentas where tipocuenta = %s and fecha_creacion >= (current_date - INTERVAL %s)', ('Premium', '6 months'))
    resultados = cursor.fetchall()
    # conteo de cuentas avanzaas creadas en 6 meses anteriores
    cursor.execute(
        'select count(*) from cuentas where tipocuenta = %s and fecha_creacion >= (current_date - INTERVAL %s)', ('Premium', '6 months'))
    conteo = cursor.fetchone()
    return render_template("query4.html", resultados=resultados, conteo=conteo)


@app.route('/prequery5/', methods=["POST", "GET"])
def prequery5():
    return render_template("prequery5.html")


@app.route('/query5/', methods=["POST", "GET"])
def query5():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    fecha = request.form['fecha']
    # ultimo query
    cursor.execute(
        'select extract(hour from hora_ingreso) as hora,count(extract(hour from hora_ingreso)) as repeticiones_hora  from horas_uso hu where fecha_ingreso = %s group by extract(hour from hora_ingreso) order by repeticiones_hora desc limit 1', (fecha,))
    resultados = cursor.fetchone()
    hora_pico = resultados['hora']
    repeticiones_hora = resultados['repeticiones_hora']
    return render_template("query5.html", hora_pico=hora_pico, repeticiones_hora=repeticiones_hora, fecha=fecha)


# PROYECTO 3 DE ACA EN ADELANTE

@app.route('/prequery6/', methods=["POST", "GET"])
def prequery6():
    return render_template("prequery6.html")


@app.route('/query6/', methods=["POST", "GET"])
def query6():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    mes = request.form['mes']

    # CREATE OR REPLACE VIEW top_copntenido_visto as
    # select c.serie_pelicula, count(c.serie_pelicula) from contenido c
    # where extract (month from c.fecha_terminado ) = 06
    # and extract (hour from c.fecha_terminado) not between 1 and 8
    # group by c.serie_pelicula order by count(c.serie_pelicula) desc limit 5  ;
    # CREATE OR REPLACE VIEW contenido_visto as
    # select * from contenido;

    # El top 5 de contenido visto en cada hora entre 9:00 a.m a 1:00 a.m para un mes dado.
    cursor.execute('select c.serie_pelicula as titulo , count(c.serie_pelicula) as vistos from contenido_visto c where extract (month from c.fecha_terminado ) = %s and extract (hour from c.fecha_terminado) not between 1 and 8 group by c.serie_pelicula order by count(c.serie_pelicula) desc limit 5', (mes,))
    resultado = cursor.fetchall()
    return render_template("query6.html", resultado=resultado)


@app.route('/query7/', methods=["POST", "GET"])
def query7():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # create index busqueda on historial(busqueda);
    # create MATERIALIZED VIEW busquedas AS
    # select busqueda , count(*) as busquedas
    #     from historial
    # group by busqueda  order by busquedas desc limit 10;

    # manda a refrescar la vista
    cursor.execute(
        'REFRESH MATERIALIZED VIEW busquedas')

    # manda a llamar el query
    cursor.execute(
        'select * from busquedas')
    busquedas = cursor.fetchall()
    return render_template("query7.html", busquedas=busquedas)


@app.route('/hacer_admins/', methods=['GET', 'POST'])
def hacer_admins():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Mando a llamar Peliculas y series
    cursor.execute(
        'select *  from cuentas')
    usuarios = cursor.fetchall()
    return render_template('hacer_admins.html', usuarios=usuarios)


@app.route('/hacer_admin/<usuario>', methods=['GET', 'POST'])
def hacer_admin(usuario):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    email1 = account['email']

    cursor.execute('''create or replace function update_cuenta()
                    returns trigger as 
                    $BODY$
                    begin 
                        insert into bitacora (correo_cuenta , accion , fecha_accion ) values (%s,%s,%s);
                        return new;
                    end;
                    $BODY$
                    language 'plpgsql'
                    ;''', (email1, "Updata Cuenta", datetime.datetime.now()))
    conn.commit()

    cursor.execute(
        'SELECT email FROM cuentas WHERE username=%s', (usuario,))
    email = cursor.fetchone()
    correo = email['email']
    # actualizar el atributo de qadmin de una cuenta
    cursor.execute(
        'UPDATE cuentas SET admin = 1 WHERE email=%s', (correo,))

    conn.commit()
    flash("Cuenta Upgradeada a Administrador con éxito")
    return render_template('hacer_admins.html')


@app.route('/precrearrepro/', methods=["POST", "GET"])
def precrearrepro():
    return render_template("precrearrepro.html")


@app.route('/crearrepro/', methods=["POST", "GET"])
def crearrepro():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    fecha = request.form['fechain']
    cantidad = request.form['cantidad']

    # ejecucion de procedimiento almacenado
    cursor.execute('call inserccion_aleatoria(%s, %s)', [fecha, cantidad, ])
    conn.commit()

    return render_template("crearrepro.html", fecha=fecha, cantidad=cantidad)

@app.route('/prequery3A/', methods=["POST", "GET"])
def prequery3A():
    return render_template("prequery3A.html")


@app.route('/query3A/', methods=["POST", "GET"])
def query3A():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    fecha1 = request.form['fechain']
    fecha2 = request.form['fechain2']

    cursor.execute('REFRESH MATERIALIZED VIEW admins')
    conn.commit()
    
    # ejecucion de vista materializada 
    cursor.execute('select email , Count(accion) as Cantidad_Acciones from admins where fecha_accion between %s and %s group by email order by Cantidad_acciones desc limit 5;', (fecha1,fecha2))
    adminstop = cursor.fetchall()

    return render_template("query3A.html", fecha1=fecha1, fecha2=fecha2, adminstop=adminstop)


@app.route('/bitacora/', methods=["POST", "GET"])
def bitacora():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Bitacora
    cursor.execute(
        'select * from bitacora;'
    )
    bitacora = cursor.fetchall()
    return render_template("bitacora.html", bitacora=bitacora)


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
