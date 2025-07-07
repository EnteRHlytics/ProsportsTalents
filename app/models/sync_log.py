from app import db
from app.models.base import BaseModel

class SyncLog(BaseModel):
    __tablename__ = 'sync_logs'

    log_id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String(100), nullable=False)
    success = db.Column(db.Boolean, default=False)
    message = db.Column(db.Text)

    def __repr__(self):
        return f'<SyncLog {self.job_name} {self.success}>'
