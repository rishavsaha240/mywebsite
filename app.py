from flask import Flask, render_template, request, redirect, jsonify, session, send_from_directory
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
from flask_sitemap import Sitemap
import bcrypt
import logging, sys

app = Flask(__name__, static_folder='static')
ext = Sitemap(app=app)
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.ERROR)

app.secret_key = "rishavsaha-mywebsite"

app.config["MONGO_URI"] = "mongodb+srv://iamtheuser:rishavbubul5240@rishav-saha-ucz6t.mongodb.net/mywebsite?retryWrites=true&w=majority"
mongo = PyMongo(app)

@app.route("/robots.txt")
def robots():
  return (
    """User-agent: *
    Disallow: /admin/
    Sitemap: http://rishavsaha.herokuapp.com/sitemap.xml"""
    )
  # return send_from_directory(app.static_folder, request.path[1:])

@app.route("/BingSiteAuth.xml")
def static_from_root():
  return send_from_directory(app.static_folder, request.path[1:])

@app.route("/", methods = ["GET"])
def home():
  return render_template("home.html")

@ext.register_generator
def home():
  yield 'home', {}

@app.route("/aboutme", methods = ["GET"])
def aboutme():
  return render_template("aboutme.html")

@app.route("/skills", methods = ["GET"])
def skills():
  return render_template("skills.html")

@app.route("/projects", methods = ["GET"])
def projects():
  return render_template("projects.html")

@app.route("/contactme", methods = ["GET", "POST"])
def contactme():
  if request.method == "POST":
    name = request.form["name"]
    email = request.form["email"]
    message = request.form["message"]
    try:
      mongo.db.contactme.insert_one({"name": name, "email": email, "message": message, "created_time":datetime.utcnow(), "read": False})
      return redirect("/contactme")
    except:
      return "There was an issue sending your message"
  else:
    return render_template("contactme.html")

@app.route("/admin", methods = ["GET", "POST"])
def admin_login_page():
  if request.method == "POST":
    email = request.form["email"]
    admin_user = mongo.db.users.find_one({"email": email})
    if admin_user:
      if bcrypt.hashpw(request.form["login-password"].encode("utf-8"), admin_user["password"]) == admin_user["password"]:
        session["email"] = request.form["email"]
        return redirect("/admin/messages")
      else:
        return "Wrong emailid/password!"
    else:
      return "No user found!"
  else:
    return render_template("login.html")

# @app.route("/admin/dontcomehere", methods = ["GET", "POST"])
# def registration():
#   if request.method == "POST":
#     if (request.form["password"] == request.form["re-password"]):
#       existing_user = mongo.db.users.find_one({"email": request.form["email"]})
#       if existing_user is None:
#         hasdedpass = bcrypt.hashpw(request.form["password"].encode("utf-8"), bcrypt.gensalt())
#         try:
#           mongo.db.users.insert_one({"email": request.form["email"], "password": hasdedpass})
#           return redirect("/admin/dontcomehere")
#         except:
#           return "Issue connecting to database!"
#       else:
#         return "User already exists!"
#     else:
#       return "Passwords do not match!"
#   else:
#     return render_template("register.html")

@app.route("/admin/messages", methods = ["GET", "POST"])
def admin_messages():
  if "email" in session:
    msgs_data = mongo.db.contactme.find().sort("created_time", -1)
    msgs = []
    unread = 0
    for x in msgs_data:
      msgs.append(x)
      if x["read"] == False:
        unread += 1
    return render_template("messages.html", msgs = msgs, total = len(msgs), unread = unread)
  else:
    return "No authorized"

@app.route("/delete/<string:_id>")
def delete(_id):
  msg_to_delete = mongo.db.contactme.find_one({"_id": ObjectId(_id)})
  if msg_to_delete:
    mongo.db.contactme.delete_one(msg_to_delete)
    return redirect("/admin/messages")
  else:
    return "Issue in deleting message!"

@app.route("/markread/<string:_id>")
def markread(_id):
  msg_to_mark = mongo.db.contactme.find_one({"_id": ObjectId(_id)})
  new_msg = {"$set": {"read": True}}
  if msg_to_mark:
    mongo.db.contactme.update_one(msg_to_mark, new_msg)
    return redirect("/admin/messages")
  else:
    return "Issue in marking as Read!"

@app.route("/logout", methods = ["GET"])
def logout():
  if "email" in session:
    session.pop("email", None)
    return redirect("/admin")
  else:
    return "Already logged out!"

@app.errorhandler(404)
def not_found(e):
  return render_template("404.html")

if __name__ == "__main__":
  app.run(threaded=True)
