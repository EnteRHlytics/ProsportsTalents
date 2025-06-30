from flask import request, send_file, abort, jsonify
from app.utils.validators import validate_json, validate_params
from app.utils.auth import login_or_token_required
from flask_restx import Resource
import logging

from app.api import api, bp
from app import db
from app.models import AthleteProfile, AthleteMedia, AthleteStat
from app.services.media_service import MediaService
from app.services.athlete_service import (
    create_athlete as create_athlete_service,
    get_athlete as get_athlete_service,
    update_athlete as update_athlete_service,
    delete_athlete as delete_athlete_service,
    list_athletes as list_athletes_service,
)



@api.route('/athletes')
class AthleteList(Resource):
    """Create or list athletes."""

    @api.doc(description="List athletes", params={
        'page': 'Page number',
        'per_page': 'Items per page'
    })
    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        q = AthleteProfile.query.filter_by(is_deleted=False)
        pagination = q.paginate(page=page, per_page=per_page, error_out=False)
        data = [a.to_dict() for a in pagination.items]
        return jsonify({'items': data, 'total': pagination.total})

    @api.doc(description="Create a new athlete")
    @login_or_token_required
    @validate_json(['user_id', 'primary_sport_id', 'primary_position_id', 'date_of_birth'])
    def post(self):
        data = request.get_json() or {}
        athlete = AthleteProfile(
            user_id=data.get('user_id'),
            primary_sport_id=data.get('primary_sport_id'),
            primary_position_id=data.get('primary_position_id'),
            date_of_birth=data.get('date_of_birth'),
        )
        db.session.add(athlete)
        db.session.commit()
        logging.getLogger(__name__).info("Created athlete %s", athlete.id)
        return jsonify(athlete.to_dict()), 201


@api.route('/athletes/<string:athlete_id>')
@api.param('athlete_id', 'Athlete identifier')
class AthleteResource(Resource):
    """Retrieve, update or delete a single athlete."""

    @api.doc(description="Get an athlete")
    def get(self, athlete_id):
        athlete = (
            AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False)
            .first_or_404()
        )
        return jsonify(athlete.to_dict())

    @api.doc(description="Update an athlete")
    @login_or_token_required
    @validate_json([])
    def put(self, athlete_id):
        athlete = (
            AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False)
            .first_or_404()
        )
        data = request.get_json() or {}
        for field in ['primary_sport_id', 'primary_position_id', 'bio']:
            if field in data:
                setattr(athlete, field, data[field])
        db.session.commit()
        logging.getLogger(__name__).info("Updated athlete %s", athlete.id)
        return jsonify(athlete.to_dict())

    @api.doc(description="Delete an athlete")
    @login_or_token_required
    def delete(self, athlete_id):
        athlete = (
            AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False)
            .first_or_404()
        )
        athlete.is_deleted = True
        db.session.commit()
        logging.getLogger(__name__).info("Deleted athlete %s", athlete.id)
        return '', 204


@api.route('/athletes/<string:athlete_id>/media')
@api.param('athlete_id', 'Athlete identifier')
class AthleteMediaList(Resource):
    """Upload or list athlete media."""

    @api.doc(description="List media for an athlete")
    def get(self, athlete_id):
        AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False).first_or_404()
        media = AthleteMedia.query.filter_by(athlete_id=athlete_id).all()
        return jsonify([m.to_dict() for m in media])

    @api.doc(description="Upload a media file", params={'file': 'File upload', 'media_type': 'Type of media'})
    @login_or_token_required
    def post(self, athlete_id):
        athlete = (
            AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False)
            .first_or_404()
        )
        if 'file' not in request.files:
            abort(400, 'No file provided')
        file = request.files['file']
        media_type = request.form.get('media_type', 'other')
        path, _ = MediaService.save_file(file, athlete_id, media_type)
        media = AthleteMedia(
            athlete_id=athlete_id,
            media_type=media_type,
            file_path=path,
            original_filename=file.filename,
        )
        db.session.add(media)
        db.session.commit()
        logging.getLogger(__name__).info("Uploaded media %s", media.id)
        return jsonify(media.to_dict()), 201


