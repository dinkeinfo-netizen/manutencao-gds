from flask_login import current_user
from functools import wraps
from flask import abort

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def converter_para_boolean(valor):
    """
    Converte string para boolean de forma segura
    """
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        valor_lower = valor.lower().strip()
        return valor_lower in ['sim', 'yes', 'true', '1', 'on', 'ok']
    return bool(valor)
