from app import flaskapp, db
from app.models import User, Paper


@flaskapp.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Paper': Paper}


flaskapp.run(host='0.0.0.0', port=81)