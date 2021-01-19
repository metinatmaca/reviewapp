from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import psycopg2
import urllib.parse as urlparse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'totallysecretkey'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.jpeg']
app.config['UPLOAD_PATH'] = 'uploads'

url = urlparse.urlparse(os.environ['DATABASE_URL'])
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port

con = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            )

cur = con.cursor()
user_id = 0
admin = 0
@app.route('/',methods=['GET','POST'])
def signup():
	if(request.method == 'POST'):
		username = request.form.get('usern')
		usersurname = request.form.get('usersurn')
		email = request.form.get('userem')
		password = request.form.get('userpass')
		cur.execute("INSERT INTO users(useremail,name,surname,password) VALUES (\'{0}\',\'{1}\',\'{2}\',\'{3}\')".format(email,username,usersurname,password))
		con.commit()
		cur.execute("SELECT user_id FROM users WHERE useremail LIKE \'{0}\'".format(email))
		global user_id
		user_id =cur.fetchall()[0][0]
		global admin
		return redirect(url_for('dashboard',admin=admin))
	return render_template('signup.html')
@app.route('/login',methods=['GET','POST'])
def login():
	global admin
	if(request.method == 'POST'):
		email = request.form.get('userem')
		password = request.form.get('userpass')
		cur.execute("SELECT user_id FROM users WHERE useremail LIKE \'{0}\' AND password = \'{1}\'".format(email,password))
		global user_id
		u_id = cur.fetchall()
		if(u_id):
			user_id = u_id[0][0]
		if(user_id):
			if (user_id == 4):
				admin = 1
			return redirect(url_for('dashboard',admin=admin))
		return render_template('login.html')
	return render_template('login.html')
@app.route('/dashboard')
def dashboard():
	cur.execute("SELECT reviewcomment FROM reviews")
	reviews = cur.fetchall()
	global admin
	return render_template('dashboard.html',reviews = reviews,admin = admin)
	
@app.route('/review')
def review():
	cur.execute("select companyname from companies")
	companies_ = cur.fetchall()
	cur.execute("select productname from products")
	products_ = cur.fetchall()
	return render_template('review.html', companies = companies_ , products = products_)
	
@app.route('/<companyx>')
def productbycompany(companyx):
	cur.execute("SELECT company_id from companies where companyname LIKE \'{0}\'".format(companyx)) 
	id = cur.fetchall()
	cur.execute("SELECT productname from products where company_id = \'{0}\'".format(id[0][0]))
	products_ = cur.fetchall()
	cur.execute("select companyname from companies")
	companies_ = cur.fetchall()
	return render_template('review.html',x = "true",company = companyx,companies = companies_, products = products_)


@app.route('/submit', methods=['POST'])
def submit():
	if request.method == 'POST':
		company = request.form.get('brand')
		product_ = request.form.get('product')
		score = request.form.get('rating')
		review = request.form.get('review')
		imagename = request.files['imagename']
		if company == '' or product_ == '':
			cur.execute("select companyname from companies")
			companies_ = cur.fetchall()
			cur.execute("select productname from products")
			products_ = cur.fetchall()
			return render_template('review.html', message='Please enter required fields',companies = companies_ , products = products_)
		cur.execute("SELECT product_id FROM products WHERE productname ILIKE '%s'"%(product_))
		p_id = cur.fetchall()
		global user_id
		cur.execute("INSERT INTO reviews(reviewcomment,reviewscore,product_id,user_id) VALUES ('{0}','{1}','{2}','{3}')".format(review,score,p_id[0][0],user_id))
		con.commit()
		cur.execute("SELECT review_id FROM reviews WHERE reviewcomment LIKE \'{0}\' AND product_id = '{1}' AND user_id = '{2}'".format(review,p_id[0][0],user_id))
		r_id = cur.fetchall()
		filename = secure_filename(imagename.filename)
		if filename != '':
			file_ext = os.path.splitext(filename)[1]
			if file_ext not in app.config['UPLOAD_EXTENSIONS']:
				return render_template('success.html')
			imagename.save(os.path.join(app.config['UPLOAD_PATH'], filename))
			path = os.path.join(app.config['UPLOAD_PATH'], filename)
			cur.execute("INSERT INTO images(imagestore,review_id,product_id) VALUES('{0}','{1}','{2}')".format(path,r_id[0][0],p_id[0][0]))
			con.commit()
		return render_template('success.html')
