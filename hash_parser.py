import hashlib

def parse_hash(passwd):
    hash_obj = hashlib.sha256(passwd.encode())
    return hash_obj.hexdigest()


