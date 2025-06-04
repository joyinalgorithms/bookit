from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, url_for, jsonify, flash
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import uuid
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)

db = SQL("sqlite:///ecommerce.db")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("You must be logged in to access this page.")
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@login_required
def index():
    return render_template("home.html")


@app.route("/books")
@login_required
def books():
    categories = [
        "Business & Money",
        "Computer & Technology",
        "Crafts, Hobbies, & Home",
        "History",
        "Education & Teaching",
        "Science",
        "Self Improvement"
    ]

    products_by_category = {}
    for category in categories:
        products = db.execute(
            "SELECT * FROM products WHERE category = :category", category=category)
        products_by_category[category] = products

    return render_template("books.html", products_by_category=products_by_category)


@app.route("/search")
@login_required
def search():
    query = request.args.get("query", "").strip()
    products = db.execute(
        "SELECT * FROM products WHERE name LIKE :query",
        query=f"%{query}%"
    )

    return render_template("searchresults.html", products=products, query=query)


@app.route("/cart")
@login_required
def cart():
    if 'user_id' not in session:
        return redirect('/login')

    customer_id = session['user_id']

    cart_items_query = """
        SELECT
            cart.productid,
            cart.quantity,
            cart.sessionid,
            products.name,
            products.product_image,
            products.description,
            products.price
        FROM cart
        JOIN products ON cart.productid = products.productid
        WHERE cart.customerid = ?
    """
    rows = db.execute(cart_items_query, (customer_id,))
    cart_items = []

    for row in rows:
        cart_items.append({
            'productid': row['productid'],
            'quantity': row['quantity'],
            'sessionid': row['sessionid'],
            'name': row['name'],
            'product_image': row['product_image'],
            'description': row['description'],
            'price': row['price']
        })

    total_cost_of_items = sum(item['quantity'] * item['price'] for item in cart_items)

    today = datetime.today()
    delivery_options = [
        {
            "date": (today + timedelta(days=7)).strftime("%A, %B %d"),
            "fee": 0.00,
            "label": "FREE Shipping"
        },
        {
            "date": (today + timedelta(days=3)).strftime("%A, %B %d"),
            "fee": 4.99,
            "label": "$4.99 Shipping"
        },
        {
            "date": (today + timedelta(days=1)).strftime("%A, %B %d"),
            "fee": 9.99,
            "label": "$9.99 Shipping"
        }
    ]

    return render_template(
        "cart.html",
        cart_items=cart_items,
        username=session.get("username"),
        cart_count=sum(item['quantity'] for item in cart_items),
        total_cost_of_items=total_cost_of_items,
        delivery_options=delivery_options
    )


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' in session:
        customer_id = session['user_id']
    else:
        return redirect('/login')

    try:
        product_id = int(request.form.get('product_id'))
        quantity = int(request.form.get('quantity', 1))

        if quantity <= 0:
            flash("Invalid quantity.")
            return redirect('/books')

        session_id = request.cookies.get('session')
        existing_cart_item = db.execute("""
            SELECT quantity FROM cart
            WHERE customerid = ? AND productid = ? AND sessionid = ?
        """, customer_id, product_id, session_id)

        if existing_cart_item:
            new_quantity = existing_cart_item[0]['quantity'] + quantity
            db.execute("""
                UPDATE cart
                SET quantity = ?
                WHERE customerid = ? AND productid = ? AND sessionid = ?
            """, new_quantity, customer_id, product_id, session_id)
        else:
            db.execute("""
                INSERT INTO cart (customerid, productid, quantity, sessionid)
                VALUES (?, ?, ?, ?)
            """, customer_id, product_id, quantity, session_id)
    except Exception as e:
        print(f"Error adding to cart: {e}")
        flash("Error processing your request.")
        return redirect('/books')

    return redirect('/books')


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'user_id' in session:
        customer_id = session['user_id']
    else:
        return redirect('/login')

    product_id = request.form.get('product_id')
    session_id = request.form.get('session_id')

    try:
        db.execute("""
            DELETE FROM cart
            WHERE customerid = :customer_id AND productid = :product_id AND sessionid = :session_id
        """, customer_id=customer_id, product_id=product_id, session_id=session_id)
    except Exception as e:
        print(f"Error deleting item from cart: {e}")
        return "Error processing your request", 500

    return redirect('/cart')


def get_cart_item_count(user_id):
    rows = db.execute("""
        SELECT SUM(quantity) AS total
        FROM cart
        WHERE customerid = ?
    """, user_id)
    return rows[0]['total'] if rows else 0


@app.context_processor
def inject_cart_count():
    if "user_id" in session:
        cart_count = get_cart_item_count(session["user_id"])
        return {"cart_count": cart_count}
    return {"cart_count": 0}


