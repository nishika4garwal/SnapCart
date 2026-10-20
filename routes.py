from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, Admin, User, Product, Category, Cart, Order, Payment
from app import app  # Import the Flask app instance
from functools import wraps
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.exc import SQLAlchemyError
from payment import (
    KEY_ID,
    client,
    create_payment_order,
    verify_payment_signature,
    fetch_payment,
)

import os
from dotenv import load_dotenv
load_dotenv()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user_layout')
def user_layout():
    return render_template('user/user_layout.html')

############################################################### user routes #################################################

# --------------------- auth ---------------------
def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue', 'danger')
            return redirect(url_for('user_login'))
        return func(*args, **kwargs)
    return inner

# --------------------- profile ---------------------
@app.route('/profile', methods = ['POST','GET'])
@auth_required
def profile():
    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        username = request.form.get('username')
        password = request.form.get('password')
        cpassword = request.form.get('cpassword')
        name = request.form.get('name')
        if username == '' or password == '' or cpassword == '':
            flash('All fields are required!', 'danger')
            return redirect(url_for('profile'))
        if username == 'admin' or password == 'admin':
            flash('Invalid credentials. Please try again.', 'danger')
            return redirect(url_for('profile'))
        if username == user.username:
            flash('This is already your current username!', 'warning')
            return redirect(url_for('profile'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('profile'))
        if not user.check_password(cpassword):
            flash('Incorrect password', 'danger')
            return redirect(url_for('profile'))
        # update user details
        user.username = username
        user.name = name
        user.password = password
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', success = "True"))
    return render_template('user/profile.html',user = User.query.get(session['user_id']))

# --------------------- user login ---------------------
@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == '' or password == '':
            flash('Username or password cannot be empty', 'danger')
            return redirect(url_for('user_login'))
        user = User.query.filter_by(username=username).first()
        if user == 'admin' or password == 'admin':
            flash('Invalid credentials. Please try again.', 'danger')
            return redirect(url_for('user_login'))
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('user_register'))
        if not user.check_password(password):
            flash('Incorrect password')
            return redirect(url_for('user_login'))
        # login successful
        session['user_id'] = user.id  # Store user ID in session
        flash('Logged in successfully!', 'success')
        return redirect(url_for('user_login', success = "True"))

    return render_template('user/user_login.html')


# --------------------- user register ---------------------
@app.route('/user_register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        existing_user = User.query.filter_by(username=request.form['username']).first()

        if existing_user:
            flash('User already exists!', 'danger')
            return redirect(url_for('user_register'))
        
        password = request.form['password']
        name = request.form['name']
        username = request.form['username']

        if username == 'admin' or password == 'admin':
            flash('Invalid credentials. Please try again.', 'danger')
            return redirect(url_for('user_register'))

        if not username or not password or not name:
            flash('All fields are required!', 'danger')
            return redirect(url_for('user_register'))

        user = User( 
            username=username,
            password=password, 
            name=name
        )
        
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id  # Store user ID in session
        flash('User registered successfully!', 'success')
        return redirect(url_for('user_register', success = "True"))
    
    return render_template('user/user_register.html')

# --------------------- user logout ---------------------
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('user_login', success="True"))


# --------------------- View Cart ---------------------
@app.route("/cart")
@auth_required
def view_cart():
    user_id = session.get("user_id")
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    return render_template("user/cart.html", user=User.query.get(user_id), cart_items=cart_items)


# --------------------- Remove from Cart ---------------------
@app.route("/cart/remove/<int:item_id>", methods=["POST"])
@auth_required
def remove_from_cart(item_id):
    user_id = session.get("user_id")

    cart_item = Cart.query.filter_by(
        id=item_id,
        user_id=user_id
    ).first()

    if not cart_item:
        flash("Item not found.", "danger")
        return redirect(url_for("view_cart"))

    if cart_item.quantity > 1:
       
        cart_item.quantity -= 1
        flash("Item quantity decreased.", "success")
    else:
       
        db.session.delete(cart_item)
        flash("Item removed from cart.", "success")

    db.session.commit()
    return redirect(url_for("view_cart"))


# --------------------- Add to Cart ---------------------
@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
@auth_required
def add_to_cart(product_id):
    user_id = session.get("user_id")
    product = Product.query.get(product_id)

    if not product:
        flash("Product not found!", "danger")
        return redirect(url_for("user_home"))

    if product.quantity <= 0:
        flash("Sorry, the product is out of stock!", "danger")
        return redirect(url_for("user_home"))

    cart_item = Cart.query.filter_by(
        user_id=user_id,
        product_id=product_id
    ).first()

    if cart_item:
        # Cart quantity must not exceed currently available stock.
        if cart_item.quantity >= product.quantity:
            flash("Not enough stock to add more!", "warning")
            return redirect(url_for("user_home"))

        cart_item.quantity += 1
    else:
        cart_item = Cart(
            user_id=user_id,
            product_id=product_id,
            quantity=1
        )
        db.session.add(cart_item)

    db.session.commit()

    flash("Product added to cart!", "success")
    return redirect(url_for("user_home"))


