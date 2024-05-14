from datetime import datetime
from flask import Flask, request, render_template_string, redirect, url_for
import connect_BD
import hash_parser


app = Flask(__name__)
id_utilizador = ""
nome_utilizador = ""
id_admin = 0
id_funcionario = 0

@app.route('/')
def index():
    return render_template_string(open('templates/login.html', encoding='utf-8').read())

@app.route('/login', methods=['POST'])
def login():
    user = request.form['user']
    passwd_original = request.form['password']
    passwd = hash_parser.parse_hash(passwd_original)
    conexao = connect_BD.conectar_mysql()
    if conexao:
        try:
            with conexao.cursor() as cursor:
                cursor.execute("SELECT * FROM funcionario WHERE (ID = %s or email = %s) and pass = %s and is_active = 1", (user, user, passwd))
                resultado = cursor.fetchone()
                if resultado:
                    global id_utilizador
                    id_utilizador = resultado[0]
                    global nome_utilizador
                    nome_utilizador = resultado[1]

                    cursor.execute("SELECT * FROM administrador WHERE id_funcionario = %s", (id_utilizador,))
                    resultado2 = cursor.fetchone()
                    if resultado2:
                        global id_admin
                        id_admin = resultado2[0]
                        return redirect(url_for("admin"))
                    else:
                        global id_funcionario
                        id_funcionario = resultado[0]
                        return redirect(url_for("home"))
                else:
                    mensagem_erro = "Utilizador ou password incorretos"
                    return render_template_string(open('templates/login.html', encoding='utf-8').read(), user = user, mensagem_erro=mensagem_erro)
        except Exception as e:
            mensagem_erro = f"Erro na execução da consulta: {e}"
            return render_template_string(open('templates/login.html', encoding='utf-8').read(), mensagem_erro=mensagem_erro)
        finally:
            conexao.close()
    else:
        mensagem_erro = "Erro na conexão com a base de dados"
        return render_template_string(open('templates/login.html', encoding='utf-8').read(), mensagem_erro=mensagem_erro)


@app.route('/main.html')
def home():
    return render_template_string(open('templates/main.html', encoding='utf-8').read(), nome = nome_utilizador)

@app.route('/admin.html')
def admin():
    return render_template_string(open('templates/admin.html', encoding='utf-8').read(), nome = nome_utilizador)


@app.route('/btn_qrcode', methods=['GET', 'POST'])
def btn_qrcode():
    if request.method == 'POST':
        return redirect('/qrcode')
    return render_template_string(open('templates/main.html', encoding='utf-8').read())


@app.route('/inserir_recurso', methods=['POST'])
def inserir_recurso():
    qr_code_result = request.form['qr_code_result']
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conexao = connect_BD.conectar_mysql()
    if conexao:
        cursor = conexao.cursor()
        query = "INSERT INTO utilizacao_recurso(data, id_fun_utilizador_recursos, id_recurso) VALUES (%s, %s, %s)"
        valores = (data, id_utilizador, qr_code_result)
        try:
            cursor.execute(query, valores)
            conexao.commit()
            return redirect(url_for('home'))
        except Exception as e:
            conexao.rollback()
            print(e)
            return "Erro ao inserir reserva na base de dados."
        finally:
            cursor.close()
            conexao.close()
    else:
        return "Erro na conexão com a base de dados."


