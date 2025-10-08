import os
import sqlite3
import tempfile
import threading
from pathlib import Path
from typing import Optional, Union

from loguru import logger

from service.core.utils.singleton import SingletonMeta


class SqliteFileCache(metaclass=SingletonMeta):
    """
    Thread-safe SQLite cache for file storage with proper binary/text handling.

    Features:
    - Thread-local connections for safety
    - WAL mode for better concurrency
    - Automatic schema initialization
    - Support for text and binary content
    - Singleton pattern for shared cache instance
    - Timestamp tracking for cache freshness validation
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize SQLite cache.

        Args:
            db_path: Path to SQLite database file. If None, uses default temp location.
        """
        # Prevent re-initialization of singleton
        if hasattr(self, "_initialized"):
            return

        self._db_path = db_path or self._get_default_db_path()
        self._lock = threading.RLock()
        self._thread_local = threading.local()

        # Initialize schema with bootstrap connection
        bootstrap_conn = self._create_connection()
        self._initialize_schema(bootstrap_conn)
        bootstrap_conn.close()

        self._initialized = True

        logger.info(f"SqliteFileCache initialized with database: {self._db_path}")

    def _get_default_db_path(self) -> Path:
        """Get default database path in system temp directory."""
        db_dir = Path(tempfile.gettempdir()) / "law_monitoring_cache"
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir / "pharia_data_cache.db"

    def _create_connection(self) -> sqlite3.Connection:
        """Create optimized SQLite connection."""
        conn = sqlite3.connect(
            str(self._db_path),
            check_same_thread=True,
            isolation_level=None,
        )
        # Performance optimizations
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        return conn

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection, recreate if closed."""
        conn = getattr(self._thread_local, "conn", None)
        if conn is not None:
            try:
                conn.execute("PRAGMA schema_version").fetchone()
                return conn
            except (sqlite3.ProgrammingError, sqlite3.OperationalError):
                # Connection is closed or corrupted, will recreate
                pass

        # Create and store new connection
        conn = self._create_connection()
        self._thread_local.conn = conn
        return conn

    def _initialize_schema(self, conn: sqlite3.Connection) -> None:
        """Initialize database schema."""
        logger.info("Initializing SQLite schema")
        try:
            with self._lock:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS file_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        folder TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        file_extension TEXT NOT NULL,
                        content_type TEXT NOT NULL CHECK (content_type IN ('text', 'binary')),
                        content_text TEXT,
                        content_binary BLOB,
                        file_size INTEGER,
                        is_json_parsed BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(folder, filename)
                    )
                """)
                # Create indexes
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_folder_filename ON file_cache(folder, filename)",
                    "CREATE INDEX IF NOT EXISTS idx_file_extension ON file_cache(file_extension)",
                    "CREATE INDEX IF NOT EXISTS idx_content_type ON file_cache(content_type)",
                    "CREATE INDEX IF NOT EXISTS idx_created_at ON file_cache(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_updated_at ON file_cache(updated_at)",
                ]

                for index_sql in indexes:
                    cursor.execute(index_sql)

                # Create trigger to automatically update updated_at on row changes
                cursor.execute("""
                    CREATE TRIGGER IF NOT EXISTS update_timestamp 
                    AFTER UPDATE ON file_cache
                    FOR EACH ROW
                    BEGIN
                        UPDATE file_cache
                        SET updated_at = CURRENT_TIMESTAMP
                        WHERE id = NEW.id;
                        END
                """)

                conn.commit()
                logger.info("SQLite schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise

    def get_file(self, folder: str, filename: str) -> Optional[Union[str, bytes]]:
        """
        Get file content from cache.

        Returns:
            File content if found (str for text, bytes for binary), None if not found
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT content_type, content_text, content_binary FROM file_cache WHERE folder = ? AND filename = ?",
                (folder, filename),
            )
            result = cursor.fetchone()

            if not result:
                return None

            content_type, content_text, content_binary = result

            if content_type == "text":
                return content_text
            elif content_type == "binary":
                return content_binary
            else:
                logger.error(
                    f"Unknown content_type '{content_type}' for {folder}/{filename}"
                )
                return None

        except Exception as e:
            logger.error(f"Failed to get file from cache: {e}")
            return None

    def save_file(self, folder: str, filename: str, content: Union[str, bytes]) -> None:
        """Save file content to cache."""
        try:
            file_extension = self._get_file_extension(filename)
            content_type = self._get_content_type(filename)
            file_size = self._get_content_size(content)

            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()

                if content_type == "text":
                    content_text = (
                        content.decode("utf-8")
                        if isinstance(content, bytes)
                        else content
                    )
                    content_binary = None
                else:
                    content_text = None
                    content_binary = (
                        content.encode("utf-8") if isinstance(content, str) else content
                    )

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO file_cache 
                    (folder, filename, file_extension, content_type, 
                     content_text, content_binary, file_size, is_json_parsed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        folder,
                        filename,
                        file_extension,
                        content_type,
                        content_text,
                        content_binary,
                        file_size,
                        False,
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to save file to cache: {e}")
            raise

    def delete_file(self, folder: str, filename: str) -> None:
        """Delete file from cache."""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM file_cache WHERE folder = ? AND filename = ?",
                    (folder, filename),
                )
        except Exception as e:
            logger.error(f"Failed to delete file from cache: {e}")

    def clear(self) -> bool:
        """Clear entire cache."""
        try:
            logger.info("Clearing SQLite cache")
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM file_cache")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='file_cache'")
                cursor.execute("VACUUM")
            logger.info("Cache cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension."""
        return os.path.splitext(filename)[1].lower()

    def _get_content_type(self, filename: str) -> str:
        """Determine content type (text/binary)."""
        extension = self._get_file_extension(filename)
        text_extensions = {".json", ".html", ".htm", ".txt", ".xml"}
        return "text" if extension in text_extensions else "binary"

    def _get_content_size(self, content: Union[str, bytes]) -> int:
        """Get content size in bytes."""
        if isinstance(content, str):
            return len(content.encode("utf-8"))
        return len(content)


sqlite_file_cache = SqliteFileCache()
