from flask import Flask
from website import create_app

app = Flask(__name__)
app = create_app(app)

if __name__ == "__main__":
    app.run(debug=True)