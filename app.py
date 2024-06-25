from flask import Flask, jsonify, render_template, request, session, redirect, url_for
import pyodbc
import pymssql
from flask_cors import CORS
import make_response

app = Flask(__name__)
app.secret_key = "123456"

# 数据库配置
DB_SERVER = "localhost"
DB_USER = "sa"
DB_PASSWORD = "password"
DB_NAME = "Blog"

# 模拟的文章数据
users = {
    "1258": {
        "password": "123456",
        "username": "somi",
        "user_info": "I am somi,a student.",
    },
    "user2": {"password": "password2"},
}
articles = {
    1: {
        "id": 1,
        "title": "第一篇文章",
        "timestamp": "2024-06-22 12:00",
        "content": "这是第一篇文章的内容 \n adasdadssada\n",
        "likes": 10,
    },
}

# 模拟的评论数据
comments = {1: [{"author": "Bob", "content": "这是一条评论"}]}


def get_db_connection():
    return pymssql.connect(
        server=DB_SERVER, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/mainpage")
def mainpage():
    user_id = session.get("user_id")
    username = session.get("username")
    if user_id and username:
        return render_template("mainpage.html", user_id=user_id, username=username)
    else:
        return redirect(url_for("index"))


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user_id = data.get("userID")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()
    # query = f'SELECT password FROM BUser WHERE userID = {0}'.format(user_id)
    # query = f'SELECT password FROM BUser WHERE userID = 80001234'
    # cursor.execute(query)
    query = "SELECT password FROM BUser WHERE userID = %s"
    cursor.execute(query, (user_id,))
    row = cursor.fetchone()
    if row:
        db_password = row[0]
        if db_password == password:
            # 登录成功
            session["username"] = "simon"
            session["user_id"] = user_id
            return jsonify({"success": True})

            # return redirect(url_for('mainpage'))

        else:
            # 登录失败
            # error_msg = "用户名或密码错误，请重新输入。"
            # return render_template('index.html', error=error_msg)
            return jsonify({"success": False})
    else:
        # 没有找到用户，提示用户不存在或输入错误
        return jsonify({"success": False})


@app.route("/register", methods=["POST"])
def register_user():
    try:
        data = request.get_json()
        user_id = data["userID"]
        username = data["username"]
        password = data["password"]
        email = data["email"]

        conn = get_db_connection()
        cursor = conn.cursor()
        # Insert new user
        query = "INSERT INTO BUser (userID, username, password, email) VALUES ('{0}', '{1}', '{2}', '{3}')".format(
            user_id, username, password, email
        )
        # cursor.execute("INSERT INTO BUser (userID, username, password, email) VALUES (%s, %s, %s, %s)",
        #               (user_id, username, password, email))
        cursor.execute(query)
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "User registered successfully!", "userID": user_id})

    except pyodbc.IntegrityError as e:
        return make_response(jsonify({"error": "UserID already exists"}), 400)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)


@app.route("/user_details")
def user_details_page():
    user_id = session.get("user_id")
    # if user_id:
    user = users.get(user_id)
    return render_template(
        "user_details.html",
        user_id=user_id,
        username=user["username"],
        password=user["password"],
        user_info=user["user_info"],
    )
    # else:
    #   return redirect(url_for('index'))


@app.route("/article_details")
def article_details():
    article = articles.get(1)
    article_comments = comments.get(1, [])
    return render_template(
        "article_details.html", article=article, comments=article_comments
    )


@app.route("/writeBlog")
def writeBlog():
    return render_template("writeBlog.html")


@app.route("/management")
def management():
    return render_template("management.html")


@app.route("/editArticle")
def editArticle():
    article = articles.get(1)
    return render_template("editArticle.html", article=article)


if __name__ == "__main__":
    app.run(debug=True)
