# SaaS Inventory & Billing System

A comprehensive web-based inventory management and billing system built with Flask. This SaaS application helps businesses manage products, customers, invoices, and generate sales reports efficiently.

## ✨ Features

- **User Authentication & Authorization**
  - Secure user registration and login
  - Session management
  - Multi-user support with data isolation

- **Product Management**
  - Add, edit, and delete products
  - SKU-based product tracking
  - Stock quantity management
  - Low stock alerts
  - Product categories and descriptions
  - Pricing and cost tracking

- **Customer Management**
  - Complete customer database
  - Customer codes for easy reference
  - Contact information management
  - Credit limit tracking
  - Account balance management

- **Invoice Generation**
  - Create professional invoices
  - Multiple items per invoice
  - Tax and discount calculations
  - Invoice status tracking (pending, paid, cancelled)
  - Automatic invoice numbering
  - Invoice PDF export (placeholder for future implementation)

- **Dashboard & Analytics**
  - Real-time statistics
  - Total products, customers, and revenue
  - Pending invoices tracking
  - Low stock alerts
  - Recent activity overview

- **Reports**
  - Sales reports with date filtering
  - Revenue analytics
  - Payment status tracking

- **Import/Export**
  - CSV product import
  - CSV product export
  - Bulk data management

- **Subscription Management**
  - Multi-tier subscription plans (Free, Basic, Premium)
  - Subscription tracking

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Saas-inventory-billing.git
   cd Saas-inventory-billing
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   On macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///saas_inventory.db
   ```

   **Important:** Change the `SECRET_KEY` to a secure random string for production use.

6. **Initialize the database**
   
   The database will be automatically created when you run the application for the first time. Alternatively, you can run:
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

7. **Create necessary directories**
   ```bash
   mkdir uploads
   ```

8. **Run the application**
   ```bash
   python app.py
   ```

9. **Access the application**
   
   Open your browser and navigate to: `http://localhost:5000`

## 📁 Project Structure

```
Saas-inventory-billing/
│
├── app.py                 # Main application file
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
│
├── instance/             # Instance-specific files (database, etc.)
│   └── saas_inventory.db # SQLite database (created on first run)
│
├── static/               # Static files
│   ├── css/
│   │   └── style.css     # Stylesheet
│   ├── js/
│   │   └── script.js     # JavaScript files
│   └── images/           # Image assets
│
├── templates/            # Jinja2 HTML templates
│   ├── layout.html       # Base template
│   ├── index.html        # Landing page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── dashboard.html    # Main dashboard
│   ├── products.html     # Product listing
│   ├── customers.html    # Customer listing
│   ├── invoices.html     # Invoice listing
│   └── ...
│
└── uploads/              # File uploads directory
```

## 🔧 Configuration

### Database

By default, the application uses SQLite for development. For production, consider using PostgreSQL or MySQL:

```env
DATABASE_URL=postgresql://user:password@localhost/saas_inventory
```

### Security

- Change the `SECRET_KEY` in production
- Use environment variables for sensitive data
- Enable HTTPS in production
- Regularly update dependencies

## 🎯 Usage

1. **Register a new account** or **login** with existing credentials
2. **Add products** to your inventory
3. **Add customers** to your database
4. **Create invoices** for your customers
5. **View dashboard** for insights and statistics
6. **Generate reports** for sales analytics

## 📊 Database Models

- **User**: User accounts and authentication
- **Product**: Inventory items with stock tracking
- **Customer**: Customer information
- **Invoice**: Invoice headers
- **InvoiceItem**: Invoice line items
- **Transaction**: Inventory transaction history
- **Subscription**: User subscription plans

## 🛠️ Technologies Used

- **Backend**: Flask 2.3.3
- **Database**: SQLAlchemy (SQLite/PostgreSQL/MySQL)
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **Data Processing**: Pandas
- **Frontend**: HTML, CSS, JavaScript
- **Template Engine**: Jinja2

## 📝 API Endpoints

### Product API
- `GET /api/products/search?q=<query>` - Search products

### Dashboard API
- `GET /api/dashboard/stats` - Get dashboard statistics

## 🔒 Security Features

- Password hashing using Werkzeug
- Session-based authentication
- CSRF protection (via Flask-WTF)
- SQL injection prevention (SQLAlchemy ORM)
- User data isolation

## 📈 Future Enhancements

- [ ] PDF invoice generation
- [ ] Email notifications
- [ ] Advanced reporting and charts
- [ ] Multi-currency support
- [ ] Barcode scanning
- [ ] Mobile app
- [ ] API for third-party integrations
- [ ] Payment gateway integration
- [ ] Automated backup system

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 👤 Author

arikaran k - [GitHub Profile](https://github.com/arikarank)

## 🙏 Acknowledgments

- Flask community for excellent documentation
- All contributors and users of this project

## 📞 Support

For support, please open an issue in the GitHub repository.

---

**Note**: This is a development version. For production deployment, ensure proper security configurations, use a production WSGI server (like Gunicorn), and set up proper error logging and monitoring.

