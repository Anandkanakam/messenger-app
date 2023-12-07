from flask import Flask,flash,redirect,render_template,url_for,request,jsonify,session,send_file,abort
from io import BytesIO
from flask_session import Session
from sdmail import sendmail
from tokenreset import token
from itsdangerous import URLSafeTimedSerializer
from key import *
import mysql.connector
import os
app=Flask(__name__)
app.secret_key="secret_key"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
db=os.environ['RDS_DB_NAME']
user=os.environ['RDS_USERNAME']
password=os.environ['RDS_PASSWORD']
host=os.environ['RDS_HOSTNAME']
port=os.environ['RDS_PORT']
with mysql.connector.connect(host=host,user=user,password=password,db=db) as conn:
    cursor=conn.cursor(buffered=True)
    cursor.execute('create table if not exists users(id varchar(80) NOT NULL,first_name varchar(50) DEFAULT NULL,last_name varchar(50) DEFAULT NULL,email varchar(100) DEFAULT NULL,password varchar(50) DEFAULT NULL,created timestamp NULL DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY (`id`)')
    cursor.execute('create table if not exists friends(followers varchar(90) DEFAULT NULL,following varchar(90) DEFAULT NULL,KEY followers(`followers`),KEY following(`following`),CONSTRAINT `friends_ibfk_1` FOREIGN KEY (`followers`) REFERENCES users(`id`) ON DELETE CASCADE ON UPDATE CASCADE,CONSTRAINT `friends_ibfk_2` FOREIGN KEY (`following`) REFERENCES users(`id`)')
    cursor.execute('create table if not exists login(id varchar(80) DEFAULT NULL,password varchar(50) DEFAULT NULL)')
    cursor.execute('create table if not exists messenger(followers varchar(80) DEFAULT NULL,following varchar(80) DEFAULT NULL,message text,created_at datetime DEFAULT CURRENT_TIMESTAMP,KEY following(`following`),KEY followers(`followers`),CONSTRAINT `messenger_ibfk_1` FOREIGN KEY (`followers`) REFERENCES users(`id`) ON DELETE CASCADE ON UPDATE CASCADE,CONSTRAINT `messenger_ibfk_2` FOREIGN KEY (`following`) REFERENCES users(`id`) ON DELETE CASCADE ON UPDATE CASCADE)')
    cursor.execute('create table if not exists profile(name varchar(50) DEFAULT NULL,about varchar(50) DEFAULT NULL)')
    cursor.execute('create table if not exists files(follower varchar(150) DEFAULT NULL,following varchar(150) DEFAULT NULL,file longblob,created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,KEY follower (`follower`),KEY following(`following`),CONSTRAINT `files_ibfk_1` FOREIGN KEY (`follower`) REFERENCES users(`id`),CONSTRAINT `files_ibfk_2` FOREIGN KEY (`following`) REFERENCES users(`id`)')

mydb=mysql.connector.connect(host=host,user=user,password=password,db=db) 
#mydb=mysql.connector.connect(host='localhost',user='root',password='Anand@19',db='mma')
@app.route('/')
def home():
    return render_template('home.html')
@app.route('/home/<id1>')
def chat(id1):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT following from friends where followers=%s',[id1])
    data=cursor.fetchall()
    return render_template('chat.html',id1=id1,data=data)
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method=="POST":
        id1=request.form['id1']
        First_Name=request.form['First_Name']
        Last_Name=request.form['Last_Name']
        Email=request.form['Email']
        Password=request.form['Password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where first_name=%s',[First_Name])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from users where email=%s',[Email])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username already in use')
            return render_template('Signup.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('Signup.html')
        data={'id1':id1,'First_Name':First_Name,'Last_Name':Last_Name,'Email':Email,'Password':Password}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm',token=token(data),_external=True)}"
        sendmail(to=Email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('login'))
    return render_template('Signup.html')
@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
        #print(e)
        return 'Link Expired register again'
    else:
        cursor=mydb.cursor(buffered=True)
        First_Name=data['First_Name']
        cursor.execute('select count(*) from users where first_name=%s',[First_Name])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('login'))
        else:
            cursor.execute('insert into  users(id,first_name,last_name,email,password) values(%s,%s,%s,%s,%s)',[data['id1'],data['First_Name'],data['Last_Name'],data['Email'],data['Password']])
            mysql.connection.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('login'))
@app.route('/forgotpassword',methods=('GET', 'POST'))
def forgotpassword():
    if request.method=='POST':
        id1 = request.form['id']
        cursor=mydb.cursor(buffered=True) 
        cursor.execute('select id from users') 
        deta=cursor.fetchall()
        if (id1,) in deta:
            cursor.execute('select email from users where id=%s',[id1])
            data=cursor.fetchone()[0]
            cursor.close()
            subject=f'Reset Password for {data}'
            body=f'Reset the passwword using-\{request.host+url_for("resetpwd",token=token(id1,300))}'
            sendmail(data,subject,body)
            flash('Reset link sent to your registered mail id')
            return redirect(url_for('login'))
        else:
            flash('user does not exits')
    return render_template('forgot.html')
