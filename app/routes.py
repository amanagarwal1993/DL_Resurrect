from flask import render_template, flash, redirect, url_for, request
from flask import jsonify, send_from_directory, abort
from app import flaskapp, db
from app.forms import LoginForm, SignupForm, EditProfileForm, NewPostForm, PasswordResetForm, ChangePasswordForm, EditPostForm, CommentForm, NewPaperForm, EditPaperForm, FragmentsForm, DeleteUserForm, SuspendUserForm, InviteForm
from app.email import send_password_reset_email, send_moderation_email, send_invitation_email, invite_friend_email
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Invitation, Post, Paper, Fragment, Visits
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask_babel import _
import inspect
from sqlalchemy import text, or_
import logging
import boto3
from botocore.exceptions import ClientError


@flaskapp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        if current_user.spammy > 5:
            flash(
                "Your account has been suspended, so you cannot make any changes to the website. Contact elisa@denselayers.com for help."
            )
            return redirect(url_for('index'))
    pass


@flaskapp.route('/about')
def about_page():
    return render_template('about_page.html', title="About")


@flaskapp.route('/rules')
def rules_page():
    return render_template('rules_page.html', title="Rules")


@flaskapp.route('/')
@flaskapp.route('/index')
def index():
    page = request.args.get('page', 1, type=int)

    papers = Paper.query.with_entities(
        Paper.title, Paper.id, Paper.publish_month, Paper.publish_year,
        Paper.img_url(Paper)).filter(
            Paper.published, Paper.fragments).order_by(
                Paper.publish_year.desc(),
                Paper.publish_month.desc()).distinct().paginate(
                    page=page,
                    per_page=flaskapp.config['POSTS_PER_PAGE'],
                    error_out=False)

    next_page_url = url_for('index',
                            page=papers.next_num) if papers.has_next else None
    prev_page_url = url_for('index',
                            page=papers.prev_num) if papers.has_prev else None

    return render_template('index.html',
                           title='Home',
                           papers=papers.items,
                           next_page_url=next_page_url,
                           prev_page_url=prev_page_url)


@flaskapp.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in.')
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next_page')
        flash('Welcome {}!'.format(user.name))
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')

        # Store new visit from user
        visit = Visits(user_id=current_user.id)
        db.session.add(visit)
        db.session.commit()
        return redirect(next_page)
    return render_template('login.html', title='Sign in', form=form)


@flaskapp.route('/signup', methods=['POST', 'GET'])
def signup():
    if current_user.is_authenticated:
        flash('Already logged in!')
        return redirect(url_for('index'))
    form = SignupForm()
    if form.validate_on_submit():
        invite = Invitation.query.filter_by(email=form.email.data).first()
        if (invite is not None or form.email.data == "aman@denselayers.com"):
            user = User.query.filter_by(email=form.email.data).first()
            if user is not None:
                flash(
                    "This email (%s) already has a DenseLayers account! You can log in directly."
                    % form.email.data)
                return redirect(url_for('login'))
            user = User(name=form.name.data, email=form.email.data)
            user.set_password(form.password.data)
            if (form.email.data == "aman@denselayers.com"):
                user.admin_privilege = 1
            else:
                invite.accepted = 1
            db.session.add(user)
            db.session.commit()
            flash('Account created! Welcome to the community.')
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash(
                "Sorry, at the moment we need you to have an invitation to join, to begin contributing your own posts. But you can still freely read papers and other people's posts on the website!"
            )
            flash(
                "If you would like to join, please get an invitation by sending a short email to aman@denselayers.com with just a few words and we would love to welcome you to our community."
            )
    return render_template('signup.html', title='Sign Up', form=form)


@flaskapp.route('/logout')
def logout():
    logout_user()
    flash('Logged out successfully')
    return redirect(url_for('login'))


# For initial "forgot password" link


