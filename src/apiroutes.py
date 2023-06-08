import flask
import uuid
import psycopg2.errors as dberr

# get the database helper functions and session dictionary
import db
import session

# generate a blueprint: a variable we can add routes and can be imported by the
# main app
api_bp = flask.Blueprint('api_bp', __name__)


@api_bp.route('/api/login', methods=['POST'])
def login():
    '''
    login authenticates login requests, creating session cookies and adding
    sessions to the dictionary. The form must contain a username and password.
    '''

    # get form data
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')
    if username is None or password is None:
        return flask.Response('<h1>Bad Request</h1>', 400)

    # get the password for that user, if it exists
    response = db.query(
        "SELECT senha FROM usuario WHERE nome=%s;", [username], db.one)

    if response is None:
        return flask.Response('<h1>User does not exist</h1>', 401)
    if response[0] != password:  # check if the password is correct
        return flask.Response('<h1>Invalid Password</h1>', 401)

    # generate a session id for the newly logged in user

    # this is not perfect, there is a user_number*2**(-128) chance to generate a
    # duplicate... but it's close enough for our uses, considering that it's
    # just a session id that in practice would be temporary
    sid = uuid.uuid4().hex
    session.sessions[sid] = username

    resp = flask.Response(status=201)
    resp.set_cookie('sid', sid)
    return resp


@api_bp.route('/api/register', methods=['POST'])
def register():
    '''
    register creates new users in the database.
    The form must contain a username, email and password.
    '''

    # get form data
    username = flask.request.form.get('username')
    email = flask.request.form.get('email')
    password = flask.request.form.get('password')
    if username is None or email is None or password is None:
        return flask.Response('<h1>Bad Request</h1>', 400)

    # try to add that user, if any error occurs, send a client error response
    statement = "INSERT INTO usuario (nome, email, senha) VALUES (%s, %s, %s)"
    try:
        db.query(statement, [username, email, password])
    except db.Error as e:
        if type(e) == dberr.UniqueViolation:
            text = 'User or email already exists'
        elif type(e) == dberr.StringDataRightTruncation:
            text = 'Text value too large'
        else:
            # catch-all if the error is uncommon
            text = f'{type(e).__name__}: {e}'

        return flask.Response(f'<h1>{text}</h1>', 409)

    # the user is registred! The main html page should redirect it to log in
    return flask.Response(status=201)
