import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from config import Config
import logging

logger = logging.getLogger(__name__)

def backup_database() -> str | None:
    '''
    Create a timestamped backup of the database.

    Returns:
        str | None: Path to backup file if successful, None if failed
    '''
    
    # Create backups directory if it doesn't exist
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)

    # Generate timestamp and backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f'crypto_portfolio_{timestamp}.db'

    try:
        # Close any exisiting connections
        source_conn = sqlite3.connect(Config.DATABASE)
        source_conn.close()

        # Create backup using sqlite3's backup feature
        with sqlite3.connect(Config.DATABASE) as source:
            backup = sqlite3.connect(str(backup_path))
            source.backup(backup)
            backup.close()

        logger.info(f'Database backed up succesfully to: {backup_path}')

        # Verify backup
        if verify_backup(backup_path):
            return str(backup_path)
        else:
            logger.error('Backup verification failed')
            return None
    except Exception as e:
        logger.error(f'Error creating backup: {str(e)}')
        return None
    
def verify_backup(backup_path: str | Path) -> bool:
    '''
    Verify the backup is valid by attempting to open it and run a simple query.

    Args:
        backup_path: Path to backup file

    Returns:
        bool: True if backup is valid, False otherwise
    '''
    try:
        conn = sqlite3.connect(str(backup_path))
        cursor = conn.cursor()

        # Try a simple query
        cursor.execute("SELECT count(*) FROM CoinPrices")
        count = cursor.fetchone()[0]

        conn.close()
        logger.info(f'Backup verified successfully. Contains {count} records.')
        return True
    
    except Exception as e:
        logger.error(f'Error verifying backup: {str(e)}')
        return False

def restore_database(backup_path: str | Path) -> bool:
    '''
    Restore database from backup.

    Args:
        backup_path: Path to backup file

    Returns:
        bool: True if restore successful, False otherwise
    '''

    try:
        # Verify backup before attempting restore
        if not verify_backup(backup_path):
            logger.error('Cannot restore from invalid backup')
            return False

        # Create a backup of current state before restore
        current_backup = backup_database()
        if current_backup:
            logger.info(f'Created safety backup before restore: {current_backup}')

        # Restore from backup
        shutil.copy2(str(backup_path), Config.DATABASE)
        logger.info(f'Successfully restored from backup: {backup_path}')
        return True
    except Exception as e:
        logger.error(f'Error restoring backup: {str(e)}')
        return False
    
def list_backups() -> list[Path]:
    '''
    List all available database backups.
    
    Returns:
        list[Path]: List of backup file paths
    '''
    backup_dir = Path('backups')
    if not backup_dir.exists():
        return []
    
    return sorted(
        [f for f in backup_dir.glob('crypto_portfolio_*.db')],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

def cleanup_old_backups(keep_days: int = 30) -> None:
    '''
    Remove backups older than specified number of days.

    Args:
        keep_days: Number of days to keep backups for
    '''

    try:
        backup_dir = Path('backups')
        if not backup_dir.exists():
            return

        cutoff = datetime.now().timestamp() - (keep_days * 86400)

        for backup in backup_dir.glob('crypto_portfolio_*.db'):
            if backup.stat().st_mtime < cutoff:
                backup.unlink()
                logger.info(f'Removed old backup: {backup}')

    except Exception as e:
        logger.error(f'Error eleaning up old backups: {str(e)}')