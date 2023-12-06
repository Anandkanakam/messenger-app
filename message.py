from flask import Flask, request, jsonify

app = Flask(__name__)

# Store messages in memory for simplicity (In a real app, you would use a database)
messages = []

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    message = {
        'sender': data.get('sender'),
        'recipient': data.get('recipient'),
        'message': data.get('message')
    }
    messages.append(message)
    return jsonify({'status': 'Message sent successfully'})

@app.route('/get_messages', methods=['GET'])
def get_messages():
    return jsonify(messages)

if __name__ == '__main__':
    app.run(debug=True)
    ''''''


@app.route('/addcontact',methods=['GET','POST'])
def addcontact():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT pid  from profile where pid!=%s',[session.get('user')])
    data=cursor.fetchall()
    cursor.execute('select bin_to_uuid(pid) as uid,Name,About,date from profile where added_by=%s',[session.get('user')])
    new_data=cursor.fetchall()
    data=tuple([i for i in data if i  not in new_data])
    print(data)
    if request.method=="POST":
        if 'Name' in request.form:
            Enter_Username=request.form['Name']
            id=session.get('user')
            cursor=mysql.connection.cursor()
            cursor.execute('insert into profile (pid,Name,added_by) values(UUID_TO_BIN(UUID()),%s,%s)',[Enter_Username,id])
            mysql.connection.commit()
            return redirect(url_for('message',id1=session.get('user')))
    return render_template('Addcontact.html',data=data)
    @app.route('/profile',methods=['GET','POST'])
def profilepage(): 
    if session.get('user'):
        if request.method=='POST':
            Name=request.form['Name']
            About=request.form['About']
            id=session.get('user')
            cursor=mysql.connection.cursor()
            cursor.execute('insert into profile (pid,Name,About,added_by) values(UUID_TO_BIN(UUID()),%s,%s,%s)',[Name,About,id])
            mysql.connection.commit()
            cursor.close()
            flash('Profile added sucessfully')
            return redirect(url_for('addcontact'))
        return render_template('Profile.html')
    else:
        return redirect(url_for('login'))
    