from flask import request, jsonify, current_app
from flask_restx import Resource
from sqlalchemy import or_, and_, func
from datetime import date
import traceback

from app.api import api
from app import db
from app.models import AthleteProfile, User, Sport, Position, AthleteStat
from app.utils.cache import cached, cache_manager
from app.utils.validators import validate_params

class AthleteSearchOptimized:
    """Optimized athlete search with advanced filtering and caching"""
    
    @staticmethod
    def build_search_query(params):
        """Build optimized search query with proper indexing"""
        try:
            # Start with base query using eager loading for performance
            query = (
                AthleteProfile.query
                .filter_by(is_deleted=False)
                .join(User)
                .outerjoin(Sport)
                .outerjoin(Position)
                .options(
                    db.joinedload(AthleteProfile.user),
                    db.joinedload(AthleteProfile.primary_sport),
                    db.joinedload(AthleteProfile.primary_position)
                )
            )
            
            # Apply filters efficiently
            filters = []
            
            # Text search with proper indexing
            q = params.get('q', '').strip()
            if q:
                pattern = f"%{q}%"
                search_conditions = or_(
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    func.concat(User.first_name, ' ', User.last_name).ilike(pattern),
                    Position.name.ilike(pattern),
                    AthleteProfile.current_team.ilike(pattern)
                )
                filters.append(search_conditions)
            
            # Sport filter with proper join
            sport = params.get('sport')
            if sport:
                if sport.isdigit():
                    filters.append(AthleteProfile.primary_sport_id == int(sport))
                else:
                    filters.append(Sport.code.ilike(sport))
            
            # Position filter
            position = params.get('position')
            if position:
                if position.isdigit():
                    filters.append(AthleteProfile.primary_position_id == int(position))
                else:
                    filters.append(or_(
                        Position.code.ilike(position),
                        Position.name.ilike(f"%{position}%")
                    ))
            
            # Team filter
            team = params.get('team')
            if team:
                filters.append(AthleteProfile.current_team.ilike(f"%{team}%"))
            
            # Age filters with date calculation
            today = date.today()
            min_age = params.get('min_age', type=int)
            if min_age is not None:
                cutoff = today.replace(year=today.year - min_age)
                filters.append(AthleteProfile.date_of_birth <= cutoff)
            
            max_age = params.get('max_age', type=int)
            if max_age is not None:
                cutoff = today.replace(year=today.year - max_age)
                filters.append(AthleteProfile.date_of_birth >= cutoff)
            
            # Physical attribute filters
            if params.get('min_height'):
                filters.append(AthleteProfile.height_cm >= int(params['min_height']))
            if params.get('max_height'):
                filters.append(AthleteProfile.height_cm <= int(params['max_height']))
            if params.get('min_weight'):
                filters.append(AthleteProfile.weight_kg >= float(params['min_weight']))
            if params.get('max_weight'):
                filters.append(AthleteProfile.weight_kg <= float(params['max_weight']))
            
            # Tab/filter handling
            filter_tab = params.get('filter', '').lower()
            if filter_tab in {'nba', 'nfl', 'mlb', 'nhl'}:
                filters.append(Sport.code == filter_tab.upper())
            elif filter_tab == 'available':
                filters.append(AthleteProfile.contract_active.is_(False))
            elif filter_tab == 'top':
                # Limit results for top performers
                query = query.limit(10)
            
            # Apply all filters
            if filters:
                query = query.filter(and_(*filters))
            
            # Ordering for performance
            query = query.order_by(
                AthleteProfile.overall_rating.desc().nullslast(),
                User.last_name,
                User.first_name
            )
            
            return query
            
        except Exception as e:
            current_app.logger.error(f"Error building search query: {e}")
            raise

@api.route('/athletes/search')
class AthleteSearch(Resource):
    """Enhanced athlete search endpoint with caching and error handling"""
    
    @api.doc(params={
        'q': 'Free text search',
        'sport': 'Sport code or id',
        'position': 'Position code or id',
        'team': 'Current team name',
        'min_age': 'Minimum age',
        'max_age': 'Maximum age',
        'min_height': 'Minimum height (cm)',
        'max_height': 'Maximum height (cm)',
        'min_weight': 'Minimum weight (kg)',
        'max_weight': 'Maximum weight (kg)',
        'filter': 'Filter tab (nba, nfl, mlb, nhl, available, top)',
        'page': 'Page number (default: 1)',
        'per_page': 'Items per page (default: 50)',
    })
    @validate_params([])
    @cached(timeout=60)  # Cache for 1 minute
    def get(self):
        """Search athletes with advanced filtering and pagination"""
        try:
            # Get parameters
            params = request.args.to_dict()
            page = int(params.get('page', 1))
            per_page = min(int(params.get('per_page', 50)), 100)  # Max 100 per page
            
            # Build optimized query
            query = AthleteSearchOptimized.build_search_query(params)
            
            # Execute with pagination
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False,
                max_per_page=100
            )
            
            # Format results
            results = []
            for athlete in pagination.items:
                try:
                    results.append(athlete.to_dict())
                except Exception as e:
                    current_app.logger.error(f"Error serializing athlete {athlete.athlete_id}: {e}")
                    continue
            
            # Log search for analytics
            if current_app.config.get('DEBUG'):
                current_app.logger.info(f"Search executed: {params}, returned {len(results)} results")
            
            return jsonify({
                'results': results,
                'count': len(results),
                'total': pagination.total,
                'page': page,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            })
            
        except Exception as e:
            current_app.logger.error(f"Search error: {e}\n{traceback.format_exc()}")
            return jsonify({
                'error': 'Search failed',
                'message': str(e) if current_app.config.get('DEBUG') else 'Internal error'
            }), 500

