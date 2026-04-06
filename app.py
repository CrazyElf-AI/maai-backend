from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import func
from flask_cors import CORS
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

# Database & Security Config
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
_secret_key = os.environ.get('SECRET_KEY')
_jwt_secret_key = os.environ.get('JWT_SECRET_KEY')

if not _secret_key:
    raise RuntimeError("FATAL: SECRET_KEY environment variable is not set. Set it on Render before deploying.")
if not _jwt_secret_key:
    raise RuntimeError("FATAL: JWT_SECRET_KEY environment variable is not set. Set it on Render before deploying.")

app.config['SECRET_KEY'] = _secret_key
app.config['JWT_SECRET_KEY'] = _jwt_secret_key

# THE SSL FIX: Prevents "Connection closed unexpectedly" errors
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

db = SQLAlchemy(app)
jwt = JWTManager(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False, default='member') # member, admin, god
    city = db.Column(db.String(50))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    

class CampProposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ngo_name = db.Column(db.String(120), nullable=True) # made nullable for compatibility
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    camp_type = db.Column(db.String(50), nullable=False) # Maps to event name
    proposal_file = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(100), nullable=True) # from ngo-dashboard
    date = db.Column(db.String(50), nullable=True) # from ngo-dashboard
    description = db.Column(db.Text, nullable=True) # from ngo-dashboard
    beneficiaries = db.Column(db.Integer, nullable=True) # from ngo-dashboard
    volunteers_required = db.Column(db.Integer, nullable=True) # from ngo-dashboard
    created_by = db.Column(db.String(120), nullable=True) # User email/id
    status = db.Column(db.String(20), nullable=False, default='pending')
    rejection_reason = db.Column(db.Text, nullable=True)

class Leadership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False) # Maps to 'role' in the UI
    image_url = db.Column(db.String(200), nullable=False)
    linkedin_url = db.Column(db.String(200), nullable=True)
    instagram_url = db.Column(db.String(200), nullable=True) # New
    bio = db.Column(db.Text, nullable=True) # New
    category = db.Column(db.String(50), nullable=False, default='Current Core Team') # New

class FlagshipInitiative(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False, default='General')
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(200), nullable=True)

class CampReel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_url = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(100), nullable=False)

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    author_position = db.Column(db.String(100), nullable=True)
    image_url = db.Column(db.String(200), nullable=True) # Add this

class Career(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    apply_link = db.Column(db.String(200), nullable=False)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

# Add this after your CampProposal model
class Camp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    beneficiaries = db.Column(db.Integer, default=0)
    volunteers = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(200)) # <--- Add this line for the camp photos

class SystemSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(100), nullable=False)

# --- Role-based Access Control Decorators ---
# --- Role-based Access Control Decorators ---
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        # Include 'it' in the authorized list for content management
        if claims.get('role') not in ['admin', 'god', 'it']:
            return jsonify({'error': 'Unauthorized access!'}), 403
        return fn(*args, **kwargs)
    return wrapper

def god_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'god':
            return jsonify({'error': 'God mode access required!'}), 403
        return fn(*args, **kwargs)
    return wrapper

# --- JWT Claims ---
@jwt.additional_claims_loader
def add_role_to_access_token(identity):
    # Now that identity is just a string (email), we look up the user to attach their role
    user = User.query.filter_by(email=identity).first()
    return {'role': user.role if user else 'member'}

# --- Public Routes ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    # ... (existing check code) ...
    new_user = User(
        full_name=data['full_name'],
        email=data['email'],
        phone_number=data['phone_number'],
        city=data.get('city') # <--- ADD THIS LINE
    )
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/register-ngo', methods=['POST'])
def register_ngo():
    data = request.get_json()
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'error': 'Email already registered'}), 409
    
    try:
        # Create user account in the main PostgreSQL table, but tag them as an NGO
        new_user = User(
            full_name=data.get('ngo_name', ''), # Store NGO name as their main name
            email=data['email'],
            phone_number=data.get('contact_number', '0000000000'),
            city=data.get('address', 'Unknown'),
            role='ngo'  # <--- This is the magic key that gives them NGO permissions!
        )
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'NGO registered successfully'}), 201
        
    except Exception as error:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred'}), 500
    
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    # THE FIX: Only pass the email string!
    access_token = create_access_token(identity=user.email) 
    return jsonify(access_token=access_token)

