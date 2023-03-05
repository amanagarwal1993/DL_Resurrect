from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, MultipleFileField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Regexp, NumberRange
from flask_wtf.file import FileField, FileRequired
from app.models import User
from flask_babel import lazy_gettext as _l

class LoginForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))

class SignupForm(FlaskForm):
    name = StringField(_l('Full Name'), validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register!')
    
class InviteForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Invite')
            
class NewPaperForm(FlaskForm):
    title = TextAreaField('Title (Required)', validators=[DataRequired(), Length(min=1, max=140)])
    journal = StringField('Journal (Required)', 
                          validators=[DataRequired(), Length(min=0, max=100)])
    scholar_link = TextAreaField('Original Paper URL (Required)', 
                                 validators=[DataRequired(), Length(min=1, max=200)])
    author_string = TextAreaField('Authors (Required)', 
                                  validators=[DataRequired(), Length(min=1, max=200)])
    shorthand = StringField('Paper name in shorthand (to act as folder in S3)', 
                         validators=[DataRequired(), Length(min=0, max=30)])
    paper_file = FileField('PDF file of paper (Required)', validators=[FileRequired()])
    img_file = FileField('Image file for banner, 480h 360w (Required)', validators=[FileRequired()])
    publish_month = IntegerField('Publication month number', 
                                validators=[DataRequired(), NumberRange(min=1,max=12)])
    publish_year = IntegerField('Publication year number', 
                                validators=[DataRequired(), NumberRange(min=1700,max=3000)])
    submit = SubmitField('Create')
    

class EditPaperForm(FlaskForm):
    title = TextAreaField('Title', validators=[DataRequired(), Length(min=1, max=140)])
    author_string = TextAreaField('Authors', 
                                  validators=[DataRequired(), Length(min=1, max=200)])
    scholar_link = TextAreaField('Original Paper URL', 
                                 validators=[DataRequired(), Length(min=1, max=200)])
    shorthand = StringField('Paper name in shorthand (to act as folder in S3)', 
                         validators=[DataRequired(), Length(min=0, max=30)])
    journal = StringField('Journal', 
                          validators=[DataRequired(), Length(min=0, max=100)])
    publish_month = IntegerField('Publication month number', 
                                validators=[DataRequired(), NumberRange(min=1,max=12)])
    publish_year = IntegerField('Publication year number', 
                                validators=[DataRequired(), NumberRange(min=1700,max=3000)])
    submit = SubmitField('Update')
    delete = SubmitField('Delete')
    
class FragmentsForm(FlaskForm):
    files = MultipleFileField('Files')
    submit = SubmitField('Submit')
    
class EditProfileForm(FlaskForm):
    name = StringField('Your name', validators=[DataRequired()])
    about_me = StringField('About Me', validators=[Length(min=0, max=140)])
    #orcid_id = StringField('ORCID ID (Optional)', validators=[Regexp('\d{4}-\d{4}-\d{4}-\d{4}')])
    submit = SubmitField('Update')
    
    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, *kwargs)
        self.original_username = original_username
    
class DeleteUserForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Delete My Account')
    
class SuspendUserForm(FlaskForm):
    submit = SubmitField('Flip suspension')
    
class NewPostForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=1, max=10000)])
    fragment_id = IntegerField('fragment_id', validators=[DataRequired()])
    submit = SubmitField('Submit')
    
class EditPostForm(FlaskForm):
    post_id = IntegerField('post_id', validators=[DataRequired()])
    user_id = IntegerField('user_id', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Confirm Edit')
    delete = SubmitField('Delete This Post')

class CommentForm(FlaskForm):
    id = IntegerField('post_id', validators=[DataRequired()])
    user_id = IntegerField('user_id', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=1, max=140)])
    
class PasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')
    
class ChangePasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')