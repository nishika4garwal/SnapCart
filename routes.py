from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, Admin, User, Product, Category, Cart, Order  # Import models
from app import app  # Import the Flask app instance
from functools import wraps
from datetime import datetime


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
        if username == '' or password == '' or cpassword == '' or name == '':
            flash('All fields are required!', 'danger')
            return redirect(url_for('profile'))
        if username == 'admin' or password == 'admin':
            flash('Invalid credentials. Please try again.', 'danger')
            return redirect(url_for('profile'))
        if User.query.filter_by(username=username).first() and username != user.username:
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
    cart_item = Cart.query.filter_by(id=item_id, user_id=user_id).first()

    if cart_item:
        product = Product.query.get(cart_item.product_id)
        if product:
            product.quantity += 1  # Restore 1 item to product stock

        if cart_item.quantity > 1:
            cart_item.quantity -= 1  # Just reduce cart quantity
        else:
            db.session.delete(cart_item)  # Remove item if quantity is 1

        db.session.commit()
        flash("Item quantity updated in cart.", "success")
    else:
        flash("Item not found.", "danger")

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

    cart_item = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cart_item:
        if cart_item.quantity >= product.quantity:
            flash("Not enough stock to add more!", "danger")
            return redirect(url_for("user_home"))
        cart_item.quantity += 1
    else:
        cart_item = Cart(user_id=user_id, product_id=product_id, quantity=1)
        db.session.add(cart_item)

    product.quantity -= 1
    db.session.commit()
    flash("Product added to cart!", "success")
    return redirect(url_for("user_home"))


# --------------------- Place Order ---------------------
@app.route('/place_order')
@auth_required
def place_order():
    user_id = session['user_id']
    user = User.query.get(user_id)
    cart_items = Cart.query.filter_by(user_id=user_id).all()

    if not cart_items:
        flash('Your cart is empty!', 'info')
        return redirect(url_for('view_cart'))

    placed_orders = []
    grand_total = 0

    for item in cart_items:
        product = Product.query.get(item.product_id)
        if not product:
            flash(f"Product not found for cart item ID {item.id}", "danger")
            continue

        total_price = product.price * item.quantity
        grand_total += total_price

        order = Order(
            user_id=user_id,
            product_id=product.id,
            quantity=item.quantity,
            price=product.price,
            datetime=datetime.now()
        )
        db.session.add(order)
        placed_orders.append(order)

        # ❌ Do NOT delete product even if quantity == 0
        # ✅ It remains in DB, just with quantity 0

        db.session.delete(item)  # Remove from cart

    db.session.commit()

    flash('Order placed successfully!', 'success')
    return render_template(
        'user/order_placed.html',
        user=user,
        order_items=placed_orders,
        grand_total=grand_total
    )

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
