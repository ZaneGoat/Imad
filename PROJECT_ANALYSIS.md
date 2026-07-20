# GESTION SPA - PROJECT ANALYSIS & DOCUMENTATION

## 📋 PROJECT OVERVIEW

**Project Name:** Gestion Spa  
**Type:** Desktop Application (GUI)  
**Purpose:** Spa Management System for clients, employees, services, appointments, payments, and reporting  
**Technology Stack:** Python + Tkinter + SQLite  
**Status:** Functional with testing framework

---

## 🏗️ ARCHITECTURE

### Directory Structure
```
Imad/
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies (pytest only)
├── README.md                  # Project documentation
├── app/
│   ├── __init__.py
│   ├── config.py             # Configuration & path management
│   ├── core/
│   │   ├── __init__.py
│   │   └── database.py       # SQLite database operations
│   ├── ui/                   # User Interface (Tkinter frames)
│   │   ├── __init__.py
│   │   ├── auth.py           # Login & user registration
│   │   ├── dashboard.py      # Main dashboard with KPIs
│   │   ├── client.py         # Client CRUD operations
│   │   ├── employe.py        # Employee management
│   │   ├── service.py        # Service catalog management
│   │   ├── rendezvous.py     # Appointment booking & management
│   │   ├── paiement.py       # Payment processing
│   │   ├── reports.py        # Analytics & reporting
│   │   ├── settings.py       # Application settings & admin panel
│   │   └── ui_utils.py       # Utility components (forms, trees, validators)
│   └── utils/
│       ├── __init__.py
│       └── pdf_utils.py      # PDF generation (receipts, reports)
├── data/
│   ├── database/spa.db       # SQLite main database
│   ├── backups/              # Timestamped database backups
│   └── pdf/                  # Generated PDF files
└── tests/
    ├── __init__.py
    ├── run_tests.py          # Test runner
    ├── test_backup.py        # Backup/restore tests
    ├── test_database.py      # Database operations tests
    ├── test_paiement.py      # Payment tests
    └── TESTS.md              # Test documentation
```

---

## 🛠️ FRAMEWORKS & TECHNOLOGIES

### Core Dependencies
- **Tkinter** (built-in) - GUI framework
- **SQLite3** (built-in) - Database engine
- **Standard Library:**
  - `hashlib` - Password hashing (SHA256)
  - `datetime` - Date/time operations
  - `os`, `shutil` - File operations
  - `re` - Regular expressions
  - `calendar` - Calendar utilities
  - `textwrap` - Text formatting

### Optional Dependencies
- **pytest** 8.3.3 - Unit testing framework

### Custom UI Components
- Custom Tkinter styles (dark/light theme)
- Modern scrollbars, tables (Treeview), forms
- Modal dialogs for CRUD operations
- Accordion-style settings panels

---

## 🗄️ DATABASE SCHEMA

### Relational Diagram
```
┌──────────────┐
│   client     │
├──────────────┤
│ id_client (PK)
│ nom
│ prenom
│ telephone
│ email
│ adresse
│ date_inscription
└──────────────┘
       ↑
       │ (1)
       │
   (N) │─────────────────┐
       │                 │
       ↓                 ↓
┌──────────────┐  ┌──────────────────┐
│ rendez_vous  │  │   paiement       │
├──────────────┤  ├──────────────────┤
│ id_rdv (PK)  │  │ id_paiement (PK) │
│ id_client(FK)│  │ id_client (FK)   │
│ id_service(FK)  │ id_rdv (FK)      │
│ id_employe(FK)  │ montant          │
│ date_rdv     │  │ methode_paiement │
│ heure_rdv    │  │ date_paiement    │
│ statut       │  └──────────────────┘
└──────────────┘         ↓
       ↑                 │
       │         ┌───────────────┐
       │         │ paiement_rdv  │
       │         ├───────────────┤
       │         │ id_paiement(FK)
       └─────────┤ id_rdv (FK)   │
                 └───────────────┘

┌──────────────┐
│  service     │
├──────────────┤
│ id_service(PK)
│ nom_service
│ description
│ prix
│ duree_minutes
└──────────────┘

┌──────────────┐
│  employe     │
├──────────────┤
│ id_employe(PK)
│ nom
│ prenom
│ specialite
│ telephone
│ salaire
│ disponibilite
└──────────────┘

┌──────────────┐
│   users      │
├──────────────┤
│ id_user (PK) │
│ username     │
│ password     │ (SHA256 hashed)
│ role         │ (Admin/Receptionist)
│ remember_me  │
│ theme        │
│ font_scale   │
│ language     │
└──────────────┘

┌──────────────┐
│ app_settings │
├──────────────┤
│ key (PK)     │
│ value        │
└──────────────┘
```

