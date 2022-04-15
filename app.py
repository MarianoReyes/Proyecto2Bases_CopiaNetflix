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

    # Mando a llamar Peliculas y series
    cursor.execute(
        'DELETE FROM cuentas WHERE username=%s', (usuario,))
    conn.commit()
    flash("Usuario desactivado con éxito")
    return render_template('borrar_usuarios.html')


@app.route('/favoritos/<name>/<sp>/<cuenta>')
def favoritos(sp, name, cuenta):

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

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
        'select * from serie_peliculas sp natural join favoritos f where nombre_perfil = (%s)', (name,))
    serie_pelicula = cursor.fetchall()

    return render_template('mylist.html', perfil=perfil, serie_pelicula=serie_pelicula)


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
        'select * from serie_peliculas sp natural join favoritos f where nombre_perfil = (%s)', (name,))
    serie_pelicula = cursor.fetchall()

    # Mandar a pagina de inicio del perfil
    # , vistos=vistos
    return render_template('watched.html', account=account, perfil=perfil, serie_pelicula=serie_pelicula)

@app.route('/vistos/<name>/<sp>/<cuenta>')
def vistos(sp, name, cuenta):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cursor.execute(
        'SELECT * FROM contenido WHERE nombre_perfil = (%s)', (name,))
    contenido = cursor.fetchone()

    cursor.execute(
        'SELECT * FROM perfiles WHERE nombre_perfil = (%s)', (name,))
    perfil = cursor.fetchone()

    cursor.execute(
        'insert into contenido (serie_pelicula,nombre_perfil,correo_cuenta) values (%s,%s,%s)', (sp, name, cuenta))
    conn.commit()

    cursor.execute(
        'select * from serie_peliculas sp natural join contenido c where nombre_perfil = (%s)', (name,))
    serie_pelicula = cursor.fetchall()
    

#Pasarse datos con el navbar
# Pass Stuff To Navbar
@app.context_processor
def base():
	form = SearchForm()
	return dict(form=form)

#Form del buscar
class SearchForm(FlaskForm):
	searched = StringField("Searched", validators=[DataRequired()])
	submit = SubmitField("Submit")

#Funcion de buscar

@app.route('/search', methods=["POST"])
def search():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    form = SearchForm()
    #posts = Post.query
    if form.validate_on_submit():

        #Obtener la data enviada
        post = form.searched.data

        #Query a la base de datos
        #pelicula o serie
        cursor.execute(
            'select serie_pelicula,imagen,link_repro from serie_peliculas where serie_pelicula like %s',(post,))
        posts= cursor.fetchall()

        #director
        cursor.execute(
            'select serie_pelicula,imagen,link_repro from serie_peliculas where director like %s',(post))
        director= cursor.fetchall()

        #actor
        cursor.execute(
            'select serie_pelicula from actores where nombre_actor like  %s',(post))
        actor= cursor.fetchall()

        #categoria
        #director
        cursor.execute(
            'select serie_pelicula,imagen,link_repro from serie_peliculas where categoria like %s',(post))
        categoria= cursor.fetchall()

        return render_template("search.html",
		 form=form,
		 searched = post,
		 posts = posts,
         actores=actor,
         directores=director,
         categorias=categoria)


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