@app.route('/api/camps/apply', methods=['POST'])
@jwt_required()
def apply_for_camp():
    data = request.get_json()
    # Basic validation — all 7 fields required
    required_fields = ['ngo_name', 'email', 'phone', 'city', 'state', 'camp_type', 'proposal_file']
    missing = [f for f in required_fields if f not in data or not data[f]]
    if missing:
        return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400

    # Only store known model fields to avoid unexpected keyword errors
    new_proposal = CampProposal(
        ngo_name=data['ngo_name'],
        email=data['email'],
        phone=data['phone'],
        city=data['city'],
        state=data['state'],
        camp_type=data['camp_type'],
        proposal_file=data['proposal_file'],
        location=data.get('location'),
        date=data.get('date'),
        description=data.get('description'),
        beneficiaries=data.get('beneficiaries'),
        volunteers_required=data.get('volunteers_required'),
        created_by=get_jwt_identity()
    )
    db.session.add(new_proposal)
    db.session.commit()

    return jsonify({'message': 'Camp proposal submitted successfully'}), 201

@app.route('/api/leadership', methods=['GET'])
def get_leadership():
    leaders = Leadership.query.all()
    return jsonify([{
        'id': l.id, 
        'name': l.name, 
        'role': l.position, 
        'imageUrl': l.image_url, 
        'linkedin': l.linkedin_url,
        'instagram': l.instagram_url,
        'bio': l.bio,
        'category': l.category
    } for l in leaders])

@app.route('/api/gallery', methods=['GET'])
def get_gallery():
    items = Gallery.query.all()
    return jsonify([{'id': i.id, 'image_url': i.image_url, 'caption': i.caption} for i in items])

@app.route('/api/reels', methods=['GET'])
def get_reels():
    reels = CampReel.query.all()
    return jsonify([{'id': r.id, 'videoUrl': r.video_url, 'title': r.title} for r in reels])

@app.route('/api/testimonials', methods=['GET'])
def get_testimonials():
    testimonials = Testimonial.query.all()
    return jsonify([{'id': t.id, 'text': t.text, 'author': t.author, 'authorPosition': t.author_position} for t in testimonials])

@app.route('/api/careers', methods=['GET'])
def get_careers():
    careers = Career.query.all()
    return jsonify([{'id': c.id, 'title': c.title, 'description': c.description, 'apply_link': c.apply_link} for c in careers])

@app.route('/api/admin/camps', methods=['GET'])
@admin_required
def get_all_camps():
    camps = CampProposal.query.all()
    return jsonify([{
        'id': c.id, 'ngo_name': c.ngo_name, 'email': c.email, 'status': c.status
    } for c in camps])

@app.route('/api/admin/camps/<int:camp_id>/status', methods=['PUT'])
@admin_required
def update_camp_status(camp_id):
    camp = CampProposal.query.get_or_404(camp_id)
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Status not provided'}), 400
    
    new_status = data['status']
    if new_status not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
    
    if new_status == 'rejected' and 'rejection_reason' not in data:
        return jsonify({'error': 'Rejection reason required'}), 400

    camp.status = new_status
    if new_status == 'rejected':
        camp.rejection_reason = data['rejection_reason']

    db.session.commit()
    return jsonify({'message': f'Camp {camp.id} status updated to {camp.status}'})

@app.route('/api/admin/gallery', methods=['POST'])
@admin_required
def add_gallery_item():
    data = request.get_json()
    if not data or 'image_url' not in data:
        return jsonify({'error': 'Image URL required'}), 400
    
    new_item = Gallery(image_url=data['image_url'], caption=data.get('caption'))
    db.session.add(new_item)
    db.session.commit()
    return jsonify({'id': new_item.id, 'image_url': new_item.image_url, 'caption': new_item.caption}), 201