# --------------------- Place Order ---------------------

@app.route("/place_order", methods=["GET", "POST"])
@auth_required
def place_order():
    return redirect(url_for("payment"))

# @app.route('/place_order')
# @auth_required
# def place_order():
#     user_id = session['user_id']
#     user = User.query.get(user_id)
#     cart_items = Cart.query.filter_by(user_id=user_id).all()

#     if not cart_items:
#         flash('Your cart is empty!', 'info')
#         return redirect(url_for('view_cart'))

#     placed_orders = []
#     grand_total = 0

#     for item in cart_items:
#         product = Product.query.get(item.product_id)
#         if not product:
#             flash(f"Product not found for cart item ID {item.id}", "danger")
#             continue

#         total_price = product.price * item.quantity
#         grand_total += total_price

#         order = Order(
#             user_id=user_id,
#             product_id=product.id,
#             quantity=item.quantity,
#             price=product.price,
#             datetime=datetime.now()
#         )

#         #will send the req to external payment api
#                 #will get an order id from the same
#                 #send it to client that opens a payment page
#                 #after successful payment, creates payment id
#                 #send order and payment id to server (here)
#                 #check if this matches what we were expecting

#         db.session.add(order)
#         placed_orders.append(order)

#         # ❌ Do NOT delete product even if quantity == 0
#         # ✅ It remains in DB, just with quantity 0

#         db.session.delete(item)  # Remove from cart

#     db.session.commit()

#     flash('Order placed successfully!', 'success')
#     return render_template(
#         'user/order_placed.html',
#         user=user,
#         order_items=placed_orders,
#         grand_total=grand_total
#     )

# --------------------- View Orders ---------------------
@app.route("/orders")
@auth_required
def view_orders():
    user_id = session.get("user_id")
    # Fetch all orders placed by the user
    orders = Order.query.filter_by(user_id=user_id).all()
    return render_template("user/orders.html", user=User.query.get(user_id), orders=orders)

# --------------------- user home ---------------------
@app.route("/user_home", methods=["GET"])
@auth_required
def user_home():
    search_query = request.args.get("search", "").strip()
    category_id = request.args.get("category_id")

    categories = Category.query.all()
    
    # Start with all products
    products_query = Product.query

    # Filter by search term if provided
    if search_query:
        products_query = products_query.filter(Product.name.ilike(f"%{search_query}%"))

    # Filter by selected category if provided
    if category_id:
        products_query = products_query.filter_by(category_id=category_id)

    products = products_query.all()

    if search_query and not products:
        flash("No products found!", "danger")
    if category_id and not products:
        flash("No products found in this category!", "danger")

    return render_template(
        "user/user_home.html",   
        categories=categories,
        products=products,
        user = User.query.get(session['user_id']),
    )


########################################################### admin routes ##########################################################
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == '' or password == '':
            flash('Username or password cannot be empty', 'danger')
            return redirect(url_for('admin_login'))
        user = Admin.query.filter_by(username=username).first()

        if username!='admin':
            flash('Incorrect username', 'danger')
            return redirect(url_for('admin_login'))
        if password!='admin':
            flash('Incorrect password', 'danger')
            return redirect(url_for('admin_login'))
        session['admin_id'] = 1
        # login successful
        flash('Logged in successfully!', 'success')
        return redirect(url_for('admin_login', success = "True"))

    return render_template('admin/admin_login.html', categories = Category.query.all())


@app.route('/admin_home')
def admin_home():
    return render_template('admin/admin_home.html')

@app.route('/admin_category')
def admin_category():
    categories = Category.query.all()
    return render_template('admin/admin_category.html', categories=categories)


@app.route('/category/add')
def add_category():
    return render_template('category/add.html', admin_id = session.get('admin_id'))

@app.route('/category/add', methods = ['POST'])
def add_category_post():
    name = request.form.get('name')
    if name == '':
        flash('Category name cannot be empty!', 'danger')
        return redirect(url_for('add_category'))
    
    existing_category = Category.query.filter_by(name=name).first()
    if existing_category:
        flash('A category with this name already exists!', 'danger')
        return redirect(url_for('add_category'))
    
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    flash('Category added successfully!', 'success')
    return redirect(url_for('add_category', success = "True"))


