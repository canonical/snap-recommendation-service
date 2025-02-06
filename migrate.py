from flask_migrate import upgrade
from snaprecommend import app

# test change delete

if __name__ == "__main__":
    with app.app_context():
        upgrade()