@app.route('/api/admin/gallery/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_gallery_item(item_id):
    item = Gallery.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Gallery item deleted'})

@app.route('/api/admin/leadership', methods=['POST'])
@admin_required
def add_leadership():
    data = request.get_json()
    new_leader = Leadership(
        name=data['name'],
        position=data['position'],
        image_url=data.get('image_url', data.get('imageUrl')),
        linkedin_url=data.get('linkedin_url', data.get('linkedinUrl')),
        instagram_url=data.get('instagram_url', data.get('instagramUrl')), # Add this
        bio=data.get('bio'), # Add this
        category=data.get('category', 'Current Core Team') # Add this
    )
    db.session.add(new_leader)
    db.session.commit()
    return jsonify({'id': new_leader.id, 'message': 'Leader added'}), 201

@app.route('/api/admin/leadership/<int:leader_id>', methods=['PUT'])
@admin_required
def update_leadership(leader_id):
    leader = Leadership.query.get_or_404(leader_id)
    data = request.get_json()
    
    leader.name = data.get('name', leader.name)
    leader.position = data.get('position', leader.position)
    leader.image_url = data.get('imageUrl', data.get('image_url', leader.image_url))
    leader.linkedin_url = data.get('linkedinUrl', data.get('linkedin_url', leader.linkedin_url))
    
    db.session.commit()
    return jsonify({'message': 'Leadership profile updated'})

@app.route('/api/admin/leadership/<int:leader_id>', methods=['DELETE'])
@admin_required
def delete_leadership(leader_id):
    leader = Leadership.query.get_or_404(leader_id)
    db.session.delete(leader)
    db.session.commit()
    return jsonify({'message': 'Leadership profile deleted'})

@app.route('/api/me', methods=['GET'])
@jwt_required()
def get_current_user():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first_or_404()
    
    response = jsonify({
        'full_name': user.full_name,
        'role': user.role
    })
    
    # Force the browser to ignore its cache for this specific request
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    return response

@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    email = get_jwt_identity() # This is now just a string!
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'full_name': user.full_name,
        'email': user.email,
        'role': user.role,
        'phone': user.phone_number
    })

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user_email = get_jwt_identity()
    admin = User.query.filter_by(email=current_user_email).first()
    
    # Security: Only 'god' can purge users
    if not admin or admin.role not in ['god', 'it']:
        return jsonify({'error': 'Higher clearance required'}), 403
    
    user_to_delete = User.query.get_or_404(user_id)
    
    # Safety Check: Prevent accidental self-deletion
    if user_to_delete.email == current_user_email:
        return jsonify({'error': 'You cannot delete your own soul!'}), 400
        
    db.session.delete(user_to_delete)
    db.session.commit()
    return jsonify({'message': f'User {user_to_delete.full_name} has been purged.'})

@app.route('/api/admin/users', methods=['GET', 'POST'])
@admin_required # This ensures only Admin/God/IT can touch this
def manage_users():
    # --- METHOD 1: GET (Fetching the list for God Mode) ---
    if request.method == 'GET':
        users = User.query.all()
        return jsonify([{
            'id': u.id, 
            'full_name': u.full_name, 
            'email': u.email, 
            'role': u.role,
            'city': u.city
        } for u in users]), 200

    # --- METHOD 2: POST (Adding a new member from the form) ---
    if request.method == 'POST':
        data = request.get_json()
        
        # Validation
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'User already exists'}), 400

        new_user = User(
            full_name=data['full_name'],
            email=data['email'],
            phone_number=data.get('phone_number', '0000000000'),
            role=data.get('role', 'member'),
            city=data.get('city', 'Mumbai')
        )
        
        # Set a default temporary password
        new_user.set_password(data.get('password', 'MAAI2026!'))

        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'Member added successfully!'}), 201

# --- Gallery Admin ---
@app.route('/api/admin/gallery', methods=['GET'])
@jwt_required()
def admin_get_gallery():
    items = Gallery.query.order_by(Gallery.id.desc()).all()
    return jsonify([{'id': i.id, 'image_url': i.image_url, 'caption': i.caption} for i in items])

# --- Leadership Admin ---
@app.route('/api/admin/leadership', methods=['GET'])
@jwt_required()
def admin_get_leadership():
    leaders = Leadership.query.all()
    return jsonify([{'id': l.id, 'name': l.name, 'position': l.position, 'imageUrl': l.image_url, 'linkedinUrl': l.linkedin_url} for l in leaders])