@api.route('/media/<string:media_id>')
@api.param('media_id', 'Media identifier')
class MediaResource(Resource):
    """Delete media."""

    @api.doc(description="Delete a media entry")
    @login_or_token_required
    def delete(self, media_id):
        media = AthleteMedia.query.get_or_404(media_id)
        MediaService.delete_file(media.file_path)
        db.session.delete(media)
        db.session.commit()
        logging.getLogger(__name__).info("Deleted media %s", media.id)
        return '', 204


@api.route('/media/<string:media_id>/download')
@api.param('media_id', 'Media identifier')
class MediaDownload(Resource):
    """Download a media file."""

    @api.doc(description="Download media")
    def get(self, media_id):
        media = AthleteMedia.query.get_or_404(media_id)
        return send_file(media.file_path, as_attachment=True, download_name=media.original_filename)


@api.route('/athletes/<string:athlete_id>/stats')
@api.param('athlete_id', 'Athlete identifier')
class AthleteStats(Resource):
    """Add, update or list athlete stats."""

    @api.doc(description="Get stats for an athlete")
    def get(self, athlete_id):
        AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False).first_or_404()
        stats = AthleteStat.query.filter_by(athlete_id=athlete_id).all()
        return jsonify([s.to_dict() for s in stats])

    @api.doc(description="Add or update a stat")
    @login_or_token_required
    @validate_json(['name'])
    def post(self, athlete_id):
        AthleteProfile.query.filter_by(athlete_id=athlete_id, is_deleted=False).first_or_404()
        data = request.get_json() or {}
        name = data.get('name')
        if not name:
            abort(400, 'Missing stat name')
        stat_type = data.get('stat_type')
        season = data.get('season')
        stat = AthleteStat.query.filter_by(
            athlete_id=athlete_id,
            name=name,
            stat_type=stat_type,
            season=season,
        ).first()
        if stat:
            stat.value = data.get('value')
            if stat_type is not None:
                stat.stat_type = stat_type
            if season is not None:
                stat.season = season
        else:
            stat = AthleteStat(
                athlete_id=athlete_id,
                name=name,
                value=data.get('value'),
                stat_type=stat_type,
                season=season,
            )
            db.session.add(stat)
        db.session.commit()
        logging.getLogger(__name__).info("Updated stat %s for athlete %s", name, athlete_id)
        return jsonify(stat.to_dict())


@api.route('/stats/<string:stat_id>')
@api.param('stat_id', 'Stat identifier')
class StatResource(Resource):
    """Delete a stat."""

    @api.doc(description="Delete a stat")
    @login_or_token_required
    def delete(self, stat_id):
        stat = AthleteStat.query.get_or_404(stat_id)
        db.session.delete(stat)
        db.session.commit()
        logging.getLogger(__name__).info("Deleted stat %s", stat_id)
        return '', 204
      
@bp.route('/athletes', methods=['POST'])
@login_or_token_required
@validate_json(['user_id', 'primary_sport_id', 'primary_position_id', 'date_of_birth'])
def create_athlete():
    data = request.get_json() or {}
    athlete = create_athlete_service(data)
    logging.getLogger(__name__).info("Created athlete %s", athlete.id)
    return jsonify(athlete.to_dict()), 201

@bp.route('/athletes/<athlete_id>', methods=['GET'])
def get_athlete(athlete_id):
    athlete = get_athlete_service(athlete_id)
    return jsonify(athlete.to_dict())

@bp.route('/athletes/<athlete_id>', methods=['PUT'])
@login_or_token_required
@validate_json([])
def update_athlete(athlete_id):
    data = request.get_json() or {}
    athlete = update_athlete_service(athlete_id, data)
    logging.getLogger(__name__).info("Updated athlete %s", athlete.id)
    return jsonify(athlete.to_dict())

