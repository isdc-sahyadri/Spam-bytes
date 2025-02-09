from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    user_type = db.Column(db.String(10), nullable=False)  # 'employer' or 'jobseeker'

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    employer = db.relationship('User', backref='jobs')

# Initialize Database
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def home():
    jobs = Job.query.all()
    return render_template('home.html', jobs=jobs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user_type = request.form['user_type']

        if not username or not password or user_type not in ['employer', 'jobseeker']:
            return "Invalid input", 400

        # Check if the username already exists
        if User.query.filter_by(username=username).first():
            return "Username already exists", 400

        user = User(username=username, password=password, user_type=user_type)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_type'] = user.user_type
            return redirect(url_for('home'))
        return "Invalid username or password", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect(url_for('login'))

    # Check if the employer exists before posting the job
    employer = User.query.get(session['user_id'])
    if not employer:
        return "Invalid employer", 400

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']

        if not title or not description:
            return "Title and description required", 400

        job = Job(title=title, description=description, employer_id=session['user_id'])
        db.session.add(job)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('post_job.html')

if __name__ == '__main__':
    app.run(debug=True)
