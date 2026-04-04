from flask import Flask, send_from_directory, redirect, url_for

from config import Config
from extensions import db, login_manager, bcrypt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view = "auth.login"

    # Register blueprints
    from routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    from routes.case_routes import case_bp
    app.register_blueprint(case_bp)

    # ✅ Root route → Redirect to login
    @app.route("/")
    def home():
     return redirect(url_for("auth.login"))


    # ✅ Serve uploaded evidence files
    @app.route("/evidence_storage/<path:filename>")
    def serve_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # Create tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
