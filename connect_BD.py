import mysql.connector
from mysql.connector import Error

def conectar_mysql():
    try:
        conexao = mysql.connector.connect(
            host="smartmanager.mysql.database.azure.com",
            user="ricardo",
            password="Martins16",
            database="smartmanager"
        )
        if conexao.is_connected():
            cursor = conexao.cursor()
            cursor.execute("select database();")
            cursor.fetchone()
            return conexao
    except Error as e:
        return None
