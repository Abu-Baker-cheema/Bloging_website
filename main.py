from fileinput import filename
from flask import Flask, render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import math
import json
import os
from datetime import datetime

with open('config.json') as c:
   params = json.load(c)['params']
   local_server = True
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = params['upload_location']
if (local_server):
  app.config["SQLALCHEMY_DATABASE_URI"] = params ['local_uri']
else:
  app.config["SQLALCHEMY_DATABASE_URI"] = params ['prod_uri']
db = SQLAlchemy(app)


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20),  nullable=False)
    email = db.Column(db.String(20), nullable=False)
    msg = db.Column(db.String, nullable=False)
    phone = db.Column(db.Integer, nullable=True)
    date = db.Column(db.Integer )

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tagline = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50))
    img_file = db.Column(db.String(100), nullable=False)

@app.route("/")
def home():
    posts = Posts.query.all()
    posts_per_page = int(params['no_of_posts'])
    last = math.ceil(len(posts) / posts_per_page)

    # Get page number safely, default to 1
    page = request.args.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        page = 1

    # Ensure page is within valid range
    if page < 1:
        page = 1
    elif page > last:
        page = last

    # Slice posts for current page
    start = (page - 1) * posts_per_page
    end = start + posts_per_page
    posts_to_show = posts[start:end]

    # Pagination links
    if page == 1:
        prev = "#"
        next = f"/?page={page + 1}" if last > 1 else "#"
    elif page == last:
        prev = f"/?page={page - 1}"
        next = "#"
    else:
        prev = f"/?page={page - 1}"
        next = f"/?page={page + 1}"

    return render_template("index.html", params=params, posts=posts_to_show, prev=prev, next=next)  # ✅ Make sure this matches the file name exactly
@app.route("/about")
def about():
    return render_template("about.html", params=params)
@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/dashboard",methods=['POST','GET'])
def dashboard():
    if ('user' in session and session['user'] == params['user_name']):
        posts = Posts.query.filter_by().all()
        return render_template("dashboard.html",params=params,posts=posts)
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if (username == params['user_name'] and password == params['password']):
            session['user']=username
            posts = Posts.query.filter_by().all()
            return render_template("dashboard.html",params=params,posts=posts)
    else:
       return render_template("sign_in.html", params=params)

@app.route("/edit/<string:sno>", methods=['GET', 'POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['user_name']:

        if request.method == "POST":
            title = request.form.get('title')
            t_line = request.form.get('t_line')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            # NEW POST
            if sno == '0':
                post = Posts(title=title, slug=slug, content=content,
                             tagline=t_line, date=date, img_file=img_file)
                db.session.add(post)
                db.session.commit()

                # ✅ Redirect to dashboard or to the new post
                return redirect('/dashboard')

            # UPDATE EXISTING POST
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.tagline = t_line
                post.slug = slug
                post.content = content
                post.date = date
                post.img_file = img_file

                db.session.commit()

                # ✅ Redirect back to edit page
                return redirect(f'/edit/{sno}')

        # GET request — Load post for editing
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post)

@app.route("/uploader",methods = ['GET','POST'])
def uplader():
    if ('user' in session and session['user'] == params['user_name']):
     if request.method == "POST":
        f = request.files['file1']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
        return "uploaded successfully"
@app.route("/contact",methods = ['GET','POST'])
def contact():
    if (request.method == "POST"):
        name=request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        msg = request.form.get("msg")
        entry = Contact(name=name,email=email,date = datetime.now(),phone=phone,msg=msg)
        db.session.add(entry)
        db.session.commit()
    return render_template("contact.html",params=params)
@app.route("/delete/<string:sno>", methods=['POST', 'GET'])
def delete(sno):
    if ('user' in session and session['user'] == params['user_name']):

        post = Posts.query.filter_by(sno=sno).first()   # ✅ use post

        db.session.delete(post)                         # ✅ delete post
        db.session.commit()

        return redirect('/dashboard')

@app.route("/post/<slug_post>", methods=['GET'])
def post(slug_post):
    post = Posts.query.filter_by(slug=slug_post).first()
    return render_template("post.html", params=params, post=post)

if __name__ == "__main__":
    app.run(debug=True)
