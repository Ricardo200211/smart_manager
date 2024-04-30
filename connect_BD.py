import mysql.connector
from mysql.connector import Error

def conectar_mysql(servidor, user, password, bd):
    try:
        conexao = mysql.connector.connect(
            host=servidor,
            user=user,
            password=password,
            database=bd
        )
        if conexao.is_connected():
            cursor = conexao.cursor()
            cursor.execute("select database();")
            cursor.fetchone()
            return conexao
    except Error as e:
        return None