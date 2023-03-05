from app import flaskapp, db

@flaskapp.errorhandler(404)
def error_404(error):
    return "404 error - it means that you are trying to load a page which doesn't exist. Maybe go to the homepage and try to find what you are looking for from there?", 404

@flaskapp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return "Internal server error! That means, we did something wrong on our side and you were successful in making it happen! Could you send an email to <a href='aman@denselayers.com'>aman@denselayers.com</a> and describe what you were trying to do? That would be very helpful!", 500