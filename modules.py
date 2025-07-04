from flask import Blueprint, request, jsonify
from database.model import db, Module

modules_bp = Blueprint('modules', __name__)

@modules_bp.route('/modules', methods=['GET'])
def get_modules():
    modules = Module.query.all()
    return jsonify([{'id': m.id, 'title': m.title, 'course_id': m.course_id} for m in modules])

@modules_bp.route('/modules/<int:module_id>', methods=['GET'])
def get_module_detail(module_id):
    module = Module.query.get_or_404(module_id)
    return jsonify({'id': module.id, 'title': module.title, 'course_id': module.course_id})

@modules_bp.route('/modules', methods=['POST'])
def create_module():
    data = request.json
    module = Module(title=data['title'], course_id=data['course_id'], description=data.get('description'))
    db.session.add(module)
    db.session.commit()
    return jsonify({'id': module.id, 'title': module.title}), 201

@modules_bp.route('/modules/<int:module_id>', methods=['PUT'])
def update_module(module_id):
    module = Module.query.get_or_404(module_id)
    data = request.json
    module.title = data.get('title', module.title)
    module.description = data.get('description', module.description)
    db.session.commit()
    return jsonify({'id': module.id, 'title': module.title})

@modules_bp.route('/modules/<int:module_id>', methods=['DELETE'])
def delete_module(module_id):
    module = Module.query.get_or_404(module_id)
    db.session.delete(module)
    db.session.commit()
    return '', 204 