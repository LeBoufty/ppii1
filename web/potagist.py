from flask import Flask,render_template,g,request,redirect, session
import logging
from flask_session import Session
from PIL import Image
import datetime
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
    return '<img src="../static/img/teapot.png"/>'


@app.route('/connexion', methods=["GET", "POST"])
def connexion():
    userid = session.get('userid', None)
    if userid is not None: return redirect('/')

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
        c.execute("SELECT * FROM liste_annonce WHERE archive=0")
        data = c.fetchall()
        data = retourne(data)
        data = transf_data_annonce_3(data)
        return render_template('annonce.html', data=data,userid=userid)
    else:
        recherche = request.form.get('recherche')
        code_postal = request.form.get('code_postal')
        offre = request.form.get('offre')
        contrepartie = request.form.get('contrepartie')
        data = cherche_annonces(recherche, code_postal, offre, contrepartie)
        data = retourne(data)
        data = transf_data_annonce_3(data)
        return render_template('annonce.html', data=data, userid=userid)

@app.route('/annonces/<string:id_annonce>')
def annonce(id_annonce):
    userid = session.get('userid', None)
    c = get_db().cursor()
    c.execute("SELECT * FROM liste_annonce WHERE id_annonce='" + id_annonce + "';")
    data = c.fetchall()
    if len(data)==0:
        return redirect('/')
    return render_template('description_annonce.html', data=data, userid=userid)

@app.route('/profil/')
def profil():
    userid = session.get('userid', None)
    if userid is None: return redirect('/connexion')
    else: return render_template('profile.html',userid=userid)

@app.route('/discussions')
def liste_discussions():
    userid = session.get('userid', None)
    if userid is None: return redirect('/connexion')
    else:
        contacts = get_contacts(userid)
        return render_template('meet.html',userid=userid, id_discu=None, contacts=contacts)

@app.route('/discussions/<string:id_discu>', methods=['GET', 'POST'])
def discussion(id_discu):
    userid = session.get('userid', None)
    if userid is None: return redirect('/connexion')
    else:
        if request.method == 'GET':
            contacts = get_contacts(userid)
            chat = get_chat(userid, id_discu)
            messages = lire_chat(chat)
            messages = retourne(messages)
            return render_template('meet.html', userid=userid, id_discu=id_discu, contacts=contacts, messages=messages)
        else:
            message = request.form.get('message')
            if message != '':
                envoyer_message(userid, id_discu, message)
            return redirect(f'/discussions/{id_discu}') # Pour éviter que F5 renvoie le message

@app.route('/mesannonces')
def mesannonces():
    userid = session.get('userid', None)
    if userid is None: 
        return redirect('/connexion')

    c = get_db().cursor()
    c.execute(f"SELECT * FROM liste_annonce WHERE annonceur='{userid}'")
    data = c.fetchall()
    data = retourne(data)
    data = transf_data_annonce_3(data)
    return render_template('mesannonces.html', data=data,userid=userid)

@app.route('/mesannonces/<string:id_annonce>')
def mesannonces_modif(id_annonce):
    userid = session.get('userid', None)
    if userid == None:
        return redirect('/connexion')

    c = get_db().cursor()
    c.execute("SELECT * FROM liste_annonce WHERE id_annonce='" + id_annonce + "' AND annonceur='" + userid + "';")
    data = c.fetchall()
    if len(data)==0:
        return redirect('/')
    return render_template('modif_annonce.html', data=data, userid=userid)

@app.route('/inscription', methods=["GET","POST"])
def inscription():
    userid = session.get('userid', None)
    if userid is not None: return redirect('/')
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

@app.route('/annonceform', methods=['POST'])
def create_ad():
    userid = session.get('userid', None)
    if userid is None: return redirect('/connexion')
    date=aujourdhui()
    name=request.form['name']
    contrepartie=request.form['contrepartie']
    cat_cntrp=request.form['cat_cntrp']
    description=request.form['description']
    cat_desc=request.form['cat_desc']
    cp=request.form['code_postal']
    image = request.files['image']
    id_annonce=hashmdp(name+userid+date)
    image.save('static/photos/'+ id_annonce+'.jpg')
    passe480p(id_annonce)
    if addannonce(name, userid, contrepartie, description, cp, cat_cntrp, date, cat_desc, id_annonce): return redirect('/')