# --- Careers Admin ---
@app.route('/api/admin/careers', methods=['GET'])
@jwt_required()
def admin_get_careers():
    jobs = Career.query.all()
    return jsonify([{'id': j.id, 'title': j.title, 'description': j.description} for j in jobs])

@app.route('/api/admin/careers/<int:career_id>', methods=['DELETE'])
@god_required
def delete_career(career_id):
    job = Career.query.get_or_404(career_id)
    db.session.delete(job)
    db.session.commit()
    return jsonify({'message': 'Job posting removed'})

@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
@god_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if not data or 'role' not in data:
        return jsonify({'error': 'No role provided'}), 400
        
    user.role = data['role']
    db.session.commit() # This makes it "stick" in PostgreSQL!
    return jsonify({'message': f'User {user.full_name} is now a {user.role}'})


@app.route('/api/admin/careers', methods=['POST'])
@admin_required
def add_career():
    data = request.get_json()
    new_job = Career(
        title=data['title'],
        description=data['description'],
        apply_link=data['apply_link']
    )
    db.session.add(new_job)
    db.session.commit()
    return jsonify({'message': 'Job posting published'}), 201

@app.route('/api/admin/reels', methods=['GET'])
@admin_required
def admin_get_reels():
    reels = CampReel.query.order_by(CampReel.id.desc()).all()
    return jsonify([{'id': r.id, 'title': r.title, 'videoUrl': r.video_url} for r in reels])

@app.route('/api/admin/reels', methods=['POST'])
@admin_required
def admin_handle_add_reel():
    data = request.get_json()
    if not data or 'video_url' not in data:
        return jsonify({'error': 'Video URL is required'}), 400
        
    new_reel = CampReel(
        title=data.get('title', 'New Reel'),
        video_url=data['video_url']
    )
    db.session.add(new_reel)
    db.session.commit()
    return jsonify({'message': 'Reel added successfully!'}), 201

@app.route('/api/admin/reels/<int:reel_id>', methods=['PUT'])
@admin_required
def update_reel(reel_id):
    reel = CampReel.query.get_or_404(reel_id)
    data = request.get_json()
    reel.title = data.get('title', reel.title)
    reel.video_url = data.get('videoUrl', data.get('video_url', reel.video_url))
    db.session.commit()
    return jsonify({'message': 'Reel updated'})

@app.route('/api/admin/testimonials', methods=['POST'])
@admin_required
def add_testimonial():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Testimonial text is required'}), 400
        
    new_test = Testimonial(
        author=data.get('author', 'Anonymous'),
        author_position=data.get('author_position', 'Volunteer'),
        text=data['text'],
        image_url=data.get('image_url')
    )
    db.session.add(new_test)
    db.session.commit()
    return jsonify({'message': 'Testimonial added successfully!'}), 201

@app.route('/api/admin/testimonials/<int:test_id>', methods=['PUT'])
@admin_required
def update_testimonial(test_id):
    test = Testimonial.query.get_or_404(test_id)
    data = request.get_json()
    test.author = data.get('author', test.author)
    test.author_position = data.get('authorPosition', data.get('author_position', test.author_position))
    test.text = data.get('text', test.text)
    db.session.commit()
    return jsonify({'message': 'Testimonial updated'})

@app.route('/api/admin/announcements', methods=['GET'])
@admin_required
def get_admin_announcements():
    notices = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return jsonify([{
        'id': a.id, 'title': a.title, 'content': a.content,
        'date': a.created_at.strftime('%Y-%m-%d')
    } for a in notices])

@app.route('/api/admin/announcements', methods=['POST'])
@admin_required
def send_broadcast():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Announcement content is required'}), 400
        
    new_notif = Announcement(
        title=data.get('title', 'Important Update'),
        content=data['content']
    )
    db.session.add(new_notif)
    db.session.commit()
    return jsonify({'message': 'Broadcast sent to all members'}), 201

