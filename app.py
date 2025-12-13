import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Quest, QuestCompletion
from datetime import date

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_quests():
    if Quest.query.count() == 0:
        quests = [
            Quest(title="Quête du Guerrier", description="Complétez 10 combats virtuels", icon="sword"),
            Quest(title="Quête du Sage", description="Répondez à 5 énigmes", icon="book"),
            Quest(title="Quête de l'Explorateur", description="Découvrez 3 nouveaux territoires", icon="map"),
            Quest(title="Quête du Collectionneur", description="Trouvez 7 objets rares", icon="gem"),
        ]
        for quest in quests:
            db.session.add(quest)
        db.session.commit()

with app.app_context():
    db.create_all()
    init_quests()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur existe déjà.', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'error')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Inscription réussie! Connectez-vous maintenant.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Connexion réussie!', 'success')
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
    
    return render_template('dashboard.html', 
                         quests=quests, 
                         completed_today=completed_today,
                         completed_quest_ids=completed_quest_ids)

@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        if amount > 0:
            current_user.deposit += amount
            current_user.balance -= amount
            db.session.commit()
            flash(f'Dépôt de {amount}€ effectué avec succès!', 'success')
        else:
            flash('Montant invalide.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('deposit.html')

@app.route('/add_balance', methods=['POST'])
@login_required
def add_balance():
    amount = float(request.form.get('amount', 0))
    if amount > 0:
        current_user.balance += amount
        db.session.commit()
        flash(f'{amount}€ ajoutés à votre solde!', 'success')
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
        'message': f'Quête complétée! Vous avez gagné {reward:.2f}€',
        'new_balance': current_user.balance,
        'completed_today': current_user.get_completed_quests_today()
    })

@app.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    amount = float(request.form.get('amount', 0))
    if amount > 0 and amount <= current_user.balance:
        current_user.balance -= amount
        db.session.commit()
        flash(f'Retrait de {amount}€ effectué!', 'success')
    else:
        flash('Montant invalide ou solde insuffisant.', 'error')
    return redirect(url_for('dashboard'))

@app.route('/history')
@login_required
def history():
    completions = QuestCompletion.query.filter_by(user_id=current_user.id).order_by(QuestCompletion.completed_at.desc()).all()
    return render_template('history.html', completions=completions)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
