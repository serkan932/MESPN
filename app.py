from flask import session, Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import socket
import os
from werkzeug.utils import secure_filename
from models import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_cle_secrete'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///messagerie.db'

# Configuration pour les photos de profil
UPLOAD_FOLDER = 'static/photos_profil'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}  # Extensions autorisées

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db.init_app(app)  # Initialise SQLAlchemy avec l'application Flask
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app)  # Initialise SocketIO pour les WebSocket

# Crée le dossier des photos de profil s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Fonction pour vérifier les fichiers autorisés
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # Correctif pour éviter LegacyAPIWarning

# Routes principales
@app.route('/')
@login_required
def index():
    friends = [friend.friend_id for friend in Friend.query.filter_by(user_id=current_user.id).all()]
    friends.append(current_user.id)  # Inclure l'utilisateur lui-même

    # Récupérer tous les utilisateurs qui ne sont pas encore amis
    users = User.query.filter(~User.id.in_(friends)).all()

    conversations = Conversation.query.filter(
        (Conversation.user_1_id == current_user.id) | 
        (Conversation.user_2_id == current_user.id)
    ).all()

    conversation_data = []
    for conversation in conversations:
        other_user = conversation.user_1 if conversation.user_2_id == current_user.id else conversation.user_2
        unread_count = Message.query.filter_by(conversation_id=conversation.id, is_read=False, sender_id=other_user.id).count()
        
        # Récupérer le dernier message de la conversation
        last_message = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.timestamp.desc()).first()

        conversation_data.append({
            'conversation': conversation,
            'other_user': other_user,
            'unread_count': unread_count,
            'last_message': last_message  # Ajouter le dernier message à la liste des données
        })

    return render_template('index.html', user=current_user, users=users, conversation_data=conversation_data)


