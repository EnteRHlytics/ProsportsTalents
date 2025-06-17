import os
from app import create_app, db
from app.models import User, Role, UserRole, UserOAuthAccount, Sport, Position
from flask.cli import with_appcontext
import click

app = create_app(os.getenv('FLASK_ENV') or 'development')

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Role': Role,
        'UserRole': UserRole,
        'UserOAuthAccount': UserOAuthAccount,
        'Sport': Sport,
        'Position': Position
    }

@app.cli.command()
@with_appcontext
def init_db():
    """Initialize database with default data"""
    db.create_all()
    
    # Create default roles
    roles_data = [
        {'name': 'admin', 'description': 'System Administrator'},
        {'name': 'agency_admin', 'description': 'Agency Administrator'},
        {'name': 'agent', 'description': 'Talent Agent'},
        {'name': 'scout', 'description': 'Talent Scout'},
        {'name': 'athlete', 'description': 'Professional Athlete'},
        {'name': 'viewer', 'description': 'Read-only Viewer'}
    ]
    
    for role_data in roles_data:
        if not Role.query.filter_by(name=role_data['name']).first():
            role = Role(
                name=role_data['name'],
                description=role_data['description'],
                is_system_role=True
            )
            db.session.add(role)
    
    # Create sports and positions
    sports_data = [
        {
            'name': 'Basketball',
            'code': 'NBA',
            'description': 'National Basketball Association',
            'positions': [
                {'name': 'Point Guard', 'code': 'PG', 'description': 'Primary ball handler'},
                {'name': 'Shooting Guard', 'code': 'SG', 'description': 'Perimeter shooter'},
                {'name': 'Small Forward', 'code': 'SF', 'description': 'Versatile wing player'},
                {'name': 'Power Forward', 'code': 'PF', 'description': 'Strong inside player'},
                {'name': 'Center', 'code': 'C', 'description': 'Primary post player'}
            ]
        },
        {
            'name': 'Football',
            'code': 'NFL',
            'description': 'National Football League',
            'positions': [
                {'name': 'Quarterback', 'code': 'QB', 'description': 'Field general'},
                {'name': 'Running Back', 'code': 'RB', 'description': 'Ball carrier'},
                {'name': 'Wide Receiver', 'code': 'WR', 'description': 'Pass catcher'},
                {'name': 'Tight End', 'code': 'TE', 'description': 'Receiver/blocker'},
                {'name': 'Offensive Line', 'code': 'OL', 'description': 'Blockers'}
            ]
        },
        {
            'name': 'Baseball',
            'code': 'MLB',
            'description': 'Major League Baseball',
            'positions': [
                {'name': 'Pitcher', 'code': 'P', 'description': 'Throws to batters'},
                {'name': 'Catcher', 'code': 'C', 'description': 'Receives pitches'},
                {'name': 'First Base', 'code': '1B', 'description': 'First base position'},
                {'name': 'Second Base', 'code': '2B', 'description': 'Second base position'},
                {'name': 'Shortstop', 'code': 'SS', 'description': 'Between 2nd and 3rd base'}
            ]
        },
        {
            'name': 'Hockey',
            'code': 'NHL',
            'description': 'National Hockey League',
            'positions': [
                {'name': 'Center', 'code': 'C', 'description': 'Forward center'},
                {'name': 'Left Wing', 'code': 'LW', 'description': 'Left wing forward'},
                {'name': 'Right Wing', 'code': 'RW', 'description': 'Right wing forward'},
                {'name': 'Defenseman', 'code': 'D', 'description': 'Defensive player'},
                {'name': 'Goaltender', 'code': 'G', 'description': 'Goal keeper'}
            ]
        }
    ]
    
    for sport_data in sports_data:
        sport = Sport.query.filter_by(code=sport_data['code']).first()
        if not sport:
            sport = Sport(
                name=sport_data['name'],
                code=sport_data['code'],
                description=sport_data['description'],
                is_active=True
            )
            db.session.add(sport)
            db.session.flush()  # Get the sport ID
            
            # Add positions
            for pos_data in sport_data['positions']:
                position = Position(
                    sport_id=sport.sport_id,
                    name=pos_data['name'],
                    code=pos_data['code'],
                    description=pos_data['description']
                )
                db.session.add(position)
    
    db.session.commit()
    click.echo('Database initialized with default roles and sports.')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)