@api.route('/athletes/featured')
class FeaturedAthletes(Resource):
    """Featured athletes endpoint with optimized queries"""
    
    @api.doc(params={'limit': 'Number of athletes to return (default: 6, max: 20)'})
    @validate_params([])
    @cached(timeout=300)  # Cache for 5 minutes
    def get(self):
        """Get featured athletes with their latest stats"""
        try:
            limit = min(request.args.get('limit', 6, type=int), 20)
            year = date.today().year
            
            # Optimized query with eager loading
            athletes = (
                AthleteProfile.query
                .filter_by(is_deleted=False, is_featured=True)
                .join(User)
                .outerjoin(Sport)
                .outerjoin(Position)
                .options(
                    db.joinedload(AthleteProfile.user),
                    db.joinedload(AthleteProfile.primary_sport),
                    db.joinedload(AthleteProfile.primary_position),
                    db.subqueryload(AthleteProfile.stats).filter(
                        AthleteStat.season == str(year)
                    )
                )
                .order_by(AthleteProfile.overall_rating.desc())
                .limit(limit)
                .all()
            )
            
            # Format response
            featured = []
            for athlete in athletes:
                try:
                    name = athlete.user.full_name if athlete.user else f"Athlete {athlete.athlete_id}"
                    initials = "".join([n[0] for n in name.split()][:2]).upper()
                    
                    # Get relevant stats based on sport
                    stats = self._get_athlete_stats(athlete, year)
                    
                    featured.append({
                        "id": athlete.athlete_id,
                        "name": name,
                        "position": athlete.primary_position.code if athlete.primary_position else None,
                        "team": athlete.current_team or "Free Agent",
                        "sport": athlete.primary_sport.code if athlete.primary_sport else None,
                        "profile_image_url": athlete.profile_image_url,
                        "initials": initials,
                        "stats": stats,
                        "rating": float(athlete.overall_rating) if athlete.overall_rating else None
                    })
                except Exception as e:
                    current_app.logger.error(f"Error processing featured athlete {athlete.athlete_id}: {e}")
                    continue
            
            return jsonify(featured)
            
        except Exception as e:
            current_app.logger.error(f"Featured athletes error: {e}\n{traceback.format_exc()}")
            return jsonify({
                'error': 'Failed to get featured athletes',
                'message': str(e) if current_app.config.get('DEBUG') else 'Internal error'
            }), 500
    
    def _get_athlete_stats(self, athlete, year):
        """Get formatted stats for an athlete"""
        sport = athlete.primary_sport.code if athlete.primary_sport else None
        
        # Define sport-specific stat mappings
        stat_mappings = {
            "NBA": [
                ("PPG", "PointsPerGame"),
                ("RPG", "ReboundsPerGame"),
                ("APG", "AssistsPerGame")
            ],
            "NFL": [
                ("Yards", "PassingYards"),
                ("TD", "Touchdowns"),
                ("QBR", "QBRating")
            ],
            "MLB": [
                ("AVG", "BattingAverage"),
                ("HR", "HomeRuns"),
                ("RBI", "RunsBattedIn")
            ],
            "NHL": [
                ("G", "Goals"),
                ("A", "Assists"),
                ("P", "Points")
            ]
        }
        
        mapping = stat_mappings.get(sport, [])
        stats = []
        
        # Get stats from database
        stat_dict = {stat.name: stat.value for stat in athlete.stats if stat.season == str(year)}
        
        for label, stat_name in mapping:
            value = stat_dict.get(stat_name, "N/A")
            if value != "N/A":
                value = self._format_stat_value(value)
            stats.append({"label": label, "value": value})
        
        return stats
    
    def _format_stat_value(self, value):
        """Format stat value for display"""
        try:
            num = float(value)
            if 0 < num < 1:
                return f"{num:.3f}".lstrip("0")
            return f"{num:.1f}" if num % 1 else str(int(num))
        except (TypeError, ValueError):
            return str(value)