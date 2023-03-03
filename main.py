from app import flaskapp, db
from app.models import User, Post


@flaskapp.shell_context_processor
def make_shell():
    return ({'db': db, 'User': User, 'Post': Post})


flaskapp.run(host='0.0.0.0', port=81)
