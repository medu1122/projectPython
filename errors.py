from flask import render_template, Blueprint

def register_error_handlers(app):
    """Register error handlers for the Flask application"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 errors"""
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        # Log the error
        app.logger.error(f'Server Error: {error}')
        # Rollback any database changes
        from app import db
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle 400 errors"""
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        """Handle 401 errors"""
        return render_template('errors/401.html'), 401
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        """Handle 405 errors"""
        return render_template('errors/405.html'), 405 