import os
import tensorflow as tf
import numpy as np
from keras.preprocessing import image
from PIL import Image
import cv2
from keras.models import load_model
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

from flask import Flask, request, render_template, redirect, url_for, session
from flask_mysqldb import MySQL, MySQLdb
import bcrypt


app = Flask(__name__)

model = load_model('BrainTumorBinary.h5')

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'braintumor'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = '*^%prettySecret%^*'
mysql = MySQL(app)




##### Pyhton Form #####

@app.route("/")
def index():
    return render_template("home.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    else:
        name = request.form['reg_name']
        email = request.form['reg_email']
        password = request.form['reg_password'].encode('utf-8')
        hash_password = bcrypt.hashpw(password, bcrypt.gensalt())

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO braintumoruser (name, email, password)  VALUES (%s, %s, %s)",(name, email,hash_password,))
        mysql.connection.commit()
        session['name'] = name
        session['email'] = email
        return redirect(url_for("login")) #method name instead of page name

@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form['log_email']
        password = request.form['log_password'].encode('utf-8')

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM braintumoruser WHERE email=%s",(email,))
        users = cur.fetchone()
        cur.close()

        if users is not None:
            if bcrypt.hashpw(password,users['password'].encode('utf-8')) == users['password'].encode('utf-8'):
                session['name'] = users['name']
                session['email'] = users['email']
                return redirect(url_for('brainTumor'))
            else:
                return "email or password didnot match"
        else:
            return "Null"
    
    else:
        return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()
    return render_template("home.html")



####### Brain Tumor Detection ######


def get_className(classNo):
	if classNo==0:
		return "No Brain Tumor"
	elif classNo==1:
		return "Yes Brain Tumor"


def getResult(img):
    image=cv2.imread(img)
    image = Image.fromarray(image, 'RGB')
    image = image.resize((64, 64))
    image=np.array(image)
    input_img = np.expand_dims(image, axis=0)
    result=model.predict(input_img)
    return result


@app.route('/braintumor', methods=['GET'])
def brainTumor():
    return render_template('braintumor.html')


@app.route('/predict', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        f = request.files['file']

        basepath = os.path.dirname(__file__)
        file_path = os.path.join(
            basepath, 'pred', secure_filename(f.filename))
        f.save(file_path)
        value=getResult(file_path)
        result=get_className(value) 
        return result
    return None


if __name__ == '__main__':
    app.run(debug=True)