@flaskapp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        flash('You must log out to reset your password.')
        return redirect(url_for('index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
            flash('Check your email for instructions to reset password')
            return redirect(url_for('login'))
        else:
            flash('This email does not exist in our database.')
            return redirect(url_for('reset_password'))
    return render_template('resetpwd.html', form=form, title="Reset Password")


# After clicking the password reset link in email


@flaskapp.route('/new_password/<token>', methods=['GET', 'POST'])
def new_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset')
        return redirect(url_for('login'))
    return render_template('new_password.html',
                           form=form,
                           title="New Password")


@flaskapp.route('/paper/<paper_id>', methods=['POST', 'GET'])
def full_paper(paper_id):
    if not paper_id.isdigit():
        flash("Woops.")
        abort(404)
        return redirect
    paper = Paper.query.filter_by(id=paper_id).first_or_404()

    form = NewPostForm()

    if (request.method == "GET"):
        if current_user.is_authenticated:
            visit = Visits(visitor=current_user)
            paper.views += 1
            db.session.add(visit)
            db.session.commit()
        if (paper.published):
            if (request.args.get('first_fragment')):
                return render_template('full_paper.html',
                                       paper=paper,
                                       form=form,
                                       first_fragment=int(
                                           request.args.get('first_fragment')))
            return render_template('full_paper.html',
                                   paper=paper,
                                   form=form,
                                   title=paper.title)
        else:
            if (current_user.is_authenticated
                    and current_user.admin_privilege):
                flash("This paper is closed off but you can view it.")
                return render_template('full_paper.html',
                                       paper=paper,
                                       form=form,
                                       title=paper.title)
            else:
                flash("Sorry, this paper is not yet available.")
        return redirect(url_for('index'))

    if (request.method == "POST"):
        if (form.validate_on_submit()):
            if current_user.is_authenticated:
                # Check if this is spammy or not
                timediff = datetime.utcnow() - current_user.last_post_time
                ### CORRECT THIS
                if (timediff.seconds > 30):
                    fragment = Fragment.query.filter_by(
                        id=form.fragment_id.data).first()

                    newpost = Post(body=form.content.data,
                                   author=current_user,
                                   fragment=fragment,
                                   timestamp_latest=datetime.utcnow())

                    current_user.last_post_time = datetime.utcnow()
                    db.session.add(newpost)
                    db.session.commit()

                    print("User ", current_user.id, " posted!")

                    form.content.data = ""
                    first_fragment = form.fragment_id.data
                    return redirect(
                        url_for('full_paper',
                                paper_id=paper_id,
                                first_fragment=first_fragment))
                    #return render_template('full_paper.html', paper=paper, form=form, first_fragment=first_fragment)
                else:
                    print("Not posting for user ", current_user.id)
                    current_user.spammy += 1
                    current_user.last_post_time = datetime.utcnow()
                    db.session.commit()
                    flash(
                        'You posted too quickly, slow down and wait a minute before you try to post again.'
                    )
                    return render_template('full_paper.html',
                                           paper=paper,
                                           form=form,
                                           title=paper.title)
            else:
                flash('You need to log in first!')
                return redirect(url_for('login'),
                                next_page=url_for('full_paper', paper_id))
        else:
            flash(
                "Something went wrong. Try again and if it doesn't work, please email elisa@denselayers.com"
            )
            return render_template('full_paper.html', paper=paper, form=form)
    return render_template('full_paper.html',
                           paper=paper,
                           form=form,
                           title=paper.title)


def upload_file(data, file_name, folder_name, bucket):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    s3 = boto3.resource('s3')
    try:
        file_name = folder_name + '/' + file_name
        s3.Bucket(bucket).put_object(Key=file_name,
                                     Body=data,
                                     ACL='public-read')
    except ClientError as e:
        logging.error(e)
        return False
    return True


def upload_paper(paper_file, image_file, folder, bucket='closed-papers'):
    paper_uploaded = upload_file(paper_file.read(),
                                 secure_filename(paper_file.filename), folder,
                                 bucket)
    image_uploaded = upload_file(image_file.read(),
                                 secure_filename(image_file.filename), folder,
                                 bucket)
    if (paper_uploaded and image_uploaded):
        return True
    return False


@flaskapp.route('/paper/new', methods=['GET', 'POST'])
@login_required
def new_paper():
    """
    1. New form on website
    2. Returns database upon posting
    """
    if current_user.admin_privilege:
        form = NewPaperForm()

        if form.validate_on_submit():
            print("New paper form validated.")
            paper_file = form.paper_file.data
            img_file = form.img_file.data
            if (upload_paper(paper_file, img_file, form.shorthand.data)):
                print("Files were able to upload.")
                paper = Paper(title=form.title.data,
                              filename=secure_filename(paper_file.filename),
                              folder=form.shorthand.data,
                              journal=form.journal.data,
                              scholar_link=form.scholar_link.data,
                              author_string=form.author_string.data,
                              img_file=secure_filename(img_file.filename),
                              publish_month=form.publish_month.data,
                              publish_year=form.publish_year.data)
                db.session.add(paper)
                db.session.commit()
                print("Created new paper.")
                return redirect(url_for('upload_fragments', paper_id=paper.id))
            flash("Something went wrong. Could not store files.")
            return redirect(url_for('new_paper'))
        else:
            print("Form is not validating.")
        return render_template('new_paper_form.html',
                               form=form,
                               title="New Paper")
    else:
        flash("You are not authorized to access this page.")
    return redirect(url_for('index'))


@flaskapp.route('/edit_paper/<paper_id>', methods=['POST', 'GET'])
@login_required
def edit_paper(paper_id):
    if not paper_id.isdigit():
        abort(404)
    if current_user.admin_privilege:
        paper = Paper.query.filter_by(id=paper_id).first_or_404()
        if paper:
            form = EditPaperForm()
            if form.validate_on_submit():
                if (form.delete.data):
                    fragments = Fragment.query.filter_by(
                        paper_id=paper_id).all()
                    for fragment in fragments:
                        db.session.delete(fragment)
                    db.session.delete(paper)
                    db.session.commit()
                    return redirect(url_for('index'))
                else:
                    paper.title = form.title.data
                    paper.folder = form.shorthand.data
                    paper.journal = form.journal.data
                    paper.scholar_link = form.scholar_link.data
                    paper.author_string = form.author_string.data
                    paper.publish_month = form.publish_month.data
                    paper.publish_year = form.publish_year.data
                    db.session.commit()
                    flash('Paper updated!')
                    return redirect(url_for('full_paper', paper_id=paper_id))
            if request.method == "POST":
                flash('Error submitting form.')
            form.title.data = paper.title
            form.shorthand.data = paper.folder
            form.journal.data = paper.journal
            form.scholar_link.data = paper.scholar_link
            form.author_string.data = paper.author_string
            form.publish_month.data = paper.publish_month
            form.publish_year.data = paper.publish_year
            return render_template('edit_paper.html',
                                   title='Edit Paper',
                                   form=form,
                                   paper_id=paper_id)
        else:
            flash("No such paper.")
            return redirect(url_for('index'))
    else:
        flash("You are not authorized to access this page.")
    return redirect(url_for('index'))


@flaskapp.route('/user/<user_id>')
@login_required
def user(user_id):
    if not user_id.isdigit():
        abort(404)
    user = User.query.filter_by(id=user_id).first_or_404()
    return render_template('user.html', user=user, title=user.name)


@flaskapp.route('/edit_profile', methods=['POST', 'GET'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.name)
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Profile updated!')
        return redirect(url_for('user', user_id=current_user.id))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.about_me.data = current_user.about_me
    return render_template('editprofile.html', title='Edit Profile', form=form)


@flaskapp.route('/suspend/<user_id>', methods=['GET', 'POST'])
@login_required
def suspend_user(user_id):
    if not user_id.isdigit():
        abort(404)
    if (current_user.admin_privilege):
        form = SuspendUserForm()
        user = User.query.filter_by(id=user_id).first_or_404()
        if form.validate_on_submit():
            if (user.flagged):
                user.flagged = 0
                db.session.commit()
                flash('The user has been unsuspended.')
            else:
                user.flagged = 1
                db.session.commit()
                flash("This user has been suspended.")
            return redirect(url_for('user', user_id=user_id))
        if request.method == 'GET':
            return render_template('ban_user.html',
                                   form=form,
                                   user_id=user_id,
                                   flagged=user.flagged,
                                   title="Ban User")
    else:
        flash("You are NOT authorized to access this page.")
    return redirect(url_for('index'))


@flaskapp.route('/deletemyaccount', methods=['POST', 'GET'])
@login_required
def deletemyaccount():
    form = DeleteUserForm()
    if form.validate_on_submit():
        if current_user.check_password(form.password.data):
            db.session.delete(current_user)
            db.session.commit()
        flash('Your account and all its history was successfully deleted.')
    elif request.method == 'GET':
        return render_template('delete_user.html',
                               title='Delete Account',
                               form=form)
    return redirect(url_for('index'))


@flaskapp.route('/invite', methods=['POST', 'GET'])
@login_required
def invite_friend():
    form = InviteForm()

    if (request.method == 'GET'):
        return render_template('invite_friend.html',
                               form=form,
                               title="Invite Friend")

    if form.validate_on_submit():
        check_invite = Invitation.query.filter_by(
            email=form.email.data).first()
        if (check_invite is None):
            new_invite = Invitation(email=form.email.data)
            db.session.add(new_invite)
            db.session.commit()
            invite_friend_email(new_invite, current_user.name)
            flash("Invite sent!")
        else:
            flash("This person has already been invited. Re-sent an email.")
            invite_friend_email(check_invite, current_user.name)
        return redirect(url_for('invite_friend'))


@flaskapp.route('/editform/u/<user_id>/p/<post_id>', methods=['POST', 'GET'])
@login_required
def editform(user_id, post_id):
    if not (post_id.isdigit() and user_id.isdigit()):
        abort(404)
    post = Post.query.filter_by(id=post_id).first()
    paper_id = post.fragment.paper.id
    if not (current_user.id == int(user_id) or current_user.admin_privilege):
        flash("You can't edit someone else's post!")
        return redirect(url_for('full_paper', paper_id=paper_id))

    editform = EditPostForm()

    if request.method == "GET":
        editform.content.data = post.body
        return render_template('editform.html',
                               form=editform,
                               post_id=post_id,
                               title="Edit Post")

    elif request.method == "POST":
        if (editform.submit.data):
            if (current_user.id != int(user_id)):
                flash(
                    "As an admin you can delete any post but only edit your own posts."
                )
            else:
                post.body = editform.content.data
                db.session.commit()
            return redirect(url_for('full_paper', paper_id=paper_id))

        elif (editform.delete.data):
            if (current_user.id != int(user_id)
                    and current_user.admin_privilege):
                send_moderation_email(user, post)
            db.session.delete(post)
            db.session.commit()
            return redirect(url_for('full_paper', paper_id=paper_id))

        #print ("Forms: ", editform.submit.data, "   ", editform.delete.data, " ", editform.content.data)

    return render_template('editform.html', form=editform, post_id=post_id)


@flaskapp.route('/admin')
@login_required
def admin_page():
    metrics = dict()
    if current_user.email == "amanagarwal@gmx.com":
        current_user.admin_privilege = 1
        db.session.commit()
    if (current_user.admin_privilege):
        # weekly active users
        # count users who were active this week as well as last week
        # these users' visits have a timestamp from "previous week".

        right_now = datetime.utcnow()
        month_ago = right_now - timedelta(days=30)
        week_ago = right_now - timedelta(days=7)
        day_ago = right_now - timedelta(days=1)

        metrics = dict()

        metrics['total_users'] = User.query.count()
        metrics['total_posts'] = Post.query.count()
        metrics['total_papers'] = Paper.query.count()
        metrics['total_fragments'] = Fragment.query.count()

        metrics['weekly_active_users'] = User.query.filter(
            User.last_seen > week_ago).all()
        metrics['weekly_active'] = User.query.filter(
            User.last_seen > week_ago).count()

        metrics['weekly_posters'] = User.query.filter(
            User.last_post_time > week_ago).all()
        metrics['weekly_posters_count'] = User.query.filter(
            User.last_post_time > week_ago).count()

        metrics['spammers'] = User.query.filter(User.spammy > 2).order_by(
            User.spammy.desc()).all()

        return render_template("admin.html",
                               metrics=metrics,
                               title="Admin Portal")

    flash("You are not authorized to access this page.")
    return redirect(url_for('index'))


@flaskapp.route('/admin/papers', methods=['GET', 'POST'])
@login_required
def publish_papers():
    if (current_user.admin_privilege):
        papers = Paper.query.all()
        if (request.method == 'GET'):
            return render_template('publish_papers.html',
                                   papers=papers,
                                   title="Admin Papers")

        if (request.method == 'POST'):
            paper_id = int(request.form['paper_id'])
            paper = Paper.query.filter_by(id=paper_id).first()
            if (paper.published == 1):
                paper.published = 0
            else:
                paper.published = 1
            db.session.add(paper)
            db.session.commit()
            return redirect(url_for('publish_papers'))
    return "Oopsie"


@flaskapp.route('/admin/invites', methods=['GET', 'POST'])
@login_required
def invitation():
    if (current_user.admin_privilege):
        form = InviteForm()
        invites = Invitation.query.order_by(
            Invitation.date_created.desc()).all()
        if (request.method == 'GET'):
            return render_template('invites.html',
                                   prior_invites=invites,
                                   form=form,
                                   title="Admin Invites")

        if form.validate_on_submit():

            check_invite = Invitation.query.filter_by(
                email=form.email.data).first()
            if (check_invite is None):
                new_invite = Invitation(email=form.email.data)
                db.session.add(new_invite)
                db.session.commit()
                send_invitation_email(new_invite)
                flash("Invite sent!")
            else:
                flash("This email has already been invited. Re-sending email.")
                send_invitation_email(check_invite)
            return redirect(url_for('invitation'))
    return "Oopsie"


def upload_file(data, file_name, folder_name, bucket):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    s3 = boto3.resource('s3')
    try:
        file_name = folder_name + '/' + file_name
        s3.Bucket(bucket).put_object(Key=file_name,
                                     Body=data,
                                     ACL='public-read')
    except ClientError as e:
        logging.error(e)
        return False
    return True


@flaskapp.route('/p/<paper_id>/upload', methods=['POST', 'GET'])
@login_required
def upload_fragments(paper_id):
    if not paper_id.isdigit():
        abort(404)
    if (current_user.admin_privilege):
        paper = Paper.query.filter_by(id=paper_id).first()
        form = FragmentsForm()
        print(paper.id)
        if form.validate_on_submit():
            folder_name = paper.folder
            fragments_uploaded = False
            for image in form.files.data:
                if (upload_file(image.read(), secure_filename(image.filename),
                                folder_name, 'paper-fragments')):
                    # create database entry
                    order = int(image.filename.split('.')[0])
                    new_fragment = Fragment(order=order,
                                            paper=paper,
                                            file_name=secure_filename(
                                                image.filename),
                                            folder=folder_name)
                    db.session.add(new_fragment)
                    db.session.commit()
                    continue
                else:
                    flash("Upload failed for " +
                          secure_filename(image.filename))
                    return redirect(
                        url_for('upload_fragments', paper_id=paper_id))
            flash("Uploads finished!")
            return redirect(url_for('full_paper', paper_id=paper_id))
        elif (request.method == "GET"):
            return render_template('upload2.html',
                                   form=form,
                                   paper=paper,
                                   title="Upload Fragments")
        flash('Error submitting form.')
        return redirect(url_for('upload_fragments', paper_id=paper_id))
    return redirect(url_for('index'))
