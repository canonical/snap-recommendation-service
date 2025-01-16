from flask_migrate import upgrade
from snaprecommend import create_app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        upgrade()
