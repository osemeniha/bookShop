import hashlib
import sqlite3

from flask import *

app = Flask(__name__)
app.secret_key = 'random string'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def getLoginDetails():
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        if 'email' not in session:
            loggedIn = False
            firstName = ''
            noOfItems = 0
        else:
            loggedIn = True
            cur.execute("SELECT userId, firstName FROM users WHERE email = '" + session['email'] + "'")
            userId, firstName = cur.fetchone()
            cur.execute("SELECT sum(count) FROM basket WHERE userId = " + str(userId) + " AND statusId = 1")
            items = cur.fetchone()[0]
            if items is None:
                noOfItems = 0
            else:
                noOfItems = items
    conn.close()
    return (loggedIn, firstName, noOfItems)


@app.route("/")
def root():
    loggedIn, firstName, noOfItems = getLoginDetails()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description FROM products')
        itemData = cur.fetchall()
        cur.execute('SELECT categoryId, name FROM categories')
        categoryData = cur.fetchall()
    itemData = parse(itemData)
    return render_template('home.html', itemData=itemData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems,
                           categoryData=categoryData)


@app.route("/displayCategory")
def displayCategory():
    loggedIn, firstName, noOfItems = getLoginDetails()
    categoryId = request.args.get("categoryId")
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT products.productId, products.name, products.price, categories.name FROM products, categories WHERE products.categoryId = categories.categoryId AND categories.categoryId = " + categoryId)
        data = cur.fetchall()
    conn.close()
    categoryName = data[0][3]
    data = parse(data)
    return render_template('displayCategory.html', data=data, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems, categoryName=categoryName)


@app.route("/search", methods=["POST"])
def search():
    loggedIn, firstName, noOfItems = getLoginDetails()
    search = request.form['search']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT productId, name, price, description FROM products WHERE name like '%'||?||'%'", (search,))
        searchData = cur.fetchall()
    conn.close()
    searchData = parse(searchData)
    return render_template("search.html", searchData=searchData, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems)


@app.route("/account/profile")
def profileHome():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT userId, email, firstName, lastName, country, city, address, zipcode, phone FROM users WHERE email = '" +
            session['email'] + "'")
        profileData = cur.fetchone()
    conn.close()
    return render_template("profileHome.html", profileData=profileData, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems)


@app.route("/orders")
def orders():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + session['email'] + "'")
        userId = cur.fetchone()[0]
        cur.execute("SELECT orderId FROM orders WHERE userId = " + str(userId))
        orders = cur.fetchall()
    conn.close()
    return render_template("orders.html", orders=orders, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)


@app.route("/order")
def order():
    loggedIn, firstName, noOfItems = getLoginDetails()
    orderId = request.args.get('orderId')
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT products.productId, products.name, products.price, basket.count FROM basket LEFT JOIN products ON products.productId = basket.productId WHERE basket.orderId = " + str(
                orderId) + " AND basket.statusId = 2")
        products = cur.fetchall()
        totalPrice = 0.0
        for row in products:
            totalPrice += row[2] * row[3]
    conn.close()
    return render_template("order.html", products=products, totalPrice=totalPrice, loggedIn=loggedIn,
                           firstName=firstName, noOfItems=noOfItems)


@app.route("/account/profile/edit")
def editProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT userId, email, firstName, lastName, country, city, address, zipcode, phone FROM users WHERE email = '" +
            session['email'] + "'")
        profileData = cur.fetchone()
    conn.close()
    return render_template("editProfile.html", profileData=profileData, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems)


@app.route("/account/profile/changePassword", methods=["GET", "POST"])
def changePassword():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    if request.method == "POST":
        oldPassword = request.form['oldpassword']
        oldPassword = hashlib.md5(oldPassword.encode()).hexdigest()
        newPassword = request.form['newpassword']
        newPassword = hashlib.md5(newPassword.encode()).hexdigest()
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId, password FROM users WHERE email = '" + session['email'] + "'")
            userId, password = cur.fetchone()
            if (password == oldPassword):
                try:
                    cur.execute("UPDATE users SET password = ? WHERE userId = ?", (newPassword, userId))
                    conn.commit()
                    msg = "Изменения успешны"
                except:
                    conn.rollback()
                    msg = "Failed"
                return render_template("changePassword.html", msg=msg)
            else:
                msg = "Wrong password"
        conn.close()
        return render_template("changePassword.html", msg=msg)
    else:
        return render_template("changePassword.html")


