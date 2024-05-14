from datetime import datetime
from flask import Flask, request, render_template_string, redirect, url_for, jsonify
import connect_BD
import id_generator
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



@app.route('/obter-nome-recurso/<codigo_qr>')
def obter_nome_recurso1(codigo_qr):
    try:
        conexao = connect_BD.conectar_mysql()
        cursor = conexao.cursor()
        query = "SELECT nome FROM recurso WHERE id = %s"
        cursor.execute(query, (codigo_qr,))
        resultado = cursor.fetchone()
        cursor.close()
        conexao.close()
        if resultado:
            return jsonify(nome_recurso=resultado[0])
        else:
            return jsonify(erro="Recurso não encontrado"), 404
    except Exception as e:
        return jsonify(erro="Erro na conexão com a BD: " + str(e)), 500


@app.route('/qrcode')
def qrcode():
    return render_template_string(open('templates/qrcode.html', encoding='utf-8').read())


@app.route('/permissoes')
def permissoes():
    conexao = connect_BD.conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            query = "SELECT * FROM view_status_permissao_recurso WHERE id_funcionario = %s"
            cursor.execute(query, (id_utilizador,))
            permissoes = cursor.fetchall()
            permissoes_lista = [{'id_r': permissao[2],'nome_r': permissao[3], 'permissao': permissao[4], 'pedido': permissao[5]} for permissao in permissoes]
            return render_template_string(open('templates/permissoes.html', encoding='utf-8').read(), permissoes=permissoes_lista, nome=nome_utilizador)
        except Exception as e:
            return f"Erro ao buscar permissões: {e}"
        finally:
            conexao.close()
    else:
        return "Erro na conexão com a base de dados"


@app.route('/solicitar_permissao', methods=['POST'])
def solicitar_permissao():
    id_recurso = request.form['id_recurso']
    id_utilizador_atual = id_utilizador
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conexao = connect_BD.conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            query = "INSERT INTO pedidos_permissao (data, id_funcionario, id_recurso) VALUES (%s, %s, %s)"
            cursor.execute(query, (data_atual, id_utilizador_atual, id_recurso))
            conexao.commit()
            return redirect(url_for('permissoes'))
        except Exception as e:
            conexao.rollback()
            return f"Erro ao inserir pedido de permissão: {e}"
        finally:
            cursor.close()
            conexao.close()
    else:
        return "Erro na conexão com a base de dados."


@app.route('/funcionarios')
def funcionarios():
    conexao = connect_BD.conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            query = "SELECT * FROM view_funcionarios_cargos"
            cursor.execute(query)
            funcionarios = cursor.fetchall()
            funcionarios_lista = [
                {'id': funcionario[0], 'nome': funcionario[1], 'email': funcionario[2], 'cargo': funcionario[3], 'ativo': funcionario[5]} for funcionario in funcionarios]
            return render_template_string(open('templates/funcionarios.html', encoding='utf-8').read(), funcionarios=funcionarios_lista)
        except Exception as e:
            return f"Erro ao listar os funcionários: {e}"
        finally:
            cursor.close()
            conexao.close()
    else:
        return "Erro na conexão com a base de dados"


@app.route('/recursos')
def admin_recursos():
    conexao = connect_BD.conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            query = "SELECT * FROM recurso where is_active=1"
            cursor.execute(query)
            recursos = cursor.fetchall()
            recursos_lista = [
                {'id': recurso[0], 'nome': recurso[1], 'descricao': recurso[2]} for recurso in recursos]
            return render_template_string(open('templates/recursos.html', encoding='utf-8').read(), recursos=recursos_lista)

        except Exception as e:
            return f"Erro ao listar os recursos: {e}"
        finally:
            cursor.close()
            conexao.close()
    else:
        return "Erro na conexão com a base de dados"


