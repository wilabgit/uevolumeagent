#docker """Database models and operations for persistent report storage using PostgreSQL."""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Text, Index, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

Base = declarative_base()


class EventReport(Base):
    """SQLAlchemy model for storing event reports."""
    
    __tablename__ = "event_reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    supi = Column(String(255), nullable=False, index=True)
    notif_id = Column(String(255), nullable=True)
    event = Column(String(128), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    event_data = Column(JSON, nullable=False)

    __table_args__ = (
        Index('idx_supi_timestamp', 'supi', 'timestamp'),
        Index('idx_notif_id', 'notif_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "id": self.id,
            "supi": self.supi,
            "notif_id": self.notif_id,
            "event": self.event,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_data": self.event_data,
        }
    
    @classmethod
    def from_event_notif(cls, notif_data: Dict[str, Any]) -> "EventReport":
        """Create EventReport from incoming notification data.
        
        Args:
            notif_data: Event notification dictionary
            
        Returns:
            EventReport instance
        """
        return cls(
            supi=notif_data.get("supi"),
            notif_id=notif_data.get("notif_id"),
            event=notif_data.get("event"),
            timestamp=datetime.fromisoformat(notif_data["timestamp"]) 
                     if isinstance(notif_data.get("timestamp"), str)
                     else notif_data.get("timestamp", datetime.now(timezone.utc)),
            event_data=notif_data,
        )


class DatabaseStore:
    """PostgreSQL-backed data store for SMF event notifications."""
    
    def __init__(self, database_url: str, echo: bool = False):
        """Initialize the database store.
        
        Args:
            database_url: PostgreSQL connection URL (e.g., postgresql://user:pass@localhost/dbname)
            echo: Enable SQL query logging
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=echo, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        self._init_database()
        logger.info("Database store initialized")
    
    def _init_database(self) -> None:
        """Create database tables if they don't exist."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables initialized")
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def add_report(self, event_notif: Dict[str, Any]) -> int:
        """Add a notification report to the database.
        
        Args:
            event_notif: Event notification data
            
        Returns:
            ID of the inserted report
        """
        session: Session = self.SessionLocal()
        try:
            report = EventReport.from_event_notif(event_notif)
            session.add(report)
            session.commit()
            report_id = report.id
            logger.info(f"Stored report for UE {event_notif.get('supi')} (ID: {report_id})")
            return report_id
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to add report: {e}")
            raise
        finally:
            session.close()
    
    def get_ue_reports(self, supi: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get reports for a specific UE.
        
        Args:
            supi: The SUPI identifier
            limit: Maximum number of reports to return (most recent)
            
        Returns:
            List of reports for the UE
        """
        session: Session = self.SessionLocal()
        try:
            if limit is not None and limit > 0:
                reports = session.query(EventReport).filter(
                    EventReport.supi == supi
                ).order_by(EventReport.timestamp.desc()).limit(limit).all()
                reports = list(reversed(reports))
            else:
                reports = session.query(EventReport).filter(
                    EventReport.supi == supi
                ).order_by(EventReport.timestamp.asc()).all()
            return [report.to_dict() for report in reports]
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve UE reports: {e}")
            return []
        finally:
            session.close()
    
    def get_all_reports(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all stored reports with pagination.
        
        Args:
            limit: Maximum number of reports to return
            offset: Number of reports to skip
            
        Returns:
            List of all reports
        """
        session: Session = self.SessionLocal()
        try:
            reports = session.query(EventReport).order_by(
                EventReport.timestamp.desc()
            ).limit(limit).offset(offset).all()
            return [report.to_dict() for report in reports]
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve all reports: {e}")
            return []
        finally:
            session.close()
    
    def get_ue_list(self) -> List[str]:
        """Get list of all UEs with stored reports.
        
        Returns:
            List of SUPI identifiers
        """
        session: Session = self.SessionLocal()
        try:
            ues = session.query(EventReport.supi.distinct()).all()
            return [ue[0] for ue in ues]
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve UE list: {e}")
            return []
        finally:
            session.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Dictionary with statistics
        """
        session: Session = self.SessionLocal()
        try:
            total_reports = session.query(EventReport).count()
            total_ues = session.query(EventReport.supi.distinct()).count()
            ues = [ue[0] for ue in session.query(EventReport.supi.distinct()).all()]
            
            return {
                "total_reports": total_reports,
                "total_ues": total_ues,
                "ues": ues,
                "storage_backend": "postgresql",
                "max_reports": None,  # Unlimited for PostgreSQL
            }
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve statistics: {e}")
            return {
                "error": str(e),
                "storage_backend": "postgresql",
            }
        finally:
            session.close()
    
    def get_reports_for_event(self, event: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent reports for a specific event type.
        
        Args:
            event: Event type to filter by
            limit: Maximum number of reports to return
            
        Returns:
            List of reports for the event
        """
        session: Session = self.SessionLocal()
        try:
            reports = session.query(EventReport).filter(
                EventReport.event == event
            ).order_by(EventReport.timestamp.desc()).limit(limit).all()
            return [report.to_dict() for report in reports]
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve event reports: {e}")
            return []
        finally:
            session.close()
    
    def delete_reports_for_supis(self, supis: List[str]) -> int:
        """Delete all stored reports for the given SUPIs."""
        if not supis:
            return 0

        session: Session = self.SessionLocal()
        try:
            deleted = session.query(EventReport).filter(
                EventReport.supi.in_(supis)
            ).delete(synchronize_session=False)
            session.commit()
            logger.info(f"Deleted {deleted} reports for {len(supis)} SUPIs")
            return deleted
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to delete reports for SUPIs: {e}")
            return 0
        finally:
            session.close()

    def clear(self) -> None:
        """Clear all stored data."""
        session: Session = self.SessionLocal()
        try:
            session.query(EventReport).delete()
            session.commit()
            logger.info("Database cleared")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to clear database: {e}")
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check if database connection is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        session: Session = self.SessionLocal()
        try:
            session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
        finally:
            session.close()