### Tables Description

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| **client** | Customer profiles | id_client, nom, prenom, telephone, email, adresse, date_inscription |
| **service** | Service catalog | id_service, nom_service, description, prix, duree_minutes |
| **employe** | Staff management | id_employe, nom, prenom, specialite, telephone, salaire, disponibilite |
| **rendez_vous** | Appointment bookings | id_rdv, id_client, id_service, id_employe, date_rdv, heure_rdv, statut |
| **paiement** | Payment records | id_paiement, id_client, id_rdv, montant, methode_paiement, date_paiement |
| **paiement_rdv** | Payment-Appointment junction | id_paiement, id_rdv (many-to-many) |
| **users** | User accounts | id_user, username, password, role, theme, font_scale, language |
| **app_settings** | Configuration storage | key, value (spa name, hours, holidays, etc.) |

---

## 🎯 MAIN FUNCTIONS & MODULES

### 1. **main.py** - Application Entry Point

**Class:** `SpaApp(tk.Tk)`

**Key Methods:**
- `__init__()` - Initializes app, sets window properties, loads remembered user
- `colors(theme)` - Returns color palette (light/dark themes)
- `font(size, weight)` - Generates fonts with scaling
- `configure_style(theme, font_scale)` - Sets up TTK styling
- `show_app(user)` - Displays main app after login
- `show_login()` - Displays login screen

**Features:**
- Window: 1260x760 px (min 1100x650)
- Dark/Light theme support
- Font scaling support
- Auto-login with "Remember Me" functionality
- Navigation tabs for all modules

---

### 2. **app/config.py** - Configuration Management

**Functions:**
- `ensure_data_dirs()` - Creates necessary directories (database/, backups/, pdf/)

**Constants:**
- `ROOT_DIR` - Project root
- `DATA_DIR` - Data directory path
- `DB_DIR` - Database directory
- `BACKUP_DIR` - Backups directory
- `PDF_DIR` - PDF output directory
- `DB_PATH` - Path to spa.db

---

### 3. **app/core/database.py** - Database Operations

**Class:** `Database`

#### Connection Methods:
- `connect()` - Opens SQLite connection with row factory & foreign keys enabled
- `execute(query, params)` - Execute INSERT/UPDATE/DELETE (returns lastrowid)
- `fetchall(query, params)` - Fetch multiple rows
- `fetchone(query, params)` - Fetch single row

#### Initialization:
- `create_tables()` - Creates all 8 tables
- `migrate()` - Runs schema migrations (adds missing columns)
- `seed_services()` - Loads default services
- `seed_users()` - Creates default users (admin/admin, reception/reception)

#### Authentication (Users Module):
- `authenticate(username, password, remember)` - Login with "remember me" option
- `create_user(username, password, role)` - Add new user (Admin/Receptionist)
- `list_users()` - Get all users with preferences
- `update_user_role(user_id, role)` - Change user role
- `reset_user_password(user_id, password)` - Reset password
- `delete_user(user_id)` - Delete user (prevents last user deletion)
- `change_username(user_id, old_password, new_username)` - Update username
- `change_password(user_id, old_password, new_password)` - Update password
- `update_user_preferences(user_id, theme, font_scale, language)` - Save preferences
- `get_user(user_id)` - Retrieve user details
- `remembered_user()` - Get auto-login user
- `clear_remembered_users()` - Reset all "remember me" flags

#### Settings:
- `get_setting(key, default)` - Get config value
- `set_setting(key, value)` - Set config value
- `all_settings()` - Get all settings as dict

#### Backup & Restore:
- `backup_database(destination)` - Copy database to destination
- `create_backup(destination)` - Auto-generate timestamped backup
- `list_backups()` - List all backup files with timestamps
- `restore_database(source)` - Restore from backup file

#### Employee Management:
- `employee_runtime_status(employee_id, manual_status)` - Calculate real-time availability
- `employees_with_availability(only_available)` - Get staff with status labels
- `available_employee_count()` - Count available staff