@app.route('/deconnexion')
def deconnexion():
    session.pop('userid')
    return redirect('/')

@app.route('/archivage/<string:id_annonce>')
def archivage(id_annonce):
    userid = session.get('userid', None)
    if userid == None:
        return redirect('/connexion')
    if not check_annonce_auteur(id_annonce, userid):
        return redirect('/')

    new_archiv = inverse_1_0(status_archivage(id_annonce))
    c = get_db().cursor()
    c.execute(f"UPDATE liste_annonce SET archive = '{new_archiv}' WHERE id_annonce='{id_annonce}';")
    c.connection.commit()
    return redirect('/mesannonces')

@app.route('/creation_contrat/<string:id_annonce>')
def creation_contrat(id_annonce):
    userid = session.get('userid', None)
    if userid == None:
        return redirect('/connexion')
    if check_annonce_auteur(id_annonce, userid):
        return redirect('/')
    if check_contrat_existant(id_annonce, userid):
        return redirect('/mescontrats')
    if check_annonce_archive(id_annonce):
        return redirect('/')

    id_contrat = hashmdp(id_annonce + userid + maintenant())
    id_annonceur = get_userid(id_annonce)
    c = get_db().cursor()
    c.execute(f"INSERT INTO contract (id_contract, annonceur, client, date_debut, id_annonceur, val_an, val_cl, accepte) VALUES ('{id_contrat}', '{id_annonceur}', '{userid}', '{aujourdhui()}', '{id_annonce}', '0', '1', 0 );")
    c.connection.commit()
    return redirect('/mescontrats')

@app.route('/mescontrats')
def mes_contrats():
    userid = session.get('userid', None)
    if userid == None:
        return redirect('/connexion')
    data_incoming, data_attente, data_cours = get_all_contracts(userid)
    return render_template('mescontrats.html', userid=userid, data_incoming=data_incoming, data_attente=data_attente, data_cours=data_cours)

@app.route('/mescontrats/<string:id_annonce>')
def mes_contrats_det(id_annonce):
    userid = session.get('userid', None)
    if userid == None:
        return redirect('/connexion')

    c = get_db().cursor()
    c.execute(f"SELECT * FROM liste_annonce AS a JOIN contract AS c ON a.id_annonce=c.id_annonceur WHERE a.id_annonce='{id_annonce}';")
    data = c.fetchall()
    if len(data)==0:
        return redirect('/')
    contrat_type = type_contract(id_annonce, userid)
    
    return render_template('mescontrats_detail.html', data=data, userid=userid, contrat_type=contrat_type)

@app.route('/commencer_discussion/<string:annonceur>')
def creer_discussion(annonceur):
    userid = session.get('userid', None)
    if userid == None:
        return redirect('/connexion')
    if userid != annonceur:
        genere_chat(userid, annonceur)
        return redirect(f'/discussions/{annonceur}')
    else:
        return redirect('/')

@app.route('/supprimer_contrat/<string:id_contrat>')
def supprimer_contrat(id_contrat):
    userid = session.get('userid', None)
    if userid == None:
        return redirect('/connexion')
    if not check_auteur_contrat(id_contrat, userid):
        return redirect('/')
    if check_contrat_accepte(id_contrat):
        return redirect('/')

    c = get_db().cursor()
    c.execute(f"DELETE FROM contract WHERE id_contract='{id_contrat}' ;")
    c.connection.commit()
    return redirect('/mescontrats')

