from flask import request, jsonify
from flask_restx import Resource
import logging

from app.api import api
from app import db
from app.models import AthleteProfile, AthleteSkill
from app.utils.validators import validate_json


@api.route('/athletes/<string:athlete_id>/skills')
@api.param('athlete_id', 'Athlete identifier')
class AthleteSkillList(Resource):
    """List or create athlete skills."""

    @api.doc(description="List skills for an athlete")
    def get(self, athlete_id):
        AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False).first_or_404()
        skills = AthleteSkill.query.filter_by(athlete_id=athlete_id).all()
        return jsonify([s.to_dict() for s in skills])

    @api.doc(description="Create a new skill", params={'name': 'Skill name', 'level': 'Skill level'})
    @validate_json(['name'])
    def post(self, athlete_id):
        AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False).first_or_404()
        data = request.get_json() or {}
        skill = AthleteSkill(
            athlete_id=athlete_id,
            name=data.get('name'),
            level=data.get('level'),
        )
        db.session.add(skill)
        db.session.commit()
        logging.getLogger(__name__).info("Created skill %s for athlete %s", skill.skill_id, athlete_id)
        return jsonify(skill.to_dict()), 201


@api.route('/skills/<string:skill_id>')
@api.param('skill_id', 'Skill identifier')
class SkillResource(Resource):
    """Update or delete a skill."""

    @api.doc(description="Update a skill")
    @validate_json([])
    def put(self, skill_id):
        skill = AthleteSkill.query.get_or_404(skill_id)
        data = request.get_json() or {}
        for field in ['name', 'level']:
            if field in data:
                setattr(skill, field, data[field])
        db.session.commit()
        logging.getLogger(__name__).info("Updated skill %s", skill_id)
        return jsonify(skill.to_dict())

    @api.doc(description="Delete a skill")
    def delete(self, skill_id):
        skill = AthleteSkill.query.get_or_404(skill_id)
        db.session.delete(skill)
        db.session.commit()
        logging.getLogger(__name__).info("Deleted skill %s", skill_id)
        return '', 204
