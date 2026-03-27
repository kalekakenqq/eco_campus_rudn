
from flask import Flask, render_template

app = Flask(__name__)

# три проекта для портфолио
projects = [
    {'name': 'Проект 1', 'desc': 'Веб-приложение на Flask'},
    {'name': 'Проект 2', 'desc': 'Телеграм-бот на Python'},
    {'name': 'Проект 3', 'desc': 'REST API для заметок'},
]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html', projects=projects)


if __name__ == '__main__':
    app.run(debug=True)
