#gemini

from flask import Flask, request, render_template
import google.generativeai as genai
from dotenv import load_dotenv
import markdown2
import os
import sqlite3, datetime

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv('GEMINI_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

app = Flask(__name__)

@app.route("/", methods=["GET","POST"])
def index():
    return(render_template("index.html"))

@app.route("/gemini", methods=["GET","POST"])
def gemini():
    print("here")
    conn = sqlite3.connect("user.db")
    c = conn.cursor()
    df = c.execute("select * from users")
    r = ""
    username = ""
    for row in c:
        username = username + " | " + str(row)
    c.close()
    conn.close()
    print("username: " + username)
    return(render_template("gemini.html", r=username))

@app.route("/gemini_reply", methods=["GET","POST"])
def gemini_reply():
    q = request.form.get("q")
    print(q)
    r = model.generate_content(q)
    r = markdown2.markdown(r.text)
    return(render_template("gemini_reply.html", r=r))

@app.route("/main", methods=["GET","POST"])
def main():
    if request.method == "POST":
        username = request.form.get("q")
        t = datetime.datetime.now()

        conn = sqlite3.connect("user.db")
        c = conn.cursor()
        c.execute("insert into users values(?, ?)",(username,t))
        conn.commit()

        # Fetch username
        c.execute("SELECT name FROM users ORDER BY timestamp DESC LIMIT 1")
        latest_user = c.fetchone()[0]

        c.close()
        conn.close()
    
    #return(render_template("gemini.html", usernames=latest_user))
    return(render_template("main.html"))

@app.route("/user_log", methods=["GET","POST"])
def user_log():
    t = datetime.datetime.now()

    conn = sqlite3.connect("user.db")
    c = conn.cursor()
    # Fetch all username
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    print("here")
    c.close()
    conn.close()
    
    return(render_template("user_log.html", usernames=users))

@app.route("/delete_log", methods=["GET","POST"])
def delete_log():
    t = datetime.datetime.now()

    conn = sqlite3.connect("user.db")
    c = conn.cursor()
    # Fetch all username
    c.execute("delete from users")
    conn.commit()
    c.close()
    conn.close()
    
    return(render_template("delete_log.html"))

@app.route("/paynow", methods=["GET","POST"])
def paynow():
    return(render_template("paynow.html"))

if __name__ == "__main__":
    app.run()