@app.route('/category/<int:id>/delete')
def delete_category(id):
    category = Category.query.get_or_404(id)
    if category.products:
        flash('Cannot delete category with products still assigned.', 'danger')
        return redirect(url_for('admin_category'))

    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin_category'))



@app.route('/category/<int:id>/edit')
def edit_category(id):
    return render_template('category/edit.html',admin_id = session.get('admin_id'), category = Category.query.get(id))

@app.route('/category/<int:id>/edit', methods=['POST'])
def edit_category_post(id):
    category = Category.query.get_or_404(id)
    name = request.form.get('name')

    if name == '':
        flash('Category name cannot be empty!', 'danger')
        return redirect(url_for('edit_category', id=id))

    existing_category = Category.query.filter_by(name=name).first()
    if existing_category and existing_category.id != id:
        flash('Another category with this name already exists!', 'danger')
        return redirect(url_for('edit_category', id=id))

    category.name = name
    db.session.commit()
    flash('Category updated successfully!', 'success')
    return redirect(url_for('admin_category'))


@app.route('/category/<int:id>/show')
def show_category(id):
    # Get the logged-in user from session
    admin_id = session.get('admin_id')
    category = Category.query.get(id)

    return render_template(
        'category/show.html',
        user=admin_id,
        category=category
    )

@app.route('/category/<int:category_id>/add-product', methods=['GET'])
def add_product(category_id):
    categories = Category.query.all()
    return render_template(
        'product/add.html',
        admin_id = session.get('admin_id'),
        product=None,
        category_id=category_id,
        categories=categories
    )

@app.route('/category/<int:category_id>/add-product', methods=['POST'])
def add_product_post(category_id):
    name = request.form.get('name')
    price = float(request.form.get('price'))
    man_date_str = request.form.get("man_date")
    man_date = datetime.strptime(man_date_str, '%Y-%m-%d').date()
    quantity = int(request.form.get('quantity'))

    # Create new product and associate it with category
    new_product = Product(name=name, price=price, man_date=man_date, category_id=category_id, quantity=quantity)
    db.session.add(new_product)
    db.session.commit()

    flash('Product added successfully!', 'success')
    return redirect(url_for('show_category', id = category_id))


@app.route('/product/<int:id>/edit')
def edit_product(id):
    product = Product.query.get(id)
    categories = Category.query.all()
    next_page = request.args.get('next')
    return render_template('product/edit.html', admin_id = session.get('admin_id'), product = product, categories = categories, next = next_page)

@app.route('/product/<int:id>/edit', methods=['POST'])
def edit_product_post(id):
    product = Product.query.get_or_404(id)
    next_page = request.form.get('next')

    product.name = request.form.get('name')
    product.price = float(request.form.get('price'))
    product.quantity = int(request.form.get('quantity'))  # ✅ Include quantity update
    man_date_str = request.form.get("man_date")
    product.man_date = datetime.strptime(man_date_str, '%Y-%m-%d').date()

    db.session.commit()
    flash('Product updated successfully!', 'success')

    if next_page:
        return redirect(url_for(next_page))
    return redirect(url_for('admin_product'))




@app.route('/product/<int:id>/delete')
def delete_product(id):
    product = Product.query.get_or_404(id)
    category_id = product.category.id

    # Check if product is part of any cart
    in_cart = Cart.query.filter_by(product_id=id).first()
    ordered = Order.query.filter_by(product_id=id).first()

    if in_cart or ordered:
        flash('Product cannot be deleted — it is currently in a cart or has been ordered.', 'danger')
        return redirect(url_for('show_category', id=category_id))

    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')

    next_page = request.args.get('next')

    if next_page == 'admin_product':
        return redirect(url_for('admin_product'))
    elif next_page == 'show_category':
        return redirect(url_for('show_category', id=category_id))

    return redirect(url_for('admin_product'))

    

@app.route('/admin_product')
def admin_product():
    products = Product.query.options(db.joinedload(Product.category)).all()
    return render_template('admin/admin_product.html', products=products)

############################## external payment gateway ##########################################

