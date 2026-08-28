# run.py
# Entry point aplikasi — dipakai oleh `python run.py`, `flask run`, atau gunicorn (run:app).
from app import app

if __name__ == '__main__':
    app.run(debug=app.config["DEBUG"])
