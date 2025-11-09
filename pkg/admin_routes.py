from flask import (
    render_template, redirect, flash, request, session, url_for, current_app as app, abort
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from datetime import datetime
import os, secrets

from pkg.forms import VendorSignupForm, AdminSignupForm, AssetForm, AssignmentForm, AdminLoginForm
from pkg.models import (
    db, Vendor, Asset, AssetCategory, AssetAssignment,
    AssetStatusHistory, AssetStatus, Admin
)

@app.route('/admin_signup/', methods=['GET', 'POST'])
def admin_signup():
    form = AdminSignupForm()
    if form.validate_on_submit():
        pw = form.password.data
        cpw = form.confirm_password.data

        # Check if username already exists
        existing_admin = Admin.query.filter_by(admin_username=form.username.data).first()
        if existing_admin:
            flash("Username already exists. Please choose another one.", "error")
            return render_template('admin/admin_signup.html', form=form)

        if pw != cpw:
            flash("Passwords do not match", 'error')
        else:
            hashed_password = generate_password_hash(pw)
            new_admin = Admin(
                admin_username=form.username.data,
                admin_password=hashed_password,
                admin_department=form.department.data,
                admin_last_login=datetime.utcnow()
            )
            db.session.add(new_admin)
            db.session.commit()
            flash('Admin account created successfully!', 'success')
            return redirect(url_for('admin_login'))
    return render_template('admin/admin_signup.html', form=form)

@app.route('/admin_login/', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm() 
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        admin_record = Admin.query.filter_by(admin_username=username).first()
        if admin_record and check_password_hash(admin_record.admin_password, password):
            session['admin_loggedin'] = admin_record.admin_id
            session['admin_username'] = admin_record.admin_username
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid username or password", "error")
            return redirect('/admin_login/')
    return render_template('admin/admin_login.html', admin=form)



# admin_required decorator
def admin_required(fn):
    def wrapper(*args, **kwargs):
        if not session.get("admin_loggedin"):
            flash("Admin login required", "error")
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

# ---------- DASHBOARD ----------
@app.route("/admin/")
@admin_required
def admin_dashboard():
    admin = AdminLoginForm()
    total_vendors = db.session.query(func.count(Vendor.id)).scalar() or 0
    total_assets = db.session.query(func.count(Asset.id)).scalar() or 0
    status_counts = {
        "inventory": db.session.query(func.count(Asset.id)).filter(Asset.current_status == AssetStatus.INVENTORY).scalar() or 0,
        "assigned": db.session.query(func.count(Asset.id)).filter(Asset.current_status == AssetStatus.ASSIGNED).scalar() or 0,
        "repair": db.session.query(func.count(Asset.id)).filter(Asset.current_status == AssetStatus.REPAIR).scalar() or 0,
        "retired": db.session.query(func.count(Asset.id)).filter(Asset.current_status == AssetStatus.RETIRED).scalar() or 0,
    }

    latest_assets = db.session.query(Asset, Vendor.vendor_name, AssetCategory.name.label("category_name"))\
        .join(Vendor, Vendor.id == Asset.vendor_id, isouter=True)\
        .join(AssetCategory, AssetCategory.id == Asset.category_id, isouter=True)\
        .order_by(Asset.created_at.desc())\
        .limit(6).all()

    return render_template(
        "admin/admin_dashboard.html",
        admin=admin,
        total_vendors=total_vendors,
        total_assets=total_assets,
        status_counts=status_counts,
        latest_assets=latest_assets
    )

# ---------- VENDORS ----------
@app.route("/admin/vendors/")
@admin_required
def admin_manage_vendors():
    vendors = Vendor.query.order_by(Vendor.date_registered.desc()).all()
    form = VendorSignupForm()
    return render_template("admin/manage_vendors.html", vendors=vendors, form=form)

@app.route("/admin/vendors/add/", methods=["POST"])
@admin_required
def admin_add_vendor():
    form = VendorSignupForm()
    if form.validate_on_submit():
        ven_pw = form.vendor_password.data
        confirm_ven_pw = form.vendor_confirm_password.data
        if ven_pw != confirm_ven_pw:
            flash("passwords do not match", "error")
        else:
            hashed = generate_password_hash(ven_pw)
            new_vendor = Vendor(
                vendor_name=form.vendor_name.data,
                vendor_email=form.vendor_email.data,
                vendor_password=hashed,
                
            )
            db.session.add(new_vendor)
            db.session.commit()
            flash("Vendor added successfully", "success")
    else:
        flash("Please check vendor form fields", "error")
    return redirect(url_for("admin_manage_vendors"))

@app.route("/admin/vendors/delete/<int:vendor_id>/", methods=["POST"])
@admin_required
def admin_delete_vendor(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    assets_count = Asset.query.filter_by(vendor_id=vendor.id).count()
    if assets_count:
        flash("Vendor has assets. Reassign/delete assets first.", "error")
        return redirect(url_for("admin_manage_vendors"))
    db.session.delete(vendor)
    db.session.commit()
    flash("Vendor deleted", "success")
    return redirect(url_for("admin_manage_vendors"))

# ---------- ASSETS ----------
@app.route("/admin/assets/")
@admin_required
def admin_manage_assets():
    assets = db.session.query(Asset, Vendor.vendor_name, AssetCategory.name.label("category_name"))\
        .join(Vendor, Vendor.id == Asset.vendor_id, isouter=True)\
        .join(AssetCategory, AssetCategory.id == Asset.category_id, isouter=True)\
        .order_by(Asset.created_at.desc()).all()
    form = AssetForm()
    form.populate_categories()
    return render_template("admin/manage_assets.html", assets=assets, form=form)

@app.route("/admin/assets/add/", methods=["POST"])
@admin_required
def admin_add_asset():
    form = AssetForm()
    form.populate_categories()
    if not form.validate_on_submit():
        flash("Please fix the errors on the form.", "error")
        return redirect(url_for("admin_manage_assets"))

    new_asset = Asset(
        name=form.name.data,
        serial_number=form.serial_number.data,
        model_number=form.model_number.data,
        make=form.make.data,
        category_id=form.category_id.data,
        quantity=form.quantity.data,
        current_holder=form.current_holder.data,
        vendor_id=form.vendor_id.data,
        current_status=AssetStatus[form.current_status.data]
    )


    if form.picture.data:
        upload_folder = os.path.join(app.root_path, "static", "uploaded")
        os.makedirs(upload_folder, exist_ok=True)
        filename = secure_filename(form.picture.data.filename)
        prefix = secrets.token_hex(8)
        filename = f"{prefix}_{filename}"
        file_path = os.path.join(upload_folder, filename)
        form.picture.data.save(file_path)
        new_asset.picture = filename

    db.session.add(new_asset)
    db.session.commit()
    flash("Asset added successfully", "success")
    return redirect(url_for("admin_manage_assets"))

@app.route("/admin/assets/delete/<int:asset_id>/", methods=["POST"])
@admin_required
def admin_delete_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    if asset.picture:
        try:
            os.remove(os.path.join(app.root_path, "static", "uploaded", asset.picture))
        except Exception:
            pass
    db.session.delete(asset)
    db.session.commit()
    flash("Asset deleted", "success")
    return redirect(url_for("admin_manage_assets"))

@app.route("/admin/assets/status/<int:asset_id>/", methods=["POST"])
@admin_required
def admin_change_asset_status(asset_id):
    new_status = request.form.get("status")
    changed_by = session.get("admin_username", "admin")
    note = request.form.get("note", "")
    asset = Asset.query.get_or_404(asset_id)
    try:
        asset.current_status = AssetStatus[new_status]
    except Exception:
        flash("Invalid status", "error")
        return redirect(url_for("admin_manage_assets"))

    history = AssetStatusHistory(
        asset_id=asset.id,
        status=asset.current_status,
        changed_by=changed_by,
        note=note
    )
    db.session.add(history)
    db.session.commit()
    flash("Status updated", "success")
    return redirect(url_for("admin_manage_assets"))

# ---------- ASSIGNMENTS ----------
@app.route("/admin/assignments/")
@admin_required
def admin_view_assignments():
    assignments = db.session.query(AssetAssignment, Asset.name.label("asset_name"))\
        .join(Asset, Asset.id == AssetAssignment.asset_id)\
        .order_by(AssetAssignment.assigned_at.desc()).all()
    form = AssignmentForm()
    return render_template("admin/view_assignments.html", assignments=assignments, form=form)

@app.route("/admin/assignments/assign/<int:asset_id>/", methods=["POST"])
@admin_required
def admin_assign_asset(asset_id):
    form = AssignmentForm()
    if not form.validate_on_submit():
        flash("Please provide assignee name", "error")
        return redirect(url_for("admin_view_assignments"))

    assignment = AssetAssignment(
        asset_id=asset_id,
        assigned_to=form.assigned_to.data,
        assigned_at=None
    )
    asset = Asset.query.get_or_404(asset_id)
    asset.current_holder = form.assigned_to.data
    asset.current_status = AssetStatus.ASSIGNED

    db.session.add(assignment)
    db.session.commit()
    flash("Asset assigned", "success")
    return redirect(url_for("admin_view_assignments"))


@app.route("/admin/assign/<int:asset_id>/", methods=["GET", "POST"])
@admin_required
def admin_assigning_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    form = AssignmentForm()

    if form.validate_on_submit():
        new_assignment = AssetAssignment(
            asset_id=asset.id,
            assigned_to=form.assigned_to.data,
            assigned_at=datetime.utcnow(),
        )
        asset.current_holder = form.assigned_to.data
        asset.current_status = AssetStatus.ASSIGNED
        status_change = AssetStatusHistory(
            asset_id=asset.id,
            status=AssetStatus.ASSIGNED,
            changed_by=form.assigned_by.data or "Admin",
            note=form.note.data or "",
        )
        db.session.add(new_assignment)
        db.session.add(status_change)
        db.session.commit()

        flash(f"Asset '{asset.name}' assigned to {form.assigned_to.data}", "success")
        return redirect(url_for("admin_view_assignments"))

    return render_template("admin/assign_asset.html", asset=asset, form=form)

# ---------- HISTORY ----------
@app.route("/admin/history/<int:asset_id>/")
@admin_required
def admin_view_status_history(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    history = AssetStatusHistory.query.filter_by(asset_id=asset_id).order_by(AssetStatusHistory.timestamp.desc()).all()
    assignments = AssetAssignment.query.filter_by(asset_id=asset_id).order_by(AssetAssignment.assigned_at.desc()).all()
    return render_template("admin/view_status_history.html", asset=asset, history=history, assignments=assignments)


@app.route('/admin/vendor/<int:vendor_id>/assets')
def view_vendor_assets(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    vendor_assets = db.session.query(Asset, AssetCategory.name).join(
        AssetCategory, Asset.category_id == AssetCategory.id
    ).filter(Asset.vendor_id == vendor_id).all()
    total_quantity = db.session.query(func.sum(Asset.quantity)).filter(
        Asset.vendor_id == vendor_id
    ).scalar() or 0
    return render_template(
        'admin/vendor_assets.html',
        vendor=vendor,
        vendor_assets=vendor_assets,
        total_quantity=int(total_quantity)
    )


@app.route("/admin_logout/")
def admin_logout():
    session.pop("admin_loggedin", None)
    return redirect('/')

