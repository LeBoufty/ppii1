from flask import Flask
from flask import render_template
from flask import g
from flask import request
from flask import redirect

import sqlite3

DATABASE='ARNAUD.db' #nom de la db

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
def status():
    return 'Up and running lika potagiste'

@app.route('/display')
def display():
    data=get_db().cursor()
    data.execute("select * from ARNAUD") #Nom de la db
    return render_template('PIERRE.html',L=data) #Nom du html

@app.route('/meet', methods=['GET'])
def add():
    data=get_db().cursor()
    CODEPOSTAL=request.args.get('CODEPOSTAL',None) 
    if CODEPOSTAL is not None :
        data.execute(f"SELECT ARNAUD.personnes FROM ARNAUD WHERE ARNAUD.codepostal='{CODEPOSTAL}';") #Nom de la db
        data.connection.commit()
    return render_template('PIERRE2.html',L=data) #Nom du html 2