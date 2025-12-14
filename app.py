import os
from functools import wraps
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf
from models import db, User, Quest, QuestCompletion, Transaction
from datetime import date, datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

if not database_url:
    raise RuntimeError("DATABASE_URL environment variable is not set. Please configure it in your environment.")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_TIME_LIMIT'] = None

db.init_app(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

ADMIN_CODE = "1289"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_access'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def init_quests():
    quests_data = [
        {
            "order": 1,
            "title": "Suivre MrBeast sur YouTube",
            "description": "Abonnez-vous à la chaîne YouTube de MrBeast",
            "icon": "youtube",
            "action_url": "https://www.youtube.com/@MrBeast",
            "action_type": "subscribe"
        },
        {
            "order": 2,
            "title": "Inviter un ami",
            "description": "Parrainez au moins une personne avec votre lien de parrainage",
            "icon": "users",
            "action_url": "",
            "action_type": "referral"
        },
        {
            "order": 3,
            "title": "Rejoindre Telegram",
            "description": "Rejoignez notre groupe Telegram",
            "icon": "telegram",
            "action_url": "https://t.me/mrbeast",
            "action_type": "join"
        },
        {
            "order": 4,
            "title": "Suivre sur TikTok",
            "description": "Suivez notre compte TikTok",
            "icon": "tiktok",
            "action_url": "https://www.tiktok.com/@mrbeast",
            "action_type": "follow"
        },
    ]
    
    for quest_data in quests_data:
        existing_quest = Quest.query.filter_by(order=quest_data["order"]).first()
        if existing_quest:
            existing_quest.title = quest_data["title"]
            existing_quest.description = quest_data["description"]
            existing_quest.icon = quest_data["icon"]
            existing_quest.action_url = quest_data["action_url"]
            existing_quest.action_type = quest_data["action_type"]
        else:
            new_quest = Quest(
                title=quest_data["title"],
                description=quest_data["description"],
                icon=quest_data["icon"],
                order=quest_data["order"],
                action_url=quest_data["action_url"],
                action_type=quest_data["action_type"]
            )
            db.session.add(new_quest)
    db.session.commit()

def create_admin():
    admin = User.query.filter_by(email='admin@questmoney.com').first()
    if not admin:
        admin = User(username='Admin', email='admin@questmoney.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

with app.app_context():
    db.create_all()
    init_quests()
    create_admin()

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

REFERRAL_BONUS = 10.0

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    ref_code = request.args.get('ref', '')
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        referral_code = request.form.get('referral_code', '').strip()
        
        if not username or not email or not password:
            flash('Tous les champs sont requis.', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur existe déjà.', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'error')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        if referral_code:
            referrer = User.query.filter_by(referral_code=referral_code).first()
            if referrer and not referrer.is_admin:
                user.referred_by_id = referrer.id
        
        db.session.add(user)
        db.session.commit()
        
        flash('Inscription réussie! Connectez-vous maintenant.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', ref_code=ref_code)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Connexion réussie!', 'success')
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou mot de passe incorrect.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    quests = Quest.query.all()
    completed_today = current_user.get_completed_quests_today()
    today_completions = QuestCompletion.query.filter(
        QuestCompletion.user_id == current_user.id,
        db.func.date(QuestCompletion.completed_at) == date.today()
    ).all()
    completed_quest_ids = [c.quest_id for c in today_completions]
    
    pending_transactions = Transaction.query.filter_by(
        user_id=current_user.id, 
        status='pending'
    ).count()
    
    return render_template('dashboard.html', 
                         quests=quests, 
                         completed_today=completed_today,
                         completed_quest_ids=completed_quest_ids,
                         pending_transactions=pending_transactions)

@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
        except (ValueError, TypeError):
            flash('Montant invalide.', 'error')
            return redirect(url_for('deposit'))
        
        if amount < 200:
            flash('Le minimum de dépôt est de 200$.', 'error')
            return redirect(url_for('deposit'))
        
        if amount > current_user.balance:
            flash('Solde insuffisant pour ce dépôt.', 'error')
            return redirect(url_for('deposit'))
        
        current_user.deposit += amount
        current_user.balance -= amount
        db.session.commit()
        flash(f'Dépôt de {amount:.2f}$ effectué avec succès!', 'success')
        return redirect(url_for('dashboard'))
    
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).limit(5).all()
    return render_template('deposit.html', transactions=user_transactions)

@app.route('/request_deposit', methods=['POST'])
@login_required
def request_deposit():
    try:
        amount = float(request.form.get('amount', 0))
    except (ValueError, TypeError):
        flash('Montant invalide.', 'error')
        return redirect(url_for('deposit'))
    
    tx_hash = request.form.get('tx_hash', '').strip()
    
    if amount < 200:
        flash('Le minimum de dépôt est de 200$.', 'error')
        return redirect(url_for('deposit'))
    
    transaction = Transaction(
        user_id=current_user.id,
        type='deposit',
        amount=amount,
        tx_hash=tx_hash,
        status='pending'
    )
    db.session.add(transaction)
    db.session.commit()
    
    flash('Demande de dépôt envoyée! En attente de validation.', 'success')
    return redirect(url_for('deposit'))

@app.route('/request_withdrawal', methods=['POST'])
@login_required
def request_withdrawal():
    DAILY_WITHDRAWAL_LIMIT = 150.0
    
    try:
        amount = float(request.form.get('amount', 0))
    except (ValueError, TypeError):
        flash('Montant invalide.', 'error')
        return redirect(url_for('dashboard'))
    
    wallet_address = request.form.get('wallet_address', '').strip()
    
    if amount <= 0:
        flash('Le montant doit être positif.', 'error')
        return redirect(url_for('dashboard'))
    
    if amount > current_user.balance:
        flash('Solde insuffisant.', 'error')
        return redirect(url_for('dashboard'))
    
    if not wallet_address:
        flash('Adresse de portefeuille requise.', 'error')
        return redirect(url_for('dashboard'))
    
    daily_total = current_user.get_daily_withdrawal_total()
    if daily_total + amount > DAILY_WITHDRAWAL_LIMIT:
        remaining = DAILY_WITHDRAWAL_LIMIT - daily_total
        if remaining <= 0:
            flash(f'Vous avez atteint la limite de retrait journalier de {DAILY_WITHDRAWAL_LIMIT:.2f}$.', 'error')
        else:
            flash(f'Ce retrait dépasse la limite journalière. Il vous reste {remaining:.2f}$ disponibles aujourd\'hui.', 'error')
        return redirect(url_for('dashboard'))
    
    transaction = Transaction(
        user_id=current_user.id,
        type='withdrawal',
        amount=amount,
        wallet_address=wallet_address,
        status='pending'
    )
    current_user.balance -= amount
    db.session.add(transaction)
    db.session.commit()
    
    flash('Demande de retrait envoyée! En attente de validation.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/add_balance', methods=['POST'])
@login_required
def add_balance():
    try:
        amount = float(request.form.get('amount', 0))
    except (ValueError, TypeError):
        flash('Montant invalide.', 'error')
        return redirect(url_for('deposit'))
    
    if amount <= 0 or amount > 10000:
        flash('Montant invalide (max 10000$ en mode démo).', 'error')
        return redirect(url_for('deposit'))
    
    current_user.balance += amount
    db.session.commit()
    flash(f'{amount:.2f}$ ajoutés à votre solde (mode démo).', 'success')
    return redirect(url_for('deposit'))

@app.route('/complete_quest/<int:quest_id>', methods=['POST'])
@login_required
def complete_quest(quest_id):
    if not current_user.can_complete_quest():
        return jsonify({'success': False, 'message': 'Vous avez déjà complété 4 quêtes aujourd\'hui ou vous n\'avez pas de dépôt.'})
    
    quest = Quest.query.get_or_404(quest_id)
    
    today_completion = QuestCompletion.query.filter(
        QuestCompletion.user_id == current_user.id,
        QuestCompletion.quest_id == quest_id,
        db.func.date(QuestCompletion.completed_at) == date.today()
    ).first()
    
    if today_completion:
        return jsonify({'success': False, 'message': 'Vous avez déjà complété cette quête aujourd\'hui.'})
    
    if quest.action_type == 'referral':
        referral_count = User.query.filter_by(referred_by_id=current_user.id).count()
        if referral_count == 0:
            return jsonify({'success': False, 'message': 'Vous devez parrainer au moins une personne pour valider cette quête. Partagez votre lien de parrainage depuis votre profil!'})
    
    reward = current_user.deposit * 0.5
    
    completion = QuestCompletion(
        user_id=current_user.id,
        quest_id=quest_id,
        reward=reward
    )
    current_user.balance += reward
    
    db.session.add(completion)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'Quête complétée! Vous avez gagné {reward:.2f}$',
        'new_balance': current_user.balance,
        'completed_today': current_user.get_completed_quests_today()
    })