@app.route('/toggle_dark_mode', methods=['POST'])
@login_required
def toggle_dark_mode():
    # Change le mode pour l'utilisateur actuel (ajoutez un champ 'dark_mode' à votre modèle User si ce n'est pas déjà fait)
    current_user.dark_mode = not current_user.dark_mode
    db.session.commit()
    session['dark_mode'] = current_user.dark_mode
    return "Mode sombre activé" if current_user.dark_mode else "Mode sombre désactivé"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']  # Peut être email, phone_number ou username
        password = request.form['password']

        # Rechercher l'utilisateur par pseudo, e-mail ou numéro de téléphone
        user = User.query.filter(
            (User.username == identifier) | 
            (User.email == identifier) | 
            (User.phone_number == identifier)
        ).first()

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']

        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter(
            (User.username == username) | 
            (User.email == email) | 
            (User.phone_number == phone_number)
        ).first()

        if existing_user:
            return "Erreur : Ce pseudo, e-mail ou numéro de téléphone est déjà utilisé."

        # Créer un nouvel utilisateur
        new_user = User(username=username, email=email, phone_number=phone_number, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))  # Rediriger vers la page de connexion après l'inscription

    return render_template('register.html')


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Récupérer les nouvelles informations du formulaire
        username = request.form['username']
        email = request.form['email']
        phone_number = request.form['phone_number']
        bio = request.form['bio']
        profile_picture = request.files.get('profile_picture')
        
        
        # Mettre à jour les informations utilisateur
        current_user.username = username
        current_user.email = email
        current_user.phone_number = phone_number
        current_user.bio = bio
        
        # Gestion de l'upload de la photo de profil
        if profile_picture and allowed_file(profile_picture.filename):
            # Supprimer l'ancienne photo si elle existe
            if current_user.profile_picture and os.path.exists(current_user.profile_picture):
                os.remove(current_user.profile_picture)
            
            # Sauvegarder la nouvelle photo
            filename = secure_filename(profile_picture.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_picture.save(file_path)  # Enregistrer le fichier
            current_user.profile_picture = file_path  # Mettre à jour le chemin dans la BDD

        db.session.commit()  # Enregistrer les modifications
        flash('Profil mis à jour avec succès.', 'success')
        return redirect(url_for('index'))  # Rediriger vers la page d'accueil

    return render_template('edit_profile.html', user=current_user)


@app.context_processor
def inject_profile_picture():
    def get_profile_picture(user):
        # Si l'utilisateur a une photo de profil, on renvoie l'URL correspondante dans le dossier 'photos_profil'
        if user.profile_picture and os.path.exists(user.profile_picture):
            return url_for('static', filename=f"photos_profil/{os.path.basename(user.profile_picture)}")
        # Sinon, on retourne l'image par défaut
        return url_for('static', filename='icone-profil-avatar-par-defaut-image-utilisateur-medias-sociaux-icone-avatar-gris-silhouette-profil-vierge-illustration-vectorielle_561158-3467.avif')
    return dict(get_profile_picture=get_profile_picture)

# Gestion des photos de profil
@app.route('/upload_profile_picture', methods=['POST'])
@login_required
def upload_profile_picture():
    if 'profile_picture' not in request.files:
        flash("Aucun fichier sélectionné.", "error")
        return redirect(url_for('index'))

    file = request.files['profile_picture']
    if file.filename == '':
        flash("Aucun fichier sélectionné.", "error")
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Mettre à jour le chemin de l'image dans le profil utilisateur
        current_user.profile_picture = filepath
        db.session.commit()

        flash("Photo de profil mise à jour avec succès.", "success")
        return redirect(url_for('index'))

    flash("Type de fichier non autorisé.", "error")
    return redirect(url_for('index'))

@app.route('/profile/<int:user_id>', methods=['GET'])
@login_required
def view_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("Utilisateur introuvable.", "error")
        return redirect(url_for('friends'))
    return render_template('view_profile.html', user=user)


# Gestion des amis
@app.route('/friends', methods=['GET'])
@login_required
def friends():
    friendships = Friend.query.filter_by(user_id=current_user.id).all()
    friends = [db.session.get(User, friendship.friend_id) for friendship in friendships]
    return render_template('friends.html', friends=friends)

@app.route('/add_friend', methods=['GET', 'POST'])
@login_required
def add_friend():
    if request.method == 'POST':
        friend_username = request.form.get('friend_username')
        friend = User.query.filter_by(username=friend_username).first()

        if not friend:
            return "Cet utilisateur n'existe pas.", 404

        if friend.id == current_user.id:
            return "Vous ne pouvez pas vous ajouter vous-même."

        existing_request = FriendRequest.query.filter_by(
            sender_id=current_user.id, 
            receiver_id=friend.id,
            status='pending'
        ).first()

        if existing_request:
            return "Une demande d'ami est déjà en cours.", 400

        new_request = FriendRequest(sender_id=current_user.id, receiver_id=friend.id)
        db.session.add(new_request)
        db.session.commit()

        return f"Demande d'ami envoyée à {friend.username}."

    return render_template('add_friend.html')

@app.route('/remove_friend/<int:friend_id>', methods=['POST'])
@login_required
def remove_friend(friend_id):
    friendship = Friend.query.filter_by(user_id=current_user.id, friend_id=friend_id).first()
    reverse_friendship = Friend.query.filter_by(user_id=friend_id, friend_id=current_user.id).first()

    if not friendship or not reverse_friendship:
        return "Erreur : Vous n'êtes pas amis avec cet utilisateur.", 404

    db.session.delete(friendship)
    db.session.delete(reverse_friendship)
    db.session.commit()

    return redirect(url_for('friends'))

@app.route('/friend_requests', methods=['GET'])
@login_required
def friend_requests():
    requests = FriendRequest.query.filter_by(receiver_id=current_user.id, status='pending').all()
    return render_template('friend_requests.html', requests=requests)

@app.route('/respond_to_request/<int:request_id>', methods=['POST'])
@login_required
def respond_to_request(request_id):
    action = request.form['action']
    friend_request = db.session.get(FriendRequest, request_id)

    if not friend_request or friend_request.receiver_id != current_user.id:
        return "Erreur : Demande non valide.", 404

    if action == 'accept':
        friend_request.status = 'accepted'
        new_friendship1 = Friend(user_id=current_user.id, friend_id=friend_request.sender_id)
        new_friendship2 = Friend(user_id=friend_request.sender_id, friend_id=current_user.id)
        db.session.add(new_friendship1)
        db.session.add(new_friendship2)
    elif action == 'reject':
        friend_request.status = 'rejected'

    db.session.commit()
    return redirect(url_for('friend_requests'))

@app.route('/search_users', methods=['GET', 'POST'])
@login_required
def search_users():
    if request.method == 'POST':
        query = request.form['query']
        users = User.query.filter(User.username.contains(query), User.id != current_user.id).all()
        return render_template('search_results.html', users=users)
    return render_template('search_users.html')

# Conversations
@app.route('/start_conversation/<int:friend_id>', methods=['POST'])
@login_required
def start_conversation(friend_id):
    friend = db.session.get(User, friend_id)
    if not friend:
        return "Cet utilisateur n'existe pas.", 404

    existing_conversation = Conversation.query.filter(
        ((Conversation.user_1_id == current_user.id) & (Conversation.user_2_id == friend_id)) |
        ((Conversation.user_1_id == friend_id) & (Conversation.user_2_id == current_user.id))
    ).first()

    if existing_conversation:
        return redirect(url_for('conversation', conversation_id=existing_conversation.id))

    new_conversation = Conversation(user_1_id=current_user.id, user_2_id=friend_id)
    db.session.add(new_conversation)
    db.session.commit()

    return redirect(url_for('conversation', conversation_id=new_conversation.id))

@app.route('/conversation/<int:conversation_id>', methods=['GET', 'POST'])
@login_required
def conversation(conversation_id):
    conversation = db.session.get(Conversation, conversation_id)

    if not conversation:
        return "Erreur : Cette conversation n'existe pas.", 404

    if not (conversation.user_1_id == current_user.id or conversation.user_2_id == current_user.id):
        return "Erreur : Vous n'avez pas accès à cette conversation.", 403

    if request.method == 'POST':
        content = request.form['content']
        if not content.strip():
            return "Erreur : Le message ne peut pas être vide.", 400
        
        new_message = Message(
            conversation_id=conversation.id,
            sender_id=current_user.id,
            content=content
        )
        db.session.add(new_message)
        db.session.commit()

    # Marquer tous les messages non lus comme lus pour l'utilisateur actuel
    unread_messages = Message.query.filter_by(conversation_id=conversation.id, is_read=False).all()
    for msg in unread_messages:
        # Ne marquez comme "lu" que les messages envoyés par l'autre utilisateur
        if msg.sender_id != current_user.id:
            msg.is_read = True
    db.session.commit()

    # Récupérez tous les messages associés à cette conversation
    messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.timestamp).all()

    # Comptez le nombre de messages non lus
    unread_count = Message.query.filter_by(conversation_id=conversation.id, is_read=False).count()

    return render_template(
        'conversation.html',
        conversation=conversation,
        messages=messages,
        unread_count=unread_count,  # Passez le nombre de messages non lus à la page
        current_user=current_user  # Passer explicitement current_user
    )


