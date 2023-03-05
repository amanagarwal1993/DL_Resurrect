@flaskapp.route('/extinguish', methods=['GET', 'POST'])
@login_required
def extinguish():
    if request.method=="POST" and current_user.admin_privilege:
        if (request.form['password'] == "confirming"):
            Paper.query.delete()
            User.query.delete()
            Fragment.query.delete()
            Post.query.delete()
            db.session.commit()
            flash("All data deleted.")
            return redirect(url_for('index'))
        else:
            flash("Fault")
            return redirect(url_for('extinguish'))
    return render_template('danger.html')
