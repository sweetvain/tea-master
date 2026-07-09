import os
import random
import time
import uuid
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
from models import db, User, Card, FriendRequest

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

UPLOAD_FOLDER = 'static/uploads'
COOLDOWN = 10 # Changed from 300 to 10

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER): 
    os.makedirs(UPLOAD_FOLDER)

# --- DÉCORATEUR ADMIN ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session: 
            return redirect(url_for('login'))
        user = User.query.filter_by(username=session['user']).first()
        if not user or not user.is_admin:
            return "Accès interdit : Vous n'êtes pas administrateur.", 403
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTES ADMIN ---
@app.route('/admin')
@admin_required
def admin_panel():
    users = User.query.all()
    cards = Card.query.all()
    return render_template('admin.html', users=users, cards=cards)

@app.route('/admin/toggle-admin/<int:user_id>', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.username.lower() == 'vain':
        user.is_admin = True  # L'utilisateur 'vain' est toujours un administrateur
    else:
        user.is_admin = not user.is_admin
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.username.lower() != 'vain':
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete-card/<string:card_id>', methods=['POST'])
@admin_required
def admin_delete_card(card_id):
    card = Card.query.get_or_404(card_id)
    db.session.delete(card)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/add-card', methods=['POST'])
@admin_required
def admin_add_card():
    file = request.files.get('photo')
    photo_filename = None
    if file and file.filename != '':
        photo_filename = f"{uuid.uuid4()}_{file.filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
    
    new_card = Card(
        id=str(uuid.uuid4()),
        name=request.form.get('name'),
        role=request.form.get('role'),
        description=request.form.get('description'),
        rarity=request.form.get('rarity'),
        initials=request.form.get('initials'),
        power=request.form.get('power'),
        photo=photo_filename
    )
    db.session.add(new_card)
    db.session.commit()
    return redirect(url_for('admin_panel'))

# --- ROUTES EXISTANTES ---

@app.route('/')
def index():
    if 'user' not in session: 
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['user']).first()
    if not user:
        session.pop('user', None)
        return redirect(url_for('login'))

    if user.last_update and time.time() - user.last_update >= COOLDOWN:
        user.packs_left = 2
        user.last_update = time.time()
        db.session.commit()

    next_refresh = (user.last_update or 0) + COOLDOWN
    message = request.args.get('message')
    return render_template('index.html', packs=user.packs_left, next_refresh=next_refresh, message=message)

@app.route('/collection')
def collection():
    if 'user' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['user']).first()
    if not user: return redirect(url_for('login'))
    
    user_cards_dicts = [card.to_dict() for card in user.cards]
    stats = {"total": len(user_cards_dicts), "hess": 0, "rare": 0, "epique": 0, "legendaire": 0, "mythique": 0, "goat": 0}
    for card in user_cards_dicts:
        rarity = card.get('rarity', '').lower()
        if rarity in stats: stats[rarity] += 1

    return render_template('collection.html', collection=user_cards_dicts, stats=stats)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'user' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files.get('photo')
        photo_filename = None
        if file and file.filename != '':
            photo_filename = f"{uuid.uuid4()}_{file.filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
        
        new_card = Card(
            id=str(uuid.uuid4()),
            name=request.form.get('name'),
            role=request.form.get('role'),
            description=request.form.get('description'),
            rarity=request.form.get('rarity'),
            initials=request.form.get('initials'),
            power=request.form.get('power'),
            photo=photo_filename
        )
        db.session.add(new_card)
        db.session.commit()
        return jsonify({"success": True, "message": "Carte créée avec succès !"})
    return render_template('create.html')

