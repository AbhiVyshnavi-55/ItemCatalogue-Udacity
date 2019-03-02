from flask import Flask, render_template, url_for
from flask import request, redirect, flash, make_response, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Data_Setup import Base,RestaurentName,ItemName, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import datetime

engine = create_engine('sqlite:///restaurent.db',
                       connect_args={'check_same_thread': False}, echo=True)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurent"

DBSession = sessionmaker(bind=engine)
session = DBSession()
# Create anti-forgery state token
tbs_cat = session.query(RestaurentName).all()


# login
@app.route('/login')
def showLogin():
    
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    tbs_cat = session.query(RestaurentName).all()
    tbes = session.query(ItemName).all()
    return render_template('login.html',
                           STATE=state, tbs_cat=tbs_cat, tbes=tbes)
    # return render_template('myhome.html', STATE=state
    # tbs_cat=tbs_cat,tbes=tbes)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; border-radius: 150px;'
    '-webkit-border-radius: 150px; -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output


# User Helper Functions
def createUser(login_session):
    User1 = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(User1)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception as error:
        print(error)
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session

#####
# Home
@app.route('/')
@app.route('/home')
def home():
    tbs_cat = session.query(RestaurentName).all()
    return render_template('myhome.html', tbs_cat=tbs_cat)

#####
# Byke Category for admins
@app.route('/RestaurentHub')
def RestaurentHub():
    try:
        if login_session['username']:
            name = login_session['username']
            tbs_cat = session.query(RestaurentName).all()
            tbs = session.query(RestaurentName).all()
            tbes = session.query(ItemName).all()
            return render_template('myhome.html', tbs_cat=tbs_cat,
                                   tbs=tbs, tbes=tbes, uname=name)
    except:
        return redirect(url_for('showLogin'))

######
# Showing bykes based on byke category
@app.route('/RestaurentHub/<int:tbid>/AllRestaurents')
def showRestaurents(tbid):
    tbs_cat = session.query(RestaurentName).all()
    tbs = session.query(RestaurentName).filter_by(id=tbid).one()
    tbes = session.query(ItemName).filter_by(restaurentnameid=tbid).all()
    try:
        if login_session['username']:
            return render_template('showRestaurents.html', tbs_cat=tbs_cat,
                                   tbs=tbs, tbes=tbes,
                                   uname=login_session['username'])
    except:
        return render_template('showRestaurents.html',
                               tbs_cat=tbs_cat, tbs=tbs, tbes=tbes)

#####
# Add New Byke
@app.route('/RestaurentHub/addRestaurentName', methods=['POST', 'GET'])
def addRestaurentName():
    if request.method == 'POST':
        restaurentname = RestaurentName(name=request.form['name'],
                           user_id=login_session['user_id'])
        session.add(restaurentname)
        session.commit()
        return redirect(url_for('RestaurentHub'))
    else:
        return render_template('addRestaurentName.html', tbs_cat=tbs_cat)

########
# Edit Byke Category
@app.route('/RestaurentHub/<int:tbid>/edit', methods=['POST', 'GET'])
def editRestaurentName(tbid):
    editRestaurentName = session.query(RestaurentName).filter_by(id=tbid).one()
    creator = getUserInfo(editRestaurentName.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot edit this RestaurentName."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('RestaurentHub'))
    if request.method == "POST":
        if request.form['name']:
            editRestaurentName.name = request.form['name']
        session.add(editRestaurentName)
        session.commit()
        flash("editRestaurentName Edited Successfully")
        return redirect(url_for('RestaurentHub'))
    else:
        # tbs_cat is global variable we can them in entire application
        return render_template('editRestaurentName.html',
                               tb=editRestaurentName, tbs_cat=tbs_cat)

######
# Delete Byke Category
@app.route('/RestaurentHub/<int:tbid>/delete', methods=['POST', 'GET'])
def deleteRestaurentName(tbid):
    tb = session.query(RestaurentName).filter_by(id=tbid).one()
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot Delete this deleteRestaurentName."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('RestaurentHub'))
    if request.method == "POST":
        session.delete(tb)
        session.commit()
        flash("RestaurentName Deleted Successfully")
        return redirect(url_for('RestaurentHub'))
    else:
        return render_template('deleteRestaurentName.html', tb=tb, tbs_cat=tbs_cat)

######not ccomplited
# Add New Byke Name Details
@app.route('/RestaurentHub/addRestaurentName/addRestaurentItemDetails/<string:tbname>/add',
           methods=['GET', 'POST'])
def addRestaurentDetails(tbname):
    tbs = session.query(RestaurentName).filter_by(name=tbname).one()
    # See if the logged in user is not the owner of byke
    creator = getUserInfo(tbs.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't add new item edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showRestaurents', tbid=tbs.id))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        feedback = request.form['feedback']
        itemdetails = ItemName(name=name, description=description,
                              price=price, feedback=feedback,
                              date=datetime.datetime.now(),
                              restaurentnameid=tbs.id,
                              user_id=login_session['user_id'])
        session.add(itemdetails)
        session.commit()
        return redirect(url_for('showRestaurents', tbid=tbs.id))
    else:
        return render_template('addRestaurentItemDetails.html',
                               tbname=tbs.name, tbs_cat=tbs_cat)

