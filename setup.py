from datetime import datetime
import os
import shutil


def create_categories():
    from pkg.models import AssetCategory, db
    # List of categories to populate
    categories = ["Laptop", "Monitors", "Cables", "Keyboards", "Mouse"]

    # I am checking if the categories already exist in the database
    existing_categories = AssetCategory.query.count()
    if existing_categories > 0:
        print(f"{existing_categories} categories already exist in the database. No new categories added.")
        return
    
    for category_name in categories:
        new_category = AssetCategory(name=category_name)  
        db.session.add(new_category)

    db.session.commit()
    print(f"Added {len(categories)} categories to the database.")