#### Analytics:
- `dashboard_stats()` - Return KPI dict:
  - Total clients
  - Total employees
  - Available employees count
  - Appointments today
  - Revenue today
  - Most requested service
- `most_requested_service()` - Get top service
- `appointment_now_condition()` - Get current date/time

---

### 4. **app/ui/auth.py** - Authentication UI

**Class:** `LoginFrame(ttk.Frame)`

**Key Methods:**
- `show_login_page()` - Display login form
- `show_create_page()` - Display user creation form
- `toggle_password()` - Show/hide password
- `login()` - Validate credentials & authenticate
- `create_account()` - Register new user account

**Features:**
- Username/password entry
- "Remember Me" checkbox
- "Show Password" toggle
- Create account flow
- Input validation with error messages

---

### 5. **app/ui/dashboard.py** - Dashboard & KPIs

**Class:** `DashboardFrame(ttk.Frame)`

**Key Methods:**
- `build()` - Construct dashboard layout
- `refresh()` - Update all KPIs and today's appointments table
- `on_appointment_action(id_rdv, action)` - Handle appointment status changes
- `navigate_action(frame_name)` - Switch to different module

**Displays:**
- **5 KPI Cards:**
  1. Total Clients (●)
  2. Appointments Today (□)
  3. Revenue Today (◇)
  4. Available Employees (▣)
  5. Most Requested Service (△)

- **Quick Actions:**
  - New Appointment
  - New Client
  - Payments

- **Today's Appointments Table:**
  - Sortable by time
  - Status: Pending, Confirmed, In Service, Completed
  - Show appointment details (client, service, employee, time)

---

### 6. **app/ui/client.py** - Client Management

**Class:** `ClientFrame(FormTableFrame)`

**Key Methods:**
- `build_form()` - Create CRUD form
- `load()` - Load all clients from database
- `add()` - Insert new client
- `update()` - Modify client details
- `delete()` - Remove client (CASCADE deletes related appointments)
- `search(name)` - Filter clients by name
- `print_clients()` - Generate & open PDF list
- `on_select(event)` - Load selected client into form

**Form Fields:**
- Nom (Name) *required
- Prenom (First Name) *required
- Telephone (Phone) *required, numeric only
- Email
- Adresse (Address)
- Date inscription (Registration Date) - auto-populated with today

**Features:**
- Add/Edit/Delete clients
- Search/filter by name
- Print client list as PDF
- Tree view with sortable columns
- Validation for phone numbers

---

### 7. **app/ui/employe.py** - Employee Management

**Class:** `EmployeFrame(FormTableFrame)`

**Key Methods:**
- `build_form()` - Create CRUD form
- `load()` - Load employees (with availability filter option)
- `add()` - Add new employee
- `update()` - Modify employee
- `delete()` - Remove employee
- `search(name)` - Filter by name
- `print_employees()` - Export employee list to PDF
- `on_select(event)` - Load selected into form

**Form Fields:**
- Nom (Name) *required
- Prenom (First Name) *required
- Specialite (Specialty) - e.g., "Massage", "Facial"
- Telephone *required, numeric only
- Salaire (Salary)
- Disponibilite (Availability) - Dropdown: "Available" / "Not Available"

**Features:**
- Full CRUD operations
- Filter by availability status
- Search by name
- Print employee roster
- Real-time availability tracking

---

### 8. **app/ui/service.py** - Service Catalog

**Class:** `ServiceFrame(FormTableFrame)`

**Key Methods:**
- `build_form()` - Create form
- `load()` - Load service catalog
- `add()` - Add new service
- `update()` - Edit service
- `delete()` - Remove service
- `search(name)` - Filter by service name
- `print_services()` - Generate service catalog PDF
- `validate(data)` - Validate prices & duration

**Form Fields:**
- Nom service (Service Name) *required
- Description
- Prix (Price) - numeric, validated
- Duree minutes (Duration) - numeric, validated

**Pre-loaded Services:**
1. Massage - €350/60 min
2. Sauna - €150/30 min
3. Hammam - €200/45 min
4. Facial - €300/50 min
5. Pedicure - €180/40 min

---

### 9. **app/ui/rendezvous.py** - Appointment Management

**Class:** `RendezVousFrame(FormTableFrame)`

