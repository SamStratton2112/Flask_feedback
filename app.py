from flask import Flask, render_template, redirect, session, flash 
from models import connect_db, db, User, Feedback
from forms import UserForm, LoginForm, FeedbackForm, EditFeedbackForm
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "secret"
app.app_context().push()

connect_db(app)
db.create_all()

@app.route('/')
def show_register_page():
    """redirect to /register"""
    return redirect('/register')

@app.route('/register', methods=["GET",'POST'])
def show_register_form():
    """show registaration form and handle registration post request"""
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)
        db.session.add(new_user)
        try:
            db.session.commit()
            session['username'] = new_user.username
            return redirect(f'/users/{username}')
        except IntegrityError:
            form.username.errors.append('Username unavailable')
            return render_template('register.html', form=form)
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login_page():
    """show login form"""
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        auth_user = User.authenticate(username, password)
        if auth_user:
            session['username'] = auth_user.username
            return redirect(f'/users/{auth_user.username}')
        else:
            form.username.errors = ['Invalid username/password']
    return render_template('login.html', form=form)

@app.route('/logout')
def logout_user():
    """remove username from session"""
    session.pop('username')
    return redirect('/login')

@app.route('/users/<username>')
def show_secret_page(username):
    """protect secrect page when no one is logged in"""
    if 'username' not in session:
        flash('Please log in or register')
        return redirect('/login') 
    else:
        user = User.query.get_or_404(username)
        feedback = Feedback.query.filter_by(username=username).all()
        return render_template('user.html', user=user, feedback=feedback)

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def show_add_feedback_form(username):
    """show add feedback form and handle new comment post request """
    form = FeedbackForm()
    user = User.query.filter_by(username=username).first()
    if form.validate_on_submit():
        if session['username'] != user.username:
            flash(f'You can only add feedback for {user.username}')
            return redirect(f'/users/{user.username}')
        else:
            title = form.title.data
            content = form.content.data
            new_comment = Feedback(title=title, content=content, username=user.username)
            db.session.add(new_comment)
            db.session.commit()
            return redirect(f'/users/{user.username}')
    return render_template('add_feedback.html', form=form)

@app.route('/users/<username>/delete')
def delete_user(username):
    """deletes a user and all associated posts"""
    comments = Feedback.query.filter_by(username=username).all()
    user = User.query.filter_by(username=username).first()
    for comment in comments:
        db.session.delete(comment)
    db.session.delete(user)
    db.session.commit()
    return redirect('/')

@app.route('/users/feedback/<int:id>/update', methods=['GET','POST'])
def edit_feedback_form(id):
    """show edit feedback form and handle updates to feedback"""
    comment = Feedback.query.get_or_404(id)
    form = EditFeedbackForm(obj=comment)
    if form.validate_on_submit():
        comment.title = form.title.data
        comment.content = form.content.data
        db.session.commit()
        print('***************************')
        print(comment)
        print('***************************')
        return redirect(f'/users/{comment.username}')
    return render_template('edit_feedback.html', form=form, comment=comment)

@app.route('/users/feedback/<int:id>/delete', methods=['POST'])
def delete_feedback(id):
    comment = Feedback.query.get_or_404(id)
    username = comment.username
    db.session.delete(comment)
    db.session.commit()
    return redirect(f'/users/{username}')    





# @app.route('/users/feedback/<int:id>/update', methods=['GET','POST'])
# def edit_feedback_form(id):
#     """show edit feedback form and handle updates to feedback"""
#     comment = Feedback.query.get_or_404(id)
#     form = EditFeedbackForm(obj=comment)
#     if session['username'] == comment.username:
#         flash('Only the user who created the post can edit the post!')
#         return redirect(f'/users/{comment.username}')
#     else:
#         if form.validate_on_submit():
#             comment.title = form.title.data
#             comment.content = form.content.data
#             db.session.commit()
#             return redirect(f'/users/{comment.username}')
#         else:
#             return render_template('edit_feedback.html', form=form, comment=comment)
