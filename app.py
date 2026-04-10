from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from functools import wraps
import bcrypt
import datetime
import jwt
import mysql.connector
from mysql.connector import Error
import os


load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "https://crazyelf-ai.github.io"
    }
}, supports_credentials=True)


SECRET_KEY = os.getenv("SECRET_KEY")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "myapp")


import os
import mysql.connector

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        ssl_disabled=False
    )

def get_table_columns(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"SHOW COLUMNS FROM {table_name}")
    columns = {row[0] for row in cursor.fetchall()}
    cursor.close()
    return columns


def ensure_schema():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(120) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'member',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS members (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(120) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'member',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ngos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ngo_name VARCHAR(150) NOT NULL,
            founder_name VARCHAR(150),
            registration_number VARCHAR(100) NOT NULL UNIQUE,
            contact_number VARCHAR(30) NOT NULL,
            email VARCHAR(120) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            address TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    existing_user_columns = get_table_columns(conn, "users")
    existing_member_columns = get_table_columns(conn, "members")
    missing_user_columns = {
        "phone_number": "ALTER TABLE users ADD COLUMN phone_number VARCHAR(30) NULL",
        "city": "ALTER TABLE users ADD COLUMN city VARCHAR(100) NULL",
        "field_of_study": "ALTER TABLE users ADD COLUMN field_of_study VARCHAR(150) NULL",
        "college": "ALTER TABLE users ADD COLUMN college VARCHAR(150) NULL",
        "year_of_study": "ALTER TABLE users ADD COLUMN year_of_study VARCHAR(50) NULL",
        "motivation": "ALTER TABLE users ADD COLUMN motivation TEXT NULL",
        "date_of_birth": "ALTER TABLE users ADD COLUMN date_of_birth DATE NULL",
        "certificate_url": "ALTER TABLE users ADD COLUMN certificate_url TEXT NULL",
    }
    for column_name, ddl in missing_user_columns.items():
        if column_name not in existing_user_columns:
            cursor.execute(ddl)
        if column_name not in existing_member_columns:
            cursor.execute(ddl.replace("ALTER TABLE users", "ALTER TABLE members"))

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS camp_proposals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ngo_name VARCHAR(120),
            email VARCHAR(120),
            phone VARCHAR(20),
            city VARCHAR(80),
            state VARCHAR(80),
            camp_type VARCHAR(150) NOT NULL,
            proposal_file TEXT,
            location VARCHAR(255),
            date VARCHAR(50),
            description TEXT,
            beneficiaries INT DEFAULT 0,
            volunteers_required INT DEFAULT 0,
            created_by VARCHAR(120),
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            rejection_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS announcements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(150) NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS drives (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255),
            description TEXT,
            location VARCHAR(255),
            date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS camp_registrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            source_type VARCHAR(20) NOT NULL,
            source_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_registration (user_id, source_type, source_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS leadership (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            position VARCHAR(150) NOT NULL,
            image_url TEXT,
            linkedin_url TEXT,
            instagram_url TEXT,
            bio TEXT,
            category VARCHAR(80) DEFAULT 'Current Core',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS initiatives (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(150) NOT NULL,
            category VARCHAR(100) DEFAULT 'General',
            image_url TEXT,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reels (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(150) NOT NULL,
            video_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS testimonials (
            id INT AUTO_INCREMENT PRIMARY KEY,
            author VARCHAR(100) NOT NULL,
            author_position VARCHAR(150),
            image_url TEXT,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS careers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(150) NOT NULL,
            type VARCHAR(100),
            description TEXT NOT NULL,
            apply_link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS gallery (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(150),
            url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS camps (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(150) NOT NULL,
            location VARCHAR(255),
            date_completed VARCHAR(50),
            description TEXT,
            beneficiaries INT DEFAULT 0,
            volunteers INT DEFAULT 0,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            setting_key VARCHAR(100) NOT NULL UNIQUE,
            setting_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        INSERT IGNORE INTO members (
            id, name, email, password_hash, role, created_at,
            phone_number, city, field_of_study, college, year_of_study, motivation, date_of_birth, certificate_url
        )
        SELECT
            id, name, email, password_hash, role, created_at,
            phone_number, city, field_of_study, college, year_of_study, motivation, date_of_birth, certificate_url
        FROM users
        WHERE role = 'member'
        """
    )

    conn.commit()
    cursor.close()
    conn.close()


def generate_token(user, account_type="staff"):
    payload = {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "account_type": account_type,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token missing"}), 401

        try:
            token = auth_header.split(" ", 1)[1]
            request.user = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except Exception:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated


def staff_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.user.get("role") not in ["god", "it"]:
            return jsonify({"error": "Staff access required"}), 403
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.user.get("role") not in ["admin", "god", "it"]:
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated


def query_all(sql, params=None):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params or ())
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def query_one(sql, params=None):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params or ())
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def execute_write(sql, params=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(sql, params or ())
    conn.commit()
    lastrowid = cursor.lastrowid
    cursor.close()
    conn.close()
    return lastrowid


def get_member_by_email(email):
    return query_one("SELECT * FROM members WHERE email = %s", (email,))


def get_staff_by_email(email):
    return query_one("SELECT * FROM users WHERE email = %s", (email,))


def get_ngo_by_email(email):
    return query_one("SELECT * FROM ngos WHERE email = %s", (email,))


def build_profile_response(table_name, email):
    conn = get_db()
    table_columns = get_table_columns(conn, table_name)
    cursor = conn.cursor(dictionary=True)
    select_fields = ["id", "email", "created_at"]

    if table_name == "ngos":
        select_fields.extend([
            "ngo_name",
            "founder_name",
            "registration_number",
            "contact_number",
            "address",
            "description",
        ])
    else:
        select_fields.extend(["name", "role"])
        for optional_field in ["phone_number", "city", "field_of_study", "college", "year_of_study", "certificate_url"]:
            if optional_field in table_columns:
                select_fields.append(optional_field)

    cursor.execute(
        f"SELECT {', '.join(select_fields)} FROM {table_name} WHERE email = %s",
        (email,),
    )
    record = cursor.fetchone()
    cursor.close()
    conn.close()

    if not record:
        return None

    if table_name != "ngos":
        for optional_field in ["phone_number", "city", "field_of_study", "college", "year_of_study", "certificate_url"]:
            record.setdefault(optional_field, None)

    return record


@app.route("/")
def home():
    return "API running"


@app.route("/signup", methods=["POST"])
@app.route("/member/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    phone_number = data.get("phone_number")
    city = data.get("city")
    field_of_study = data.get("field_of_study")
    college = data.get("college")
    year_of_study = data.get("year_of_study")
    motivation = data.get("motivation")
    date_of_birth = data.get("date_of_birth")

    if not name or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    user_columns = get_table_columns(conn, "members")

    cursor.execute("SELECT id FROM members WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Member already exists"}), 400

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    insert_fields = ["name", "email", "password_hash", "role"]
    insert_values = [name, email, password_hash, "member"]

    optional_fields = {
        "phone_number": phone_number,
        "city": city,
        "field_of_study": field_of_study,
        "college": college,
        "year_of_study": year_of_study,
        "motivation": motivation,
        "date_of_birth": date_of_birth or None,
    }
    for field_name, field_value in optional_fields.items():
        if field_name in user_columns:
            insert_fields.append(field_name)
            insert_values.append(field_value)

    placeholders = ", ".join(["%s"] * len(insert_fields))
    field_list = ", ".join(insert_fields)
    cursor.execute(
        f"INSERT INTO members ({field_list}) VALUES ({placeholders})",
        tuple(insert_values),
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Member created"}), 201


@app.route("/login", methods=["POST"])
@app.route("/member/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = get_member_by_email(email)
    account_type = "member"

    if not user:
        user = get_staff_by_email(email)
        account_type = "staff"

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"token": generate_token(user, account_type), "account_type": account_type})


@app.route("/ngo/signup", methods=["POST"])
@app.route("/register-ngo", methods=["POST"])
def register_ngo():
    data = request.get_json() or {}
    required = [
        "ngo_name",
        "registration_number",
        "contact_number",
        "email",
        "password",
    ]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    existing = get_ngo_by_email(data.get("email"))
    if existing:
        return jsonify({"error": "NGO already exists"}), 400

    registration_exists = query_one(
        "SELECT id FROM ngos WHERE registration_number = %s",
        (data.get("registration_number"),),
    )
    if registration_exists:
        return jsonify({"error": "Registration number already exists"}), 400

    password_hash = bcrypt.hashpw(
        data.get("password").encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")
    ngo_id = execute_write(
        """
        INSERT INTO ngos (
            ngo_name, founder_name, registration_number, contact_number,
            email, password_hash, address, description
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            data.get("ngo_name"),
            data.get("founder_name"),
            data.get("registration_number"),
            data.get("contact_number"),
            data.get("email"),
            password_hash,
            data.get("address"),
            data.get("description"),
        ),
    )
    return jsonify({"id": ngo_id, "message": "NGO created"}), 201


@app.route("/ngo/login", methods=["POST"])
def ngo_login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    ngo = get_ngo_by_email(email)
    if not ngo:
        return jsonify({"error": "Invalid credentials"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), ngo["password_hash"].encode("utf-8")):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"token": generate_token({**ngo, "role": "ngo"}, "ngo"), "account_type": "ngo"})


@app.route("/profile", methods=["GET"])
@token_required
def profile():
    account_type = request.user.get("account_type", "staff")
    table_name = "members" if account_type == "member" else "users"
    user = build_profile_response(table_name, request.user["email"])

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user)


@app.route("/ngo/profile", methods=["GET"])
@token_required
def ngo_profile():
    if request.user.get("account_type") != "ngo":
        return jsonify({"error": "NGO access required"}), 403

    ngo = build_profile_response("ngos", request.user["email"])
    if not ngo:
        return jsonify({"error": "NGO not found"}), 404
    return jsonify(ngo)


@app.route("/drives", methods=["GET"])
@token_required
def get_drives():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                id,
                title,
                COALESCE(location, 'India') AS location,
                COALESCE(description, '') AS description,
                'drive' AS source_type,
                date,
                created_at
            FROM drives
            """
        )
        drives = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                id,
                camp_type AS title,
                COALESCE(location, CONCAT_WS(', ', city, state), city, state, 'India') AS location,
                COALESCE(description, CONCAT('Organized by ', COALESCE(ngo_name, 'MAAI'))) AS description,
                'proposal' AS source_type,
                date,
                created_at
            FROM camp_proposals
            WHERE status = 'approved'
            """
        )
        drives.extend(cursor.fetchall())
        drives.sort(key=lambda item: item.get("created_at") or "", reverse=True)

        cursor.close()
        conn.close()
        return jsonify(drives)
    except Error as exc:
        return jsonify({"error": f"Failed to load drives: {exc.msg}"}), 500


@app.route("/notices", methods=["GET"])
@token_required
def get_notices():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, title, content, created_at FROM announcements ORDER BY created_at DESC"
        )
        notices = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(notices)
    except Error:
        return jsonify([])


@app.route("/api/me", methods=["GET"])
@token_required
def api_me():
    if request.user.get("account_type") == "ngo":
        ngo = ngo_profile().get_json()
        return jsonify({
            "full_name": ngo.get("ngo_name"),
            "role": "ngo",
            "profession": ngo.get("registration_number"),
        })
    profile_data = profile().get_json()
    return jsonify({
        "full_name": profile_data.get("name"),
        "role": profile_data.get("role"),
        "profession": profile_data.get("field_of_study") or profile_data.get("city"),
        "certificate_url": profile_data.get("certificate_url"),
    })


@app.route("/api/active-drives", methods=["GET"])
def api_active_drives():
    drives = query_all(
        """
        SELECT id, title, COALESCE(location, 'India') AS location, COALESCE(description, '') AS description, title AS category, 'drive' AS source_type
        FROM drives
        """
    )
    drives.extend(query_all(
        """
        SELECT
            id,
            camp_type AS title,
            COALESCE(location, CONCAT_WS(', ', city, state), city, state, 'India') AS location,
            COALESCE(description, CONCAT('Organized by ', COALESCE(ngo_name, 'MAAI'))) AS description,
            camp_type AS category,
            'proposal' AS source_type
        FROM camp_proposals
        WHERE status = 'approved'
        ORDER BY created_at DESC
        """
    ))
    return jsonify(drives)


@app.route("/api/camps/apply", methods=["POST"])
@token_required
def api_apply_camp():
    return apply_camp()


@app.route("/api/initiatives", methods=["GET"])
def api_get_initiatives():
    rows = query_all(
        """
        SELECT id, title, category, image_url, description, created_at
        FROM initiatives
        ORDER BY created_at DESC
        """
    )
    return jsonify([
        {
            "id": row["id"],
            "title": row["title"],
            "category": row["category"],
            "image_url": row["image_url"],
            "imageUrl": row["image_url"],
            "description": row["description"],
            "createdAt": str(row["created_at"]),
        }
        for row in rows
    ])


@app.route("/api/initiatives/<int:item_id>", methods=["GET"])
def api_get_initiative(item_id):
    row = query_one(
        """
        SELECT id, title, category, image_url, description, created_at
        FROM initiatives
        WHERE id = %s
        """,
        (item_id,),
    )
    if not row:
        return jsonify({"error": "Initiative not found"}), 404
    return jsonify({
        "id": row["id"],
        "title": row["title"],
        "category": row["category"],
        "image_url": row["image_url"],
        "imageUrl": row["image_url"],
        "description": row["description"],
        "date": str(row["created_at"]),
    })


@app.route("/api/leadership", methods=["GET"])
def api_get_leadership():
    rows = query_all(
        """
        SELECT id, name, position, image_url, linkedin_url, instagram_url, bio, category
        FROM leadership
        ORDER BY created_at DESC
        """
    )
    return jsonify([
        {
            "id": row["id"],
            "name": row["name"],
            "position": row["position"],
            "role": row["position"],
            "image_url": row["image_url"],
            "imageUrl": row["image_url"],
            "linkedin_url": row["linkedin_url"],
            "linkedin": row["linkedin_url"],
            "instagram_url": row["instagram_url"],
            "instagram": row["instagram_url"],
            "bio": row["bio"],
            "category": row["category"],
        }
        for row in rows
    ])


@app.route("/api/reels", methods=["GET"])
def api_get_reels():
    rows = query_all("SELECT id, title, video_url FROM reels ORDER BY created_at DESC")
    return jsonify([
        {
            "id": row["id"],
            "title": row["title"],
            "video_url": row["video_url"],
            "videoUrl": row["video_url"],
        }
        for row in rows
    ])


@app.route("/api/testimonials", methods=["GET"])
def api_get_testimonials():
    rows = query_all(
        """
        SELECT id, author, author_position, image_url, text
        FROM testimonials
        ORDER BY created_at DESC
        """
    )
    return jsonify([
        {
            "id": row["id"],
            "author": row["author"],
            "author_position": row["author_position"],
            "authorPosition": row["author_position"],
            "image_url": row["image_url"],
            "text": row["text"],
        }
        for row in rows
    ])


@app.route("/api/careers", methods=["GET"])
def api_get_careers():
    rows = query_all(
        """
        SELECT id, title, type, description, apply_link
        FROM careers
        ORDER BY created_at DESC
        """
    )
    return jsonify(rows)


@app.route("/api/gallery", methods=["GET"])
def api_get_gallery():
    rows = query_all("SELECT id, title, url FROM gallery ORDER BY created_at DESC")
    return jsonify(rows)


@app.route("/api/camps", methods=["GET"])
def api_get_camps():
    rows = query_all(
        """
        SELECT id, title, location, date_completed, description, beneficiaries, volunteers, image_url
        FROM camps
        ORDER BY created_at DESC
        """
    )
    return jsonify([
        {
            "id": row["id"],
            "title": row["title"],
            "location": row["location"],
            "dateCompleted": row["date_completed"],
            "description": row["description"],
            "beneficiaries": row["beneficiaries"],
            "volunteers": row["volunteers"],
            "image_url": row["image_url"],
            "imageUrl": row["image_url"],
        }
        for row in rows
    ])


@app.route("/api/admin/initiatives", methods=["GET", "POST"])
@admin_required
def api_admin_initiatives():
    if request.method == "GET":
        return api_get_initiatives()

    data = request.get_json() or {}
    if not data.get("title") or not data.get("description"):
        return jsonify({"error": "Title and description are required"}), 400
    item_id = execute_write(
        """
        INSERT INTO initiatives (title, category, image_url, description)
        VALUES (%s, %s, %s, %s)
        """,
        (
            data.get("title"),
            data.get("category", "General"),
            data.get("image_url") or data.get("imageUrl"),
            data.get("description"),
        ),
    )
    return jsonify({"id": item_id, "message": "Initiative created"}), 201


@app.route("/api/admin/initiatives/<int:item_id>", methods=["DELETE"])
@admin_required
def api_admin_delete_initiative(item_id):
    execute_write("DELETE FROM initiatives WHERE id = %s", (item_id,))
    return jsonify({"message": "Initiative deleted"})


@app.route("/api/admin/leadership", methods=["POST"])
@admin_required
def api_admin_add_leadership():
    data = request.get_json() or {}
    if not data.get("name") or not data.get("position"):
        return jsonify({"error": "Name and position are required"}), 400
    leader_id = execute_write(
        """
        INSERT INTO leadership (name, position, image_url, linkedin_url, instagram_url, bio, category)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            data.get("name"),
            data.get("position"),
            data.get("image_url") or data.get("imageUrl"),
            data.get("linkedin_url") or data.get("linkedinUrl"),
            data.get("instagram_url") or data.get("instagramUrl"),
            data.get("bio"),
            data.get("category", "Current Core"),
        ),
    )
    return jsonify({"id": leader_id, "message": "Leader added"}), 201


@app.route("/api/admin/leadership/<int:leader_id>", methods=["DELETE"])
@admin_required
def api_admin_delete_leadership(leader_id):
    execute_write("DELETE FROM leadership WHERE id = %s", (leader_id,))
    return jsonify({"message": "Leader deleted"})


@app.route("/api/admin/reels", methods=["POST"])
@admin_required
def api_admin_add_reel():
    data = request.get_json() or {}
    if not data.get("title") or not data.get("video_url"):
        return jsonify({"error": "Title and video URL are required"}), 400
    reel_id = execute_write(
        "INSERT INTO reels (title, video_url) VALUES (%s, %s)",
        (data.get("title"), data.get("video_url")),
    )
    return jsonify({"id": reel_id, "message": "Reel added"}), 201


@app.route("/api/admin/reels/<int:reel_id>", methods=["DELETE"])
@admin_required
def api_admin_delete_reel(reel_id):
    execute_write("DELETE FROM reels WHERE id = %s", (reel_id,))
    return jsonify({"message": "Reel deleted"})


@app.route("/api/admin/testimonials", methods=["POST"])
@admin_required
def api_admin_add_testimonial():
    data = request.get_json() or {}
    if not data.get("author") or not data.get("text"):
        return jsonify({"error": "Author and text are required"}), 400
    testimonial_id = execute_write(
        """
        INSERT INTO testimonials (author, author_position, image_url, text)
        VALUES (%s, %s, %s, %s)
        """,
        (
            data.get("author"),
            data.get("author_position") or data.get("authorPosition"),
            data.get("image_url"),
            data.get("text"),
        ),
    )
    return jsonify({"id": testimonial_id, "message": "Testimonial added"}), 201


@app.route("/api/admin/testimonials/<int:testimonial_id>", methods=["DELETE"])
@admin_required
def api_admin_delete_testimonial(testimonial_id):
    execute_write("DELETE FROM testimonials WHERE id = %s", (testimonial_id,))
    return jsonify({"message": "Testimonial deleted"})


@app.route("/api/admin/careers", methods=["GET", "POST"])
@admin_required
def api_admin_careers():
    if request.method == "GET":
        return api_get_careers()

    data = request.get_json() or {}
    if not data.get("title"):
        return jsonify({"error": "Title is required"}), 400
    career_id = execute_write(
        """
        INSERT INTO careers (title, type, description, apply_link)
        VALUES (%s, %s, %s, %s)
        """,
        (
            data.get("title"),
            data.get("type"),
            data.get("description", ""),
            data.get("apply_link"),
        ),
    )
    return jsonify({"id": career_id, "message": "Career added"}), 201


@app.route("/api/admin/careers/<int:career_id>", methods=["DELETE"])
@admin_required
def api_admin_delete_career(career_id):
    execute_write("DELETE FROM careers WHERE id = %s", (career_id,))
    return jsonify({"message": "Career deleted"})


@app.route("/api/admin/gallery", methods=["POST"])
@admin_required
def api_admin_add_gallery():
    data = request.get_json() or {}
    image_url = data.get("url") or data.get("image_url")
    if not image_url:
        return jsonify({"error": "Image URL is required"}), 400
    gallery_id = execute_write(
        "INSERT INTO gallery (title, url) VALUES (%s, %s)",
        (data.get("title"), image_url),
    )
    return jsonify({"id": gallery_id, "message": "Gallery item added"}), 201


@app.route("/api/admin/gallery/<int:item_id>", methods=["DELETE"])
@admin_required
def api_admin_delete_gallery(item_id):
    execute_write("DELETE FROM gallery WHERE id = %s", (item_id,))
    return jsonify({"message": "Gallery item deleted"})


@app.route("/api/admin/users", methods=["GET", "POST"])
@admin_required
def api_admin_users():
    if request.method == "GET":
        rows = query_all(
            """
            SELECT id, name, email, role, certificate_url
            FROM users
            ORDER BY created_at DESC
            """
        )
        return jsonify([
            {
                "id": row["id"],
                "name": row["name"],
                "full_name": row["name"],
                "email": row["email"],
                "role": row["role"],
                "certificate_url": row.get("certificate_url"),
            }
            for row in rows
        ])

    data = request.get_json() or {}
    name = data.get("full_name") or data.get("name")
    email = data.get("email")
    role = data.get("role", "member")
    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400
    existing = query_one("SELECT id FROM users WHERE email = %s", (email,))
    if existing:
        return jsonify({"error": "User already exists"}), 400
    hashed = bcrypt.hashpw("MAAI2026!".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_id = execute_write(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
        (name, email, hashed, role),
    )
    return jsonify({"id": user_id, "message": "User added"}), 201


@app.route("/api/admin/users/<int:user_id>/role", methods=["PUT"])
@admin_required
def api_admin_update_user_role(user_id):
    data = request.get_json() or {}
    if not data.get("role"):
        return jsonify({"error": "Role is required"}), 400
    execute_write("UPDATE users SET role = %s WHERE id = %s", (data.get("role"), user_id))
    return jsonify({"message": "Role updated"})


@app.route("/api/admin/users/<int:user_id>/certificate", methods=["PUT"])
@admin_required
def api_admin_update_user_certificate(user_id):
    data = request.get_json() or {}
    execute_write("UPDATE users SET certificate_url = %s WHERE id = %s", (data.get("certificate_url"), user_id))
    return jsonify({"message": "Certificate updated"})


@app.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@admin_required
def api_admin_delete_user(user_id):
    execute_write("DELETE FROM users WHERE id = %s", (user_id,))
    return jsonify({"message": "User deleted"})


@app.route("/api/admin/stats", methods=["GET"])
@admin_required
def api_admin_stats():
    users_count = query_one("SELECT COUNT(*) AS count FROM users")
    members_count = query_one("SELECT COUNT(*) AS count FROM members")
    pending_count = query_one("SELECT COUNT(*) AS count FROM camp_proposals WHERE status = 'pending'")
    initiatives_count = query_one("SELECT COUNT(*) AS count FROM initiatives")
    return jsonify({
        "total_users": users_count["count"] + members_count["count"],
        "active_volunteers": members_count["count"],
        "pending_requests": pending_count["count"],
        "initiatives": initiatives_count["count"],
    })


@app.route("/api/admin/camp-proposals", methods=["GET"])
@admin_required
def api_admin_camp_proposals():
    proposals = query_all(
        """
        SELECT
            id,
            ngo_name,
            email,
            phone,
            city,
            state,
            camp_type,
            location,
            date,
            description,
            beneficiaries,
            volunteers_required,
            status,
            rejection_reason,
            created_at
        FROM camp_proposals
        ORDER BY
            CASE status
                WHEN 'pending' THEN 0
                WHEN 'approved' THEN 1
                WHEN 'rejected' THEN 2
                ELSE 3
            END,
            created_at DESC
        """
    )
    return jsonify(proposals)


@app.route("/api/admin/camp-proposals/<int:proposal_id>/status", methods=["PUT"])
@admin_required
def api_admin_update_camp_proposal_status(proposal_id):
    data = request.get_json() or {}
    status = (data.get("status") or "").strip().lower()
    rejection_reason = data.get("rejection_reason")

    if status not in ["approved", "rejected"]:
        return jsonify({"error": "Status must be approved or rejected"}), 400

    existing = query_one("SELECT id FROM camp_proposals WHERE id = %s", (proposal_id,))
    if not existing:
        return jsonify({"error": "Camp proposal not found"}), 404

    execute_write(
        """
        UPDATE camp_proposals
        SET status = %s, rejection_reason = %s
        WHERE id = %s
        """,
        (status, rejection_reason if status == "rejected" else None, proposal_id),
    )
    return jsonify({"message": f"Camp proposal {status}."})


@app.route("/apply-camp", methods=["POST"])
@token_required
def apply_camp():
    if request.user.get("account_type") not in ["ngo", "staff"]:
        return jsonify({"error": "Only NGO and staff accounts can submit camp proposals"}), 403

    data = request.get_json() or {}
    required = ["ngo_name", "email", "phone", "city", "state", "camp_type"]
    missing = [field for field in required if not data.get(field)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO camp_proposals
        (ngo_name, email, phone, city, state, camp_type, proposal_file, location, date,
         description, beneficiaries, volunteers_required, created_by, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            data.get("ngo_name"),
            data.get("email"),
            data.get("phone"),
            data.get("city"),
            data.get("state"),
            data.get("camp_type"),
            data.get("proposal_file"),
            data.get("location"),
            data.get("date"),
            data.get("description"),
            data.get("beneficiaries", 0),
            data.get("volunteers_required", 0),
            request.user["email"],
            "pending",
        ),
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Camp proposal submitted"}), 201


@app.route("/ngo/camp-proposals", methods=["GET"])
@token_required
def ngo_camp_proposals():
    if request.user.get("account_type") != "ngo":
        return jsonify({"error": "NGO access required"}), 403

    proposals = query_all(
        """
        SELECT
            id,
            camp_type AS title,
            location,
            date,
            description,
            beneficiaries,
            volunteers_required,
            status,
            rejection_reason,
            created_at
        FROM camp_proposals
        WHERE created_by = %s
        ORDER BY created_at DESC
        """,
        (request.user["email"],),
    )
    return jsonify(proposals)


@app.route("/camp-registrations", methods=["POST"])
@token_required
def register_for_camp():
    if request.user.get("account_type") != "member":
        return jsonify({"error": "Only members can register for drives"}), 403

    data = request.get_json() or {}
    source_type = data.get("source_type")
    source_id = data.get("source_id")

    if source_type not in ["drive", "proposal"] or not source_id:
        return jsonify({"error": "Invalid camp reference"}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, role FROM members WHERE email = %s", (request.user["email"],))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        return jsonify({"error": "User not found"}), 404

    if source_type == "drive":
        cursor.execute("SELECT id FROM drives WHERE id = %s", (source_id,))
    else:
        cursor.execute("SELECT id FROM camp_proposals WHERE id = %s", (source_id,))
    camp = cursor.fetchone()

    if not camp:
        cursor.close()
        conn.close()
        return jsonify({"error": "Camp not found"}), 404

    insert_cursor = conn.cursor()
    try:
        insert_cursor.execute(
            """
            INSERT INTO camp_registrations (user_id, source_type, source_id)
            VALUES (%s, %s, %s)
            """,
            (user["id"], source_type, source_id),
        )
        conn.commit()
    except Error as exc:
        insert_cursor.close()
        cursor.close()
        conn.close()
        if exc.errno == 1062:
            return jsonify({"error": "You have already registered for this camp"}), 409
        return jsonify({"error": exc.msg}), 500

    insert_cursor.close()
    cursor.close()
    conn.close()
    return jsonify({"message": "Registered successfully"}), 201


@app.route("/camp-registrations", methods=["GET"])
@staff_required
def get_camp_registrations():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            cr.id,
            cr.source_type,
            cr.source_id,
            cr.created_at AS registered_at,
            u.name,
            u.email,
            u.phone_number,
            u.field_of_study,
            CASE
                WHEN cr.source_type = 'drive' THEN d.title
                WHEN cr.source_type = 'proposal' THEN cp.camp_type
                ELSE 'Camp'
            END AS camp_title,
            CASE
                WHEN cr.source_type = 'drive' THEN d.location
                WHEN cr.source_type = 'proposal' THEN COALESCE(cp.location, CONCAT_WS(', ', cp.city, cp.state))
                ELSE NULL
            END AS camp_location
        FROM camp_registrations cr
        JOIN members u ON u.id = cr.user_id
        LEFT JOIN drives d ON cr.source_type = 'drive' AND cr.source_id = d.id
        LEFT JOIN camp_proposals cp ON cr.source_type = 'proposal' AND cr.source_id = cp.id
        ORDER BY camp_title ASC, cr.created_at DESC
        """
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    camps = {}
    for row in rows:
        key = f"{row['source_type']}:{row['source_id']}"
        if key not in camps:
            camps[key] = {
                "source_type": row["source_type"],
                "source_id": row["source_id"],
                "camp_title": row["camp_title"],
                "camp_location": row["camp_location"],
                "registrations": [],
            }
        camps[key]["registrations"].append(
            {
                "name": row["name"],
                "email": row["email"],
                "phone_number": row["phone_number"],
                "field_of_study": row["field_of_study"],
                "registered_at": row["registered_at"],
            }
        )

    return jsonify(list(camps.values()))


with app.app_context():
    ensure_schema()

if __name__ == "__main__":
    app.run(debug=True)