# WebSockets pour les conversations en temps réel
@socketio.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f"{current_user.username} a rejoint la salle."}, room=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = data['message']
    new_message = Message(
        conversation_id=room,
        sender_id=current_user.id,
        content=message
    )
    db.session.add(new_message)
    db.session.commit()
    emit('message', {'sender': current_user.username, 'message': message}, room=room)

# Serveur UDP
def start_udp_server():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("0.0.0.0", 12346))  # Port ajusté pour éviter les conflits
    print("Serveur UDP en écoute sur le port 12346")

    while True:
        data, addr = udp_socket.recvfrom(1024)
        print(f"Message reçu de {addr}: {data.decode()}")
        udp_socket.sendto("Message reçu".encode('utf-8'), addr)


@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        group_name = request.form['group_name']
        friend_ids = request.form.getlist('friends')  # Récupère les ID des amis sélectionnés
        
        # Crée le groupe avec l'utilisateur connecté comme admin
        new_group = Group(name=group_name, admin_id=current_user.id)
        db.session.add(new_group)
        db.session.commit()
        
        # Ajoute les membres sélectionnés
        for friend_id in friend_ids:
            new_member = GroupMember(group_id=new_group.id, user_id=friend_id)
            db.session.add(new_member)
        
        # Ajoute l'utilisateur connecté au groupe en tant que membre
        admin_member = GroupMember(group_id=new_group.id, user_id=current_user.id)
        db.session.add(admin_member)

        db.session.commit()
        return redirect(url_for('groups'))
    
    # Récupère les amis de l'utilisateur pour les afficher dans la page de création
    friendships = Friend.query.filter_by(user_id=current_user.id).all()
    friends = [db.session.get(User, friendship.friend_id) for friendship in friendships]
    return render_template('create_group.html', friends=friends)


@app.route('/groups', methods=['GET'])
@login_required
def groups():
    groups = Group.query.join(GroupMember).filter(GroupMember.user_id == current_user.id).all()
    return render_template('groups.html', groups=groups, user=current_user)


