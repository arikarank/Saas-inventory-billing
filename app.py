import os
from datetime import datetime, timedelta
from decimal import Decimal
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import pandas as pd
from io import BytesIO
import json

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///saas_inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv', 'xlsx', 'xls'}

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    company_name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)
    products = db.relationship('Product', backref='user', lazy=True)
    customers = db.relationship('Customer', backref='user', lazy=True)
    invoices = db.relationship('Invoice', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    price = db.Column(db.Numeric(10, 2), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2))
    quantity = db.Column(db.Integer, default=0)
    low_stock_threshold = db.Column(db.Integer, default=10)
    image_url = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    tax_id = db.Column(db.String(50))
    credit_limit = db.Column(db.Numeric(10, 2), default=0)
    balance = db.Column(db.Numeric(10, 2), default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    invoice_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, paid, cancelled
    total_amount = db.Column(db.Numeric(10, 2), default=0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer = db.relationship('Customer', backref='invoices')
    items = db.relationship('InvoiceItem', backref='invoice', cascade='all, delete-orphan')

class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(50))  # sale, purchase, adjustment
    reference_id = db.Column(db.Integer)  # invoice_id or purchase_id
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity_change = db.Column(db.Integer)
    previous_quantity = db.Column(db.Integer)
    new_quantity = db.Column(db.Integer)
    notes = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product', backref='transactions')

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_type = db.Column(db.String(50), default='free')  # free, basic, premium
    subscription_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        company_name = request.form.get('company_name')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        user = User(email=email, company_name=company_name)
        user.set_password(password)
        
        # Create free subscription
        subscription = Subscription(
            user=user,
            plan_type='free',
            expiry_date=datetime.utcnow() + timedelta(days=30)
        )
        
        db.session.add(user)
        db.session.add(subscription)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get dashboard statistics
    total_products = Product.query.filter_by(user_id=current_user.id).count()
    total_customers = Customer.query.filter_by(user_id=current_user.id).count()
    
    # Calculate total revenue (from paid invoices)
    revenue_result = db.session.query(db.func.sum(Invoice.total_amount))\
        .filter(Invoice.user_id == current_user.id, Invoice.status == 'paid')\
        .first()
    total_revenue = float(revenue_result[0] or 0)
    
    # Get recent invoices
    recent_invoices = Invoice.query.filter_by(user_id=current_user.id)\
        .order_by(Invoice.invoice_date.desc())\
        .limit(5)\
        .all()
    
    # Get low stock products
    low_stock_products = Product.query.filter(
        Product.user_id == current_user.id,
        Product.quantity <= Product.low_stock_threshold
    ).limit(5).all()
    
    # Get pending invoices count
    pending_invoices = Invoice.query.filter_by(
        user_id=current_user.id, status='pending'
    ).count()
    
    return render_template('dashboard.html',
                         total_products=total_products,
                         total_customers=total_customers,
                         total_revenue=total_revenue,
                         pending_invoices=pending_invoices,
                         recent_invoices=recent_invoices,
                         low_stock_products=low_stock_products)

# Product Management Routes
@app.route('/products')
@login_required
def products():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    products = Product.query.filter_by(user_id=current_user.id)\
        .order_by(Product.name)\
        .paginate(page=page, per_page=per_page)
    return render_template('products.html', products=products)

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        sku = request.form.get('sku')
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        price = Decimal(request.form.get('price', 0))
        cost_price = Decimal(request.form.get('cost_price', 0))
        quantity = int(request.form.get('quantity', 0))
        low_stock_threshold = int(request.form.get('low_stock_threshold', 10))
        
        # Check if SKU already exists
        existing_product = Product.query.filter_by(sku=sku).first()
        if existing_product:
            flash('SKU already exists. Please use a different SKU.', 'danger')
            return redirect(url_for('add_product'))
        
        product = Product(
            sku=sku,
            name=name,
            description=description,
            category=category,
            price=price,
            cost_price=cost_price,
            quantity=quantity,
            low_stock_threshold=low_stock_threshold,
            user_id=current_user.id
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('products'))
    
    return render_template('add_product.html')

@app.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    
    if product.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('products'))
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.category = request.form.get('category')
        product.price = Decimal(request.form.get('price', 0))
        product.cost_price = Decimal(request.form.get('cost_price', 0))
        product.quantity = int(request.form.get('quantity', 0))
        product.low_stock_threshold = int(request.form.get('low_stock_threshold', 10))
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products'))
    
    return render_template('edit_product.html', product=product)

@app.route('/products/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    
    if product.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'success': True})

