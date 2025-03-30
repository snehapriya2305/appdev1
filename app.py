from flask import Flask, render_template, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime 
from flask import request,flash,redirect
from flask_login import login_required

app=Flask(__name__)
app.secret_key = 'supersecretkey123!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.db'
db = SQLAlchemy(app)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    qualification = db.Column(db.String(120))
    dob = db.Column(db.Date)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    date_of_quiz = db.Column(db.Date, nullable=False)
    time_duration = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.Text)
    # Relationship with Chapter
    chapter = db.relationship('Chapter', backref=db.backref('quizzes', lazy=True))

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_statement = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(120), nullable=False)
    option2 = db.Column(db.String(120), nullable=False)
    option3 = db.Column(db.String(120), nullable=False)
    option4 = db.Column(db.String(120), nullable=False)
    correct_option = db.Column(db.String(120), nullable=False)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_stamp_of_attempt = db.Column(db.DateTime, nullable=False, default=datetime.now)
    total_scored = db.Column(db.Integer, nullable=False)
    # Relationship with Quiz
    quiz = db.relationship('Quiz', backref=db.backref('scores', lazy=True))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        
        if user:
            session['user_id'] = user.id  # Store user_id in session
            session['full_name'] = user.full_name
            subjects = Subject.query.all()  # Fetch all subjects
            return render_template('user_dashboard.html', user=user, subjects=subjects)
        else:
            flash('Invalid credentials. Please try again.', 'error')
            return render_template('index.html')
    
    return render_template('index.html')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('fullname')
        qualification = request.form.get('qualification')
        dob_str = request.form.get('dob')

        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
            return redirect(url_for('register'))


        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different username.', 'error')
            return redirect(url_for('register'))


        new_user = User(
            username=username,
            password=password,  
            full_name=full_name,
            qualification=qualification,
            dob=dob
        )


        db.session.add(new_user)
        db.session.commit()


        flash('Registration successful!', 'success')


        return redirect(url_for('success'))


    return render_template('register.html')

@app.route('/success/')
def success():
    return render_template('success.html')

@app.route('/admin/login/', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_username = request.form.get('admin_username')
        admin_password = request.form.get('admin_password')

        if admin_username == 'snehapriya' and admin_password == 'priya':  
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard')) 
        else:
            flash('Invalid admin credentials. Please try again.', 'error')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

@app.route('/admin/dashboard/')
def admin_dashboard():
    subjects = Subject.query.all()
    return render_template('admin_dashboard.html', subjects=subjects)

@app.route('/admin/manage-users/')
def manage_users():
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    else:
        flash('User not found.', 'error')

    return redirect(url_for('manage_users'))

@app.route('/admin/manage_user_quiz/<int:user_id>', methods=['GET', 'POST'])
def manage_user_quiz(user_id):
    user = User.query.get_or_404(user_id)

    scores = (
        db.session.query(Score, Quiz, Chapter, db.func.count(Question.id).label("max_marks"))
        .join(Quiz, Score.quiz_id == Quiz.id)
        .join(Chapter, Quiz.chapter_id == Chapter.id)
        .join(Question, Quiz.id == Question.quiz_id) 
        .filter(Score.user_id == user_id)
        .group_by(Score.id, Quiz.id, Chapter.id)
        .all()
    )

    if request.method == 'POST':
        if 'delete_score' in request.form:
            score_id = request.form.get('delete_score')
            score_to_delete = Score.query.get(score_id)

            if score_to_delete:
                db.session.delete(score_to_delete)
                db.session.commit()
                flash("Score deleted successfully!", "success")
            else:
                flash("Score not found!", "danger")

        else:
            for score, quiz, chapter, max_marks in scores:
                new_score = request.form.get(f'score_{score.id}')

                if new_score is not None and new_score.isdigit():
                    new_score = int(new_score)
                    if 0 <= new_score <= max_marks:  # Ensure it's within valid range
                        score.total_scored = new_score
                    else:
                        flash(f"Score for {chapter.name} must be between 0 and {max_marks}.", "danger")

            db.session.commit()
            flash("Scores updated successfully!", "success")

        return redirect(url_for('manage_user_quiz', user_id=user_id))

    return render_template('manage_user_quiz.html', user=user, scores=scores)

@app.route('/admin/delete-subject/<int:subject_id>/', methods=['POST', 'GET'])
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)


    Chapter.query.filter_by(subject_id=subject_id).delete()
    db.session.delete(subject)
    db.session.commit()

    flash('Subject deleted successfully!', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-chapter/<int:chapter_id>/', methods=['POST', 'GET'])
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)

    db.session.delete(chapter)
    db.session.commit()

    flash('Chapter deleted successfully!', 'danger')
    return redirect(url_for('manage_subject', subject_id=chapter.subject_id))