@app.route('/validation_contrat/<string:id_contrat>')
def validation_contrat(id_contrat):
    userid = session.get('userid', None)
    if userid == None:
        return redirect('/connexion')
    if not check_auteur_contrat(id_contrat, userid):
        return redirect('/')
    if check_contrat_accepte(id_contrat):
        return redirect('/')

    c = get_db().cursor()
    c.execute(f"UPDATE contract SET accepte = 1, val_an = 1 WHERE id_contract='{id_contrat}' ;")
    c.connection.commit()
    id_annonce = get_annonce_from_contract(id_contrat)
    d = get_db().cursor()
    d.execute(f"UPDATE liste_annonce SET archive = 2 WHERE id_annonce='{id_annonce}'")
    d.connection.commit()

    return redirect('/mescontrats')


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
    codes = open('static/codes_postaux.txt', 'r', encoding='utf-8').read()
    return code_postal in codes.split(';')

def adduser(usrname, mdp, cp):
    c = get_db().cursor()
    hash = hashmdp(mdp)
    c.execute(f"INSERT INTO utilisateur (pseudo, mdphash, code_postal, admin) VALUES ('{usrname}', '{hash}', '{cp}', 0)")
    c.connection.commit()
    return True

def addannonce(nom, user, cntrp, desc, cp, cat_cntrp, date, cat_desc,id_annonce='0'):
    c = get_db().cursor()
    if id_annonce=='0':
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
    params.append(f"archive = 0")
    query += " AND ".join(params)
    c = get_db().cursor()
    c.execute(query)
    return c.fetchall()

def get_contacts(userid):
    userid = session.get('userid', None)
    if userid is None: return None
    c = get_db().cursor()
    c.execute(f"SELECT * FROM chat WHERE pseudo1 = '{userid}' OR pseudo2 = '{userid}'")
    tuples = c.fetchall()
    pseudos = []
    for i in tuples:
        if i[0] == userid: pseudos.append(i[1])
        else: pseudos.append(i[0])
    return pseudos

def get_chat(userid, i):
    c = get_db().cursor()
    c.execute(f"SELECT texte FROM chat WHERE (pseudo1 = '{userid}' AND pseudo2 = '{i}') OR (pseudo1 = '{i}' AND pseudo2 = '{userid}')")
    return c.fetchone()[0]

def envoyer_message(userid, dest, message):
    chat = get_chat(userid, dest)
    while '¤*¤' in message or '¤%¤' in message:
        message = message.replace('¤*¤', '*')
        message = message.replace('¤%¤', '%')
    f = open(f'chat/{chat}', 'a', encoding='utf-8')
    f.write(f"{userid}¤%¤{maintenant()}¤%¤{message}¤*¤")

def lire_chat(chat):
    f = open(f'chat/{chat}', 'r', encoding='utf-8')
    data = f.read().split('¤*¤')[:-1]
    for i in range(len(data)): data[i] = data[i].split('¤%¤')
    return data

aujourdhui = lambda : datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
maintenant = lambda : datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

retourne = lambda L : [L[-i] for i in range(1,len(L)+1)]

def genere_chat(usr1, usr2) :
    nom = hashmdp(usr1+usr2)+'.txt'
    open(f'chat/{nom}', 'a', encoding='utf-8').close()
    c = get_db().cursor()
    c.execute(f"SELECT * FROM chat WHERE (pseudo1 = '{usr1}' AND pseudo2 = '{usr2}') OR (pseudo1 = '{usr2}' AND pseudo2 = '{usr1}');")
    if c.fetchall() == []:
        c.execute(f"INSERT INTO chat VALUES ('{usr1}', '{usr2}', '{nom}');")
        c.connection.commit()
    return nom

def passe480p(img: str):
    image=Image.open('static/photos/'+img+'.jpg')
    image=image.convert("RGB")
    image=image.resize((704,480))
    image.save('static/photos/'+img+'.jpg')

def transf_data_annonce_3(data):
    new_data = []
    data_en_attente = []

    for i in range(len(data)):
        data_en_attente.append(data[i])

        if len(data_en_attente) >= 3:
            new_data.append(data_en_attente)
            data_en_attente = []

    if data_en_attente != []:
        new_data.append(data_en_attente)

    return new_data

def check_annonce_auteur(id_annonce, userid): # Permet de savoir si l'annonce a été écrite par cette personne
    c = get_db().cursor()
    c.execute(f"SELECT * FROM liste_annonce WHERE annonceur='{userid}' AND id_annonce='{id_annonce}';")
    data = c.fetchall()
    if len(data) == 0:
        return False
    return True

