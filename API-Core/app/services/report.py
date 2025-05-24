from ..models import User
from ..models.report import Report, ReportStatus
from ..extensions import db

def create_report(data):
    reporter_id = data.get("reporter_id")
    if reporter_id is None:
        raise ValueError("Missing 'reporter_id' in data.")

    # Check if reporter exists
    if not User.query.get(reporter_id):
        raise ValueError(f"Invalid reporter_id: user with id {reporter_id} does not exist.")

    try:
        report = Report(**data)
        db.session.add(report)
        db.session.commit()
        return report
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"Failed to create report: {e}")


def get_all_reports():
    return Report.query.order_by(Report.created_at.desc()).all()

def update_report_status(report_id, new_status):
    report = Report.query.get_or_404(report_id)
    try:
        report.status = ReportStatus(new_status)
    except ValueError:
        return None
    db.session.commit()
    return report
