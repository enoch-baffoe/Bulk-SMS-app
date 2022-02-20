from flask import Flask,render_template,request,redirect,flash,url_for,g,session
from flask_mysqldb import MySQL
import os
import bcrypt
from mnotifySMS import sendSMS
app=Flask(__name__)

app.secret_key =os.urandom(24)

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "power"
app.config["MYSQL_DB"] = "SMS_db"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql=MySQL(app)

@app.route('/',methods=['GET','POST'])
def home():
    if g.loggedIn and g.type=='admin':
        return render_template('index.html')
    else:
        return redirect(url_for("login"))

@app.route('/admin/addContact',methods=['GET','POST'])
def addContact():
    if g.loggedIn and g.type=='admin':
        return render_template('addContact.html')
    else:
        return redirect(url_for("login"))
@app.route('/admin/quickSMS',methods=['GET','POST'])
def quickSMS():
    if g.loggedIn and g.type=='admin':
        if request.method=='POST':
            message=request.form['message']
            contacts=request.form['contacts']
            groups=request.form.getlist('groups')
            contactList = list(contacts.split(","))
            print (contactList,flush=True)
            if groups: #
                # we get the phone numbers from the selected groups
                cur=mysql.connection.cursor()
                cur.execute("SELECT phone_number FROM `members` where groups_id in %s;",[groups])
                dictPhones=cur.fetchall()
                for item in dictPhones:
                    contactList.append(item['phone_number'])
                
            # we remove duplicates
            contactList = list(set(contactList))
            sendSMS(message,contactList)
            #print (contactList,flush=True)
            flash("Message Delivered","success")
            return redirect(url_for('home'))
        cur=mysql.connection.cursor()
        cur.execute("SELECT id,name FROM `groups`;")
        groups=cur.fetchall()
        return render_template('quickSMS.html',groups=groups)
    else:
        return redirect(url_for("login"))
@app.route('/admin/addBulkContacts',methods=['GET','POST'])
def addBulkContacts():
    if g.loggedIn and g.type=='admin':
        return render_template('addBulkContacts.html')
    else:
        return redirect(url_for("login"))
    
@app.route('/admin/createGroup',methods=['GET','POST'])
def createGroup():
    if g.loggedIn and g.type=='admin':
        if request.method=='POST':
            group=request.form['group']
            cur=mysql.connection.cursor()
            cur.execute("SELECT name FROM `groups` where name=%s;",[group])
            groupExists=cur.fetchone();
            if groupExists:
                flash("Group already exists","warning")
                return redirect(url_for("createGroup"))
            cur.execute("INSERT INTO `groups` (name) VALUE (%s)",[group])
            mysql.connection.commit()
            flash('New group created','success')
            return redirect(url_for('home'))
        return render_template('createGroup.html')
    else:
        return redirect(url_for("login"))

@app.route('/admin/changePassword',methods=['GET','POST'])
def changePassword():
    if g.loggedIn and g.type=='admin':
        return render_template('changePassword.html')
    else:
        return redirect(url_for("login"))

@app.route('/admin/bulkContacts',methods=['GET','POST'])
def bulkContacts():
    if g.loggedIn and g.type=='admin':
        return render_template('bulkContacts.html')
    else:
        return redirect(url_for("login"))
    

    

@app.route('/admin/resetPassword',methods=['GET','POST'])
def resetPassword():
    return render_template('resetPassword.html')
#---------------------------------
#--------LOGIN----------------------
#--------------------------------
@app.route('/admin/login',methods=['GET','POST'])
def login(email='',password=''):
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        cur=mysql.connection.cursor()
        cur.execute('SELECT id,email,hashed_password FROM admin WHERE email = %s', [email])
        account = cur.fetchone()
        cur.close()
        if account:
            hashed_password=account['hashed_password']
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                session['type']='admin'
                session['loggedIn'] = True
                session['id'] = account['id']
                return redirect(url_for('home'))
            else:
                flash('Password is incorrect',"danger")
                return render_template('login.html',email=email,password=password)
        else:
            flash('Email not found',"danger")
            return render_template('login.html',email=email,password=password)
    return render_template('login.html')

@app.route('/create_admin')
def reset_admin():
    cur=mysql.connection.cursor()
    password= "admin"
    username="bafpep@gmail.com"
    hashed_password=bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
    cur.execute("INSERT INTO admin(email,hashed_password) VALUES (%s,%s);",(username,hashed_password))
    mysql.connection.commit()
    return 'DONE'

#----------------------------------------------------------------
#------------BEFORE REQUESTS-------------------------------------
#----------------------------------------------------------------
@app.route('/logout',methods=['GET','POST'])
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedIn', None)
   session.pop('id', None)
   session.pop('type', None)
   # Redirect to login page
   return redirect(request.referrer)

@app.before_request
def before_request():
    g.id=None
    g.type=None
    g.loggedIn=None
    if 'loggedIn' in session:
        g.type=session['type']
        g.loggedIn= True
        g.id=session['id']

if __name__=='__main__':
    app.run(debug=True)