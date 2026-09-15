"""
Database Models for Integrated Fitness Ecosystem
Gym Management + Personal Fitness Tracker + AI Coach
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

# ============================================================================
# 1. USER & AUTHENTICATION MODELS
# ============================================================================

class User(UserMixin, db.Model):
    """Staff/Admin/Trainer users"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='staff')  # 'admin', 'staff', 'trainer'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    staff_profile = db.relationship('Staff', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Staff(db.Model):
    """Staff/Trainer profiles"""
    __tablename__ = 'staff'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    specialties = db.Column(db.Text)  # comma-separated: 'Yoga,HIIT,Boxing'
    hourly_rate = db.Column(db.Float)
    hire_date = db.Column(db.Date, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    classes = db.relationship('Class', backref='instructor', lazy=True)
    
    def __repr__(self):
        return f'<Staff {self.first_name} {self.last_name}>'


# ============================================================================
# 2. MEMBER MODELS
# ============================================================================

class Member(UserMixin, db.Model):
    """Gym members"""
    __tablename__ = 'members'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))  # 'M', 'F'
    join_date = db.Column(db.Date, default=datetime.utcnow)
    profile_photo = db.Column(db.LargeBinary)  # Store as BLOB
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    memberships = db.relationship('Membership', backref='member', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='member', lazy=True, cascade='all, delete-orphan')
    workouts = db.relationship('Workout', backref='member', lazy=True, cascade='all, delete-orphan')
    class_attendances = db.relationship('ClassAttendance', backref='member', lazy=True, cascade='all, delete-orphan')
    goals = db.relationship('MemberGoal', backref='member', lazy=True, cascade='all, delete-orphan')
    measurements = db.relationship('MemberMeasurement', backref='member', lazy=True, cascade='all, delete-orphan')
    muscle_recovery = db.relationship('MuscleRecovery', backref='member', lazy=True, cascade='all, delete-orphan')
    ai_logs = db.relationship('AICoachLog', backref='member', lazy=True, cascade='all, delete-orphan')
    
    def get_current_membership(self):
        """Get active membership"""
        return Membership.query.filter(
            Membership.member_id == self.id,
            Membership.status == 'Active'
        ).first()
    
    def get_membership_status(self):
        """Check membership status"""
        membership = self.get_current_membership()
        if not membership:
            return 'No Active Membership'
        return membership.status
    
    def __repr__(self):
        return f'<Member {self.first_name} {self.last_name}>'


# ============================================================================
# 3. MEMBERSHIP & BILLING MODELS
# ============================================================================

class Membership(db.Model):
    """Member memberships"""
    __tablename__ = 'memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    membership_type = db.Column(db.String(20), nullable=False)  # 'Basic', 'Premium', 'VIP'
    start_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.Date)
    monthly_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Active')  # 'Active', 'Expired', 'Paused', 'Cancelled'
    renewal_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Membership {self.membership_type} - {self.status}>'


