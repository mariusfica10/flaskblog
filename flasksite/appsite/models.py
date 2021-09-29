from appsite import db, login_manager, app
from datetime import datetime
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

'''
desc: functie cautare in baza de si returnare obiect
param: user_id - user de cautat
'''
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

'''
clasa user pentru salvare user in baza de date
params:
id- id user, primary key, int
username- username cont, string(maxim 20)
email- emailul contului dupa care se face recuperare parola/logare, string(maxim 120)
image_file- route ul imaginii care se gaseste in static/profile_pics, string
password- parola criptata a contului, string(maxim 60)
posts- relationship pentru foreign key, legare postare cu user
'''
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    '''
    generare token pentru email reset
    return: token
    '''
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    """
    functie statica
    care verifica token ul de resetare parola
    return: userul cu token
    """
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    '''
    metoda to string
    '''
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

'''
clasa postare pentru salvare postari ale userilor existenti in baza de date
params:
id- id obiect, primary key, int
title- titlu postare, string(maxim 100)
date_posted- data postare, datetime.utcnow
content- ce contine postarea, string
user_id- foreign key care repr. userul a carui postari este, int
'''
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    '''
    metoda to string
    '''
    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

