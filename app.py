from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, Conversation  # Importation des modèles

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_cle_secrete'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///messagerie.db'

db.init_app(app)  # Initialise SQLAlchemy avec l'application Flask
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Gestion des utilisateurs connectés
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes principales
@app.route('/')
@login_required
def index():
    friends = User.query.filter(User.id != current_user.id).all()
    conversations = Conversation.query.filter(
        (Conversation.user_1_id == current_user.id) | 
        (Conversation.user_2_id == current_user.id)
    ).all()
    return render_template('index.html', user=current_user, friends=friends, conversations=conversations)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        return "Erreur : Identifiants incorrects"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_friend', methods=['POST'])
@login_required
def add_friend():
    friend_id = request.form['friend_id']
    friend = User.query.get(friend_id)
    if friend:
        return jsonify({'message': f'Demande envoyée à {friend.username}'})
    return jsonify({'message': 'Utilisateur introuvable'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