@app.route("/updateProfile", methods=["GET", "POST"])
def updateProfile():
    if request.method == 'POST':
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        country = request.form['country']
        city = request.form['city']
        address = request.form['address1']
        zipcode = request.form['zipcode']
        phone = request.form['phone']
        with sqlite3.connect('database.db') as con:
            try:
                cur = con.cursor()
                cur.execute(
                    'UPDATE users SET firstName = ?, lastName = ?, country = ?, city = ?, address = ?, zipcode = ?, phone = ? WHERE email = ?',
                    (firstName, lastName, country, city, address, zipcode, phone, email))

                con.commit()
                msg = "Изменения сохранены"
            except:
                con.rollback()
                msg = "Error occured"
        con.close()
        return redirect(url_for('profileHome'))


@app.route("/loginForm")
def loginForm():
    if 'email' in session:
        return redirect(url_for('root'))
    else:
        return render_template('login.html', error='')


@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            error = 'Неправильный e-mail или пароль'
            return render_template('login.html', error=error)


@app.route("/productDescription")
def productDescription():
    loggedIn, firstName, noOfItems = getLoginDetails()
    productId = request.args.get('productId')
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description FROM products WHERE productId = ' + productId)
        productData = cur.fetchone()
        cur.execute(
            'SELECT comments.body FROM comments, products WHERE products.productId = comments.productId AND comments.productID = ' + str(
                productData[0]))
        #comments = cur.fetchall()
        comments = [r[0] for r in cur]
    conn.close()
    return render_template("productDescription.html", data=productData, comments=comments, loggedIn=loggedIn,
                           firstName=firstName, noOfItems=noOfItems)


@app.route("/productDescription/addComment", methods=['GET', 'POST'])  # сохранение отзыва
def addComment():
    loggedIn, firstName, noOfItems = getLoginDetails()
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    else:
        body = request.form['comment']
        productId = int(request.args.get('productId'))
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute(
                'SELECT productId FROM products WHERE productId = ' + str(productId))
            productId = cur.fetchone()[0]
            cur.execute("SELECT userId FROM users WHERE email = '" + session['email'] + "'")
            userId = cur.fetchone()[0]
            cur.execute("INSERT INTO comments (body, userId, productId) VALUES (?, ?, ?)", (body, userId, productId))
            conn.commit()
        conn.close()
        return redirect(url_for('productDescription', productId=productId))


@app.route("/addToBasket")
def addToBasket():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    else:
        productId = int(request.args.get('productId'))
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = '" + session['email'] + "'")
            userId = cur.fetchone()[0]
            cur.execute("SELECT count, statusId FROM basket WHERE userId = " + str(
                userId) + " AND statusID = 1 AND productId = " + str(productId))
            info = cur.fetchone()
            if info is not None:
                count = info[0]
                status = info[1]
                if status == 1:
                    cur.execute(
                        "UPDATE basket SET count = ? WHERE userId = ? AND basket.statusID = 1 AND productId = " + str(
                            productId), (count + 1, userId))
                    conn.commit()
            else:
                cur.execute("INSERT INTO basket (userId, productId, count, statusId) VALUES (?, ?, ?, ?)",
                            (userId, productId, 1, 1))
                conn.commit()
        conn.close()
        return redirect(url_for('productDescription', productId=productId))


@app.route("/basket")
def basket():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        cur.execute(
            "SELECT products.productId, products.name, products.price, basket.count FROM basket LEFT JOIN products ON products.productId = basket.productId WHERE basket.userId = " + str(
                userId) + " AND basket.statusId = 1")
        products = cur.fetchall()
    totalPrice = 0.0
    for row in products:
        totalPrice += row[2] * row[3]
    return render_template("basket.html", products=products, totalPrice=totalPrice, loggedIn=loggedIn,
                           firstName=firstName, noOfItems=noOfItems)


