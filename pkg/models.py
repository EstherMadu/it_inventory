from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
import enum

db = SQLAlchemy()

class AssetStatus(enum.Enum):
    INVENTORY = "inventory"
    ASSIGNED = "assigned"
    REPAIR = "repair"
    RETIRED = "retired"

class Vendor(db.Model):
    __tablename__ = "vendors"
    id = db.Column(db.Integer, primary_key=True)
    vendor_name = db.Column(db.String(140), nullable=False)
    vendor_email = db.Column(db.String(20), nullable=False)
    vendor_password = db.Column(db.String(20), nullable=False)
    assets = db.relationship("Asset", backref="vendor", lazy="dynamic")
    date_registered = db.Column(db.DateTime(), default=datetime.utcnow)

class AssetCategory(db.Model):
    __tablename__ = "asset_categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False, unique=True)
    assets = db.relationship("Asset", backref="category", lazy="dynamic")

class Asset(db.Model):
    __tablename__ = "assets"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    serial_number = db.Column(db.String(140), unique=True)
    model_number = db.Column(db.String(140))
    make = db.Column(db.String(140))
    picture = db.Column(db.String(256))
    quantity = db.Column(db.String(256))
    vendor_id = db.Column(db.Integer, db.ForeignKey("vendors.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("asset_categories.id"))
    current_status = db.Column(Enum(AssetStatus), default=AssetStatus.INVENTORY, nullable=False)
    current_holder = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assignments = db.relationship("AssetAssignment", backref="asset", lazy="dynamic")
    status_history = db.relationship("AssetStatusHistory", backref="asset", lazy="dynamic")

class AssetAssignment(db.Model):
    __tablename__ = "asset_assignments"
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"))
    assigned_to = db.Column(db.String(128), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    returned_at = db.Column(db.DateTime)

class AssetStatusHistory(db.Model):
    __tablename__ = "asset_status_history"
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id"))
    status = db.Column(Enum(AssetStatus), nullable=False)
    changed_by = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.String(256))

class Admin(db.Model):
    __tablename__ = 'admin'
    admin_id = db.Column(db.Integer, primary_key=True)
    admin_username = db.Column(db.String(75), unique=True, nullable=False)
    admin_department = db.Column(db.String(100), nullable=False)
    admin_password = db.Column(db.String(200), nullable=False)
    admin_last_login = db.Column(db.DateTime, nullable=False)


