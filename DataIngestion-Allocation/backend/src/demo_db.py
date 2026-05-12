"""
demo_db.py — SQLite database for demo mode
Provides isolated data storage for demo mode without affecting Supabase
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("DEMO_DB")

# Database path
DB_PATH = Path(__file__).parent.parent / "demo.db"

# Schema SQL
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    incident_name TEXT NOT NULL,
    incident_type TEXT,
    location TEXT,
    title TEXT,
    severity INTEGER,
    summary TEXT,
    created_at TEXT,
    status TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS need_cards (
    id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL,
    type TEXT NOT NULL,
    item TEXT NOT NULL,
    qty REAL NOT NULL,
    note TEXT,
    explanation TEXT NOT NULL,
    done_by TEXT,
    fulfilled BOOLEAN DEFAULT 0,
    pending_approval BOOLEAN DEFAULT 0,
    show_pd BOOLEAN DEFAULT 1,
    created_at TEXT,
    updated_at TEXT,
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
);

CREATE TABLE IF NOT EXISTS activity_feed (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
"""


def init_demo_db():
    """Initialize demo database with schema and seed data."""
    logger.info(f"Initializing demo database at {DB_PATH}")
    
    # Remove old database to reset it
    if DB_PATH.exists():
        DB_PATH.unlink()
        logger.info("Cleared old demo database")
    
    # Create connection and schema
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript(SCHEMA_SQL)
    logger.info("Created database schema")
    
    conn.commit()
    conn.close()
    logger.info("Demo database initialized successfully (no seed data)")


def get_demo_connection():
    """Get a connection to the demo database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def create_need_card_demo(need_card_data: dict) -> dict:
    """Create a need card in demo database."""
    conn = get_demo_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO need_cards
            (id, incident_id, type, item, qty, note, explanation, done_by, fulfilled, pending_approval, show_pd, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            need_card_data.get("id"),
            need_card_data.get("incident_id"),
            need_card_data.get("type"),
            need_card_data.get("item"),
            need_card_data.get("qty"),
            need_card_data.get("note"),
            need_card_data.get("explanation"),
            need_card_data.get("done_by"),
            need_card_data.get("fulfilled", False),
            need_card_data.get("pending_approval", False),
            need_card_data.get("show_pd", True),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        logger.info(f"Created need card {need_card_data.get('id')} in demo DB")
        
        return {
            "id": need_card_data.get("id"),
            "incident_id": need_card_data.get("incident_id"),
            "type": need_card_data.get("type"),
            "item": need_card_data.get("item"),
            "qty": need_card_data.get("qty"),
            "note": need_card_data.get("note"),
            "explanation": need_card_data.get("explanation"),
            "done_by": need_card_data.get("done_by"),
            "fulfilled": need_card_data.get("fulfilled", False),
            "pending_approval": need_card_data.get("pending_approval", False),
            "show_pd": need_card_data.get("show_pd", True),
        }
    finally:
        conn.close()


def get_all_need_cards_demo() -> list:
    """Get all need cards from demo database."""
    conn = get_demo_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM need_cards")
        rows = cursor.fetchall()
        
        cards = []
        for row in rows:
            cards.append({
                "id": row["id"],
                "incident_id": row["incident_id"],
                "type": row["type"],
                "item": row["item"],
                "qty": row["qty"],
                "note": row["note"],
                "explanation": row["explanation"],
                "done_by": row["done_by"],
                "fulfilled": bool(row["fulfilled"]),
                "pending_approval": bool(row["pending_approval"]),
                "show_pd": bool(row["show_pd"]),
            })
        
        logger.info(f"Retrieved {len(cards)} need cards from demo DB")
        if len(cards) > 0:
            logger.debug(f"First card: {cards[0]}")
        return cards
    finally:
        conn.close()


def approve_need_card_demo(need_card_id: str, approved: bool) -> dict:
    """Approve or reject a need card in demo database."""
    conn = get_demo_connection()
    cursor = conn.cursor()
    
    try:
        if approved:
            cursor.execute("""
                UPDATE need_cards
                SET show_pd = 1, pending_approval = 0, updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), need_card_id))
        else:
            cursor.execute("""
                UPDATE need_cards
                SET pending_approval = 0, show_pd = 0, updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), need_card_id))
        
        conn.commit()
        
        # Fetch updated card
        cursor.execute("SELECT * FROM need_cards WHERE id = ?", (need_card_id,))
        row = cursor.fetchone()
        
        if row:
            logger.info(f"Updated need card {need_card_id} in demo DB (approved={approved})")
            return {
                "id": row["id"],
                "incident_id": row["incident_id"],
                "type": row["type"],
                "item": row["item"],
                "qty": row["qty"],
                "note": row["note"],
                "explanation": row["explanation"],
                "done_by": row["done_by"],
                "fulfilled": bool(row["fulfilled"]),
                "pending_approval": bool(row["pending_approval"]),
                "show_pd": bool(row["show_pd"]),
            }
        
        return None
    finally:
        conn.close()


def take_up_need_card_demo(need_card_id: str, name: str) -> dict:
    """Mark a need card as taken in demo database."""
    conn = get_demo_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE need_cards
            SET fulfilled = 1, done_by = ?, updated_at = ?
            WHERE id = ?
        """, (name, datetime.now().isoformat(), need_card_id))
        
        conn.commit()
        
        # Fetch updated card
        cursor.execute("SELECT * FROM need_cards WHERE id = ?", (need_card_id,))
        row = cursor.fetchone()
        
        if row:
            logger.info(f"Marked need card {need_card_id} as taken by {name} in demo DB")
            return {
                "id": row["id"],
                "incident_id": row["incident_id"],
                "type": row["type"],
                "item": row["item"],
                "qty": row["qty"],
                "note": row["note"],
                "explanation": row["explanation"],
                "done_by": row["done_by"],
                "fulfilled": bool(row["fulfilled"]),
                "pending_approval": bool(row["pending_approval"]),
                "show_pd": bool(row["show_pd"]),
            }
        
        return None
    finally:
        conn.close()


