import datetime
import random
import string
import hash_parser
import connect_BD


def get_last_index(tipo):
    conexao = connect_BD.conectar_mysql()
    if conexao:
        try:
            cursor = conexao.cursor()
            query = f"SELECT id FROM {tipo} ORDER BY id DESC LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            if result:
                last_id = result[0]
                last_index = int(last_id[-4:])
                return last_index
            else:
                return 0
        except Exception as e:
            print(e)
            conexao.rollback()
            return "Erro na conexão com a base de dados"
        finally:
            conexao.close()
    else:
        return "Erro na conexão com a base de dados."


class EmployeeIDGenerator:
    def __init__(self, start_index=0):
        self.index = get_last_index('funcionario')

    def increment_index(self):
        self.index += 1
        return self.index

    def generate_id(self, name):
        year_suffix = datetime.datetime.now().year % 100
        name_prefix = name[:3].lower()
        increment = f"{self.increment_index():04d}"
        employee_id = f"F{name_prefix}{year_suffix}{increment}"
        return employee_id


class ResourceIDGenerator:
    def __init__(self):
        pass

    def generate_random_sequence(self):
        letters = ''.join(random.choices(string.ascii_lowercase, k=2))
        numbers = ''.join(random.choices(string.digits, k=2))
        result = letters + numbers
        return result

    def generate_short_hash(self, name):
        hash = hash_parser.parse_hash(name)
        short_hash_hex = hash[:6]
        return short_hash_hex

    def generate_resource_id(self, name):
        name_prefix = name[:3].lower()
        hash_part = self.generate_short_hash(name)
        random_sequence = self.generate_random_sequence()
        resource_id = f"R{name_prefix}{hash_part}{random_sequence}"
        return resource_id

