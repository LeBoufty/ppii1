from flask import Flask,render_template,g,request,redirect, session
import logging
from flask_session import Session
from PIL import Image
import sqlite3
import hashlib

### INITIALISATION ###

DATABASE='potadata.db' #nom de la db
app=Flask(__name__)
app.config.from_object(__name__)
app.config['SESSION_TYPE'] = 'filesystem' # On stocke les sessions localement (c'est dans le .gitignore)
app.config['SECRET_KEY'] = "potakey" # J'ai compris à quoi ça sert !!
Session(app)
app.logger.setLevel(logging.INFO)

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
    return render_template('index.html', userid=userid)

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

@app.route('/annonces', methods=['GET', 'POST'])
def annonces():
    userid = session.get('userid', None)
    if request.method == "GET":
        c = get_db().cursor()
        c.execute("SELECT * FROM liste_annonce")
        data = c.fetchall()
        return render_template('annonce.html', data=data,userid=userid)
    else:
        recherche = request.form.get('recherche')
        code_postal = request.form.get('code_postal')
        offre = request.form.get('offre')
        contrepartie = request.form.get('contrepartie')
        data = cherche_annonces(recherche, code_postal, offre, contrepartie)
        return render_template('annonce.html', data=data, userid=userid)

@app.route('/annonces/<string:id_annonce>')
def annonce(id_annonce):
    pass

@app.route('/profil/')
def profil():
    userid = session.get('userid', None)
    if userid is None: return redirect('/connexion')
    else: return 'WIP profil utilisateur'

@app.route('/discussions')
def liste_discussions():
    userid = session.get('userid', None)
    if userid is None: return redirect('/connexion')
    else: return render_template('meet.html',userdid=userid)

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

@app.route('/crea_annonce')
def crea_annonce():
    userid = session.get('userid', None)
    if userid is None: return redirect('/connexion')
    return render_template('crea_annonce.html', userid=userid)

@app.route('/upload_im', methods=['POST'])
def upload_file():
    file=request.files['file']
    file.save('photos/' + file.filename)
    passe480p(file.filename)
    return redirect('/')

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

def addannonce(nom, user, cntrp, desc, cp, cat_cntrp, date, cat_desc):
    c = get_db().cursor()
    id_annonce = hashmdp(nom+user+date)
    desc, cntrp, nom = desc.replace("'", "''"), cntrp.replace("'", "''"), nom.replace("'", "''")
    c.execute(f"INSERT INTO liste_annonce VALUES ('{id_annonce}', '{nom}', '{user}', '{cntrp}', '{desc}', '{cp}', '{cat_cntrp}', 0, '{date}', '{cat_desc}')")
    c.connection.commit()
    return True

def cherche_annonces(recherche, cp, offre, cntrp):
    if recherche == cp == offre == cntrp == None: query = "SELECT * FROM liste_annonce"
    else: query = "SELECT * FROM liste_annonce WHERE "
    params = []
    if recherche != '':
        params.append(f"(nom_annonce LIKE '%{recherche}%' OR description LIKE '%{recherche}%')")
    if cp != '':
        params.append(f"code_postal = '{cp}'")
    if offre is not None:
        params.append(f"categorie_description = '{offre}'")
    if cntrp is not None:
        params.append(f"categorie_contrepartie = '{cntrp}'")
    query += " AND ".join(params)
    c = get_db().cursor()
    c.execute(query)
    return c.fetchall()

def passe480p(img: str):
    image=Image.open('photos/'+img)
    image=image.resize((704,480))
    image.save('photos/'+img)

#adduser('dummy01', 'admin', '01150')
#addannonce('Potit Potager', 'dummy01', '15€/mois', 'Bonjour à tous les amis je m''appelle ahmed j''aime tous les sports surtout le football', '01150', 'argent', '23/12/2022', 'terrain')
#addannonce("J'ai besoin de pêches", 'JEAN !!!!', '1kg de pêches', "Bonjour ahmed je m'appelle jean et j'essaie de faire marcher les apostrophes comme ça : ' par exemple ' youpi ''''''''", '01150', 'produits', '05/12/2022', 'argent')