def create_incident_demo(incident_data: dict) -> dict:
    """Create an incident in demo database. If it already exists, return the existing one."""
    conn = get_demo_connection()
    cursor = conn.cursor()
    
    incident_id = incident_data.get("incident_id")
    
    try:
        # Check if incident already exists
        cursor.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,))
        existing = cursor.fetchone()
        
        if existing:
            logger.info(f"Incident {incident_id} already exists in demo DB, returning existing record")
            return {
                "incident_id": existing["incident_id"],
                "incident_name": existing["incident_name"],
                "incident_type": existing["incident_type"],
                "location": existing["location"],
                "title": existing["title"],
                "severity": existing["severity"],
                "summary": existing["summary"],
                "status": existing["status"],
            }
        
        # Insert new incident
        cursor.execute("""
            INSERT INTO incidents
            (incident_id, incident_name, incident_type, location, title, severity, summary, created_at, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident_id,
            incident_data.get("incident_name", incident_id),
            incident_data.get("incident_type"),
            incident_data.get("location"),
            incident_data.get("title"),
            incident_data.get("severity", 5),
            incident_data.get("summary"),
            datetime.now().isoformat(),
            incident_data.get("status", "active"),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        logger.info(f"Created incident {incident_id} in demo DB")
        
        return {
            "incident_id": incident_data.get("incident_id"),
            "incident_name": incident_data.get("incident_name", incident_data.get("incident_id")),
            "incident_type": incident_data.get("incident_type"),
            "location": incident_data.get("location"),
            "title": incident_data.get("title"),
            "severity": incident_data.get("severity", 5),
            "summary": incident_data.get("summary"),
            "status": incident_data.get("status", "active"),
        }
    finally:
        conn.close()


def reset_demo_db():
    """Reset demo database - clear all data completely."""
    logger.info("Resetting demo database...")
    
    conn = get_demo_connection()
    cursor = conn.cursor()
    
    try:
        # Delete all need cards
        cursor.execute("DELETE FROM need_cards")
        deleted_cards = cursor.rowcount
        logger.info(f"Deleted {deleted_cards} need cards")
        
        # Delete all incidents
        cursor.execute("DELETE FROM incidents")
        deleted_incidents = cursor.rowcount
        logger.info(f"Deleted {deleted_incidents} incidents")
        
        # Delete all activity feed
        cursor.execute("DELETE FROM activity_feed")
        deleted_feed = cursor.rowcount
        logger.info(f"Deleted {deleted_feed} activity feed items")
        
        conn.commit()
        
        # Verify deletion
        cursor.execute("SELECT COUNT(*) as count FROM need_cards")
        remaining_cards = cursor.fetchone()["count"]
        logger.info(f"Verification: {remaining_cards} need cards remaining in DB")
        
        logger.info("Demo database reset complete - all data cleared")
    finally:
        conn.close()


def get_activity_feed_demo() -> list:
    """Get all activity feed items from demo database."""
    conn = get_demo_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM activity_feed ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        
        items = []
        for row in rows:
            items.append({
                "id": row["id"],
                "type": row["type"],
                "message": row["message"],
                "timestamp": row["timestamp"],
            })
        
        logger.info(f"Retrieved {len(items)} activity feed items from demo DB")
        return items
    finally:
        conn.close()


def add_activity_log_demo(activity_type: str, message: str) -> dict:
    """Add an activity log entry to demo database."""
    conn = get_demo_connection()
    cursor = conn.cursor()
    
    try:
        activity_id = f"log_{datetime.now().timestamp()}"
        cursor.execute("""
            INSERT INTO activity_feed
            (id, type, message, timestamp)
            VALUES (?, ?, ?, ?)
        """, (
            activity_id,
            activity_type,
            message,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        logger.debug(f"Added activity log: {activity_type} - {message}")
        
        return {
            "id": activity_id,
            "type": activity_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
    finally:
        conn.close()
