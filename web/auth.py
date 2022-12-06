import hashlib

ouvre_db = lambda : [i.replace('\n', '').split(',') for i in open('static/users.txt').readlines() if i[0] != '#']
# Ouvre la base de données rudimentaire et ignore les commentaires

def adduser(usrname, mdp):
    """Ajoute un utilisateur à la base de données. Renvoie True si l'ajout est fait, False s'il est refusé"""
    if not pseudolibre(usrname): return False # On n'ajoute pas un utilisateur dont le pseudo est déjà pris
    idmax = int(open('static/users.txt', 'r').readlines()[-1].split(',')[0]) # Récupération du plus grand id
    with open('static/users.txt', 'a') as f:
        hash = hashlib.md5(mdp.encode('utf-8')).hexdigest() # Le mdp est hashé
        f.write(f'\n{idmax+1},{usrname},{hash}')
    return True

#adduser('titouan', 'titanp0t')
#adduser('pierre', 'foutu pull')
#adduser('arnaud', 'jolie_bdd')

def pseudolibre(usrname):
    """Vérifie si un pseudo est déjà pris"""
    data = ouvre_db()
    for i in data:
        if i[1] == usrname: return False
    return True

def login_valide(usrname, mdp):
    """Vérifie si un login (pseudo + mdp) est valide"""
    data = ouvre_db()
    hash = hash = hashlib.md5(mdp.encode('utf-8')).hexdigest()
    for i in data:
        if (i[1], i[2]) == (usrname, hash): return True
    return False

def get_id(usrname, mdp):
    """Renvoie l'id de l'utilisateur spécifié. Ne vérifie pas s'il existe."""
    data = ouvre_db()
    hash = hash = hashlib.md5(mdp.encode('utf-8')).hexdigest()
    for i in data:
        if (i[1], i[2]) == (usrname, hash): return int(i[0])
    return None

# login_valide et get_id sont des fonctions différentes pour simplifier la création d'un message d'erreur en cas de mauvaise connexion.
# elles seront aussi un tantinet plus différentes lorsqu'on implémentera la vraie BDD