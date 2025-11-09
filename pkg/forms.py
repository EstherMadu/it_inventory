from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FileField,  PasswordField, SubmitField, TextAreaField
from flask_wtf.file import FileAllowed
from wtforms.validators import DataRequired, Email, Optional
from pkg.models import AssetStatus
from enum import Enum


class VendorSignupForm(FlaskForm):
   vendor_name = StringField('Vendor Name', validators=[DataRequired()])
   vendor_email = StringField('Email',
                        validators=[DataRequired(message="Email is required"), Email(message="Enter a valid email")])
   vendor_contact_info = StringField('Contact Info')
   vendor_password = PasswordField('Password', validators=[DataRequired()])
   vendor_confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
   submit = SubmitField("Save Vendor")

class Vendorlogform(FlaskForm):
    email = StringField("Email", validators=[Optional()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField("Save Vendor")

class AssetForm(FlaskForm):
    name = StringField("Asset Name", validators=[DataRequired()])
    serial_number = StringField("Serial Number", validators=[DataRequired()])
    model_number = StringField("Model Number")
    make = StringField("Make / Manufacturer")
    quantity = StringField("Quantity", validators=[DataRequired()])
    picture = FileField('Product Picture',
                            validators=[FileAllowed(['jpg', 'png', 'jpeg'],
                                                    'Images only!')])
    vendor_id = SelectField("Vendor", coerce=int, validators=[DataRequired()])
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    current_status = SelectField(
        "Status",
        choices=[(status.name, status.value) for status in AssetStatus],
        validators=[DataRequired()]
    )
    current_holder = StringField("Current Holder")
    submit = SubmitField("Add Asset")

    def populate_categories(self):
        from pkg.models import AssetCategory, Vendor
        self.category_id.choices = [
            (cat.id, cat.name)
            for cat in AssetCategory.query.order_by(AssetCategory.name).all()
        ]
        self.vendor_id.choices = [
            (v.id, v.vendor_name)
            for v in Vendor.query.order_by(Vendor.vendor_name).all()
        ]

class AssignmentForm(FlaskForm):
    assigned_to = StringField("Assign to (name/department)", validators=[DataRequired()])
    assigned_by = StringField("Assigned by", validators=[Optional()])
    note = TextAreaField("Note", validators=[Optional()])
    submit = SubmitField("Assign")

class AdminSignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    department = SelectField('Department', choices=[('IT', 'IT'), ('HR', 'HR'), ('Finance', 'Finance')])
    submit = SubmitField('Sign Up')

class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')