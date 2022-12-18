from flask import Flask,render_template,g,request,redirect, session
from flask_session import Session
import auth
import sqlite3

DATABASE='potadata.db' #nom de la db

app=Flask(__name__)
app.config.from_object(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = "je ne sais pas à quoi ça sert"
Session(app)

def get_db():
    db=getattr(g,'_database',None)
    if db is None:
        db=g.database=sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g,'_database',None)
    if db is not None:
        db.close()

@app.route('/')
def index(): # Penser à faire une différence si l'utilisateur est connecté ou non...
    userid = session.get('userid', None)
    if userid is None: return render_template('index.html')
    else: return render_template('index_connecte.html')

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
        if auth.login_valide(pseudo, password):
            session['userid'] = auth.get_id(pseudo, password)
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
    else: return 'WIP'

@app.route('/discussions')
def liste_discussions():
    return 'WIP : liste des discussions'

@app.route('/discussions/<string:id_discu>')
def discussion(id_discu):
    return 'WIP : discussion particulière'

@app.route('/mesannonces')
def mesannonces():
    return "WIP : liste des annonces de l'utilisateur"

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
        if auth.pseudolibre(pseudo) and auth.cp_valide(code_postal): # Si tout est valide
            auth.adduser(pseudo, password) # On ajoute l'utilisateur
            session['userid'] = auth.get_id(pseudo, password) # Puis on le connecte
            return redirect('/')
        else: # On ajoute les messages d'erreur personnalisés
            probleme = '/connexion?'
            if not auth.pseudolibre(pseudo): probleme += 'usrnerror=1&'
            if not auth.cp_valide(code_postal): probleme += 'pcerror=1'
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