# Customer Management Routes
@app.route('/customers')
@login_required
def customers():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    customers = Customer.query.filter_by(user_id=current_user.id)\
        .order_by(Customer.name)\
        .paginate(page=page, per_page=per_page)
    return render_template('customers.html', customers=customers)

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        customer_code = request.form.get('customer_code')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        tax_id = request.form.get('tax_id')
        credit_limit = Decimal(request.form.get('credit_limit', 0))
        
        # Check if customer code already exists
        existing_customer = Customer.query.filter_by(customer_code=customer_code).first()
        if existing_customer:
            flash('Customer code already exists. Please use a different code.', 'danger')
            return redirect(url_for('add_customer'))
        
        customer = Customer(
            customer_code=customer_code,
            name=name,
            email=email,
            phone=phone,
            address=address,
            tax_id=tax_id,
            credit_limit=credit_limit,
            user_id=current_user.id
        )
        
        db.session.add(customer)
        db.session.commit()
        
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers'))
    
    return render_template('add_customer.html')

@app.route('/customers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    
    if customer.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('customers'))
    
    if request.method == 'POST':
        customer.name = request.form.get('name')
        customer.email = request.form.get('email')
        customer.phone = request.form.get('phone')
        customer.address = request.form.get('address')
        customer.tax_id = request.form.get('tax_id')
        customer.credit_limit = Decimal(request.form.get('credit_limit', 0))
        
        db.session.commit()
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customers'))
    
    return render_template('edit_customer.html', customer=customer)

@app.route('/customers/<int:id>/delete', methods=['POST'])
@login_required
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    
    if customer.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    db.session.delete(customer)
    db.session.commit()
    
    return jsonify({'success': True})

# Invoice Management Routes
@app.route('/invoices')
@login_required
def invoices():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    invoices = Invoice.query.filter_by(user_id=current_user.id)\
        .order_by(Invoice.invoice_date.desc())\
        .paginate(page=page, per_page=per_page)
    return render_template('invoices.html', invoices=invoices)

@app.route('/invoices/create', methods=['GET', 'POST'])
@login_required
def create_invoice():
    if request.method == 'POST':
        data = request.get_json()
        
        # Generate invoice number
        invoice_count = Invoice.query.filter_by(user_id=current_user.id).count()
        invoice_number = f"INV-{datetime.now().strftime('%Y%m')}-{invoice_count + 1:04d}"
        
        invoice = Invoice(
            invoice_number=invoice_number,
            customer_id=data['customer_id'],
            invoice_date=datetime.strptime(data['invoice_date'], '%Y-%m-%d'),
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d'),
            status='pending',
            total_amount=Decimal(data['total_amount']),
            tax_amount=Decimal(data.get('tax_amount', 0)),
            discount_amount=Decimal(data.get('discount_amount', 0)),
            notes=data.get('notes', ''),
            user_id=current_user.id
        )
        
        db.session.add(invoice)
        db.session.flush()  # Get invoice ID
        
        # Add invoice items
        for item in data['items']:
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=item.get('product_id'),
                description=item['description'],
                quantity=item['quantity'],
                unit_price=Decimal(item['unit_price']),
                total_price=Decimal(item['total_price'])
            )
            db.session.add(invoice_item)
            
            # Update product quantity if product_id exists
            if item.get('product_id'):
                product = Product.query.get(item['product_id'])
                if product and product.user_id == current_user.id:
                    # Create transaction record
                    transaction = Transaction(
                        transaction_type='sale',
                        reference_id=invoice.id,
                        product_id=product.id,
                        quantity_change=-item['quantity'],
                        previous_quantity=product.quantity,
                        new_quantity=product.quantity - item['quantity'],
                        user_id=current_user.id,
                        notes=f'Sale via invoice {invoice_number}'
                    )
                    db.session.add(transaction)
                    
                    # Update product quantity
                    product.quantity -= item['quantity']
        
        db.session.commit()
        
        return jsonify({'success': True, 'invoice_id': invoice.id, 'invoice_number': invoice_number})
    
    # GET request - show form
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    products = Product.query.filter_by(user_id=current_user.id).all()
    
    # Add today's date for default value
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('create_invoice.html', 
                         customers=customers, 
                         products=products,
                         today=today)

@app.route('/invoices/<int:id>')
@login_required
def view_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    
    if invoice.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('invoices'))
    
    return render_template('view_invoice.html', invoice=invoice)

@app.route('/invoices/<int:id>/pdf')
@login_required
def download_invoice_pdf(id):
    invoice = Invoice.query.get_or_404(id)
    
    if invoice.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Placeholder for PDF generation
    # In a real application, you would generate PDF here
    # For now, we'll return a JSON response
    return jsonify({
        'success': True,
        'message': 'PDF generation would be implemented here',
        'invoice_number': invoice.invoice_number
    })

@app.route('/invoices/<int:id>/update_status', methods=['POST'])
@login_required
def update_invoice_status(id):
    invoice = Invoice.query.get_or_404(id)
    
    if invoice.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    status = request.json.get('status')
    if status in ['pending', 'paid', 'cancelled']:
        invoice.status = status
        db.session.commit()
        return jsonify({'success': True, 'status': status})
    
    return jsonify({'success': False, 'message': 'Invalid status'})