**Key Methods:**
- `build_form()` - Calendar & booking form
- `load()` - Load appointments with filters
- `add()` - Create new appointment
- `update()` - Modify appointment
- `delete()` - Cancel appointment
- `get_available_employees(date, time, duration)` - Check staff availability
- `check_conflict(date, time, employee_id, duration)` - Detect double-bookings
- `mark_as_completed()` - Change status to "Completed"
- `change_status(id_rdv, new_status)` - Update appointment status

**Form Fields:**
- Date (Calendar picker)
- Client (Dropdown - loaded from database)
- Service (Dropdown - with duration & price)
- Employe (Dropdown - filtered by availability)
- Heure (Time) - formatted HH:MM
- Statut (Status) - Dropdown: "Confirme", "En attente", "En Service", "Annulé"

**Features:**
- Date/time picker
- Real-time availability check
- Conflict detection
- Status management
- Filter by date/status
- PDF receipt generation

---

### 10. **app/ui/paiement.py** - Payment Management

**Class:** `PaiementFrame(FormTableFrame)`

**Key Methods:**
- `build_form()` - Create payment form
- `load()` - Load payment records
- `add()` - Record payment
- `update()` - Modify payment
- `delete()` - Remove payment record
- `calculate_balance()` - Calculate appointment balance
- `apply_discount()` - Apply client discount
- `generate_receipt()` - Create PDF receipt

**Form Fields:**
- Client (Dropdown)
- Rendez-vous (Dropdown - linked to client)
- Montant (Amount) - numeric
- Methode paiement (Payment Method) - Dropdown: Cash, Card, Cheque, Bank Transfer
- Date paiement (Payment Date)

**Features:**
- Link multiple appointments to single payment
- Calculate totals
- Generate receipts (PDF)
- Payment method tracking
- Balance calculation

---

### 11. **app/ui/reports.py** - Analytics & Reporting

**Class:** `ReportsFrame(ttk.Frame)`

**Key Methods:**
- `build()` - Layout setup
- `refresh_data()` - Fetch analytics
- `generate_monthly_report()` - Revenue by month
- `generate_service_report()` - Service popularity
- `generate_client_report()` - Client statistics
- `export_report(report_type)` - Generate PDF report

**Reports Available:**
1. **Monthly Revenue** - Income by month (graph/table)
2. **Service Popularity** - Most/least used services
3. **Client Acquisition** - New clients by month
4. **Employee Performance** - Appointments per employee
5. **Payment Methods** - Breakdown of payment types

---

### 12. **app/ui/settings.py** - Admin Settings & Preferences

**Class:** `SettingsFrame(ttk.Frame)`

**Key Sections:**

#### User Account
- Change username
- Change password
- Current role display

#### User Management (Admin only)
- Create user (Admin/Receptionist role)
- List users with roles
- Reset user passwords
- Delete users
- Manage user preferences

#### Spa Settings (Admin only)
- Spa name
- Address
- Phone number
- Email
- Footer message
- Opening hours (HH:MM format)
- Closing hours
- Working days (checkboxes)
- Holidays (date picker)

#### Appointment Alerts
- Enable/disable appointment notifications
- Enable/disable payment notifications
- Enable/disable availability alerts

#### Preferences
- Theme: Dark / Light (with real-time preview)
- Font scale: 0.8 - 1.5
- Language: French (extensible)

#### Backup & Restore
- Create backup (auto-timestamped)
- List & restore from backups
- Download backup files
- Automatic restart after restore

---

### 13. **app/ui/ui_utils.py** - Utility Components

**Classes:**

#### FormTableFrame
- Base class for CRUD screens
- Methods: `add_search()`, `add_tree()`, `button_row()`
- Handles form layout, tree views, search bars

#### DateEntry
- Custom date picker widget
- Input validation
- Configurable date format

#### Validators
- `valid_phone(value)` - Phone number validation
- `valid_email(value)` - Email validation
- `valid_date(value)` - Date format validation

#### UI Helpers
- `attach_modern_scrollbar()` - Enhanced scrollbar styling
- `bind_mousewheel(widget)` - Mousewheel scrolling
- `show_pdf()` - Display PDF in default viewer
- `ask_delete()` - Confirmation dialog
- `clear_entries()` - Reset form fields
- `table_lines()` - Format data for PDF tables

---

### 14. **app/utils/pdf_utils.py** - PDF Generation

**Functions:**

#### PDF Generation
- `create_pdf(filename, title, lines)` - Generate PDF from text lines
- `open_pdf(filepath)` - Open PDF with default viewer
- `table_lines(rows, col_widths)` - Format table data for PDF

