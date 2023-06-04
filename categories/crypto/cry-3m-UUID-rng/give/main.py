from flask import Flask, redirect ,make_response, request ,render_template,url_for
from flask_login import UserMixin 
from random import randint 
from flask_sqlalchemy import SQLAlchemy
import uuid
import hashlib


app = Flask(__name__)

db= SQLAlchemy(app)


P = 6979520618971463181853952779744486485758205309313269005483564634973779590390774016808091656989799435166737441010157234689596767531301352351693565240807853


class RNG(): 
    def __init__(self):
        self.m = 2**72
        self.a = 0xdeedbeef
        self.b = 0xc
        self.x = randint(0 , self.m)

    def next_state(self):
        self.x = (self.x * self.a + self.b) % self.m
        return self.x >> (72 - 8)

    def random(self, lenght):
        res = b""
        for i in range(lenght):
            res += bytes([self.next_state()])
        return res

RNGenerator = RNG()

class User(db.Model , UserMixin):
    __tablename__ = 'Users'
    #...

@app.route('/' , methods = ['get' , 'post'])
def start():
    if request.method == 'POST':
        if 'sign_button' in request.form:
            return redirect(url_for('sign'))
        elif 'login_button' in request.form:
            return redirect(url_for('login'))
    return render_template("index.html")

@app.route("/sign" , methods=['post' , 'get'])
def sign():
    if request.method == 'POST':
        if db.session.query(User).filter_by(username =  request.form.get('username')).all():
            return render_template('sign.html', error="Пользователь с таким именем уже есть")

        id_ = db.session.query(User).count() + 1
        uuid_ = uuid.UUID(bytes=RNGenerator.random(16) , version=4)
        u = User(username = request.form.get('username') , user_uid=str(uuid_) )
        u.set_password(request.form.get('password'))
        db.session.add(u)
        db.session.commit()
        res = make_response(redirect(url_for('cabinet' , id=id_)))
        res.set_cookie("uuid",str(uuid_) ,max_age=60*60*365*24)
        return res 
    return render_template("sign.html")

@app.route('/login',methods=['post','get'])
def login():
    if request.method == 'POST':
        user = db.session.query(User).filter(User.username == request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            id_ = int(db.session.query(User.id).filter(User.username == request.form.get('username')).all()[0][0])
            res = make_response(redirect(url_for('cabinet' , id=id_)))
            uuid_ = str(db.session.query(User.user_uid).filter(User.username == request.form.get('username')).all()[0][0])
            res.set_cookie("uuid",uuid_ , max_age = 60 * 60 * 24 * 365)
            return res
        else:
            return render_template('login.html', error="Неверный пароль/логин")
    return render_template('login.html')

@app.route("/cabinet/<int:id>/" , methods=['post','get'])
def cabinet(id ):
    if "uuid" not in request.cookies:
        return redirect(url_for('login'))
    if len(db.session.query(User).filter(User.user_uid == request.cookies["uuid"]).all()) == 0:
        return redirect(url_for('login'))
    id_ = int(db.session.query(User.id).filter(User.user_uid == request.cookies["uuid"]).all()[0][0])
    
    if id_ == id:
        if request.method == 'POST':
            return redirect(url_for('settings' , id = id_))
        username , public_info ,private_info , points = db.session.query(User.username , User.info_public , User.info_private ,User.points).filter(User.id == id_).all()[0]
        table_point = db.session.query(User.username).order_by(User.points.desc()).all()
        for i,j in enumerate(table_point):
            if j[0] == username:
                rating = i + 1
                break
        return render_template("cabinet.html" , id = id_, username = username , owner= True , public_info = public_info if public_info != None else "" , private_info = private_info  if private_info != None else "", points = points , rating = rating)
    else:
        if id > db.session.query(User).count() or id <= 0:
            return redirect(url_for('cabinet' ,  id = id_  ))
        else:
            username , public_info  , points = db.session.query(User.username , User.info_public ,User.points).filter(User.id == id).all()[0]
            table_point = db.session.query(User.username).order_by(User.points.desc()).all()
            for i,j in enumerate(table_point):
                if j[0] == username:
                    rating = i + 1
                    break
            return render_template("cabinet.html",id = id_ , username = username , owner= False , public_info = public_info if public_info != None else "" , points = points , rating = rating)



@app.route("/cabinet/<int:id>/settings" , methods=['post','get'])
def settings(id):
    if "uuid" not in request.cookies:
        return redirect(url_for('login'))
    if len(db.session.query(User).filter(User.user_uid == request.cookies["uuid"]).all()) == 0:
        return redirect(url_for('login'))
    id_ = int(db.session.query(User.id).filter(User.user_uid == request.cookies["uuid"]).all()[0][0])
    if id_ == id:
        if request.method == 'POST':
            username = request.form.get('username')
            public_info = request.form.get('public_info')
            private_info = request.form.get('private_info')
            U = db.session.query(User).get(id)
            U.info_public = public_info
            U.info_private = private_info
            if db.session.query(User).filter(User.username == username).count() == 0 and U.username != username:
                U.username = username
            db.session.commit()
            return redirect(url_for('cabinet' , id = id_))

        username , public_info ,private_info = db.session.query(User.username , User.info_public , User.info_private ).filter(User.id == id_).all()[0]
        return render_template("settings.html",id = id_ , username = username , public_info = public_info if public_info != None else "" , private_info = private_info  if private_info != None else "")
    else:
        return redirect(url_for('cabinet' , id = id_))
            

@app.route("/cabinet/rating")
def rating():
    table_bd = db.session.query(User.id , User.username , User.points).order_by(User.points.desc()).all()
    table = []
    for i, U in enumerate(table_bd):
        a = []
        a.append(i+1)
        a.append(U.id)
        a.append(U.username)
        a.append(U.points)
        table.append(a)
    if "uuid" not in request.cookies or len(db.session.query(User).filter(User.user_uid == request.cookies["uuid"]).all()) == 0:
        return render_template("rating.html" , table = table , nologin=True)
    id_ = int(db.session.query(User.id).filter(User.user_uid == request.cookies["uuid"]).all()[0][0])
    return render_template("rating.html" ,id = id_, table = table , login=True)

@app.route("/cabinet/game" , methods = ["get" , "post"])
def game():
    if "uuid" not in request.cookies:
        return redirect(url_for('login'))
    if len(db.session.query(User).filter(User.user_uid == request.cookies["uuid"]).all()) == 0:
        return redirect(url_for('login'))
    while request.method == 'POST':
        id = int(db.session.query(User.id).filter(User.user_uid == request.cookies["uuid"]).all()[0][0])
        try:
            score = int(request.args.get('score'))
            p_req = int(request.args.get('p'))
            y = int(request.args.get('y'))
            r = int(request.args.get('r'))
            s = int(request.args.get('s'))
        except Exception as e:
            print(e)
            break
        g = 2
        h = hashlib.sha256(str(score).encode()).hexdigest()
        h = int(h , 16)
        if p_req != P or r > P or s > P or pow(y , r , P) * pow(r, s % (P-1),P) % P != pow(g , h , P):
            break
        U = db.session.query(User).get(id) 
        points_old = U.points
        if score > points_old :
            U.points = score
        db.session.commit()
        break
    id_ = int(db.session.query(User.id).filter(User.user_uid == request.cookies["uuid"]).all()[0][0])
    return render_template("game.html" , id=id_)


@app.route("/logout")
def logout():
    res = make_response(redirect(url_for('login')))
    res.set_cookie("uuid" , "" , max_age = 0)
    return res

if __name__ == "__main__":
    db.create_all()
    app.run("0.0.0.0" , port=port)