@bp.route('/athletes/<athlete_id>', methods=['DELETE'])
@login_or_token_required
def delete_athlete(athlete_id):
    delete_athlete_service(athlete_id)
    logging.getLogger(__name__).info("Deleted athlete %s", athlete_id)
    return '', 204

@bp.route('/athletes', methods=['GET'])
def list_athletes():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    pagination = list_athletes_service(page, per_page)
    data = [a.to_dict() for a in pagination.items]
    return jsonify({'items': data, 'total': pagination.total})

# Media endpoints
@bp.route('/athletes/<athlete_id>/media', methods=['POST'])
@login_or_token_required
def upload_media(athlete_id):
    athlete = AthleteProfile.query.get_or_404(athlete_id)
    if 'file' not in request.files:
        abort(400, 'No file provided')
    file = request.files['file']
    media_type = request.form.get('media_type', 'other')
    path, filename = MediaService.save_file(file, athlete_id, media_type)
    media = AthleteMedia(
        athlete_id=athlete_id,
        media_type=media_type,
        file_path=path,
        original_filename=file.filename,
    )
    db.session.add(media)
    db.session.commit()
    logging.getLogger(__name__).info("Uploaded media %s", media.id)
    return jsonify(media.to_dict()), 201

@bp.route('/athletes/<athlete_id>/media', methods=['GET'])
def list_media(athlete_id):
    AthleteProfile.query.get_or_404(athlete_id)
    media = AthleteMedia.query.filter_by(athlete_id=athlete_id).all()
    return jsonify([m.to_dict() for m in media])

@bp.route('/media/<media_id>', methods=['DELETE'])
@login_or_token_required
def delete_media(media_id):
    media = AthleteMedia.query.get_or_404(media_id)
    MediaService.delete_file(media.file_path)
    db.session.delete(media)
    db.session.commit()
    logging.getLogger(__name__).info("Deleted media %s", media.id)
    return '', 204

@bp.route('/media/<media_id>/download', methods=['GET'])
def download_media(media_id):
    media = AthleteMedia.query.get_or_404(media_id)
    return send_file(media.file_path, as_attachment=True, download_name=media.original_filename)

# Stats endpoints
@bp.route('/athletes/<athlete_id>/stats', methods=['POST'])
@login_or_token_required
@validate_json(['name'])
def add_or_update_stat(athlete_id):
    AthleteProfile.query.get_or_404(athlete_id)
    data = request.get_json() or {}
    name = data.get('name')
    stat_type = data.get('stat_type')
    season = data.get('season')
    stat = AthleteStat.query.filter_by(
        athlete_id=athlete_id,
        name=name,
        stat_type=stat_type,
        season=season,
    ).first()
    if stat:
        stat.value = data.get('value')
        if stat_type is not None:
            stat.stat_type = stat_type
        if season is not None:
            stat.season = season
    else:
        stat = AthleteStat(
            athlete_id=athlete_id,
            name=name,
            value=data.get('value'),
            stat_type=stat_type,
            season=season,
        )
        db.session.add(stat)
    db.session.commit()
    logging.getLogger(__name__).info("Updated stat %s for athlete %s", name, athlete_id)
    return jsonify(stat.to_dict())

@bp.route('/athletes/<athlete_id>/stats', methods=['GET'])
def get_stats(athlete_id):
    AthleteProfile.query.get_or_404(athlete_id)
    stats = AthleteStat.query.filter_by(athlete_id=athlete_id).all()
    return jsonify([s.to_dict() for s in stats])

@bp.route('/stats/<stat_id>', methods=['DELETE'])
@login_or_token_required
def delete_stat(stat_id):
    stat = AthleteStat.query.get_or_404(stat_id)
    db.session.delete(stat)
    db.session.commit()
    logging.getLogger(__name__).info("Deleted stat %s", stat_id)
    return '', 204
