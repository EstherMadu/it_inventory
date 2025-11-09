from flask import render_template, redirect, flash, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import generate_csrf
from flask import current_app as app
from sqlalchemy import func

from pkg.forms import AssetForm, VendorSignupForm, Vendorlogform
from pkg.models import Vendor, Asset, AssetCategory, db
from werkzeug.utils import secure_filename
import os
import secrets


@app.route('/vendor-signup/', methods=['GET', 'POST'])
def handle_vendor_signup():
    vendor = VendorSignupForm()
    if vendor.validate_on_submit():
        if vendor.vendor_password.data != vendor.vendor_confirm_password.data:
            flash('Password mismatch, please try again', 'errormsg')
            return render_template('vendor/vendor_signup.html', vendor=vendor)
        hashed = generate_password_hash(vendor.vendor_password.data)
        new_vendor = Vendor(
            vendor_name=vendor.vendor_name.data,
            vendor_email=vendor.vendor_email.data,
            vendor_password=hashed
        )
        db.session.add(new_vendor)
        db.session.commit()
        flash('An account has been created for you', 'feedback')
        return redirect('/vendor-login/')
    return render_template('vendor/vendor_signup.html', vendor=vendor)

@app.route('/vendor-login/', methods=['GET', 'POST'])  
def vendor_login():
    vendor = Vendorlogform()
    if request.method == "GET":
        return render_template('vendor/vendor_login.html', vendor=vendor)
    else:
        if vendor.validate_on_submit():
            email = request.form.get('email')
            password = request.form.get('password')
            print(password)
            check_record = db.session.query(Vendor).filter(Vendor.vendor_email == email).first()
            print(check_record)
            if check_record:
                session["vendor_loggedin"] = check_record.id
                flash('You were successfully logged in!', 'success')
                return redirect('/vendor/')
            else:
                flash('Invalid username or password.', 'error')
    return render_template('vendor/vendor_login.html', vendor=vendor)

@app.route('/vendor/')
def vendor():
    vendor_id = session.get("vendor_loggedin")
    if not vendor_id:
        flash('You need to log in first!', 'error')
        return redirect('/vendor-login/')

    vendor = db.session.query(Vendor).filter(Vendor.id == vendor_id).first()
    vendeets = db.session.query(Asset, AssetCategory.name)\
    .join(AssetCategory, AssetCategory.id == Asset.category_id)\
    .filter(Asset.vendor_id == vendor_id).all()
    total = len(vendeets)
    quantity = db.session.query(
        func.sum(Asset.quantity)
    ).filter(
        Asset.vendor_id == vendor_id
    ).scalar() or 0
    quantity = int(quantity)
    print(vendeets)
    if not vendor:
        flash('Vendor not found', 'error')
        return redirect('/vendor-login/')

    form = AssetForm()
    form.populate_categories()  

    return render_template(
        'vendor/vendor_dashboard.html',
        vendor_name=vendor.vendor_name,
        vendeets=vendeets, total=total,
        quantity=quantity, form=form  
    )


@app.route('/vendor-add-asset/', methods=['GET', 'POST'])
def vendor_addasset():
    vendor_id = session.get("vendor_loggedin")
    if not vendor_id or not db.session.query(Vendor).filter(Vendor.id == vendor_id).first():
        flash('You need to log in first!', 'error')
        return redirect('/vendor-login/')

    form = AssetForm()
    form.populate_categories()

    # GET or failed validation
    if request.method == "GET":
        return render_template('vendor/vendor_dashboard.html', form=form)

    # Handle form submission
    new_asset = Asset(
        name=form.name.data,
        serial_number=form.serial_number.data,
        model_number=form.model_number.data,
        make=form.make.data,
        category_id=form.category_id.data,
        quantity=form.quantity.data,
        current_holder=form.current_holder.data,
        vendor_id=vendor_id
        
    )

    if form.picture.data:
        upload_folder = os.path.join(app.root_path, 'static', 'uploaded')
        os.makedirs(upload_folder, exist_ok=True)
        filename = secure_filename(form.picture.data.filename)
        file_path = os.path.join(upload_folder, filename)
        form.picture.data.save(file_path)
        new_asset.picture = filename

    db.session.add(new_asset)
    db.session.commit()

    flash('Product added successfully!', 'success')
    return redirect(url_for('vendor'))

@app.route("/vendor-logout/")
def vendor_logout():
    session.pop('vendor_loggedin', None)
    return redirect('/')