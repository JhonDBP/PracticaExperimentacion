from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import random

app = Flask(__name__)
app.secret_key = 'trivia-secret'

# Config DB
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flasktrivia'
mysql = MySQL(app)

@app.route('/', methods=['GET', 'POST'])
def welcome():
    if request.method == 'POST':
        player_name = request.form['player_name']
        session['player_name'] = player_name
        session['score'] = 0
        session['question_ids'] = []
        return redirect(url_for('next_question'))
    return render_template('welcome.html')

@app.route('/question')
def next_question():
    if 'question_ids' not in session:
        session['question_ids'] = []

    cur = mysql.connection.cursor()
    cur.execute('SELECT id FROM questions')
    all_ids = [row[0] for row in cur.fetchall()]
    available_ids = list(set(all_ids) - set(session.get('question_ids', [])))

    if not available_ids:
        return render_template('finished.html', score=session['score'])

    question_id = random.choice(available_ids)
    session['question_ids'].append(question_id)
    session.modified = True  # << Para asegurar que la sesión se actualiza correctamente

    cur.execute('SELECT * FROM questions WHERE id = %s', (question_id,))
    question = cur.fetchone()
    cur.execute('SELECT * FROM questions')
    all_questions = cur.fetchall()

    return render_template('question.html', question=question, all_questions=all_questions)



@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        question = request.form['question']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_option = request.form['correct']

        cur = mysql.connection.cursor()
        cur.execute('''
            INSERT INTO questions (question, option_a, option_b, option_c, option_d, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (question, option_a, option_b, option_c, option_d, correct_option))
        mysql.connection.commit()
        flash('Pregunta agregada correctamente')
        return redirect(url_for('manage_questions'))

    return render_template('add_question.html')

@app.route('/feedback/<int:question_id>', methods=['POST'])
def feedback(question_id):
    selected = request.form['answer']
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM questions WHERE id = %s', (question_id,))
    question = cur.fetchone()

    correct_option = question[6]
    is_correct = (selected == correct_option)

    if is_correct:
        session['score'] += 1

    return render_template('feedback.html', question=question, selected=selected, is_correct=is_correct)

@app.route('/manage_questions')
def manage_questions():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM questions')
    questions = cur.fetchall()
    return render_template('manage_questions.html', questions=questions)

@app.route('/delete_question/<int:question_id>')
def delete_question(question_id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM questions WHERE id = %s', (question_id,))
    mysql.connection.commit()
    flash('Pregunta eliminada')
    return redirect(url_for('manage_questions'))

@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        question = request.form['question']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_option = request.form['correct']

        cur.execute('''
            UPDATE questions SET question=%s, option_a=%s, option_b=%s, option_c=%s, option_d=%s, correct_option=%s
            WHERE id = %s
        ''', (question, option_a, option_b, option_c, option_d, correct_option, question_id))
        mysql.connection.commit()
        flash('Pregunta actualizada')
        return redirect(url_for('manage_questions'))

    cur.execute('SELECT * FROM questions WHERE id = %s', (question_id,))
    question = cur.fetchone()
    return render_template('edit_question.html', question=question)

if __name__ == '__main__':
    app.run(port=3000, debug=True)
