from flask import Flask,render_template,g,request,redirect, session
from flask_session import Session
import sqlite3
import hashlib

### INITIALISATION ###

DATABASE='potadata.db' #nom de la db
app=Flask(__name__)
app.config.from_object(__name__)
app.config['SESSION_TYPE'] = 'filesystem' # On stocke les sessions localement (c'est dans le .gitignore)
app.config['SECRET_KEY'] = "potakey" # J'ai compris à quoi ça sert !!
Session(app)

def get_db():
    with app.app_context():
        db=getattr(g,'_database',None)
        if db is None:
            db=g.database=sqlite3.connect(DATABASE)
        return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g,'_database',None)
    if db is not None:
        db.close()


### ROUTES ###

@app.route('/')
def index():
    userid = session.get('userid', None)
    if userid is None: return render_template('index.html')
    else: return render_template('index_connecte.html', userid=userid)

@app.route('/teapot')
def teapot():
    #Trouver une teapot drôle
    pass

@app.route('/display') #Provisoire 
def display():
    data=get_db().cursor()
    data.execute("select * from utilisateur")
    return render_template('display.html',L=data) 

@app.route('/connexion', methods=["GET", "POST"])
def connexion():
    if request.method == "GET":
        failed = request.args.get('failed')
        return render_template('connexion.html', error=failed is not None)
    else:
        pseudo = request.form.get('pseudo')
        password = request.form.get('password')
        if login_valide(pseudo, password):
            session['userid'] = get_id(pseudo, password)
            return redirect('/')
        else: 
            return redirect('/connexion?failed=yes')

@app.route('/annonces')
def annonces():
    return render_template('annonce.html')

@app.route('/profil/')
def profil():
    userid = session.get('userid', None)
    if userid is None: return redirect('/connexion')
    else: return 'WIP profil utilisateur'

@app.route('/discussions')
def liste_discussions():
    userid = session.get('userid', None)
    if userid is None: return redirect('/connexion')
    else: return 'WIP liste des discussions'

@app.route('/discussions/<string:id_discu>')
def discussion(id_discu):
    userid = session.get('userid', None)
    if userid is None: return redirect('/connexion')
    else: return 'WIP une discussion'

@app.route('/mesannonces')
def mesannonces():
    userid = session.get('userid', None)
    if userid is None: return redirect('/connexion')
    else: return 'WIP annonces utilisateur'

@app.route('/inscription', methods=["GET","POST"])
def inscription():
    if request.method == "GET":
        usrnerror = request.args.get('usrnerror') # Erreur : pseudo déjà pris
        pcerror = request.args.get('pcerror') # Erreur : code postal invalide
        return render_template('inscription.html', usrnerror=usrnerror is not None, pcerror=pcerror is not None)
    else:
        pseudo = request.form.get('pseudo')
        password = request.form.get('password')
        code_postal = request.form.get('code_postal')
        if pseudolibre(pseudo) and cp_valide(code_postal): # Si tout est valide
            adduser(pseudo, password, code_postal) # On ajoute l'utilisateur
            session['userid'] = get_id(pseudo, password) # Puis on le connecte
            return redirect('/')
        else: # On ajoute les messages d'erreur personnalisés
            probleme = '/inscription?'
            if not pseudolibre(pseudo): probleme += 'usrnerror=1&'
            if not cp_valide(code_postal): probleme += 'pcerror=1'
            return redirect(probleme)

@app.route('/meet', methods=['GET'])
def meet():
    data=get_db().cursor()
    CODEPOSTAL=request.args.get('CODEPOSTAL',None) 
    if CODEPOSTAL is not None :
        data.execute(f"SELECT utilisateur.pseudo FROM utilisateur WHERE utilisateur.code_postal='{CODEPOSTAL}';") 
        data.connection.commit()
    return render_template('PIERRE2.html',L=data) #Nom du html 2


sess = Session()
sess.init_app(app)


### FONCTIONS ###

hashmdp = lambda mdp: hashlib.md5(mdp.encode('utf-8')).hexdigest()

def pseudolibre(usrname):
    """Vérifie si un pseudo est déjà pris"""
    c = get_db().cursor()
    c.execute(f"SELECT * FROM utilisateur WHERE pseudo = '{usrname}'")
    return c.fetchall() == []

def login_valide(usrname, mdp):
    """Vérifie si un login (pseudo + mdp) est valide"""
    c = get_db().cursor()
    hash = hashmdp(mdp)
    c.execute(f"SELECT * FROM utilisateur WHERE pseudo = '{usrname}' AND mdphash = '{hash}'")
    return c.fetchall() != []

def get_id(usrname, mdp):
    """Renvoie l'id de l'utilisateur spécifié. Ne vérifie pas s'il existe."""
    c = get_db().cursor()
    hash = hashmdp(mdp)
    c.execute(f"SELECT pseudo FROM utilisateur WHERE pseudo = '{usrname}' AND mdphash = '{hash}'")
    return c.fetchall()[0][0]

def cp_valide(code_postal):
    """Vérifie si un code postal existe"""
    codes = open('static/codes_postaux.txt', 'r').read()
    return code_postal in codes

def adduser(usrname, mdp, cp):
    c = get_db().cursor()
    hash = hashmdp(mdp)
    c.execute(f"INSERT INTO utilisateur (pseudo, mdphash, code_postal, admin) VALUES ('{usrname}', '{hash}', '{cp}', 0)")
    c.connection.commit()
    return True

#adduser('dummy01', 'admin', '01150')