######
# Edit Byke details
@app.route('/RestaurentHub/<int:tbid>/<string:tbename>/edit',
           methods=['GET', 'POST'])
def editRestaurentItem(tbid, tbename):
    tb = session.query(RestaurentName).filter_by(id=tbid).one()
    itemdetails = session.query(ItemName).filter_by(name=tbename).one()
    # See if the logged in user is not the owner of byke
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't edit this item edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showResaturents', tbid=tb.id))
    # POST methods
    if request.method == 'POST':
        itemdetails.name = request.form['name']
        itemdetails.description = request.form['description']
        itemdetails.price = request.form['price']
        itemdetails.feedback = request.form['feedback']
        itemdetails.date = datetime.datetime.now()
        session.add(itemdetails)
        session.commit()
        flash("Item Edited Successfully")
        return redirect(url_for('showRestaurents', tbid=tbid))
    else:
        return render_template('editRestaurentItem.html',
                               tbid=tbid, itemdetails=itemdetails, tbs_cat=tbs_cat)

#####
# Delte Byke Edit
@app.route('/RestaurentHub/<int:tbid>/<string:tbename>/delete',
           methods=['GET', 'POST'])
def deleteRestaurentItem(tbid, tbename):
    tb = session.query(RestaurentName).filter_by(id=tbid).one()
    itemdetails = session.query(ItemName).filter_by(name=tbename).one()
    # See if the logged in user is not the owner of byke
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't delete this item edition"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showRestaurents', tbid=tb.id))
    if request.method == "POST":
        session.delete(itemdetails)
        session.commit()
        flash("Deleted Item Successfully")
        return redirect(url_for('showRestaurents', tbid=tbid))
    else:
        return render_template('deleteRestaurentItem.html',
                               tbid=tbid, itemdetails=itemdetails, tbs_cat=tbs_cat)

####
# Logout from current user
@app.route('/logout')
def logout():
    access_token = login_session['access_token']
    print ('In gdisconnect access token is %s', access_token)
    print ('User name is: ')
    print (login_session['username'])
    if access_token is None:
        print ('Access Token is None')
        response = make_response(
            json.dumps('Current user not connected....'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = \
        h.request(uri=url, method='POST', body=None,
                  headers={'content-type': 'application/x-www-form-urlencoded'})[0]

    print (result['status'])
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected user..'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Successful logged out")
        return redirect(url_for('showLogin'))
        # return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

#####
# Json
@app.route('/RestaurentHub/JSON')
def allRestaurentsJSON():
    restaurentnames = session.query(RestaurentName).all()
    category_dict = [c.serialize for c in restaurentnames]
    for c in range(len(category_dict)):
        restaurents = [i.serialize for i in session.query(
                 ItemName).filter_by(restaurentnameid=category_dict[c]["id"]).all()]
        if restaurent:
            category_dict[c]["restaurent"] = restaurents
    return jsonify(RestaurentName=category_dict)

####
@app.route('/RestaurentHub/restaurentname/JSON')
def categoriesJSON():
    restaurents = session.query(RestaurentName).all()
    return jsonify(restaurentName=[c.serialize for c in restaurents])

####
@app.route('/RestaurentHub/restaurents/JSON')
def itemsJSON():
    items = session.query(ItemName).all()
    return jsonify(restaurents=[i.serialize for i in items])

#####
@app.route('/RestaurentHub/<path:restaurent_name>/restaurents/JSON')
def categoryItemsJSON(restaurent_name):
    restaurentName = session.query(RestaurentName).filter_by(name=restaurent_name).one()
    restaurents = session.query(ItemName).filter_by(itemname=restaurentName).all()
    return jsonify(restaurentName=[i.serialize for i in restaurents])

#####
@app.route('/RestaurentHub/<path:restaurent_name>/<path:restaurentitem_name>/JSON')
def ItemJSON(restaurent_name, restaurentitem_name):
    restaurentName = session.query(RestaurentName).filter_by(name=restaurent_name).one()
    restaurentItemName = session.query(ItemName).filter_by(
           name=restaurentitem_name, item=restaurentName).one()
    return jsonify(restaurentItemName=[restaurentItemName.serialize])

if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host='127.0.0.1', port=8000)