# API Endpoints
@app.route('/api/products/search')
@login_required
def search_products():
    query = request.args.get('q', '')
    products = Product.query.filter(
        Product.user_id == current_user.id,
        Product.quantity > 0,  # Only show products in stock
        Product.name.ilike(f'%{query}%')
    ).limit(10).all()
    
    results = [{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'price': float(p.price),
        'quantity': p.quantity,
        'description': p.description or ''
    } for p in products]
    
    return jsonify(results)

@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    # Calculate various statistics
    total_products = Product.query.filter_by(user_id=current_user.id).count()
    total_customers = Customer.query.filter_by(user_id=current_user.id).count()
    
    # Calculate total revenue (from paid invoices)
    revenue_result = db.session.query(db.func.sum(Invoice.total_amount))\
        .filter(Invoice.user_id == current_user.id, Invoice.status == 'paid')\
        .first()
    total_revenue = float(revenue_result[0] or 0)
    
    # Calculate pending invoices
    pending_invoices = Invoice.query.filter_by(
        user_id=current_user.id, status='pending'
    ).count()
    
    # Calculate total sales
    total_sales_result = db.session.query(db.func.sum(Invoice.total_amount))\
        .filter(Invoice.user_id == current_user.id)\
        .first()
    total_sales = float(total_sales_result[0] or 0)
    
    # Get low stock count
    low_stock_count = Product.query.filter(
        Product.user_id == current_user.id,
        Product.quantity <= Product.low_stock_threshold
    ).count()
    
    return jsonify({
        'success': True,
        'total_products': total_products,
        'total_customers': total_customers,
        'total_revenue': total_revenue,
        'total_sales': total_sales,
        'pending_invoices': pending_invoices,
        'low_stock_count': low_stock_count
    })

# Import/Export
@app.route('/products/import', methods=['POST'])
@login_required
def import_products():
    if 'file' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('products'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('products'))
    
    if file and file.filename.endswith('.csv'):
        try:
            df = pd.read_csv(file)
            imported = 0
            skipped = 0
            
            for _, row in df.iterrows():
                # Check if SKU already exists
                existing_product = Product.query.filter_by(
                    sku=str(row.get('sku', '')),
                    user_id=current_user.id
                ).first()
                
                if existing_product:
                    skipped += 1
                    continue
                
                product = Product(
                    sku=str(row.get('sku', f'IMPORT-{datetime.now().timestamp()}')),
                    name=row.get('name', ''),
                    description=row.get('description', ''),
                    category=row.get('category', ''),
                    price=Decimal(str(row.get('price', 0))),
                    cost_price=Decimal(str(row.get('cost_price', 0))) if row.get('cost_price') else None,
                    quantity=int(row.get('quantity', 0)),
                    low_stock_threshold=int(row.get('low_stock_threshold', 10)),
                    user_id=current_user.id
                )
                db.session.add(product)
                imported += 1
            
            db.session.commit()
            flash(f'Successfully imported {imported} products. Skipped {skipped} duplicates.', 'success')
        except Exception as e:
            flash(f'Error importing file: {str(e)}', 'danger')
    
    return redirect(url_for('products'))

@app.route('/products/export')
@login_required
def export_products():
    products = Product.query.filter_by(user_id=current_user.id).all()
    
    data = [{
        'sku': p.sku,
        'name': p.name,
        'description': p.description or '',
        'category': p.category or '',
        'price': float(p.price),
        'cost_price': float(p.cost_price) if p.cost_price else '',
        'quantity': p.quantity,
        'low_stock_threshold': p.low_stock_threshold,
        'created_at': p.created_at.strftime('%Y-%m-%d')
    } for p in products]
    
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'products_export_{datetime.now().strftime("%Y%m%d")}.csv'
    )

# Reports
@app.route('/reports/sales')
@login_required
def sales_report():
    # Get date range from request or default to last 30 days
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
    
    # Get sales data
    invoices = Invoice.query.filter(
        Invoice.user_id == current_user.id,
        Invoice.invoice_date >= start_date,
        Invoice.invoice_date <= end_date
    ).order_by(Invoice.invoice_date).all()
    
    # Calculate totals
    total_sales = sum(invoice.total_amount for invoice in invoices)
    total_paid = sum(invoice.total_amount for invoice in invoices if invoice.status == 'paid')
    total_pending = sum(invoice.total_amount for invoice in invoices if invoice.status == 'pending')
    
    return render_template('sales_report.html',
                         invoices=invoices,
                         start_date=start_date.strftime('%Y-%m-%d'),
                         end_date=end_date.strftime('%Y-%m-%d'),
                         total_sales=total_sales,
                         total_paid=total_paid,
                         total_pending=total_pending)

# Settings
@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    company_name = request.form.get('company_name')
    
    if company_name:
        current_user.company_name = company_name
        db.session.commit()
        flash('Settings updated successfully!', 'success')
    
    return redirect(url_for('settings'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Helper functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    # Create uploads directory if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Initialize database
    init_db()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)