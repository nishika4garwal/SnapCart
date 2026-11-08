# 🛒 SnapCart – Full-Stack E-Commerce Platform

SnapCart is a full-stack e-commerce web application built using **Flask, Python, and SQLite**, featuring secure user authentication, role-based access control, product and inventory management, shopping cart functionality, and online payment integration.

The platform provides dedicated interfaces for customers and administrators, enabling seamless shopping experiences alongside centralized store and inventory management.

##  Features

### 👤 User Features

- **User Registration & Login:** Secure account registration and credential-based authentication with password hashing and session management.
- **Google Authentication:** Integrated Google OAuth 2.0 using Flask-Dance, allowing users to sign in using their Google accounts.
- **Product Catalog:** Browse products with individual product detail pages.
- **Product Search & Filtering:** Search products by name and filter listings by category.
- **Server-Side Pagination:** Paginated product listings to efficiently retrieve and display products.
- **Shopping Cart Management:** Add products to the cart, update quantities, reduce quantities, and remove items.
- **Online Payments:** Integrated Razorpay Payment Gateway for processing online transactions.
- **Checkout & Order Management:** Place orders and manage purchase information.
- **Order History:** Access previously placed orders.

### 🛠️ Admin Features

- **Admin Dashboard:** Dedicated administrative interface for managing store operations.
- **Product Management:** Add, edit, and delete products.
- **Role-Based Access Control (RBAC):** Restrict administrative functionality and protected routes based on user roles.

### 🔐 Security & Authentication

- Password hashing for secure credential storage.
- Google OAuth 2.0 authentication.
- Session-based user authentication.
- Role-based authorization for administrative operations.
- Server-side validation of user inputs.
- Protected routes for authenticated users and administrators.

### 💳 Payment Integration

- Razorpay Payment Gateway integration.
- Payment order creation through Razorpay APIs.
- Payment verification and transaction-status handling.
- Integration of payment processing into the checkout workflow.

## 🧰 Tech Stack

| Category | Technologies |
|---|---|
| **Frontend** | HTML, CSS, Bootstrap 5, Jinja2 |
| **Backend** | Python, Flask |
| **Database** | SQLite |
| **ORM** | SQLAlchemy, Flask-SQLAlchemy |
| **Database Migrations** | Flask-Migrate |
| **Authentication** | Flask-Login, Flask-Dance, Google OAuth 2.0 |
| **Payment Gateway** | Razorpay API |
| **Forms & Validation** | Flask-WTF, WTForms |
| **HTTP Requests** | Requests |
| **Environment Management** | python-dotenv |
| **Version Control** | Git, GitHub |

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd SnapCart
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

**Windows**
```bash
venv\Scripts\activate
```

**Linux / macOS**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root and configure the required credentials:

```env
SECRET_KEY=your_secret_key
SQLALCHEMY_DATABASE_URI=sqlite:///snapcart.db

GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret

RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
```

Ensure that your Google OAuth redirect URI is configured correctly in Google Cloud Console.

Use Razorpay test credentials during development. Never commit your `.env` file or expose secret keys publicly.

### 5. Initialize the Database

If using Flask-Migrate:

```bash
flask db upgrade
```

### 6. Run the Application

```bash
python app.py
```

Open your browser and navigate to:

```text
http://127.0.0.1:5000/
```

## 👩‍💻 Author

Developed as a full-stack web development project to explore backend engineering, authentication, database management, payment gateway integration, and e-commerce workflows.
Thanks <3