@app.route('/admin/create-subject/', methods=['GET', 'POST'])
def create_subject():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        new_subject = Subject(name=name, description=description)
        db.session.add(new_subject)
        db.session.commit()

        flash('Subject created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('create_subject.html')

@app.route('/admin/edit-chapter/<int:chapter_id>/', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    # Fetch the chapter
    chapter = Chapter.query.get_or_404(chapter_id)

    if request.method == 'POST':
        # Get form data
        chapter.name = request.form.get('name')
        chapter.description = request.form.get('description')

        # Update database
        db.session.commit()

        flash('Chapter updated successfully!', 'success')
        return redirect(url_for('manage_chapter', chapter_id=chapter_id))

    return render_template('edit_chapter.html', chapter=chapter)

@app.route('/admin/manage-subject/<int:subject_id>/')
def manage_subject(subject_id):
    # Fetch the subject by ID
    subject = Subject.query.get_or_404(subject_id)

    # Fetch all chapters for this subject
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()

    return render_template('manage_subject.html', subject=subject, chapters=chapters)

@app.route('/admin/edit-subject/<int:subject_id>/', methods=['GET', 'POST'])
def edit_subject(subject_id):
    # Fetch the subject
    subject = Subject.query.get_or_404(subject_id)

    if request.method == 'POST':
        # Get form data
        subject.name = request.form.get('name')
        subject.description = request.form.get('description')

        # Update database
        db.session.commit()

        flash('Subject updated successfully!', 'success')
        return redirect(url_for('manage_subject', subject_id=subject_id))

    return render_template('edit_subject.html', subject=subject)

@app.route('/admin/create-chapter/<int:subject_id>/', methods=['GET', 'POST'])
def create_chapter(subject_id):
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description')

        # Insert into Chapter table
        new_chapter = Chapter(name=name, description=description, subject_id=subject_id)
        db.session.add(new_chapter)
        db.session.commit()

        flash('Chapter created successfully!', 'success')
        return redirect(url_for('manage_subject', subject_id=subject_id))

    return render_template('create_chapter.html', subject_id=subject_id)

@app.route('/admin/manage-chapter/<int:chapter_id>/')
def manage_chapter(chapter_id):
    # Fetch the chapter by ID
    chapter = Chapter.query.get_or_404(chapter_id)

    # Fetch all quizzes for this chapter
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()

    return render_template('manage_chapter.html', chapter=chapter, quizzes=quizzes)

@app.route('/admin/create-quiz/<int:chapter_id>/', methods=['GET', 'POST'])
def create_quiz(chapter_id):
    if request.method == 'POST':
        # Get form data
        date_of_quiz = request.form.get('date_of_quiz')
        time_duration = request.form.get('time_duration')
        remarks = request.form.get('remarks')
        #dob = datetime.strptime(dob_str, '%Y-%m-%d').date()

        # Insert into Quiz table
        date_of_quiz = datetime.strptime(date_of_quiz, '%Y-%m-%d').date()
        new_quiz = Quiz(
            chapter_id=chapter_id,
            date_of_quiz=date_of_quiz,
            time_duration=time_duration,
            remarks=remarks
        )
        db.session.add(new_quiz)
        db.session.commit()

        flash('Quiz created successfully!', 'success')
        return redirect(url_for('manage_chapter', chapter_id=chapter_id))

    return render_template('create_quiz.html', chapter_id=chapter_id)

@app.route('/admin/manage-quiz/<int:quiz_id>/')
def manage_quiz(quiz_id):
    # Fetch the quiz by ID
    quiz = Quiz.query.get_or_404(quiz_id)

    # Fetch all questions for this quiz
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    return render_template('manage_quiz.html', quiz=quiz, questions=questions)

@app.route('/admin/edit-question/<int:question_id>/', methods=['GET', 'POST'])
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    if request.method == 'POST':
        # Update question details
        question.question_statement = request.form.get('question_statement')
        question.option1 = request.form.get('option1')
        question.option2 = request.form.get('option2')
        question.option3 = request.form.get('option3')
        question.option4 = request.form.get('option4')
        question.correct_option = request.form.get('correct_option')
        db.session.commit()
        flash('Question updated successfully!', 'success')
        return redirect(url_for('manage_quiz', quiz_id=question.quiz_id))
    return render_template('edit_question.html', question=question)

@app.route('/admin/delete-question/<int:question_id>/')
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('manage_quiz', quiz_id=question.quiz_id))

@app.route('/admin/create-question/<int:quiz_id>/', methods=['GET', 'POST'])
def create_question(quiz_id):
    if request.method == 'POST':
        # Get form data
        question_statement = request.form.get('question')
        option1 = request.form.get('option_a')
        option2 = request.form.get('option_b')
        option3 = request.form.get('option_c')
        option4 = request.form.get('option_d')
        correct_option = request.form.get('correct_option')

        # Ensure required fields are provided
        if not question_statement or not option1 or not option2 or not option3 or not option4 or not correct_option:
            flash('All fields are required!', 'danger')
            return redirect(url_for('create_question', quiz_id=quiz_id))

        # Normalize correct_option to prevent whitespace issues
        correct_option = correct_option.strip()

        # Debugging Print Statement
        print(f"Saving Question: '{question_statement}', Correct Answer: '{correct_option}'")

        # Insert into database
        new_question = Question(
            quiz_id=quiz_id,
            question_statement=question_statement.strip(),
            option1=option1.strip(),
            option2=option2.strip(),
            option3=option3.strip(),
            option4=option4.strip(),
            correct_option=correct_option  # Ensuring trimmed correct_option
        )
        db.session.add(new_question)
        db.session.commit()

        flash('Question created successfully!', 'success')
        return redirect(url_for('manage_quiz', quiz_id=quiz_id))

    return render_template('create_question.html', quiz_id=quiz_id)

@app.route('/admin/delete-quiz/<int:quiz_id>/', methods=['POST', 'GET'])
def delete_quiz(quiz_id):
    # Fetch the quiz by ID
    quiz = Quiz.query.get_or_404(quiz_id)

    # Delete all associated questions first
    Question.query.filter_by(quiz_id=quiz_id).delete()

    # Delete the quiz itself
    db.session.delete(quiz)
    db.session.commit()

    flash('Quiz deleted successfully!', 'danger')
    return redirect(url_for('manage_chapter', chapter_id=quiz.chapter_id))

@app.route('/admin/edit-quiz/<int:quiz_id>/', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if request.method == 'POST':
        quiz.date_of_quiz = request.form['date_of_quiz']
        quiz.time_duration = request.form['time_duration']
        quiz.remarks = request.form['remarks']
        db.session.commit()
        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('manage_quiz', quiz_id=quiz.id))
    return render_template('edit_quiz.html', quiz=quiz)

"""@app.route('/dashboard')
def user_dashboard():
    subjects = Subject.query.all()  # Fetch all subjects
    return render_template('user_dashboard.html', subjects=subjects)"""

@app.route('/dashboard')
def user_dashboard():
    # Ensure user is logged in
    if 'user_id' not in session:
        return redirect(url_for('index'))  # Redirect to login if not logged in

    user = User.query.get(session['user_id'])  # Fetch user from the database
    if not user:
        return redirect(url_for('index'))  # If user not found, redirect to login

    subjects = Subject.query.all()  # Fetch all subjects

    return render_template('user_dashboard.html', subjects=subjects, user=user)

@app.route('/subject/<int:subject_id>/chapters')
def view_chapters(subject_id):
    subject = Subject.query.get_or_404(subject_id)  # Use get_or_404 for better error handling
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('chapters.html', subject=subject, chapters=chapters)

@app.route('/chapter/<int:chapter_id>')
def view_chapter_details(chapter_id):
    # Fetch the chapter and related quizzes
    chapter = Chapter.query.get_or_404(chapter_id)
    
    # Fetch quizzes for this chapter
    quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()

    # Fetch all questions associated with the quizzes in this chapter
    questions = Question.query.join(Quiz).filter(Quiz.chapter_id == chapter.id).all()

    return render_template('chapter_details.html', chapter=chapter, quizzes=quizzes, questions=questions)

@app.route('/user/scores/<int:user_id>')
def user_scores(user_id):
    # Ensure user is logged in
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('index'))

    # Check if the logged-in user is trying to access their own scores
    if session['user_id'] != user_id:
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for('user_dashboard'))

    # Fetch user scores with max marks (total questions per quiz)
    scores = (
        db.session.query(Score, Quiz, Chapter, db.func.count(Question.id).label("max_marks"))
        .join(Quiz, Score.quiz_id == Quiz.id)
        .join(Chapter, Quiz.chapter_id == Chapter.id)
        .join(Question, Quiz.id == Question.quiz_id)
        .filter(Score.user_id == user_id)
        .group_by(Score.id, Quiz.id, Chapter.id)
        .all()
    )

    return render_template('user_scores.html', scores=scores)