@app.route('/api/admin/announcements/<int:ann_id>', methods=['PUT'])
@admin_required
def update_announcement(ann_id):
    ann = Announcement.query.get_or_404(ann_id)
    data = request.get_json()
    ann.title = data.get('title', ann.title)
    ann.content = data.get('content', ann.content)
    db.session.commit()
    return jsonify({'message': 'Announcement updated'})

def it_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        # Allows access to both 'god' and 'it' roles
        if claims.get('role') not in ['god', 'it']:
            return jsonify({'error': 'IT or God clearance required!'}), 403
        return fn(*args, **kwargs)
    return wrapper  
@app.route('/api/initiatives', methods=['GET'])
def get_initiatives():
    items = FlagshipInitiative.query.order_by(FlagshipInitiative.created_at.desc()).all()
    return jsonify([{'id': i.id, 'title': i.title, 'description': i.description, 'imageUrl': i.image_url, 'category': i.category, 'createdAt': i.created_at.strftime('%Y-%m-%d')} for i in items])

@app.route('/api/announcements', methods=['GET'])
def get_announcements_live():
    notices = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return jsonify([{
        'id': a.id, 'title': a.title, 'content': a.content, 
        'date': a.created_at.strftime('%Y-%m-%d')
    } for a in notices])

@app.route('/api/active-drives', methods=['GET'])
def get_active_drives():
    # Only show APPROVED proposals on the public website
    drives = CampProposal.query.filter_by(status='approved').all()
    return jsonify([{
        'title': d.camp_type, 
        'location': f"{d.city}, {d.state}", 
        'description': f"Coordinated with {d.ngo_name}",
        'category': d.camp_type
    } for d in drives])

@app.route('/api/camps', methods=['GET'])
def get_past_camps():
    camps = Camp.query.order_by(Camp.id.desc()).all()
    return jsonify([{
        'id': c.id, 
        'title': c.title, 
        'location': c.location, 
        'dateCompleted': c.date, # Matches frontend 'dateCompleted'
        'description': c.description, 
        'beneficiaries': c.beneficiaries, 
        'volunteers': c.volunteers,
        'imageUrl': c.image_url # Matches frontend 'imageUrl'
    } for c in camps])

@app.route('/api/admin/initiatives', methods=['POST'])
@admin_required
def create_initiative():
    try:
        data = request.get_json()
        
        # 1. Use .get() to prevent crashes if a field is missing
        # 2. Check for both 'image_url' and 'imageUrl' to be safe
        title = data.get('title')
        description = data.get('description')
        img = data.get('image_url') or data.get('imageUrl')
        cat = data.get('category', 'General')

        if not title or not description:
            return jsonify({'error': 'Title and Description are required'}), 400

        new_init = FlagshipInitiative(
            title=title,
            category=cat,
            image_url=img or "https://via.placeholder.com/800x400?text=MAAI+Initiative",
            description=description
        )
        
        db.session.add(new_init)
        db.session.commit()
        return jsonify({'message': 'Initiative created', 'id': new_init.id}), 201

    except Exception as e:
        db.session.rollback()
        # This will now appear in your Render "Logs" tab!
        print(f"DEBUG ERROR: {str(e)}") 
        return jsonify({'error': 'Server processed a bad request', 'details': str(e)}), 500

@app.route('/api/admin/initiatives/<int:item_id>', methods=['PUT'])
@admin_required
def update_initiative(item_id):
    item = FlagshipInitiative.query.get_or_404(item_id)
    data = request.get_json()
    item.title = data.get('title', item.title)
    item.description = data.get('description', item.description)
    item.image_url = data.get('imageUrl', data.get('image_url', item.image_url))
    item.category = data.get('category', item.category)
    db.session.commit()
    return jsonify({'message': 'Initiative updated'})

@app.route('/api/admin/camps', methods=['POST'])
@admin_required
def add_past_camp():
    data = request.get_json()
    new_camp = Camp(
        title=data['title'],
        location=data['location'],
        date=data.get('dateCompleted', data.get('date')),
        description=data['description'],
        beneficiaries=data.get('beneficiaries', 0),
        volunteers=data.get('volunteers', 0),
        image_url=data.get('imageUrl', data.get('image_url'))
    )
    db.session.add(new_camp)
    db.session.commit()
    return jsonify({'message': 'Past camp record created'}), 201

