from flask_migrate import upgrade
from snaprecommend import app
import json
import os


def sync_categories():
    """Sync categories from categories.json file"""
    from snaprecommend.models import RecommendationCategory
    from snaprecommend import db

    try:
        path = os.path.join("migrations/data/categories.json")
        with open(path, "r") as file:
            categories = json.load(file)

        added_count = 0
        for cat_data in categories:
            existing = RecommendationCategory.query.filter_by(
                id=cat_data["id"]
            ).first()
            if not existing:
                new_category = RecommendationCategory(
                    id=cat_data["id"],
                    name=cat_data["name"],
                    description=cat_data["description"],
                )
                db.session.add(new_category)
                added_count += 1
                print(f"Added category: {cat_data['id']}")

        db.session.commit()
        print(
            f"Successfully synced {added_count} new categories from "
            "categories.json"
        )

    except Exception as e:
        print(f"Error syncing categories: {e}")
        db.session.rollback()


if __name__ == "__main__":
    with app.app_context():
        print("Running database migrations...")
        upgrade()
        print("Database migrations completed.")

        print("Syncing categories...")
        sync_categories()
        print("Category sync completed.")
