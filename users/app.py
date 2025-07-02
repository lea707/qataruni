from flask import Blueprint

bp = Blueprint('users', __name__, url_prefix='/users')

@bp.route('/')
def index():
    return 'Users page'