@app.route('/add',methods=['GET','POST'])
def add():
	if request.method == 'POST':
		companyname = request.form['companyname']
		companyemail = request.form['companyemail']
		companypw = request.form['companypw']
		cur.execute("SELECT company_id FROM companies WHERE companyname LIKE \'{0}\' OR companyemail LIKE \'{1}\'".format(companyname,companyemail))
		id = cur.fetchall()
		if id:
			return render_template('add.html',message ="Already exists")
		else:
			cur.execute("INSERT INTO companies(companyname,companyemail,password) VALUES('{0}','{1}','{2}')".format(companyname,companyemail,companypw))
			con.commit()
			global admin
			return redirect(url_for('dashboard',admin=admin))
	return render_template('add.html')
@app.route('/addpr',methods=['GET','POST'])
def addpr():
	if request.method == 'POST':
		companyname = request.form['company']
		productname = request.form['productname']
		cur.execute("SELECT product_id FROM products where productname LIKE \'{0}\'".format(productname))
		id = cur.fetchall()
		if id:
			cur.execute("select companyname from companies")
			companies_ = cur.fetchall()
			return render_template('addpr.html',message="Already exists",companies=companies_)
		else:
			cur.execute("SELECT company_id FROM companies WHERE companyname LIKE \'{0}\'".format(companyname))
			id = cur.fetchall()
			cur.execute("INSERT INTO products(productname,company_id) VALUES('{0}','{1}')".format(productname,id[0][0]))
			con.commit()
			global admin
			return redirect(url_for('dashboard',admin=admin))
	cur.execute("select companyname from companies")
	companies_ = cur.fetchall()
	return render_template('addpr.html',companies = companies_)
@app.route('/logout')
def logout():
	global user_id
	global admin
	user_id = 0
	admin = 0
	return redirect(url_for('signup'))
@app.route('/deleteuser',methods=['GET','POST'])
def deleteuser():
	if(request.method=='POST'):
		useremail = request.form['user']
		cur.execute("DELETE FROM users WHERE useremail = '{0}'".format(useremail))
		con.commit()
		global admin
		return redirect(url_for('dashboard',admin=admin))
	cur.execute("SELECT useremail FROM users")
	emails = cur.fetchall()
	return render_template('deleteuser.html',users = emails)
@app.route('/deletecompany',methods=['GET','POST'])
def deletecompany():
	if(request.method=='POST'):
		companyemail = request.form['company']
		cur.execute("DELETE FROM companies WHERE companyemail = '{0}'".format(companyemail))
		con.commit()
		global admin
		return redirect(url_for('dashboard',admin=admin))
	cur.execute("SELECT companyemail FROM companies")
	emails = cur.fetchall()
	return render_template('deletecompany.html',companies = emails)
@app.route('/deleteproduct',methods=['GET','POST'])
def deleteproduct():
	if(request.method=='POST'):
		product = request.form['product']
		cur.execute("DELETE FROM products WHERE productname = '{0}'".format(product))
		con.commit()
		global admin
		return redirect(url_for('dashboard',admin=admin))
	cur.execute("SELECT productname FROM products")
	productlist = cur.fetchall()
	return render_template('deleteproduct.html',products = productlist)
@app.route('/updateuser',methods=['GET','POST'])
def updateuser():
	if(request.method=='POST'):
		useremail = request.form['user']
		newemail = request.form['email']
		cur.execute("UPDATE users SET useremail = '{0}' WHERE useremail = '{1}'".format(newemail,useremail))
		con.commit()
		global admin
		return redirect(url_for('dashboard',admin=admin))
	cur.execute("SELECT useremail FROM users")
	emaillist = cur.fetchall()
	return render_template('updateuser.html',users = emaillist)

@app.route('/updatecompany',methods=['GET','POST'])
def updatecompany():
	if(request.method=='POST'):
		companyemail = request.form['company']
		newemail = request.form['email']
		cur.execute("UPDATE companies SET companyemail = '{0}' WHERE companyemail = '{1}'".format(newemail,companyemail))
		con.commit()
		global admin
		return redirect(url_for('dashboard',admin=admin))
	cur.execute("SELECT companyemail FROM companies")
	emaillist = cur.fetchall()
	return render_template('updatecompany.html',companies = emaillist)

@app.route('/updateproduct',methods=['GET','POST'])
def updateproduct():
	if(request.method=='POST'):
		productname = request.form['product']
		newname = request.form['name']
		cur.execute("UPDATE products SET productname = '{0}' WHERE productname = '{1}'".format(newname,productname))
		con.commit()
		global admin
		return redirect(url_for('dashboard',admin=admin))
	cur.execute("SELECT productname FROM products")
	productlist = cur.fetchall()
	return render_template('updateproduct.html',products = productlist)

if __name__ == '__main__':
    app.run()
