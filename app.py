from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import *  # Importation des modèles

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


@app.route('/add_friend', methods=['GET', 'POST'])
@login_required
def add_friend():
    if request.method == 'POST':
        friend_id = request.form.get('friend_id')
        friend_username = request.form.get('friend_username')

        if friend_id:
            friend = User.query.get(friend_id)
        elif friend_username:
            friend = User.query.filter_by(username=friend_username).first()
        else:
            return "Erreur : Aucun utilisateur spécifié.", 400

        if not friend:
            return "Erreur : Cet utilisateur n'existe pas.", 404

        if friend.id == current_user.id:
            return "Erreur : Vous ne pouvez pas vous ajouter vous-même."

        # Vérifier si une demande existe déjà
        existing_request = FriendRequest.query.filter_by(
            sender_id=current_user.id, 
            receiver_id=friend.id,
            status='pending'
        ).first()

        if existing_request:
            return "Une demande d'ami est déjà en cours.", 400

        # Créer une nouvelle demande d'ami
        new_request = FriendRequest(sender_id=current_user.id, receiver_id=friend.id)
        db.session.add(new_request)
        db.session.commit()

        return f"Demande d'ami envoyée à {friend.username}."

    # Si méthode GET, afficher la page pour rechercher des amis
    return render_template('add_friend.html')



@app.route('/friend_requests', methods=['GET'])
@login_required
def friend_requests():
    # Récupérer les demandes reçues par l'utilisateur connecté
    requests = FriendRequest.query.filter_by(receiver_id=current_user.id, status='pending').all()
    return render_template('friend_requests.html', requests=requests)

@app.route('/respond_to_request/<int:request_id>', methods=['POST'])
@login_required
def respond_to_request(request_id):
    action = request.form['action']  # 'accept' ou 'reject'
    friend_request = FriendRequest.query.get(request_id)

    if not friend_request or friend_request.receiver_id != current_user.id:
        return "Erreur : Demande non valide.", 404

    if action == 'accept':
        # Accepter la demande d'ami
        friend_request.status = 'accepted'

        # Ajouter la relation d'amitié
        new_friendship1 = Friend(user_id=current_user.id, friend_id=friend_request.sender_id)
        new_friendship2 = Friend(user_id=friend_request.sender_id, friend_id=current_user.id)
        db.session.add(new_friendship1)
        db.session.add(new_friendship2)

    elif action == 'reject':
        # Refuser la demande d'ami
        friend_request.status = 'rejected'

    db.session.commit()
    return redirect(url_for('friend_requests'))

@app.route('/friends', methods=['GET'])
@login_required
def friends():
    # Obtenez la liste des amis en fonction des relations d'amitié
    friendships = Friend.query.filter_by(user_id=current_user.id).all()
    friends = [User.query.get(friendship.friend_id) for friendship in friendships]
    return render_template('friends.html', friends=friends)

@app.route('/start_conversation/<int:friend_id>', methods=['POST'])
@login_required
def start_conversation(friend_id):
    # Vérifiez que l'ami existe et qu'il est dans la liste des amis
    friend = User.query.get(friend_id)
    if not friend:
        return "Erreur : Cet utilisateur n'existe pas.", 404

    # Vérifiez si une conversation existe déjà entre ces deux utilisateurs
    existing_conversation = Conversation.query.filter(
        ((Conversation.user_1_id == current_user.id) & (Conversation.user_2_id == friend_id)) |
        ((Conversation.user_1_id == friend_id) & (Conversation.user_2_id == current_user.id))
    ).first()

    if existing_conversation:
        return redirect(url_for('conversation', conversation_id=existing_conversation.id))

    # Créez une nouvelle conversation
    new_conversation = Conversation(user_1_id=current_user.id, user_2_id=friend_id)
    db.session.add(new_conversation)
    db.session.commit()

    return redirect(url_for('conversation', conversation_id=new_conversation.id))

@app.route('/conversation/<int:conversation_id>', methods=['GET', 'POST'])
@login_required
def conversation(conversation_id):
    conversation = Conversation.query.get(conversation_id)

    # Vérifiez que l'utilisateur fait partie de la conversation
    if not (conversation.user_1_id == current_user.id or conversation.user_2_id == current_user.id):
        return "Erreur : Vous n'avez pas accès à cette conversation.", 403

    if request.method == 'POST':
        content = request.form['content']
        if not content:
            return "Erreur : Le message ne peut pas être vide.", 400

        # Créez un nouveau message
        new_message = Message(
            conversation_id=conversation.id,
            sender_id=current_user.id,
            content=content
        )
        db.session.add(new_message)
        db.session.commit()

    # Récupérez les messages de la conversation
    messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.timestamp).all()
    return render_template('conversation.html', conversation=conversation, messages=messages)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Erreur : Ce nom d'utilisateur est déjà pris."

        # Créer un nouvel utilisateur
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))  # Rediriger vers la page de connexion après l'inscription

    # Si méthode GET, afficher le formulaire d'inscription
    return render_template('register.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