def status_archivage(id_annonce):
    c = get_db().cursor()
    c.execute(f"SELECT archive FROM liste_annonce WHERE id_annonce='{id_annonce}';")
    data = c.fetchall()
    return data[0][0]

def inverse_1_0(entre):
    if entre == 1:
        return 0
    return 1

def check_contrat_existant(id_annonce, userid_cl):
    c = get_db().cursor()
    c.execute(f"SELECT * FROM contract WHERE id_annonceur='{id_annonce}' AND client='{userid_cl}';")
    data = c.fetchall()
    if len(data) == 0:
        return False
    return True

def get_userid(id_annonce):
    c = get_db().cursor()
    c.execute(f"SELECT annonceur FROM liste_annonce WHERE id_annonce='{id_annonce}';")
    data = c.fetchall()
    return data[0][0]

def get_all_contracts(userid):
    c = get_db().cursor()
    c.execute(f"SELECT * FROM liste_annonce AS a JOIN contract AS c ON a.id_annonce=c.id_annonceur WHERE c.annonceur='{userid}' AND c.accepte=0;")
    data_c_incoming = c.fetchall()
    data_incoming = transf_data_annonce_3(data_c_incoming)

    d = get_db().cursor()
    d.execute(f"SELECT * FROM liste_annonce AS a JOIN contract AS c ON a.id_annonce=c.id_annonceur WHERE c.client='{userid}' AND c.accepte=0;")
    data_c_attente = d.fetchall()
    data_attente = transf_data_annonce_3(data_c_attente)

    e = get_db().cursor()
    e.execute(f"SELECT * FROM liste_annonce AS a JOIN contract AS c ON a.id_annonce=c.id_annonceur WHERE (c.client='{userid}' OR c.annonceur='{userid}') AND accepte=1;")
    data_c_cours = e.fetchall()
    data_cours = transf_data_annonce_3(data_c_cours)
    
    return [data_incoming,data_attente,data_cours]

def check_annonce_archive(id_annonce):
    c = get_db().cursor()
    c.execute(f"SELECT archive FROM liste_annonce WHERE id_annonce='{id_annonce}';")
    reponse = c.fetchall()
    return reponse[0][0]

def type_contract(id_annonce, userid):
    c = get_db().cursor()
    c.execute(f"SELECT annonceur, client, accepte FROM contract WHERE (client='{userid}' OR annonceur='{userid}') AND id_annonceur='{id_annonce}' ;")
    
    data = c.fetchall()

    if data[0][2] == 1:
        return 3
    if data[0][1] == userid:
        return 2
    return 1

def check_auteur_contrat(id_contrat, userid):
    c = get_db().cursor()
    c.execute(f"SELECT val_an, val_cl FROM contract WHERE (client='{userid}' OR annonceur='{userid}') AND id_contract='{id_contrat}' ;")
    data = c.fetchall()
    if len(data) == 0:
        return False
    return True

def check_contrat_accepte(id_contrat):
    c = get_db().cursor()
    c.execute(f"SELECT accepte FROM contract WHERE id_contract='{id_contrat}' ;")
    data = c.fetchall()
    if data[0][0] == 1:
        return True
    return False

def get_annonce_from_contract(id_contract):
    c = get_db().cursor()
    c.execute(f"SELECT id_annonceur FROM contract WHERE id_contract='{id_contract}' ")
    data = c.fetchall()
    return data[0][0]

#adduser('dummy01', 'admin', '01150')
#addannonce('Potit Potager', 'dummy01', '15€/mois', 'Bonjour à tous les amis je m''appelle ahmed j''aime tous les sports surtout le football', '01150', 'argent', '23/12/2022', 'terrain')
#addannonce("J'ai besoin de pêches", 'JEAN !!!!', '1kg de pêches', "Bonjour ahmed je m'appelle jean et j'essaie de faire marcher les apostrophes comme ça : ' par exemple ' youpi ''''''''", '01150', 'produits', '05/12/2022', 'argent')
#app.run(debug=True)
