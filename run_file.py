from pkg import create_app, db

app = create_app()

with app.app_context():
    db.create_all()
    from pkg import routes, vendor_routes, admin_routes
    from pkg import forms
    from setup import *
    create_categories()

if __name__ == "__main__":
    app.run(debug=True)
