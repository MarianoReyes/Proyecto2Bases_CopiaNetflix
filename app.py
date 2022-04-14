# app.py
from cmath import acos
from flask import Flask, request, session, redirect, url_for, render_template, flash
import psycopg2  # pip install psycopg2
import psycopg2.extras
import re
from werkzeug.security import generate_password_hash, check_password_hash
import json

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

                if account['admin'] == 1:
                    return redirect(url_for('home_admin'))
                else:
                    # Redirect to home page
                    return redirect(url_for('home'))

            else:
                # Account doesnt exist or username/password incorrect
                flash('Incorrect username/password')
        else:
            # Account doesnt exist or username/password incorrect
            flash('Incorrect username/password')

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
            cursor.execute("INSERT INTO cuentas (fullname, username, password, email, tipocuenta, admin) VALUES (%s,%s,%s,%s,%s,%s)",
                           (fullname, username, _hashed_password, email, tipocuenta, admin))
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

    cursor.execute(
        'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
    perfil = cursor.fetchone()

    # Mando a llamar Peliculas y series
    cursor.execute(
        'select distinct serie_pelicula,imagen,link_repro from serie_peliculas')
    series_peliculas = cursor.fetchall()

    # Mandar a pagina de inicio del perfil
    return render_template('homep.html', account=account, perfil=perfil, series_peliculas=series_peliculas)


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


    # Mandar a pagina de inicio del perfil
    # , vistos=vistos
    return render_template('mylist.html', account=account, perfil=perfil, serie_pelicula=serie_pelicula)


@app.route('/watched/<name>')
def watched(name):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute('SELECT * FROM cuentas WHERE id = %s', [session['id']])
    account = cursor.fetchone()

    cursor.execute(
        'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
    perfil = cursor.fetchone()

    # Mando a llamar Peliculas y series
    # cursor.execute(
    # 'select distinct serie_pelicula from contenido inner join serie_peliculas ON serie_pelicula = serie_pelicula')
    #vistos = cursor.fetchall()

    # Mandar a pagina de inicio del perfil
    # , vistos=vistos
    return render_template('watched.html', account=account, perfil=perfil)


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


@app.route('/modificar_pos')
def modificar_pos():
    # Mandar a pagina para agregar series o peliculas
    return render_template('modificar_pos.html')


@app.route('/borrar_pos', methods=['GET', 'POST'])
def borrar_pos():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Mando a llamar Peliculas y series
    cursor.execute(
        'select distinct serie_pelicula,imagen,link_repro from serie_peliculas')
    series_peliculas = cursor.fetchall()

    if request.method == 'POST' and 'nombrepos' in request.form:

        nombrepos = request.form['nombrepos']
        # se comprueba si existe la serie/pelicula
        cursor.execute(
            'SELECT * FROM serie_peliculas WHERE serie_pelicula = %s', (nombrepos,))
        seriepelicula = cursor.fetchone()

        if seriepelicula:
            cursor.execute(
                "DELETE FROM serie_peliculas WHERE serie_pelicula = %s", (nombrepos,))
            cursor.execute(
                "DELETE FROM actores WHERE serie_pelicula = %s", (nombrepos,))
            conn.commit()
            flash('Serie / Película borrada con exito')
        else:
            flash('Serie / Película no existente')

    # Mandar a pagina para borrar series o peliculas
    return render_template('borrar_pos.html', series_peliculas=series_peliculas)


@app.route('/favoritos/<name>/<sp>/<cuenta>')
def favoritos(sp, name, cuenta):

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
<<<<<<< Updated upstream

    print(sp)
    print(name)
    print(cuenta)
    # Mandar a pagina de inicio del perfil

=======
    
>>>>>>> Stashed changes
    cursor.execute(
        'SELECT * FROM favoritos WHERE nombre_perfil = (%s)', (name,))
    favoritos = cursor.fetchone()

    if sp in favoritos:
        flash('Serie / pelicula ya en favoritos')
    else:
        cursor.execute(
            'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
        perfil = cursor.fetchone()

    cursor.execute(
        'insert into favoritos (serie_pelicula,nombre_perfil,correo_cuenta) values (%s,%s,%s)', (sp, name, cuenta))
    conn.commit()

    cursor.execute(
<<<<<<< Updated upstream
        'select * from favoritos where nombre_perfil = (%s)', (name,))
    favoritos = cursor.fetchall()
=======
        'select * from serie_peliculas sp natural join favoritos f where nombre_perfil = (%s)', (name,))
    serie_pelicula = cursor.fetchall()

    return render_template('mylist.html', perfil=perfil,serie_pelicula=serie_pelicula)

@app.route('/borrar_favoritos/<sp>/<name>')
def borrar_favoritos(sp,name):

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute(
        'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
    perfil = cursor.fetchone()

    cursor.execute(
        'DELETE FROM favoritos WHERE serie_pelicula= (%s)',(sp,))
    conn.commit()
    flash('Serie / Película borrada con exito')
>>>>>>> Stashed changes

    cursor.execute(
        'select * from serie_peliculas sp natural join favoritos f where nombre_perfil = (%s)', (name,))
    serie_pelicula = cursor.fetchall()

    return render_template('mylist.html', perfil=perfil, serie_pelicula=serie_pelicula)




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
