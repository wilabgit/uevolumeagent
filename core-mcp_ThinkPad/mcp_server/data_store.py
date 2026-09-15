"""In-memory data store for event notifications and usage reports."""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from threading import Lock

logger = logging.getLogger(__name__)


class DataStore:
    """Thread-safe in-memory storage for SMF event notifications."""
    
    def __init__(self, max_reports: int = 10000):
        """Initialize the data store.
        
        Args:
            max_reports: Maximum number of reports to keep in memory
        """
        self.max_reports = max_reports
        self._lock = Lock()
        self._reports: List[Dict[str, Any]] = []
        self._ue_index: Dict[str, List[int]] = {}  # Map SUPI to report indices
    
    def add_report(self, event_notif: Dict[str, Any]) -> None:
        """Add a notification report to storage.
        
        Args:
            event_notif: Event notification data
        """
        with self._lock:
            # Enforce max size
            if len(self._reports) >= self.max_reports:
                removed = self._reports.pop(0)
                removed_supi = removed.get("supi")
                if removed_supi and removed_supi in self._ue_index:
                    self._ue_index[removed_supi].pop(0)
                    if not self._ue_index[removed_supi]:
                        del self._ue_index[removed_supi]
            
            # Add new report
            index = len(self._reports)
            self._reports.append(event_notif)
            
            # Update index
            supi = event_notif.get("supi")
            if supi:
                if supi not in self._ue_index:
                    self._ue_index[supi] = []
                self._ue_index[supi].append(index)
            
            logger.info(f"Stored report for UE {supi} (total: {len(self._reports)})")
    
    def get_ue_reports(self, supi: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get reports for a specific UE.
        
        Args:
            supi: The SUPI identifier
            limit: Maximum number of reports to return (most recent)
            
        Returns:
            List of reports for the UE
        """
        with self._lock:
            if supi not in self._ue_index:
                return []
            reports = [self._reports[i] for i in self._ue_index[supi]]
            if limit is not None and limit > 0:
                return reports[-limit:]
            return reports
    
    def get_all_reports(self) -> List[Dict[str, Any]]:
        """Get all stored reports.
        
        Returns:
            List of all reports
        """
        with self._lock:
            return self._reports.copy()
    
    def get_ue_list(self) -> List[str]:
        """Get list of all UEs with stored reports.
        
        Returns:
            List of SUPI identifiers
        """
        with self._lock:
            return list(self._ue_index.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                "total_reports": len(self._reports),
                "total_ues": len(self._ue_index),
                "max_reports": self.max_reports,
                "ues": list(self._ue_index.keys())
            }
    
    def delete_reports_for_supis(self, supis: List[str]) -> int:
        """Delete all stored reports for the given SUPIs."""
        if not supis:
            return 0

        target_supis = set(supis)
        with self._lock:
            remaining_reports: List[Dict[str, Any]] = []
            removed = 0

            for report in self._reports:
                if report.get("supi") in target_supis:
                    removed += 1
                    continue
                remaining_reports.append(report)

            self._reports = remaining_reports
            self._ue_index = {}
            for index, report in enumerate(self._reports):
                supi = report.get("supi")
                if supi:
                    self._ue_index.setdefault(supi, []).append(index)

            logger.info(f"Deleted {removed} reports for {len(target_supis)} SUPIs")
            return removed

    def clear(self) -> None:
        """Clear all stored data."""
        with self._lock:
            self._reports.clear()
            self._ue_index.clear()
            logger.info("Data store cleared")


def get_data_store() -> DataStore:
    """Factory function to get appropriate data store based on configuration.
    
    Returns:
        DataStore or DatabaseStore instance
    """
    from config import config
    
    if config.STORAGE_TYPE == "postgresql":
        from database import DatabaseStore
        try:
            db_store = DatabaseStore(config.DATABASE_URL, echo=config.DB_ECHO)
            logger.info("Using PostgreSQL database backend")
            return db_store
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL backend: {e}")
            logger.warning("Falling back to in-memory storage")
            return DataStore(max_reports=config.MAX_REPORTS)
    else:
        logger.info("Using in-memory storage backend")
        return DataStore(max_reports=config.MAX_REPORTS)


# Global data store instance
data_store = get_data_store()