@app.route('/quiz/<int:quiz_id>')
def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Fetch questions for this quiz
    questions = Question.query.filter_by(quiz_id=quiz.id).all()

    return render_template('quiz.html', quiz=quiz, questions=questions)

@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    
    user_id = session.get('user_id')
    if not user_id:
        flash("User ID not found. Please log in again.", "danger")
        return redirect(url_for('index')) 

    total_questions = len(questions)
    correct_answers = 0

    for question in questions:
        user_answer = request.form.get(f'question_{question.id}', None)
        correct_option = str(question.correct_option).strip()  # A, B, C, or D

        # Map option letters to their statements
        options_map = {
            "A": question.option1,
            "B": question.option2,
            "C": question.option3,
            "D": question.option4
        }

        # Find the selected option letter based on user answer
        user_selected_letter = next(
            (letter for letter, statement in options_map.items() if statement.strip() == user_answer.strip()), None
        )

        # Check if the answer is correct
        if user_selected_letter == correct_option:
            correct_answers += 1

    # Save score in the database
    new_score = Score(
        quiz_id=quiz.id,
        user_id=user_id,
        time_stamp_of_attempt=datetime.now(),
        total_scored=correct_answers
    )

    db.session.add(new_score)
    db.session.commit()
    flash(f"Quiz Submitted! Your Score: {correct_answers}/{total_questions}", "success")

    return redirect(url_for('user_dashboard'))









if __name__ == '__main__':
    app.run(debug=True)