@app.route('/u_recursos')
def admin_u_recursos():
    conexao = connect_BD.conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            query = "SELECT * FROM view_utilizacao_recursos"
            cursor.execute(query)
            u_recursos = cursor.fetchall()
            u_recursos_lista = [
                {'funcionario': u_recurso[1], 'recurso': u_recurso[2], 'data': u_recurso[0]} for u_recurso in u_recursos]
            return render_template_string(open('templates/utilizacao_recursos.html', encoding='utf-8').read(), u_recursos=u_recursos_lista)

        except Exception as e:
            return f"Erro ao listar as utilizações dos recursos: {e}"
        finally:
            cursor.close()
            conexao.close()
    else:
        return "Erro na conexão com a base de dados"

@app.route('/admin_permissoes')
def admin_permissoes():
    conexao = connect_BD.conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            query = "SELECT * FROM view_resumo_funcionarios"
            cursor.execute(query)
            funcionarios = cursor.fetchall()
            funcionarios_lista = [
                {'id': funcionario[0], 'nome': funcionario[1], 'permissoes': funcionario[2], 'pedidos': funcionario[3]} for funcionario in funcionarios]
            return render_template_string(open('templates/permissoes_admin.html', encoding='utf-8').read(), funcionarios=funcionarios_lista)

        except Exception as e:
            return f"Erro ao listar as permissões: {e}"
        finally:
            cursor.close()
            conexao.close()
    else:
        return "Erro na conexão com a base de dados"


@app.route('/permissoes_funcionario_admin')
def permissoes_funcionario_admin():
    funcionario_id = request.args.get('id')
    conexao = connect_BD.conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            query = "SELECT * FROM view_status_permissao_recurso WHERE id_funcionario = %s"
            cursor.execute(query, (funcionario_id,))
            permissoes = cursor.fetchall()
            permissoes_lista = [{'id_r': permissao[2],'nome_r': permissao[3], 'permissao': permissao[4], 'pedido': permissao[5]} for permissao in permissoes]
            return render_template_string(open('templates/permissoes_funcionario_admin.html', encoding='utf-8').read(), permissoes=permissoes_lista, nome=nome_utilizador, id=funcionario_id)
        except Exception as e:
            return f"Erro ao buscar permissões: {e}"
        finally:
            conexao.close()
    else:
        return "Erro na conexão com a base de dados"


@app.route('/abrir_criar_funcionario')
def abrir_criar_funcionario():
    return render_template_string(open('templates/criar_funcionario.html', encoding='utf-8').read())


@app.route('/criar_funcionario', methods=['POST'])
def criar_funcionario():
    nome = request.form['nome']
    email = request.form['email']
    cargo = request.form['cargo']
    tipo = request.form['tipo']
    generator = id_generator.EmployeeIDGenerator()
    id = generator.generate_id(nome)
    passwd_default = "12345"
    passwd = hash_parser.parse_hash(passwd_default)
    try:
        conexao = connect_BD.conectar_mysql()
        cursor = conexao.cursor()
        query = "INSERT INTO funcionario(id, nome, email, pass) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (id, nome, email, passwd))
        if tipo == 'funcionario':
            query = "INSERT INTO fun_utilizador_recursos (cargo, id_funcionario) VALUES (%s, %s)"
            cursor.execute(query, (cargo, id))
        if tipo == 'admin':
            query = "INSERT INTO administrador (id_funcionario) VALUES (%s)"
            cursor.execute(query, (id,))
        conexao.commit()
        return redirect(url_for('funcionarios'))
    except Exception as e:
        print(e)
        return "Erro ao conectar com a base de dados"
    finally:
        conexao.close()


@app.route('/abrir_criar_recurso')
def abrir_criar_recurso():
    return render_template_string(open('templates/criar_recurso.html', encoding='utf-8').read())


@app.route('/criar_recurso', methods=['POST'])
def criar_recurso():
    nome = request.form['nome']
    desc = request.form['desc']
    generator = id_generator.ResourceIDGenerator()
    id = generator.generate_resource_id(nome)
    try:
        conexao = connect_BD.conectar_mysql()
        cursor = conexao.cursor()
        query = "INSERT INTO recurso(id, nome, descricao) VALUES (%s, %s, %s)"
        cursor.execute(query, (id, nome, desc))
        conexao.commit()
        return redirect(url_for('admin_recursos'))
    except Exception as e:
        print(e)
        return "Erro ao conectar com a base de dados"
    finally:
        conexao.close()


