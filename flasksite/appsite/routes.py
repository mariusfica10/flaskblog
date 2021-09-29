from flask import render_template, url_for, flash, redirect, request, abort
from appsite.forms import RegistrationForm, LoginForm, SearchBoxForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm
from appsite.models import User, Post
from appsite import app, db, bcrypt, mail
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from PIL import Image
from flask_mail import Message


"""
pentru toate
@app.route - caile web ale functiilor care returneaza pagina cu render_template
@login_required - asigurarea ca este un user conectat pentru a accesa functia/route ul
return render_template returnarea route
"""


"""
desc: incarcare toate postarile de la toti userii descrescator in functie de data
      si afisarea acestora prin ruta cu render_template
TODO scrolling infinit
"""
@app.route('/')
@app.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    
    return render_template('home.html', posts = posts, title='Index')

'''
returneaza cale pentru about page
'''
@app.route('/about')
def about():
    return render_template('about.html', title = 'About')

'''
methods: get(luare informatii de la server) and post(schimbari server)
desc: incarcare pagina register in care un form trebuie completat pentru inregistrare cont
      daca toate lucrurile sunt valide
'''
@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

'''
methods: get(luare informatii de la server) and post(schimbari server)
desc: incarcare pagina login in care se incearca conectarea prin verificarea parolei si a userului 
      in baza de date
      daca este totul valid se face redirect la home page
      daca nu este afisat un flash error
'''
@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

'''
desc: apelare functie delogare user
      redirect catre pagina principala
'''
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

'''
desc: salvare poza de profil cu nume generat random si cu miscroarea acesteia prin 
      biblioteca pil
param: form_picture - poza de salvat
'''
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    f_name, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

'''
desc: update cont form si afisare user cu datele sale si poza
      mesaj flash daca totul este updatat
methods: get(luare informatii de la server) and post(schimbari server)
'''
@app.route('/account',  methods=['GET','POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file = image_file, form=form)


"""

desc: postare noua care va fi introdusa in baza de date, logarea necesara
    formul daca este valid postarea este introdusa in baza de date
methods: get(luare informatii de la server) and post(schimbari server)
TODO: schimbare in functie de time zone
"""
@app.route('/post/new', methods=['GET','POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')

'''
desc: route care este randat in functie de id ul postarii
    este aruncata eroare 404 daca nu este valid
'''
@app.route("/post/<int:post_id>")
def post(post_id):
    post=Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

'''
desc: se cauta postarea in baza de date si se completeaza formul pentru update, daca este valid se face
      schimbarea in baza de date, cu postarea updatata
param: post_id - route update post
methods: get(luare informatii de la server) and post(schimbari server)
'''
@app.route("/post/<int:post_id>/update", methods=['GET','POST'])
@login_required
def update_post(post_id):
    post=Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')

'''
methods: post(schimbare in server)
desc: route de stergere, baza de date este updatata
      sau daca contul nu este valid eroare 403
      redirect home + flash message
'''
@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post=Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


"""
parametru dinamic cu <X:> unde e X putem sa punem tipul de data
param: username - selectare user
desc: se executa o interogare in care toate postarile sunt luate
de la username, paginate, cu 5 postari pe pagina
"""
@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)

'''
params: userul care vrea parola schimbata
desc: emailul este trimis cu ajutorul functiei mail din flask
'''
def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
    msg.body = f''' To reset your password, visit the following link:
{url_for('reset_token', token = token, _external=True)}
If you did not make this request then simply ignore this email and no change will be made


Have a nice day!
'''
    mail.send(msg)


"""
methods: get from server / post to server
params: -
desc: functie care primeste un request de la server cu emailul
redirect la login cu mesajul de email trimis
TODO new email
"""
@app.route('/reset_password', methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)

'''
methods: get from server / post to server
param: token- linkul valabil pentru resetare, string
desc: resetarea parolei prin form de inserare de parola noua de 2 ori
trimitere pe pagina de resetare
daca este validat formul, se fac schimbarile in baza de date cu parola criptata
'''
@app.route('/reset_password/<token>', methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)