@app.route("/remove")
def remove():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    email = session['email']
    productId = int(request.args.get('productId'))
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        cur.execute("SELECT id, userId, productId, count, statusId FROM basket WHERE userId = " + str(
            userId) + " AND  productId = " + str(productId) + " AND statusId = 1")
        info = cur.fetchone()
        product = info[0]
        count = info[3]
        if count == 1:
            cur.execute("DELETE FROM basket WHERE id = " + str(product))
            conn.commit()
        else:
            cur.execute(
                "UPDATE basket SET count = ? WHERE userId = ? AND basket.statusID = 1 AND basket.productId = ?",
                (count - 1, userId, productId))
            conn.commit()
    conn.close()
    return redirect(url_for('basket'))


@app.route("/add")
def add():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    email = session['email']
    productId = int(request.args.get('productId'))
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        cur.execute("SELECT count FROM basket WHERE userId = " + str(userId) + " AND  productId = " + str(
            productId) + " AND statusId = 1")
        info = cur.fetchone()
        count = info[0]
        cur.execute(
            "UPDATE basket SET count = ? WHERE userId = ? AND basket.statusID = 1 AND basket.productId = ?",
            (count + 1, userId, productId))
        conn.commit()
    conn.close()
    return redirect(url_for('basket'))


#
# @app.route("/removeFromBasket")
# def removeFromBasket():
#     if 'email' not in session:
#         return redirect(url_for('loginForm'))
#     email = session['email']
#     productId = int(request.args.get('productId'))
#     with sqlite3.connect('database.db') as conn:
#         cur = conn.cursor()
#         cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
#         userId = cur.fetchone()[0]
#         cur.execute("SELECT id, userId, productId FROM basket WHERE userId = " + str(userId) + " AND  productId = " + str(productId))
#         product = cur.fetchone()[0]
#         cur.execute("DELETE FROM basket WHERE id = " + str(product))
#         conn.commit()
#     conn.close()
#     return redirect(url_for('root'))


@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))


def is_valid(email, password):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('SELECT email, password FROM users')
    data = cur.fetchall()
    for row in data:
        if row[0] == email and row[1] == hashlib.md5(password.encode()).hexdigest():
            return True
    return False


@app.route("/checkout", methods=['GET', 'POST'])
def payment():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']

    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT userId FROM users WHERE email = '" + email + "'")
        userId = cur.fetchone()[0]
        cur.execute('INSERT INTO orders(userId) VALUES (' + str(userId) + ')')
        conn.commit()
        cur.execute("SELECT MAX(orderId) FROM orders WHERE userId = " + str(userId))
        orderId = cur.fetchone()[0]
        cur.execute("UPDATE basket SET statusId = 2, orderId = ? WHERE userId = ? AND orderId = 0",
                    (str(orderId), str(userId)))
        conn.commit()
        cur.execute(
            "SELECT products.productId, products.name, products.price, basket.count FROM basket LEFT JOIN products ON products.productId = basket.productId WHERE basket.orderId = " + str(
                orderId) + " AND basket.statusId = 2")
        products = cur.fetchall()
    totalPrice = 0.0
    for row in products:
        totalPrice += row[2] * row[3]
    return render_template("checkout.html", products=products, totalPrice=totalPrice, loggedIn=loggedIn,
                           firstName=firstName, noOfItems=noOfItems)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Parse form data
        password = request.form['password']
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        country = request.form['country']
        city = request.form['city']
        address = request.form['address1']
        zipcode = request.form['zipcode']
        phone = request.form['phone']

        with sqlite3.connect('database.db') as con:
            try:
                cur = con.cursor()
                cur.execute(
                    'INSERT INTO users (password, email, firstName, lastName, country, city, address, zipcode, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (hashlib.md5(password.encode()).hexdigest(), email, firstName, lastName, country, city, address,
                     zipcode, phone))

                con.commit()

                msg = "Регистрация прошла успешно"
            except:
                con.rollback()
                msg = "Ошибка при регистрации"
        con.close()
        return render_template("login.html", error=msg)


@app.route("/registerationForm")
def registrationForm():
    return render_template("register.html")


def parse(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(7):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans


if __name__ == '__main__':
    app.run(debug=True)
