import sys
import traceback

from flask import *
from sqlite3 import *

app = Flask(__name__)
app.secret_key = 'Fz<6z9=Izmdn$&sdzDaz'

con = connect("./database/database", check_same_thread=False)

app.run(debug=True)


def connect_to_db(con):
    """
            Se connecte à la base de donnée
            
            Args :
                con (object) : L'objet de connexion à la base de donnée.

            Returns :
                object : L'objet de connexion à la base de donnée.
    """
    con.close()
    con = connect("./database/database", check_same_thread=False)
    return con


def get_forms(user_id, completed):
    """
        Récupère les formulaires complétés ou non complétés par un utilisateur.

        Args:
            user_id (int): L'identifiant de l'utilisateur.
            completed (bool): Indique si les formulaires renvoyés doivent être complétés (True) ou non complétés (False).

        Returns:
            List[]: Une liste de dictionnaires contenant les informations des formulaires
            récupérés.
        """
    cur = connect_to_db(con).cursor()

    if completed:
        query = """
        SELECT f.id, f.name, f.description, q.label, q.type 
        FROM Forms f
        JOIN Questions q ON f.id = q.id_form
        JOIN Completed_forms cf ON f.id = cf.id_form
        WHERE cf.id_user = ?
        """
    else:
        query = """
        SELECT f.id, f.name, f.description, q.label, q.type 
        FROM Forms f
        JOIN Questions q ON f.id = q.id_form
        WHERE f.id NOT IN (
            SELECT DISTINCT cf.id_form 
            FROM Completed_forms cf 
            WHERE cf.id_user = ?
        )
        """

    cur.execute(query, (user_id,))
    results = cur.fetchall()

    forms = {}
    for row in results:
        form_id = row[0]
        form_name = row[1]
        form_description = row[2]
        question_label = row[3]
        question_type = row[4]

        if form_name not in forms:
            forms[form_name] = {'id': form_id, 'description': form_description, 'questions': []}

        forms[form_name]['questions'].append({'label': question_label, 'type': question_type})

    rslt = [{'id': v['id'], 'nom': k, 'description': v['description'], 'questions': v['questions']} for k, v in forms.items()]

    return rslt


def form_review(form_id, player_id):
    """
        Récupère les informations sur un formulaire ainsi que les réponses d'un joueur pour ce formulaire.

        Args:
            form_id (int): L'ID du formulaire à récupérer.
            player_id (int): L'ID du joueur dont on souhaite récupérer les réponses.

        Returns:
            List[]: Un tableau contenant les informations du formulaire
            ainsi que ses questions et réponses.
    """
    # Connexion à la base de données
    cur = connect_to_db(con).cursor()

    # Récupération des informations sur le formulaire
    cur.execute("SELECT name, description FROM Forms WHERE id=?", (form_id,))
    form_info = cur.fetchone()

    # Récupération des questions et des réponses du joueur pour les questions du formulaire
    cur.execute("""
        SELECT q.id, q.label, q.type, r.value 
        FROM Questions q 
        LEFT JOIN reponses r ON q.id=r.id_question AND r.user_id=? 
        WHERE q.id_form=?
        """, (player_id, form_id))
    questions_and_answers = cur.fetchall()

    # Construction du tableau résultat
    rslt = [{
        "nom": form_info[0],
        "description": form_info[1],
        "reponses": [{"question": {"label": q[1], "type": q[2]}, "reponse": q[3]} for q in questions_and_answers]
    }]
    return rslt


def get_users_completed_form(form_id):
    """
    Récupère tous les utilisateurs ayant complété un formulaire spécifié.

    Args:
        form_id (int): l'id du formulaire.

    Returns:
        list of dict: un tableau de dictionnaires, où chaque dictionnaire représente un utilisateur ayant complété le formulaire,
        avec les clés suivantes :
            - id (int): l'id de l'utilisateur.
            - name (str): le nom de l'utilisateur.
        Si aucun utilisateur n'a complété le formulaire, retourne un tableau vide.
    """
    # Connexion à la base de données
    cur = connect_to_db(con).cursor()

    cur.execute("""
        SELECT users.id, users.username
        FROM users
        INNER JOIN completed_forms ON completed_forms.id_user = users.id
        WHERE Completed_forms.id_form = ?
    """, (form_id,))

    users = [{"id": row[0], "name": row[1]} for row in cur.fetchall()]

    return users


def get_form_details(form_id):
    """
        Renvoie les détails d'un formulaire et ses questions sous forme de dictionnaire.

        Args :
            form_id (int) : L'ID du formulaire à récupérer.

        Returns :
            dict : Un dictionnaire contenant les détails du formulaire et ses questions.
    """
    # Connexion à la base de données
    cur = connect_to_db(con).cursor()

    # Récupération des informations sur le formulaire
    cur.execute("SELECT name, description FROM Forms WHERE id=?", (form_id,))
    form_info = cur.fetchone()

    # Récupération des questions du formulaire
    cur.execute("SELECT id, label, type FROM Questions WHERE id_form=?", (form_id,))
    questions = cur.fetchall()

    # Construction du tableau résultat
    rslt = {
        "id": form_id,
        "nom": form_info[0],
        "description": form_info[1],
        "questions": [{"id": q[0], "label": q[1], "type": q[2]} for q in questions]
    }
    return rslt