@app.route("/payment", methods=["GET"])
@auth_required
def payment():
    user_id = session["user_id"]

    cart_items = Cart.query.filter_by(user_id=user_id).all()

    if not cart_items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("cart"))

    total = Decimal("0.00")

    for item in cart_items:
        product = Product.query.get(item.product_id)

        if product is None or item.quantity <= 0:
            flash("Your cart contains an invalid item.", "danger")
            return redirect(url_for("cart"))

        total += (
            Decimal(str(product.price)) * item.quantity
        )

    total = total.quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    amount_paise = int(total * 100)

    try:
        razorpay_order = create_payment_order(amount_paise)

        payment_record = Payment(
            user_id=user_id,
            razorpay_order_id=razorpay_order["id"],
            amount_paise=amount_paise,
            status="created",
        )

        db.session.add(payment_record)
        db.session.commit()

    except Exception:
        db.session.rollback()
        app.logger.exception("Unable to create Razorpay order")
        flash("Could not start payment. Please try again.", "danger")
        return redirect(url_for("cart"))

    return render_template(
        "payment.html",
        key_id=KEY_ID,
        razorpay_order_id=razorpay_order["id"],
        amount_paise=amount_paise,
        total=total,
    )

@app.route("/verify-payment", methods=["POST"])
@auth_required
def verify_payment():
    user_id = session["user_id"]
    data = request.get_json(silent=True) or {}

    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")

    if not all([
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature,
    ]):
        return jsonify({
            "success": False,
            "message": "Missing payment verification details.",
        }), 400

    payment_record = Payment.query.filter_by(
        razorpay_order_id=razorpay_order_id,
        user_id=user_id,
    ).with_for_update().first()

    if not payment_record:
        return jsonify({
            "success": False,
            "message": "Payment order not found.",
        }), 404

    # Make repeated callbacks safe.
    if payment_record.status == "paid":
        return jsonify({
            "success": True,
            "message": "Order already confirmed.",
        }), 200

    if payment_record.status != "created":
        return jsonify({
            "success": False,
            "message": "This payment attempt cannot be processed.",
        }), 400

    if not verify_payment_signature(
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature,
    ):
        return jsonify({
            "success": False,
            "message": "Invalid payment signature.",
        }), 400

    try:
        # Confirm the payment with Razorpay's server, not the browser.
        razorpay_payment = fetch_payment(razorpay_payment_id)

        if (
            razorpay_payment.get("order_id") != razorpay_order_id
            or razorpay_payment.get("amount") != payment_record.amount_paise
            or razorpay_payment.get("currency") != "INR"
        ):
            return jsonify({
                "success": False,
                "message": "Payment details do not match the order.",
            }), 400

        if razorpay_payment.get("status") != "captured":
            return jsonify({
                "success": False,
                "message": (
                    "Payment is not captured yet. "
                    "Please check its status before retrying."
                ),
            }), 400

        cart_items = Cart.query.filter_by(user_id=user_id).all()

        if not cart_items:
            return jsonify({
                "success": False,
                "message": "Your cart is empty. Contact support to resolve this payment.",
            }), 409

        # Recalculate the total from current database values.
        current_total = Decimal("0.00")

        for item in cart_items:
            product = Product.query.get(item.product_id)

            if product is None or item.quantity <= 0:
                return jsonify({
                    "success": False,
                    "message": "A cart item is no longer valid.",
                }), 409

            current_total += Decimal(str(product.price)) * item.quantity

        current_total = current_total.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if int(current_total * 100) != payment_record.amount_paise:
            return jsonify({
                "success": False,
                "message": (
                    "Cart total changed after checkout. "
                    "Contact support before retrying."
                ),
            }), 409

        # First validate that every cart item is available.
        products = {}

        for item in cart_items:
            product = Product.query.get(item.product_id)

            if product is None:
                return jsonify({
                    "success": False,
                    "message": "A product in your cart no longer exists."
                }), 409

            if item.quantity > product.quantity:
                return jsonify({
                    "success": False,
                    "message": (
                        f"Insufficient stock for {product.name}. "
                        "Please update your cart."
                    )
                }), 409

            products[item.product_id] = product
        
        # Only after all items pass validation, update inventory and orders.
        for item in cart_items:
            product = products[item.product_id]

            # Reduce available stock
            product.quantity -= item.quantity

            # Create an order for each cart item
            db.session.add(Order(
                user_id=user_id,
                product_id=product.id,
                quantity=item.quantity,
                price=product.price,
                datetime=datetime.utcnow()
            ))

            # Remove this item from the cart
            db.session.delete(item)

        payment_record.razorpay_payment_id = razorpay_payment_id
        payment_record.status = "paid"

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Payment successful! Your order is confirmed.",
            "redirect_url": url_for("view_orders"),
        }), 200

    except Exception:
        db.session.rollback()
        app.logger.exception("Payment verification/finalization failed")

        return jsonify({
            "success": False,
            "message": (
                "We could not confirm the order. "
                "If your payment was deducted, contact support with your payment ID."
            ),
        }), 500