@app.route('/resetpwd/<token>',methods=('GET', 'POST'))
def resetpwd(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        id1=s.loads(token)['user']
        if request.method=='POST':
            npwd = request.form['npassword']
            cpwd = request.form['cpassword']
            if npwd == cpwd:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update users set password=%s where id=%s',[npwd,id1])
                mysql.connection.commit()
                cursor.close()
                return 'Password reset Successfull'
            else:
                return 'Password does not matched try again'
        return render_template('newpassword.html')
    except Exception as e:
        abort(410,description='reset link expired')
@app.route('/login', methods =['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('chat',id1=session['user']))
    if request.method=="POST":
        user=request.form['id']
        password=request.form['Password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT Id from USERS')
        users=cursor.fetchall()            
        cursor.execute('select password from Users where Id=%s',[user])
        data=cursor.fetchone()
        cursor.close()
        if (user,) in users:
            if password==data[0]:
                session["user"]=user
                return redirect(url_for('chat',id1=user))
            else:
                flash('Invalid Password')
                return render_template('login.html')
        else:
            flash('Invalid id')
            return render_template('login.html')
    return render_template('login.html')
@app.route('/logout')
def logout():
    session['user']=None
    return redirect(url_for('home'))
@app.route('/addcontact',methods=['GET','POST'])
def addcontact():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT id  from users where id!=%s',[session.get('user')])
    data=cursor.fetchall()
    cursor.execute('select following from friends where followers=%s',[session.get('user')])
    new_data=cursor.fetchall()
    data=tuple([i for i in data if i  not in new_data])
    print(data)
    if request.method=="POST":
        if 'Enter_Username' in request.form:
            Enter_Username=request.form['Enter_Username']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into friends values(%s,%s)',[session.get('user'),Enter_Username])
            mysql.connection.commit()
            return redirect(url_for('chat',id1=session.get('user')))
    return render_template('Addcontact.html',data=data)
@app.route('/profile',methods=['GET','POST'])
def profilepage():
    if request.method=="POST":
        name=request.form['name']
        about=request.form['about']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT following from friends where followers=%s',[session.get('user')])
        data=cursor.fetchall()
        cursor.execute('insert into profile(name,about) values(%s,%s)',[name,about])
        cursor.fetchall()
        cursor.close()
        return redirect(url_for('chat',id1=session.get('user')))
    else:
        return render_template('Profile.html')  
@app.route('/settings')
def settings():
    return render_template('setting.html')
@app.route('/back')
def back():
    return redirect(url_for('login'))
@app.route('/message/<id1>',methods=['GET','POST'])
def message(id1):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute("SELECT message,date_format(created_at,'%%h:%%i %%p') as date from messenger where followers=%s and following=%s order by date",(session.get('user'),id1))
        sender=cursor.fetchall()
        cursor.execute("SELECT message,date_format(created_at,'%%h:%%i %%p') as date from messenger where followers=%s and following=%s order by date",(id1,session.get('user')))
        reciever=cursor.fetchall()
        cursor.execute('select filename from files where follower=%s and following=%s',(session.get('user'),id1))
        sender_files=cursor.fetchall()
        cursor.execute('select filename from files where follower=%s and following=%s',(id1,session.get('user')))
        reciever_files=cursor.fetchall()
        cursor.close()
        if request.method=='POST':
            if 'file' in request.files:
                file=request.files['file']
                filename=file.filename
                cursor=mydb.cursor(buffered=True)
                cursor.execute('INSERT INTO files (follower,following,filename,file) values(%s,%s,%s,%s)',(session.get('user'),id1,filename,file.read()))
                mysql.connection.commit()
                cursor.execute('select filename from files where follower=%s and following=%s',(session.get('user'),id1))
                sender_files=cursor.fetchall()
                cursor.execute('select filename from files where follower=%s and following=%s',(id1,session.get('user')))
                reciever_files=cursor.fetchall()
                return render_template('Messenger.html',id1=id1,sender=sender,reciever=reciever,sender_files=sender_files,reciever_files=reciever_files)
            message=request.form['Message']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('INSERT INTO messenger(followers,following,message) values(%s,%s,%s)',(session['user'],id1,message))
            mysql.connection.commit()
            cursor.execute("SELECT message,date_format(created_at,'%%h:%%i %%p') as date from messenger where followers=%s and following=%s order by date",(session.get('user'),id1))
            sender=cursor.fetchall()
            cursor.execute("SELECT message,date_format(created_at,'%%h:%%i %%p') as date from messenger where followers=%s and following=%s order by date",(id1,session.get('user')))
            reciever=cursor.fetchall()
        return render_template('Messenger.html',id1=id1,sender=sender,reciever=reciever,sender_files=sender_files,reciever_files=reciever_files)
    return redirect(url_for('login'))

@app.route('/download/<filename>')
def download(filename):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('SELECT file from files where filename=%s',[filename])
    data=cursor.fetchone()[0]
    return send_file(BytesIO(data),download_name=filename,as_attachment=True)
if __name__=="__main__":
    app.run()

