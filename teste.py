from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string(open('templates/login.html', encoding='utf-8').read())

if __name__ == '__main__':
    app.run(port=5000)