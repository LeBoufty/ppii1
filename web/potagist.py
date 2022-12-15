from flask import Flask,render_template,g,request,redirect
import auth
import sqlite3

DATABASE='potadata.db' #nom de la db

app=Flask(__name__)

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
    return render_template('index.html')

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
        if auth.login_valide(pseudo, password): return 'Login valide'
        else: 
            return redirect('/connexion?failed=yes')

@app.route('/annonces')
def annonces():
    return render_template('annonce.html')

@app.route('/profil/<string:utilisateur>')
def profil(utilisateur):
    return 'WIP : profil utilisateur'

@app.route('/discussions')
def liste_discussions():
    return 'WIP : liste des discussions'

@app.route('/discussions/<string:id_discu>')
def discussion(id_discu):
    return 'WIP : discussion particulière'

@app.route('/mesannonces')
def mesannonces():
    return "WIP : liste des annonces de l'utilisateur"

@app.route('/inscription')
def inscription():
    return render_template('inscription.html')

@app.route('/meet', methods=['GET'])
def meet():
    data=get_db().cursor()
    CODEPOSTAL=request.args.get('CODEPOSTAL',None) 
    if CODEPOSTAL is not None :
        data.execute(f"SELECT utilisateur.pseudo FROM utilisateur WHERE utilisateur.code_postal='{CODEPOSTAL}';") 
        data.connection.commit()
    return render_template('PIERRE2.html',L=data) #Nom du html 2