@app.route('/group/<int:group_id>', methods=['GET', 'POST'])
@login_required
def group_chat(group_id):
    group = db.session.get(Group, group_id)

    # Vérifiez que l'utilisateur est membre du groupe
    is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    if not is_member:
        return "Erreur : Vous n'êtes pas membre de ce groupe.", 403

    if request.method == 'POST':
        content = request.form['content']
        if not content.strip():
            return "Erreur : Le message ne peut pas être vide.", 400

        # Ajoutez le message au groupe
        new_message = Message(group_id=group_id, sender_id=current_user.id, content=content)
        db.session.add(new_message)
        db.session.commit()

    # Récupérez tous les messages du groupe
    messages = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp).all()
    return render_template('group_chat.html', group=group, messages=messages)

@app.route('/group/<int:group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    group = db.session.get(Group, group_id)
    if not group:
        return "Erreur : Groupe introuvable.", 404

    membership = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    if not membership:
        return "Erreur : Vous n'êtes pas membre de ce groupe.", 403

    db.session.delete(membership)

    # Vérifiez si l'utilisateur est l'administrateur
    if group.admin_id == current_user.id:
        remaining_members = GroupMember.query.filter_by(group_id=group_id).all()
        if not remaining_members:
            # Supprimez le groupe s'il n'a plus de membres
            db.session.delete(group)

    db.session.commit()
    return redirect(url_for('groups'))

@app.route('/group/<int:group_id>/delete', methods=['POST'])
@login_required
def delete_group(group_id):
    group = db.session.get(Group, group_id)
    if not group:
        return "Erreur : Groupe introuvable.", 404

    if group.admin_id != current_user.id:
        return "Erreur : Seul l'administrateur peut supprimer ce groupe.", 403

    # Supprimez tous les membres et le groupe
    GroupMember.query.filter_by(group_id=group_id).delete()
    db.session.delete(group)
    db.session.commit()
    return redirect(url_for('groups'))

@app.route('/group/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    group = db.session.get(Group, group_id)
    if not group:
        return "Erreur : Groupe introuvable.", 404

    if group.admin_id != current_user.id:
        return "Erreur : Seul l'administrateur peut modifier ce groupe.", 403

    if request.method == 'POST':
        new_name = request.form['group_name']
        group.name = new_name
        db.session.commit()
        return redirect(url_for('groups'))

    return render_template('edit_group.html', group=group)


@app.route('/call/<int:user_id>', methods=['GET'])
@login_required
def call_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return "Utilisateur introuvable.", 404

    return render_template('call.html', user=user, current_user=current_user)


@app.route('/group_call/<int:group_id>', methods=['GET'])
@login_required
def group_call(group_id):
    group = Group.query.get(group_id)
    if not group:
        return "Groupe introuvable.", 404

    is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    if not is_member:
        return "Vous n'êtes pas membre de ce groupe.", 403

    return render_template('group_call.html', group=group, current_user=current_user)

@socketio.on('call-user')
def handle_call(data):
    user_id = data['userId']
    offer = data['offer']
    emit('call-made', {'offer': offer, 'from': current_user.id}, to=user_id)

#websocket pour les appels, pour gerer les connexions WebRTC
@socketio.on('make-answer')
def handle_answer(data):
    answer = data['answer']
    emit('answer-made', {'answer': answer, 'to': current_user.id}, to=data['to'])


@socketio.on('ice-candidate')
def handle_ice_candidate(data):
    candidate = data['candidate']
    emit('ice-candidate', {'candidate': candidate}, to=data['to'])

@app.route('/send_friend_request', methods=['POST'])
@login_required
def send_friend_request():
    user_id = request.form.get('user_id')
    if not user_id:
        return "Erreur : Aucun utilisateur sélectionné.", 400

    friend = User.query.get(user_id)
    if not friend:
        return "Erreur : Utilisateur introuvable.", 404

    if friend.id == current_user.id:
        return "Erreur : Vous ne pouvez pas vous ajouter vous-même.", 400

    existing_request = FriendRequest.query.filter_by(sender_id=current_user.id, receiver_id=friend.id, status='pending').first()
    if existing_request:
        return "Erreur : Une demande d'ami est déjà en cours.", 400

    new_request = FriendRequest(sender_id=current_user.id, receiver_id=friend.id)
    db.session.add(new_request)
    db.session.commit()

    flash(f"Demande d'ami envoyée à {friend.username}.", "success")
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    udp_thread = threading.Thread(target=start_udp_server, daemon=True)
    udp_thread.start()

    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
