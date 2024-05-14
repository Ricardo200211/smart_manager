import smtplib
import dns.resolver
import socket

def get_mx_records(domain):
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        return [record.exchange.to_text() for record in mx_records]
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout, dns.resolver.NoNameservers):
        return []

def is_real_email(email):
    domain = email.split('@')[-1]
    mx_records = get_mx_records(domain)

    if not mx_records:
        return False

    for mx in mx_records:
        try:
            server = smtplib.SMTP(mx)
            server.set_debuglevel(0)
            server.helo(socket.gethostname())
            server.mail('test@example.com')
            code, message = server.rcpt(email)
            server.quit()
            if code == 250:
                return True
        except Exception as e:
            print(f"Erro ao verificar email {email} no servidor {mx}: {e}")
            continue

    return False