@app.route('/api/admin/camps/<int:camp_id>', methods=['PUT'])
@admin_required
def update_camp(camp_id):
    camp = Camp.query.get_or_404(camp_id)
    data = request.get_json()
    camp.title = data.get('title', camp.title)
    camp.location = data.get('location', camp.location)
    camp.date = data.get('dateCompleted', data.get('date', camp.date))
    camp.description = data.get('description', camp.description)
    camp.beneficiaries = data.get('beneficiaries', camp.beneficiaries)
    camp.volunteers = data.get('volunteers', camp.volunteers)
    camp.image_url = data.get('imageUrl', data.get('image_url', camp.image_url))
    db.session.commit()
    return jsonify({'message': 'Camp updated'})

@app.route('/api/admin/initiatives/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_initiative(item_id):
    item = FlagshipInitiative.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Initiative deleted'})

@app.route('/api/admin/camps/<int:camp_id>', methods=['DELETE'])
@admin_required
def delete_camp(camp_id):
    camp = Camp.query.get_or_404(camp_id)
    db.session.delete(camp)
    db.session.commit()
    return jsonify({'message': 'Camp deleted'})

@app.route('/api/admin/reels/<int:reel_id>', methods=['DELETE'])
@admin_required
def delete_reel(reel_id):
    reel = CampReel.query.get_or_404(reel_id)
    db.session.delete(reel)
    db.session.commit()
    return jsonify({'message': 'Reel deleted'})

@app.route('/api/admin/testimonials/<int:test_id>', methods=['DELETE'])
@admin_required
def delete_testimonial(test_id):
    test = Testimonial.query.get_or_404(test_id)
    db.session.delete(test)
    db.session.commit()
    return jsonify({'message': 'Testimonial deleted'})

@app.route('/api/admin/announcements/<int:ann_id>', methods=['DELETE'])
@admin_required
def delete_announcement(ann_id):
    ann = Announcement.query.get_or_404(ann_id)
    db.session.delete(ann)
    db.session.commit()
    return jsonify({'message': 'Announcement deleted'})

@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def get_admin_stats():
    total_users = User.query.count()
    active_volunteers = User.query.filter_by(role='member').count()
    pending_requests = CampProposal.query.filter_by(status='pending').count()
    return jsonify({
        'total_users': total_users,
        'active_volunteers': active_volunteers,
        'pending_requests': pending_requests
    })

@app.route('/api/stats', methods=['GET'])
def get_platform_stats():
    # 1. Count total completed camps
    total_camps = Camp.query.count()
    
    # 2. Sum up all beneficiaries from those camps
    db_beneficiaries = db.session.query(func.sum(Camp.beneficiaries)).scalar() or 0
    
    # 3. Sum up all volunteers engaged
    db_volunteers = db.session.query(func.sum(Camp.volunteers)).scalar() or 0
    
    # PRO-TIP: Add your established base numbers so your site never 
    # dips below your current achievements (22, 8100, 1100) while you migrate!
    return jsonify({
        'camps': total_camps + 22,
        'beneficiaries': db_beneficiaries + 8100,
        'volunteers': db_volunteers + 1100
    })

@app.route('/api/admin/settings', methods=['GET'])
@admin_required
def get_settings():
    settings = SystemSetting.query.all()
    return jsonify({s.key: s.value for s in settings})

@app.route('/api/admin/settings', methods=['POST'])
@admin_required
def update_settings():
    data = request.get_json()
    for key, value in data.items():
        setting = SystemSetting.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            db.session.add(SystemSetting(key=key, value=str(value)))
    db.session.commit()
    return jsonify({'message': 'Settings updated'})


@app.route('/api/initiatives/<int:item_id>', methods=['GET'])
def get_single_initiative(item_id):
    # This looks into your FlagshipInitiative table for the specific ID
    item = FlagshipInitiative.query.get_or_404(item_id)
    return jsonify({
        'id': item.id,
        'title': item.title,
        'category': item.category,
        'description': item.description,
        'imageUrl': item.image_url,
        'date': item.created_at.strftime('%d %B %Y')
    })

# ... after all your routes and models ...

# This ensures tables are created even when running on Render/Gunicorn
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)