@app.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    try:
        amount = float(request.form.get('amount', 0))
    except (ValueError, TypeError):
        flash('Montant invalide.', 'error')
        return redirect(url_for('dashboard'))
    
    if amount <= 0:
        flash('Le montant doit être positif.', 'error')
        return redirect(url_for('dashboard'))
    
    if amount > current_user.balance:
        flash('Solde insuffisant.', 'error')
        return redirect(url_for('dashboard'))
    
    current_user.balance -= amount
    db.session.commit()
    flash(f'Retrait de {amount:.2f}$ effectué!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/history')
@login_required
def history():
    completions = QuestCompletion.query.filter_by(user_id=current_user.id).order_by(QuestCompletion.completed_at.desc()).all()
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).all()
    return render_template('history.html', completions=completions, transactions=transactions)

@app.route('/profile')
@login_required
def profile():
    referral_count = User.query.filter_by(referred_by_id=current_user.id).count()
    referral_link = request.host_url + 'register?ref=' + (current_user.referral_code or '')
    return render_template('profile.html', 
                         referral_count=referral_count,
                         referral_link=referral_link,
                         referral_bonus=REFERRAL_BONUS)

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not current_user.check_password(current_password):
        flash('Mot de passe actuel incorrect.', 'error')
        return redirect(url_for('profile'))
    
    if len(new_password) < 6:
        flash('Le nouveau mot de passe doit contenir au moins 6 caracteres.', 'error')
        return redirect(url_for('profile'))
    
    if new_password != confirm_password:
        flash('Les mots de passe ne correspondent pas.', 'error')
        return redirect(url_for('profile'))
    
    current_user.set_password(new_password)
    db.session.commit()
    flash('Mot de passe mis a jour avec succes!', 'success')
    return redirect(url_for('profile'))

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_access'):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        code = request.form.get('code', '')
        if code == ADMIN_CODE:
            session['admin_access'] = True
            flash('Accès administrateur accordé.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Code incorrect.', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_access', None)
    flash('Déconnexion de l\'espace admin.', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    pending_deposits = Transaction.query.filter_by(type='deposit', status='pending').count()
    pending_withdrawals = Transaction.query.filter_by(type='withdrawal', status='pending').count()
    total_users = User.query.filter_by(is_admin=False).count()
    
    recent_transactions = Transaction.query.filter_by(status='pending').order_by(Transaction.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         pending_deposits=pending_deposits,
                         pending_withdrawals=pending_withdrawals,
                         total_users=total_users,
                         recent_transactions=recent_transactions)

@app.route('/admin/transactions')
@admin_required
def admin_transactions():
    status_filter = request.args.get('status', 'pending')
    type_filter = request.args.get('type', 'all')
    
    query = Transaction.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if type_filter != 'all':
        query = query.filter_by(type=type_filter)
    
    transactions = query.order_by(Transaction.created_at.desc()).all()
    
    return render_template('admin/transactions.html',
                         transactions=transactions,
                         status_filter=status_filter,
                         type_filter=type_filter)

@app.route('/admin/transaction/<int:tx_id>/approve', methods=['POST'])
@admin_required
def approve_transaction(tx_id):
    transaction = Transaction.query.get_or_404(tx_id)
    
    if transaction.status != 'pending':
        flash('Cette transaction a déjà été traitée.', 'error')
        return redirect(url_for('admin_transactions'))
    
    transaction.status = 'approved'
    transaction.processed_at = datetime.utcnow()
    transaction.processed_by = current_user.id if current_user.is_authenticated else None
    transaction.admin_note = request.form.get('note', '')
    
    user = User.query.get(transaction.user_id)
    if transaction.type == 'deposit':
        previous_approved_deposits = Transaction.query.filter(
            Transaction.user_id == user.id, 
            Transaction.type == 'deposit', 
            Transaction.status == 'approved',
            Transaction.id != transaction.id
        ).count()
        
        user.balance += transaction.amount
        
        if previous_approved_deposits == 0 and user.referred_by_id:
            referrer = User.query.get(user.referred_by_id)
            if referrer:
                referrer.balance += REFERRAL_BONUS
                referrer.referral_bonus_earned = (referrer.referral_bonus_earned or 0) + REFERRAL_BONUS
    
    db.session.commit()
    flash(f'Transaction #{tx_id} approuvée.', 'success')
    return redirect(url_for('admin_transactions'))

@app.route('/admin/transaction/<int:tx_id>/reject', methods=['POST'])
@admin_required
def reject_transaction(tx_id):
    transaction = Transaction.query.get_or_404(tx_id)
    
    if transaction.status != 'pending':
        flash('Cette transaction a déjà été traitée.', 'error')
        return redirect(url_for('admin_transactions'))
    
    transaction.status = 'rejected'
    transaction.processed_at = datetime.utcnow()
    transaction.processed_by = current_user.id if current_user.is_authenticated else None
    transaction.admin_note = request.form.get('note', '')
    
    if transaction.type == 'withdrawal':
        user = User.query.get(transaction.user_id)
        user.balance += transaction.amount
    
    db.session.commit()
    flash(f'Transaction #{tx_id} rejetée.', 'success')
    return redirect(url_for('admin_transactions'))

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>/add_balance', methods=['POST'])
@admin_required
def admin_add_balance(user_id):
    user = User.query.get_or_404(user_id)
    try:
        amount = float(request.form.get('amount', 0))
    except (ValueError, TypeError):
        flash('Montant invalide.', 'error')
        return redirect(url_for('admin_users'))
    
    user.balance += amount
    db.session.commit()
    flash(f'{amount:.2f}$ ajoutés au compte de {user.username}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/quick_add_balance', methods=['POST'])
@admin_required
def admin_quick_add_balance():
    user_email = request.form.get('user_email', '').strip()
    add_type = request.form.get('add_type', 'balance')
    
    try:
        amount = float(request.form.get('amount', 0))
    except (ValueError, TypeError):
        flash('Montant invalide.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if amount <= 0:
        flash('Le montant doit être positif.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    user = User.query.filter_by(email=user_email).first()
    if not user:
        flash(f'Aucun utilisateur trouvé avec l\'email: {user_email}', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if user.is_admin:
        flash('Impossible d\'ajouter des fonds à un compte admin.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if add_type == 'deposit':
        user.deposit += amount
        flash(f'{amount:.2f}$ ajoutés au dépôt actif de {user.username}.', 'success')
    else:
        user.balance += amount
        flash(f'{amount:.2f}$ ajoutés au solde de {user.username}.', 'success')
    
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