class Payment(db.Model):
    """Payment transactions"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    payment_method = db.Column(db.String(50))  # 'Cash', 'Credit Card', 'Transfer'
    payment_type = db.Column(db.String(50))  # 'Membership', 'Class', 'Training'
    description = db.Column(db.Text)
    receipt_number = db.Column(db.String(50), unique=True)
    is_confirmed = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.payment_type} - ${self.amount}>'


# ============================================================================
# 4. GYM LAYOUT & MACHINES/EXERCISES MODELS
# ============================================================================

class GymZone(db.Model):
    """Gym zones/areas"""
    __tablename__ = 'gym_zones'
    
    id = db.Column(db.Integer, primary_key=True)
    zone_name = db.Column(db.String(100), nullable=False)
    location_type = db.Column(db.String(50))  # 'Cardio Zone', 'Weights Zone', 'Stretching Area'
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    machines = db.relationship('GymMachine', backref='zone', lazy=True)
    
    def __repr__(self):
        return f'<GymZone {self.zone_name}>'


class GymMachine(db.Model):
    """Gym machines (from 1,324 exercise dataset)"""
    __tablename__ = 'gym_machines'
    
    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.String(50))  # ID from exercises.json
    name = db.Column(db.String(200), nullable=False)  # e.g., "Barbell Bench Press"
    zone_id = db.Column(db.Integer, db.ForeignKey('gym_zones.id'))
    location_x = db.Column(db.Float)  # For 2D/3D map
    location_y = db.Column(db.Float)
    location_z = db.Column(db.Float)  # For 3D visualization
    
    # Exercise data (from dataset)
    category = db.Column(db.String(100))  # Body part: 'chest', 'back', 'legs'
    target_muscle = db.Column(db.String(100))  # 'biceps', 'pectorals', etc.
    muscle_group = db.Column(db.String(100))  # Supporting muscles
    equipment = db.Column(db.String(100))  # 'barbell', 'dumbbell', 'cable', 'body weight'
    
    # Media & Instructions
    instructions_en = db.Column(db.Text)  # English instructions
    instructions_es = db.Column(db.Text)  # Spanish
    instructions_fr = db.Column(db.Text)  # French
    instructions_ar = db.Column(db.Text)  # Arabic (optional)
    
    video_url = db.Column(db.String(500))  # Link to how-to video/GIF
    image_url = db.Column(db.String(500))  # Thumbnail
    
    difficulty_level = db.Column(db.String(20))  # 'Beginner', 'Intermediate', 'Advanced'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    workout_exercises = db.relationship('WorkoutExercise', backref='machine', lazy=True)
    
    def __repr__(self):
        return f'<GymMachine {self.name}>'


# ============================================================================
# 5. WORKOUT & EXERCISE LOGGING MODELS
# ============================================================================

class Workout(db.Model):
    """Member workouts"""
    __tablename__ = 'workouts'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    workout_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    duration_minutes = db.Column(db.Integer)  # Total workout duration
    intensity = db.Column(db.String(20))  # 'Light', 'Moderate', 'Heavy'
    total_volume_kg = db.Column(db.Float)  # Total weight lifted
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    exercises = db.relationship('WorkoutExercise', backref='workout', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Workout {self.member_id} - {self.workout_date}>'


class WorkoutExercise(db.Model):
    """Individual exercises in a workout"""
    __tablename__ = 'workout_exercises'
    
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workouts.id'), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey('gym_machines.id'), nullable=False)
    
    sets = db.Column(db.Integer)  # Number of sets
    reps = db.Column(db.Integer)  # Reps per set
    weight_kg = db.Column(db.Float)  # Weight used
    form_rating = db.Column(db.Integer)  # 1-10 form quality
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<WorkoutExercise {self.sets}x{self.reps} @ {self.weight_kg}kg>'


# ============================================================================
# 6. CLASSES & ATTENDANCE MODELS
# ============================================================================

class Class(db.Model):
    """Gym classes"""
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 'Yoga', 'Boxing', 'HIIT'
    instructor_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)  # 'Monday', 'Tuesday'
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    capacity = db.Column(db.Integer, default=20)
    room_location = db.Column(db.String(50))
    difficulty_level = db.Column(db.String(20))  # 'Beginner', 'Intermediate', 'Advanced'
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendances = db.relationship('ClassAttendance', backref='class_', lazy=True, cascade='all, delete-orphan')
    
    def get_enrolled_count(self):
        """Count current enrollments"""
        return ClassAttendance.query.filter_by(class_id=self.id, status='Enrolled').count()
    
    def __repr__(self):
        return f'<Class {self.name}>'


class ClassAttendance(db.Model):
    """Class attendance tracking"""
    __tablename__ = 'class_attendances'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False)
    check_in_time = db.Column(db.Time)
    status = db.Column(db.String(20), default='Present')  # 'Present', 'Absent', 'Late', 'Enrolled'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ClassAttendance {self.member_id} - {self.status}>'


# ============================================================================
# 7. MEMBER HEALTH & PROGRESS MODELS
# ============================================================================

class MemberGoal(db.Model):
    """Member fitness goals"""
    __tablename__ = 'member_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    goal_type = db.Column(db.String(50), nullable=False)  # 'Weight Loss', 'Strength', 'Endurance'
    target_value = db.Column(db.Float)  # Target metric
    current_value = db.Column(db.Float)  # Current metric
    start_date = db.Column(db.Date, default=datetime.utcnow)
    target_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Active')  # 'Active', 'Completed', 'Paused'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_progress_percentage(self):
        """Calculate progress %"""
        if not self.target_value or not self.current_value:
            return 0
        return (self.current_value / self.target_value) * 100
    
    def __repr__(self):
        return f'<MemberGoal {self.goal_type} - {self.status}>'


class MemberMeasurement(db.Model):
    """Member body measurements"""
    __tablename__ = 'member_measurements'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    measurement_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    
    weight_kg = db.Column(db.Float)  # Weight in kg
    chest_cm = db.Column(db.Float)
    waist_cm = db.Column(db.Float)
    arms_cm = db.Column(db.Float)
    legs_cm = db.Column(db.Float)
    body_fat_percentage = db.Column(db.Float)
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Measurement {self.weight_kg}kg - {self.measurement_date}>'


class MuscleRecovery(db.Model):
    """Muscle group recovery tracking (for 3D visualization)"""
    __tablename__ = 'muscle_recovery'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    muscle_group = db.Column(db.String(50), nullable=False)  # 'Chest', 'Back', 'Biceps', etc.
    recovery_percentage = db.Column(db.Integer, default=100)  # 0-100%
    last_trained_date = db.Column(db.Date)
    
    def calculate_recovery(self):
        """Calculate recovery % based on time since last training"""
        from datetime import timedelta
        if not self.last_trained_date:
            return 100
        
        days_since = (datetime.utcnow().date() - self.last_trained_date).days
        # Assume 48 hours = full recovery
        recovery = min((days_since * 50), 100)  # 50% per day, max 100%
        return int(recovery)
    
    def __repr__(self):
        return f'<MuscleRecovery {self.muscle_group} - {self.recovery_percentage}%>'


# ============================================================================
# 8. AI COACHING MODEL
# ============================================================================

class AICoachLog(db.Model):
    """Log of AI coach conversations"""
    __tablename__ = 'ai_coach_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    response_type = db.Column(db.String(50))  # 'Form Tip', 'Recommendation', 'Motivation', etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AICoachLog {self.member_id} - {self.timestamp}>'


# ============================================================================
# 9. ANALYTICS MODEL
# ============================================================================

class MemberActivityLog(db.Model):
    """Track member activity for analytics"""
    __tablename__ = 'member_activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    activity_type = db.Column(db.String(50))  # 'login', 'workout_start', 'class_join', 'ai_chat'
    activity_data = db.Column(db.Text)  # JSON data if needed
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ActivityLog {self.activity_type} - {self.timestamp}>'