#### PDF Structure
- Custom PDF objects (pages, fonts, content streams)
- Multi-page support with page breaks
- Text escaping & encoding (Latin-1)
- Customizable margins & line height

**Generated PDFs:**
- Client lists
- Employee rosters
- Service catalogs
- Appointment receipts
- Monthly revenue reports
- Monthly statistics

---

## 📊 APPLICATION WORKFLOW

### User Journey

1. **Launch** → `main.py`
   - Check for remembered user
   - Show login or app

2. **Login** → `auth.py`
   - Enter credentials
   - Option to create account
   - Option to "Remember Me"

3. **Dashboard** → `dashboard.py`
   - View KPIs
   - Quick actions
   - Today's appointments

4. **Main Operations:**
   - **Clients** → `client.py` (Add/Edit/Search)
   - **Employees** → `employe.py` (Add/Edit/Filter)
   - **Services** → `service.py` (Manage catalog)
   - **Appointments** → `rendezvous.py` (Book/Manage)
   - **Payments** → `paiement.py` (Record/Receipt)
   - **Reports** → `reports.py` (Analytics)
   - **Settings** → `settings.py` (Admin/Preferences)

5. **Export:**
   - Generate PDF lists/receipts/reports
   - Create backups
   - Restore from backups

---

## 🧪 TESTING

**Test Files Location:** `/tests/`

### Test Modules:

1. **test_database.py** - Database operations
   - CRUD operations for all tables
   - User authentication
   - Backup/restore functionality

2. **test_backup.py** - Backup system
   - Create backup
   - List backups
   - Restore functionality

3. **test_paiement.py** - Payment operations
   - Record payment
   - Link multiple appointments
   - Calculate totals

### Run Tests:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 🚀 DEFAULT CREDENTIALS

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin` |
| Receptionist | `reception` | `reception` |

---

## 💾 FILE STRUCTURE & DATA FLOW

```
User Input (UI)
    ↓
[Tkinter Frames: auth, dashboard, client, etc.]
    ↓
[Database Class - Core Operations]
    ↓
[SQLite Database: spa.db]
    ↓
[PDF Generation: receipts, reports, exports]
    ↓
Output (Display/Files)
```

---

## 🎨 THEMING SYSTEM

**Supported Themes:** Dark (default) & Light

**Color Palettes:**
- Background, Sidebar, Cards, Text, Accents
- Button states (hover, active, disabled)
- Entry fields, Trees, Borders

**User Customization:**
- Theme selection (Settings)
- Font scaling (0.8 - 1.5x)
- Remembered preferences (per user)

---

## 🔒 Security Features

1. **Password Hashing:** SHA256 (hashlib)
2. **User Roles:** Admin / Receptionist
3. **Role-based Features:**
   - Only Admin can: manage users, backup/restore, settings
   - Receptionist: basic CRUD for clients/appointments
4. **Foreign Keys:** Enabled in SQLite to maintain referential integrity
5. **Cascade Delete:** Related records deleted automatically

---

## 📦 DEPENDENCIES SUMMARY

- **Python:** 3.10+ recommended
- **Built-in Libraries:** tkinter, sqlite3, hashlib, datetime, os, shutil, re, calendar, textwrap
- **Optional:** pytest 8.3.3 (for testing)
- **No external packages required** to run main application

---

## 🎯 KEY FEATURES CHECKLIST

✅ User authentication & role management  
✅ Client relationship management (CRUD)  
✅ Employee scheduling & availability  
✅ Service catalog management  
✅ Appointment booking with conflict detection  
✅ Payment processing & recording  
✅ Analytics & reporting (monthly, by service, etc.)  
✅ PDF export (receipts, lists, reports)  
✅ Database backup/restore functionality  
✅ Dark/Light theme support  
✅ Font scaling  
✅ Multi-language support (French default)  
✅ Settings management  
✅ Real-time KPI dashboard  
✅ Search/filter functionality  
✅ Responsive UI with modern styling  

---

## 📝 NOTES

- All dates in ISO format (YYYY-MM-DD)
- All times in 24-hour format (HH:MM)
- Monetary values stored as REAL (float)
- Phone numbers stored as TEXT (numeric validation only)
- Database enforces foreign keys & cascading deletes
- All tables use AUTOINCREMENT for primary keys
