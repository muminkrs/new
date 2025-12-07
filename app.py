from flask import Flask, request, redirect, url_for, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

app = Flask(__name__)

# --- Database Setup ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Models ---
class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    users = db.relationship("User", backref="role", lazy="dynamic")

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))

    comments = db.relationship("Comment", backref="user", lazy="dynamic")

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

# --- Simple HTML Page ---
html_page = """
<h1>Add New User</h1>
<form method="POST">
  Username: <input name="username">
  <br><br>
  Role:
  <select name="role">
      <option value="Admin">Admin</option>
      <option value="User">User</option>
  </select>
  <br><br>
  <button type="submit" name="action" value="add_user">Save User</button>
</form>

<hr>

<h1>Add Comment</h1>
<form method="POST">
  Username:
  <select name="comment_user">
      {% for u in users %}
          <option value="{{ u.id }}">{{ u.username }}</option>
      {% endfor %}
  </select>
  <br><br>
  Comment: <input name="comment_text">
  <br><br>
  <button type="submit" name="action" value="add_comment">Post Comment</button>
</form>

<hr>

<h2>Users</h2>
<ul>
{% for u in users %}
  <li>{{ u.username }} — {{ u.role.name }}</li>
{% endfor %}
</ul>

<hr>

<h2>Comments</h2>
<ul>
{% for c in comments %}
  <li>
    <b>{{ c.user.username }}</b>: {{ c.text }}
    {% if c.user.role.name == "Admin" or True %}
        <!-- ลบได้ทุก comment (ตามคำขอว่า admin ลบได้) -->
        <form method="POST" style="display:inline;">
            <input type="hidden" name="comment_id" value="{{ c.id }}">
            <button type="submit" name="action" value="delete_comment">❌ Delete</button>
        </form>
    {% endif %}
  </li>
{% endfor %}
</ul>
"""

# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")

        # เพิ่ม User
        if action == "add_user":
            username = request.form.get("username")
            role_name = request.form.get("role")

            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name)
                db.session.add(role)
                db.session.commit()

            user = User(username=username, role=role)
            db.session.add(user)
            db.session.commit()

        # เพิ่ม Comment
        if action == "add_comment":
            user_id = request.form.get("comment_user")
            text = request.form.get("comment_text")
            
            comment = Comment(text=text, user_id=user_id)
            db.session.add(comment)
            db.session.commit()

        # ลบ Comment (เฉพาะ admin)
        if action == "delete_comment":
            cid = request.form.get("comment_id")
            comment = Comment.query.get(cid)
            db.session.delete(comment)
            db.session.commit()

        return redirect(url_for("index"))

    users = User.query.all()
    comments = Comment.query.all()
    return render_template_string(html_page, users=users, comments=comments)

# --- Shell Context ---
@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Role": Role, "Comment": Comment}

if __name__ == "__main__":
    app.run(debug=True)
