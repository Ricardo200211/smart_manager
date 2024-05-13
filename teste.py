from flask import Flask, render_template_string, redirect, url_for, request
import connect_BD
import hash_parser
app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string(open('templates/login.html', encoding='utf-8').read())

@app.route('/login', methods=['POST'])
def login():
    user = request.form['user']
    passwd_original = request.form['password']
    passwd = hash_parser.parse_hash(passwd_original)
    conexao = connect_BD.conectar_mysql('localhost', 'root', 'roots', 'smartmanager')
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
if __name__ == '__main__':
    app.run(port=5000)