@app.route('/retirar_permissao', methods=['POST'])
def retirar_permissao():
    id_recurso = request.form['id_recurso']
    id_funcionario = request.form['id_funcionario']
    conexao = connect_BD.conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute("delete from permissao where id_recurso = %s and id_funcionario = %s", (id_recurso, id_funcionario))
            conexao.commit()
            return redirect('/permissoes_funcionario_admin?id=' + id_funcionario)
        finally:
            conexao.close()

@app.route('/adicionar_permissao', methods=['POST'])
def adicionar_permissao():
    id_recurso = request.form['id_recurso']
    id_funcionario = request.form['id_funcionario']
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conexao = connect_BD.conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            cursor.execute("insert into permissao (data, id_funcionario, id_administrador, id_recurso) "
                           "values (%s, %s, %s, %s)", (data_atual, id_funcionario, id_admin, id_recurso))
            conexao.commit()
            return redirect('/permissoes_funcionario_admin?id=' + id_funcionario)
        finally:
            conexao.close()


@app.route('/aceitar_permissao', methods=['POST'])
def aceitar_permissao():
    id_recurso = request.form['id_recurso']
    id_funcionario = request.form['id_funcionario']
    action = request.form['action']
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conexao = connect_BD.conectar_mysql()
    if conexao:
        try:
            if action == '1':
                cursor = conexao.cursor()
                cursor.execute("update pedidos_permissao set resposta = %s,"
                               " id_administrador = %s, data_resposta = %s "
                               "where id_funcionario = %s and id_recurso = %s",
                               (action, id_admin, data_atual, id_funcionario, id_recurso))
                cursor2 = conexao.cursor()
                cursor2.execute("insert into permissao (data, id_funcionario, id_administrador, id_recurso) "
                               "values (%s, %s, %s, %s)", (data_atual, id_funcionario, id_admin, id_recurso))
            else:
                cursor = conexao.cursor()
                cursor.execute("update pedidos_permissao set resposta = %s,"
                               " id_administrador = %s, data_resposta = %s "
                               "where id_funcionario = %s and id_recurso = %s",
                               (action, id_admin, data_atual, id_funcionario, id_recurso))
            conexao.commit()
            return redirect('/permissoes_funcionario_admin?id=' + id_funcionario)
        except Exception:
            return "Erro ao conectar com a base de dados"
        finally:
            conexao.close()


@app.route('/alterar_funcionario')
def alterar_funcionario():
    funcionario_id = request.args.get('id')
    conexao = connect_BD.conectar_mysql()
    try:
        with conexao.cursor(dictionary=True) as cursor:
            query = "SELECT * FROM view_funcionarios_cargos WHERE funcionario_id = %s"
            cursor.execute(query, (funcionario_id,))
            funcionario = cursor.fetchone()
            if funcionario:
                return render_template_string(open('templates/alterar_funcionario.html', encoding='utf-8').read(), funcionario=funcionario)
    except Exception as e:
        return "Erro ao conectar com a base de dados"
    finally:
        conexao.close()


@app.route('/alterar_funcionario_bd',  methods=['POST'])
def alterar_funcionario_bd():
    id = request.form.get('id')
    email = request.form.get('email')
    nome = request.form.get('nome')
    cargo = request.form.get('cargo')
    status = request.form.get('status')
    conexao = connect_BD.conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            query = "update funcionario set " \
                    "nome = %s, " \
                    "email = %s, " \
                    "is_active = %s " \
                    "where id = %s"
            cursor.execute(query, (nome, email, status, id))
            conexao.commit()
            query = "update fun_utilizador_recursos set " \
                    "cargo = %s " \
                    "where id_funcionario = %s"
            cursor.execute(query, (cargo, id))
            conexao.commit()
            return redirect(url_for("funcionarios"))
        except Exception as e:
            print(e)
            return "Erro ao conectar com a base de dados"
        finally:
            conexao.close()



if __name__ == '__main__':
    app.run(port=5000)