def get_users():
    """
        Récupère toutes les informations sur les utilisateurs et les retourne sous forme de liste de dictionnaires.
        Les utilisateurs sont distingués en fonction de leur statut (0 pour employé, 1 pour admin).

        Returns:
            List[Dict]: Une liste de dictionnaires contenant les informations sur les utilisateurs.
    """
    # Connexion à la base de données
    cur = connect_to_db(con).cursor()

    # Récupération des informations sur les utilisateurs
    cur.execute("SELECT * FROM Users")
    results = cur.fetchall()

    # Formatage des résultats
    users = []
    for row in results:
        user_id = row[0]
        username = row[1]
        password = row[2]
        token = row[3]
        admin = False if row[4] == 0 else True

        users.append({"id": user_id, "username": username, "password": password, "token": token, "admin": admin})

    return users


@app.before_request
def before_request():
    g.user = None

    cur = connect_to_db(con).cursor()
    if 'token' in session:
        user = list(cur.execute(
            'SELECT * '
            'FROM users '
            f'WHERE token="{session["token"]}"'
        ))
        g.user = user[0]


@app.route('/login', methods=['GET', 'POST'])
def login():
    cur = connect_to_db(con).cursor()

    if request.method == 'POST':
        session.pop('token', None)

        username = request.form['username']
        password = request.form['password']

        user = list(cur.execute(
            'SELECT * '
            'FROM users '
            f'WHERE username="{username}"'
        ))

        if user and user[0][2] == password:
            session['token'] = user[0][3]
            return redirect(url_for('back_office'))

        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/employee')
def employee():
    if not g.user:
        return redirect(url_for('login'))

    if g.user[4] == 1:
        return redirect(url_for('back_office'))

    return render_template('employee.html', non_completed_forms=get_forms(g.user[0], False))


@app.route('/questionnairesRemplis')
def questionnairesRemplis():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('questionnairesRemplis.html', completed_forms=get_forms(g.user[0], True))


@app.route('/back_office')
def back_office():
    if not g.user:
        return redirect(url_for('login'))

    if g.user[4] == 0:
        return redirect(url_for('employee'))

    return render_template('back_office.html', forms=get_forms(g.user[0], False))


@app.route('/accounts')
def accounts():
    if not g.user:
        return redirect(url_for('login'))

    if g.user[4] == 0:
        return redirect(url_for('employee'))

    return render_template('accounts.html', accounts=get_users())


@app.route('/remplir/<int:form_id>', methods=['GET', 'POST'])
def remplir(form_id):
    if not g.user:
        return redirect(url_for('login'))

    form = get_form_details(form_id)

    if request.method == 'GET':
        return render_template('remplir.html', form=form)

    conn = connect_to_db(con)
    for question in form['questions']:
        value = request.form[str(question['id'])]
        if value:
            conn.cursor().execute("""
                INSERT INTO reponses (id_question, user_id, value)
                VALUES (?, ?, ?)
            """, (question['id'], g.user[0], value))

    conn.cursor().execute("""
                    INSERT INTO completed_forms (id_form, id_user)
                    VALUES (?, ?)
                """, (form_id, g.user[0]))
    conn.commit()

    return redirect(url_for('employee'))


@app.route('/reponses/<int:form_id>/<int:player_id>')
def reponses(form_id, player_id):
    if not g.user:
        return redirect(url_for('login'))

    if g.user[4] == 0:
        return redirect(url_for('employee'))

    return render_template('reponses.html', form=form_review(form_id, player_id)[0], users=get_users_completed_form(form_id), current_user=player_id, current_form=form_id)


@app.route('/create_form', methods=['GET', 'POST'])
def create_form():
    if request.method == 'POST':
        # Récupération des données du formulaire
        form_name = request.form['form_name']
        form_description = request.form['form_description']

        # Connexion à la base de données
        conn = connect_to_db(con)
        cur =  conn.cursor()

        # Création du formulaire dans la base de données
        cur.execute("""
            INSERT INTO Forms (name, description) VALUES (?, ?)
        """, (form_name, form_description))
        form_id = cur.lastrowid

        # Récupération des questions et des types de réponse
        questions = []
        types = []
        for key in request.form:
            if key.startswith('label-'):
                question_id = int(key.split('-')[1])
                questions.append((question_id, request.form[key]))
            elif key.startswith('type-'):
                question_id = int(key.split('-')[1])
                types.append((question_id, request.form[key]))

        # Ajout des questions dans la base de données
        for q, t in zip(questions, types):
            cur.execute("""
                INSERT INTO Questions (id_form, label, type) VALUES (?, ?, ?)
            """, (form_id, q[1], t[1]))

        conn.commit()
        return redirect(url_for('back_office'))

    # Si la méthode est GET, on renvoie simplement le template
    return render_template('create_form.html')