@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    if 'user_id' not in session:
        return redirect('/login')

    customer_id = session['user_id']
    delivery_address = request.form.get('delivery_address', '').strip()
    shipping_fee = float(request.form.get('delivery_option', ''))
    items_total = float(request.form.get('items_total', '0.00'))
    grand_total = items_total + shipping_fee
    delivery_date = request.form.get('delivery_date', '')

    if not delivery_address or not shipping_fee or items_total <= 0:
        flash("All fields must be filled correctly.")
        return redirect('/cart')

    cart_items = db.execute("""
        SELECT cart.productid, cart.quantity, products.price, products.stocks
        FROM cart
        JOIN products ON cart.productid = products.productid
        WHERE cart.customerid = ?
    """, (customer_id,))

    if not cart_items:
        flash("Your cart is empty.")
        return redirect('/cart')

    tracking_id = str(uuid.uuid4())[:8]
    print(f"Generated Tracking ID: {tracking_id}")

    order_id = db.execute("""
        INSERT INTO orders (customerid, orderdate, deliverydate, productstotal, shippingfee, grandtotal, status, delivery_address, order_tracking_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
                          customer_id, datetime.now(
                          ), delivery_date, items_total, shipping_fee, grand_total, 'pending', delivery_address, tracking_id
                          )

    for item in cart_items:
        product_id = item['productid']
        quantity = item['quantity']
        unit_price = item['price']
        subtotal = quantity * unit_price
        current_stock = item['stocks']

        if current_stock < quantity:
            flash(f"Insufficient stock for product ID {product_id}.")
            return redirect('/cart')

        db.execute("""
            INSERT INTO orderdetails (orderid, productid, quantity, unitprice, subtotal)
            VALUES (?, ?, ?, ?, ?)
        """, order_id, product_id, quantity, unit_price, subtotal)

        db.execute("""
            UPDATE products
            SET stocks = stocks - ?
            WHERE productid = ?
        """, quantity, product_id)

    db.execute("DELETE FROM cart WHERE customerid = ?", (customer_id,))
    flash("Order placed successfully!")
    return redirect('/books')


@app.route('/update_shipping_fee', methods=['POST'])
def update_shipping_fee():
    data = request.get_json()
    shipping_fee = data.get('shipping_fee', 0)
    print(f"Received shipping fee: {shipping_fee}")
    return jsonify({'success': True, 'shipping_fee': shipping_fee})


@app.route("/mypurchases")
@login_required
def purchases():
    if 'user_id' not in session:
        return redirect('/login')

    customer_id = session['user_id']
    print(f"{customer_id}")
    pending_orders = db.execute("""
        SELECT * FROM orders
        WHERE customerid = :customer_id AND status = 'pending'
    """, customer_id=customer_id)

    completed_orders = db.execute("""
        SELECT * FROM orders
        WHERE customerid = :customer_id AND status = 'completed'
    """, customer_id=customer_id)

    canceled_orders = db.execute("""
        SELECT * FROM orders
        WHERE customerid = :customer_id AND status = 'canceled'
    """, customer_id=customer_id)

    return render_template(
        "purchases.html",
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        canceled_orders=canceled_orders
    )


@app.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    customer_id = session["user_id"]

    order = db.execute("""
        SELECT * FROM orders
        WHERE orderid = :order_id AND customerid = :customer_id AND status = 'pending'
    """, order_id=order_id, customer_id=customer_id)

    if not order:
        flash("Invalid order or it cannot be canceled.")
        return redirect('/mypurchases')

    db.execute("""
        UPDATE orders
        SET status = 'canceled'
        WHERE orderid = :order_id AND customerid = :customer_id
    """, order_id=order_id, customer_id=customer_id)

    flash("Order canceled successfully.")
    return redirect('/mypurchases')


@app.route("/privacypolicy")
def privacy():
    return render_template("privacy.html")


@app.route("/termsconditions")
def terms():
    return render_template("terms.html")


@app.route("/reviews")
@login_required
def reviews():
    return render_template("reviews.html")


@app.route("/submit_review", methods=["POST"])
@login_required
def submit_review():
    """Handle review submissions."""
    if request.method == "POST":
        feedback = request.form.get("feedback").strip()
        customer_id = session["user_id"]

        if not feedback:
            return jsonify({"error": "Feedback cannot be empty"}), 400

        try:
            db.execute("""
                INSERT INTO reviews (customerid, feedback)
                VALUES (?, ?)
            """, customer_id, feedback)
            return redirect(url_for("index"))
        except Exception as e:
            print(f"Error inserting review: {e}")
            return jsonify({"error": "An error occurred while saving your review"}), 500


@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('adminlog'))
    products = db.execute("SELECT * FROM products")

    pending_orders = db.execute("""
        SELECT o.*, c.firstname || ' ' || c.lastname AS customer_name
        FROM orders o
        JOIN customers c ON o.customerid = c.customerid
        WHERE status = 'pending'
    """)

    reviews = db.execute("""
        SELECT r.*, c.firstname || ' ' || c.lastname AS customer_name
        FROM reviews r
        JOIN customers c ON r.customerid = c.customerid
    """)

    return render_template(
        "admin.html",
        products=products,
        pending_orders=pending_orders,
        reviews=reviews
    )


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/add_product', methods=['POST'])
def add_product():
    barcode = request.form['productbarcode']
    name = request.form['productname']
    category = request.form['productcategory']
    description = request.form['productdesc']
    try:
        price = float(request.form['productprice'])
    except ValueError:
        flash('Invalid price format. Please enter a valid decimal value.', 'danger')
        return redirect(url_for('admin_dashboard'))

    stocks = request.form['productstocks']
    file = request.files.get('productimage')

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(app.root_path, 'static/images/books')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        relative_path = f'static/images/books/{filename}'
    else:
        flash('Invalid file format. Only PNG, JPG, and JPEG are allowed.', 'danger')
        return redirect(url_for('admin_dashboard'))

    try:
        query = """INSERT INTO products (barcode, name, category, description, price, stocks, product_image)
                   VALUES (?, ?, ?, ?, ?, ?, ?)"""
        db.execute(query, barcode, name, category, description, price, stocks, relative_path)
        flash('Product added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding product: {e}', 'danger')

    return redirect(url_for('admin_dashboard'))


@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    dependent_cart_items = db.execute(
        "SELECT * FROM cart WHERE productid = :product_id",
        product_id=product_id
    )
    dependent_order_details = db.execute(
        "SELECT * FROM orderdetails WHERE productid = :product_id",
        product_id=product_id
    )

    if dependent_cart_items or dependent_order_details:
        flash("Cannot delete product: It has dependencies in cart or orders.")
        return redirect('/admin_dashboard')

    db.execute("DELETE FROM products WHERE productid = :product_id", product_id=product_id)
    flash("Product deleted successfully!")
    return redirect('/admin_dashboard')


@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if request.method == 'POST':
        new_stock = request.form['stocks']
        db.execute(
            "UPDATE products SET stocks = :stocks WHERE productid = :product_id",
            stocks=new_stock,
            product_id=product_id
        )
        flash("Stock updated successfully!")
        return redirect('/admin_dashboard')

    product = db.execute("SELECT * FROM products WHERE productid = :product_id",
                         product_id=product_id)
    return render_template("editproduct.html", product=product[0])


@app.route('/complete_order/<int:order_id>', methods=['POST'])
def complete_order(order_id):
    db.execute("UPDATE orders SET status = 'completed' WHERE orderid = :order_id", order_id=order_id)
    flash("Order marked as completed!")
    return redirect('/admin_dashboard')


@app.route('/acancel_order/<int:order_id>', methods=['POST'])
def acancel_order(order_id):
    db.execute("UPDATE orders SET status = 'canceled' WHERE orderid = :order_id", order_id=order_id)
    flash("Order canceled successfully!")
    return redirect('/admin_dashboard')


@app.route('/delete_review/<int:review_id>')
def delete_review(review_id):
    db.execute("DELETE FROM reviews WHERE reviewid = :review_id", review_id=review_id)
    flash("Review deleted successfully!")
    return redirect('/admin_dashboard')


@app.route("/forgotpassword")
def forgotpassword():
    return render_template("forgotpassword.html")


@app.context_processor
def inject_user():
    username = session.get("username")
    return dict(username=username)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        rpwd = request.form.get("rpwd")
        address = request.form.get("address")
        phone = request.form.get("phone")

        if not firstname or not lastname or not username or not email or not password or not rpwd:
            flash("All fields are required.")
            return redirect("/signup")
        if password != rpwd:
            flash("Passwords do not match.")
            return redirect("/signup")

        hashedpassword = generate_password_hash(password)

        try:
            db.execute(
                """
                INSERT INTO customers (firstname, lastname, username, email, hashedpassword, address, phone_number)
                VALUES (:firstname, :lastname, :username, :email, :hashedpassword, :address, :phone)
                """,
                firstname=firstname,
                lastname=lastname,
                username=username,
                email=email,
                hashedpassword=hashedpassword,
                address=address,
                phone=phone,
            )
            flash("Signup successful! You can now log in.")
            return redirect("/login")
        except:
            flash("Username or email already exists.")
            return redirect("/signup")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = db.execute("SELECT * FROM customers WHERE username = :username", username=username)
        if len(user) != 1 or not check_password_hash(user[0]["hashedpassword"], password):
            print("Invalid username or password.")
            return redirect("/login")

        session["user_id"] = user[0]["customerid"]
        session["username"] = user[0]["username"]
        print("Logged in successfully.")
        return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/adminlog", methods=["GET", "POST"])
def adminlog():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = db.execute("SELECT * FROM admin WHERE username = :username", username=username)

        if admin and check_password_hash(admin[0]['hashedpassword'], password):
            session['admin_logged_in'] = True
            session['admin_username'] = admin[0]['username']
            return redirect('/admin_dashboard')
        else:
            flash('Invalid username or password', 'error')

    return render_template('adminlogin.html')
