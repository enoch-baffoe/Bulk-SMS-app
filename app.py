from flask import Flask,render_template,request,redirect,jsonify,flash,url_for,g,session
from flask_mysqldb import MySQL
import os
import bcrypt
from werkzeug.utils import secure_filename
from mnotifySMS import sendSMS
import pandas as pd
from pandas.io import sql

app=Flask(__name__)

app.secret_key =os.urandom(24)

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "power"
app.config["MYSQL_DB"] = "SMS_db"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql=MySQL(app)


def check_phone_number(phone):

    if str(phone).isdigit() and (len(str(phone)) == 10 or len(str(phone)) == 9 or len(str(phone))==12):
        return True
    else:
        return False


def check_name(name):
    name= name.replace("."," ")
    name = name.translate({ord(c): None for c in "- "})
    
    # pass the regular expression
    # and the string into the fullmatch() method
    if name.isalpha():
        return True
    else:
        return False


def confirm_input(name,phone_number):
    if (check_name(name) and check_phone_number(phone_number)):
        return True
    return False


@app.route('/',methods=['GET','POST'])
def home():
    if g.loggedIn and g.type=='admin':
        return render_template('index.html')
    else:
        return redirect(url_for("login"))

@app.route('/admin/addContact',methods=['GET','POST'])
def addContact():
    if g.loggedIn and g.type=='admin':
        if request.method=='POST':
            name=request.form['name']
            phone_number=request.form['phone_number']
            group=request.form['group']
            meetsRequirement=True
            if not check_name(name):
                flash('Name does not meet specified format','warning')
                meetsRequirement=False
            if not check_phone_number:
                flash('Phone Number does not match specified format','warning')
                meetsRequirement=False
            if not meetsRequirement:
                return redirect(request.referrer)
            try:
                cur=mysql.connection.cursor()
                cur.execute("INSERT into members(name, phone_number,groups_id) VALUES (%s,%s,%s)",(name,phone_number,group))
                mysql.connection.commit()
                flash("Contact added successfully","success")
            except:
                mysql.connection.rollback()
                flash("Contact Already Exists in Database","danger")
        cur=mysql.connection.cursor()
        cur.execute("SELECT id,name FROM `groups`")
        groups=cur.fetchall()
        
        return render_template('addContact.html',groups=groups)
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
            #sendSMS(message,contactList)
            print (contactList,flush=True)
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
        if request.method=='POST':
            if 'bulkContacts' not in request.files:
                flash('File not uploaded',"danger")
                return redirect(request.url)
            group_id=request.form['group_id']
            file = request.files['bulkContacts']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file','danger')
                return redirect(request.url)
            filePd=pd.read_excel(file,sheet_name=0)
            #add group id to dataframe
            filePd['groups_id']=group_id
            cur=mysql.connection.cursor()
            meetsRequirement=True
            newMembersList=[]
            i=1
            try:
                i=i+1
                #for i in range(0, len(filePd)):
                    #print(filePd.iloc[i]['phone_number'], filePd.iloc[i]['name'],flush=True)
                for index,row in filePd.iterrows():
                    if check_phone_number(row['phone_number']) ==False:
                        meetsRequirement==False
                        flash('Phone Number at line '+str(i)+ ' does not meet specified format','warning')
                    if check_name(row['name'])==False:
                        meetsRequirement=False
                        flash('Name at line '+str(i)+ ' does not meet specified format','warning')
                    if meetsRequirement==False:
                        break
                    else:
                        k = (row['name'],row['phone_number'],row['groups_id'])
                        newMembersList.append(k)
                        
                print(newMembersList,flush=True)
            except BaseException as error:
                    flash('An error occured. Check if you inserted the correct file following all the rules given','warning')
                    print('An exception occurred: {}'.format(error),flush=True)
            #filePd.to_sql(name="members",con=cur,if_exists='append',method='multi')
            # print(filePd,flush=True)
            try:
                cur=mysql.connection.cursor()
                cur.executemany('INSERT INTO members(name,phone_number,groups_id) VALUES (%s,%s,%s)',newMembersList)
                mysql.connection.commit()
                flash('Lecturers successfuly added to database','success')
            except mysql.connection.IntegrityError:
                mysql.connection.rollback()
                cur.close
                flash('Data could not be inserted. Some Lecturers may already exist in the database','warning')
                
        return redirect(request.referrer) 
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
        if request.method == "POST":
            oldPassword = request.form["password"]
            newPassword = request.form["newPassword"]
            cur = mysql.connection.cursor()
            cur.execute("SELECT hashed_password from admin where id=%s", [g.id])
            is_account = cur.fetchone()
            hashed_password = is_account["hashed_password"]
            if bcrypt.checkpw(
                oldPassword.encode("utf-8"), hashed_password.encode("utf-8")
            ):
                newHashedPassword = bcrypt.hashpw(
                    newPassword.encode("utf-8"), bcrypt.gensalt()
                )
                cur.execute(
                    "UPDATE admin SET hashed_password=%s WHERE id=%s",
                    (newHashedPassword, g.id),
                )
                mysql.connection.commit()
                cur.close()
                flash("Password changed successfully", "success")
                return redirect(request.referrer)
            else:
                flash("Password is incorrect", "warning")
        return render_template('changePassword.html')
    else:
        return redirect(url_for("login"))

@app.route('/admin/bulkContacts',methods=['GET','POST'])
def bulkContacts():
    if g.loggedIn and g.type=='admin':
        cur=mysql.connection.cursor()
        cur.execute("SELECT id,name FROM `groups`")
        groups=cur.fetchall()
        return render_template('addBulkContacts.html',groups=groups)
    else:
        return redirect(url_for("login"))
    

 #----------------------------------------------
 #------TO DO
 # show contacts
 #edit contact
 # Delete contact
 #---------------------------------  
@app.route('/admin/contacts',methods=['GET','POST'])
def showContacts():
    if g.loggedIn and g.type=='admin':
        return render_template('contacts.html')
    else:
        return redirect(url_for("login"))
    
@app.route("/livesearch", methods=["POST"])
def livesearch():
    cur = mysql.connection.cursor()
    input = request.form["text"]
    search_num = input
    if input.startswith("0"):
        search_num = input[1:]
    search_num = "%" + str(search_num) + "%"
    search = "%" + str(input) + "%"

    # print("search Term is  :{}".format(search),flush=True)
    cur.execute(
        "SELECT members.id AS id ,members.name AS name,groups.name AS group_name, members.groups_id AS groupId, IFNULL(members.phone_number, 'N/A') AS phone_number FROM members INNER JOIN `groups` on members.groups_id=groups.id WHERE members.name LIKE %s  OR members.phone_number LIKE %s OR members.phone_number LIKE %s OR groups.name LIKE %s ORDER BY members.name ASC",(search, search, search_num, search),
    )
    result = cur.fetchall()
    # print("\n\n\n\result is below \n\n\n\n",flush=True)
    # print(result,flush=True)
    return jsonify(result)


@app.route('/admin/editContact/<string:id>')
def editContact(id):
    if g.loggedIn and g.type=='admin':
        return render_template('editContact.html')
    else:
        return redirect(url_for("login"))
    
@app.route('/admin/deleteContact/<string:id>')
def deleteContact(id):
    if g.loggedIn and g.type=='admin':
        flash("Contact Deleted Successfully","success")
        return redirect(request.referrer)
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