@app.route('/pull', methods=['POST'])
def pull():
    if 'user' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['user']).first()
    if not user: return redirect(url_for('login'))

    if user.packs_left > 0:
        owned_card_ids = {card.id for card in user.cards}
        available_cards = Card.query.filter(Card.id.notin_(owned_card_ids)).all()
        if available_cards:
            drawn = random.sample(available_cards, min(len(available_cards), 3))
            for card in drawn: user.cards.append(card)
            user.packs_left -= 1
            if user.packs_left == 0 and not user.last_update: user.last_update = time.time()
            db.session.commit()
            return render_template('pull.html', drawn_cards=[card.to_dict() for card in drawn])
        else:
            return redirect(url_for('index', message="Vous avez collecté toutes les cartes disponibles !"))
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user'] = user.username
            return redirect(url_for('index'))
        error = "Pseudo ou code secret incorrect."
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            error = "Ce pseudo est déjà pris."
        else:
            new_user = User(username=username, packs_left=2, last_update=time.time())
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            session['user'] = new_user.username
            return redirect(url_for('index'))
    return render_template('register.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'user' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['user']).first()
    if not user: return redirect(url_for('login'))

    friends = user.friends.all()
    friend_usernames = {f.username for f in friends}
    sent_req_usernames = {req.receiver.username for req in user.sent_requests}
    received_req_usernames = {req.sender.username for req in user.received_requests}

    all_users = User.query.all()
    friend_suggestions = [
        u for u in all_users
        if u.username != user.username 
        and u.username not in friend_usernames
        and u.username not in sent_req_usernames
        and u.username not in received_req_usernames
    ]

    pending_requests = user.received_requests
    user_cards_dicts = [card.to_dict() for card in user.cards]
    stats = {"total": len(user_cards_dicts), "hess": 0, "rare": 0, "epique": 0, "legendaire": 0, "mythique": 0, "goat": 0}
    for card in user_cards_dicts:
        rarity = card.get('rarity', '').lower()
        if rarity in stats: stats[rarity] += 1

    return render_template('profile.html', user=user, friends=friends, friend_suggestions=friend_suggestions, stats=stats, pending_requests=pending_requests)

# --- AMIS ---
@app.route('/send_friend_request/<string:friend_username>', methods=['POST'])
def send_friend_request(friend_username):
    if 'user' not in session: return jsonify({"success": False, "error": "Non connecté"}), 401
    current_user = User.query.filter_by(username=session['user']).first()
    target_user = User.query.filter_by(username=friend_username).first()
    if not target_user: return jsonify({"success": False, "error": "Introuvable"}), 404
    if current_user == target_user: return jsonify({"success": False, "error": "Impossible"}), 400
    
    existing = FriendRequest.query.filter(
        ((FriendRequest.sender_id == current_user.id) & (FriendRequest.receiver_id == target_user.id)) |
        ((FriendRequest.sender_id == target_user.id) & (FriendRequest.receiver_id == current_user.id))
    ).first()

    if existing: return jsonify({"success": False, "error": "Demande en cours"}), 400
    new_req = FriendRequest(sender_id=current_user.id, receiver_id=target_user.id)
    db.session.add(new_req)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/accept_friend_request/<int:request_id>', methods=['POST'])
def accept_friend_request(request_id):
    if 'user' not in session: return jsonify({"success": False}), 401
    current_user = User.query.filter_by(username=session['user']).first()
    req = FriendRequest.query.get_or_404(request_id)
    if req.receiver_id != current_user.id: return jsonify({"success": False}), 403
    sender = User.query.get(req.sender_id)
    if sender:
        current_user.friends.append(sender)
        sender.friends.append(current_user)
        db.session.delete(req)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False}), 404

@app.route('/reject_friend_request/<int:request_id>', methods=['POST'])
def reject_friend_request(request_id):
    if 'user' not in session: return jsonify({"success": False}), 401
    req = FriendRequest.query.get_or_404(request_id)
    db.session.delete(req)
    db.session.commit()
    return jsonify({"success": True})

@app.route('/remove_friend/<string:friend_username>', methods=['POST'])
def remove_friend(friend_username):
    if 'user' not in session: return jsonify({"success": False}), 401
    current_user = User.query.filter_by(username=session['user']).first()
    friend_to_remove = User.query.filter_by(username=friend_username).first()
    if current_user and friend_to_remove:
        current_user.friends.remove(friend_to_remove)
        friend_to_remove.friends.remove(current_user)
        db.session.commit()
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

# Permet d'utiliser {{ is_admin }} dans tous tes fichiers HTML
@app.context_processor
def inject_user_status():
    is_admin = False
    if 'user' in session:
        user = User.query.filter_by(username=session['user']).first()
        if user:
            is_admin = user.is_admin
    return dict(is_admin=is_admin)

@app.route('/admin/edit-card/<string:card_id>', methods=['GET', 'POST'])
@admin_required
def edit_card(card_id):
    card = Card.query.get_or_404(card_id)
    
    if request.method == 'POST':
        # Mise à jour des champs
        card.name = request.form.get('name')
        card.role = request.form.get('role')
        card.description = request.form.get('description')
        card.rarity = request.form.get('rarity')
        card.initials = request.form.get('initials')
        card.power = request.form.get('power')
        
        # Gestion photo (optionnel)
        file = request.files.get('photo')
        if file and file.filename != '':
            photo_filename = f"{uuid.uuid4()}_{file.filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
            card.photo = photo_filename
            
        db.session.commit()
        return redirect(url_for('admin_panel'))
        
    return render_template('edit_card.html', card=card)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)