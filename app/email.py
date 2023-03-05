from flask_mail import Message
from app import mail, flaskapp
from flask import render_template
from threading import Thread

def send_async_email(flaskapp, msg):
    with flaskapp.app_context():
        mail.send(msg)
        print ("Sent!")

def send_email(subject, sender, recipients, cc, bcc, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients, cc=cc, bcc=bcc)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(flaskapp, msg)).start()
    
def send_password_reset_email(user):
    token = user.reset_password_token()
    send_email(subject='DenseLayers: Password Reset',
               sender=flaskapp.config['ADMINS'][1], 
               recipients=[user.email], 
               cc=None, bcc=None,
               text_body=render_template('emails/reset_password.txt', user=user, token=token),
               html_body=render_template('emails/reset_password.html', user=user, token=token))
    
def send_moderation_email(user, post):
    send_email(subject='DenseLayers: Your post was removed',
               sender=flaskapp.config['ADMINS'][1], 
               recipients=[user.email], 
               cc=None, bcc=None,
               text_body=render_template('emails/moderation_email.txt', user=user, post=post),
               html_body=render_template('emails/moderation_email.html', user=user, post=post))

def send_invitation_email(invitation):
    send_email(subject='DenseLayers: You are invited!',
               sender=flaskapp.config['ADMINS'][1], 
               recipients=[invitation.email], 
               cc=None, bcc=None,
               text_body=render_template('emails/invitation_email.txt'),
               html_body=render_template('emails/invitation_email.html'))
    
def invite_friend_email(invitation, friend):
    subject_line = ("Your friend {name} wants you to join DenseLayers.".format(name=friend))
    send_email(subject=subject_line,
               sender=flaskapp.config['ADMINS'][1], 
               recipients=[invitation.email], 
               cc=None, bcc=None,
               text_body=render_template('emails/invite_friend.txt', friend=friend),
               html_body=render_template('emails/invite_friend.html', friend=friend))
