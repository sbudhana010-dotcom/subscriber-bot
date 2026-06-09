"""
Database layer - SQLite for easy deployment
"""

import sqlite3
from datetime import datetime, date
from config import Config


class Database:
    def __init__(self, db_path="bot_data.db"):
        self.db_path = db_path
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id     INTEGER PRIMARY KEY,
                    username    TEXT DEFAULT '',
                    full_name   TEXT DEFAULT '',
                    free_subs   INTEGER DEFAULT 0,
                    paid_subs   INTEGER DEFAULT 0,
                    referrals   INTEGER DEFAULT 0,
                    total_earned INTEGER DEFAULT 0,
                    ref_code    TEXT UNIQUE,
                    referred_by INTEGER DEFAULT NULL,
                    joined_date TEXT DEFAULT (date('now'))
                );

                CREATE TABLE IF NOT EXISTS task_progress (
                    user_id     INTEGER PRIMARY KEY,
                    subscribed  INTEGER DEFAULT 0,
                    completed   INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER,
                    pkg_id      INTEGER,
                    status      TEXT DEFAULT 'pending',
                    created_at  TEXT DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    FOREIGN KEY(pkg_id)  REFERENCES packages(id)
                );

                CREATE TABLE IF NOT EXISTS packages (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT,
                    subs        INTEGER,
                    price       INTEGER,
                    delivery    TEXT DEFAULT '1-2 Ghante'
                );
            """)
            # Insert default packages if empty
            cur = conn.execute("SELECT COUNT(*) FROM packages")
            if cur.fetchone()[0] == 0:
                conn.executemany(
                    "INSERT INTO packages (name, subs, price, delivery) VALUES (?,?,?,?)",
                    [
                        ("🥉 Starter Pack",    100,   200,  "1-2 Ghante"),
                        ("🥈 Basic Pack",      500,   800,  "2-4 Ghante"),
                        ("🥇 Standard Pack",  1000,  1400,  "4-6 Ghante"),
                        ("💎 Premium Pack",   5000,  5500,  "1 Din"),
                        ("👑 VIP Pack",      10000, 10000,  "1-2 Din"),
                    ]
                )

    # ── USER METHODS ────────────────────────────────────────────────────────────

    def register_user(self, user_id, username, full_name, ref_code=None):
        """Returns True if new user, False if existing"""
        with self._conn() as conn:
            existing = conn.execute(
                "SELECT user_id FROM users WHERE user_id=?", (user_id,)
            ).fetchone()
            if existing:
                return False

            my_ref = f"ref_{user_id}"
            referred_by = None

            if ref_code:
                # Task referral: task_USERID
                if ref_code.startswith("task_"):
                    referrer_id = int(ref_code.split("_")[1])
                    if referrer_id != user_id:
                        referred_by = referrer_id
                        # Update task progress
                        conn.execute("""
                            INSERT INTO task_progress (user_id, subscribed)
                            VALUES (?, 1)
                            ON CONFLICT(user_id) DO UPDATE
                            SET subscribed = subscribed + 1
                        """, (referrer_id,))
                # Normal referral: ref_USERID
                elif ref_code.startswith("ref_"):
                    referrer_id = int(ref_code.split("_")[1])
                    if referrer_id != user_id:
                        referred_by = referrer_id
                        conn.execute("""
                            UPDATE users
                            SET referrals = referrals + 1,
                                total_earned = total_earned + ?
                            WHERE user_id = ?
                        """, (Config.REFERRAL_REWARD, referrer_id))

            conn.execute("""
                INSERT INTO users (user_id, username, full_name, ref_code, referred_by)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, full_name, my_ref, referred_by))
            return True

    def get_user(self, user_id):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id=?", (user_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_user_by_ref(self, ref_code):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT user_id FROM users WHERE ref_code=?", (ref_code,)
            ).fetchone()
            return row["user_id"] if row else None

    def add_free_subscribers(self, user_id, amount):
        with self._conn() as conn:
            conn.execute("""
                UPDATE users
                SET free_subs = free_subs + ?,
                    total_earned = total_earned + ?
                WHERE user_id = ?
            """, (amount, amount, user_id))

    # ── TASK METHODS ────────────────────────────────────────────────────────────

    def get_task_status(self, user_id):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM task_progress WHERE user_id=?", (user_id,)
            ).fetchone()
            return dict(row) if row else {"subscribed": 0, "completed": 0}

    def complete_task(self, user_id):
        """Award 5 free subs, reset task counter"""
        with self._conn() as conn:
            conn.execute("""
                UPDATE task_progress
                SET subscribed = subscribed - 10,
                    completed = completed + 1
                WHERE user_id = ?
            """, (user_id,))
            conn.execute("""
                UPDATE users
                SET free_subs = free_subs + 5,
                    total_earned = total_earned + 5
                WHERE user_id = ?
            """, (user_id,))
        return 5

    # ── ORDER METHODS ───────────────────────────────────────────────────────────

    def create_order(self, user_id, pkg_id):
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO orders (user_id, pkg_id) VALUES (?,?)",
                (user_id, pkg_id)
            )
            return cur.lastrowid

    def get_order(self, order_id):
        with self._conn() as conn:
            row = conn.execute("""
                SELECT o.*, u.user_id, u.full_name,
                       p.name as pkg_name, p.subs, p.price
                FROM orders o
                JOIN users u ON o.user_id = u.user_id
                JOIN packages p ON o.pkg_id = p.id
                WHERE o.id = ?
            """, (order_id,)).fetchone()
            return dict(row) if row else None

    def approve_order(self, order_id):
        with self._conn() as conn:
            conn.execute(
                "UPDATE orders SET status='approved' WHERE id=?", (order_id,)
            )
            row = conn.execute("""
                SELECT o.user_id, p.name as pkg_name, p.subs
                FROM orders o JOIN packages p ON o.pkg_id = p.id
                WHERE o.id = ?
            """, (order_id,)).fetchone()
            if row:
                conn.execute("""
                    UPDATE users
                    SET paid_subs = paid_subs + ?,
                        total_earned = total_earned + ?
                    WHERE user_id = ?
                """, (row["subs"], row["subs"], row["user_id"]))
            return dict(row) if row else {}

    def reject_order(self, order_id):
        with self._conn() as conn:
            conn.execute(
                "UPDATE orders SET status='rejected' WHERE id=?", (order_id,)
            )

    def get_pending_orders(self):
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT o.id, o.created_at,
                       u.full_name, u.user_id,
                       p.name as pkg_name, p.subs, p.price
                FROM orders o
                JOIN users u ON o.user_id = u.user_id
                JOIN packages p ON o.pkg_id = p.id
                WHERE o.status = 'pending'
                ORDER BY o.id DESC
            """).fetchall()
            return [dict(r) for r in rows]

    def get_user_orders(self, user_id):
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT o.id, o.status, o.created_at,
                       p.name as pkg_name, p.subs, p.price
                FROM orders o
                JOIN packages p ON o.pkg_id = p.id
                WHERE o.user_id = ?
                ORDER BY o.id DESC
            """, (user_id,)).fetchall()
            return [dict(r) for r in rows]

    # ── PACKAGE METHODS ─────────────────────────────────────────────────────────

    def get_packages(self):
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM packages ORDER BY subs").fetchall()
            return [dict(r) for r in rows]

    def get_package(self, pkg_id):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM packages WHERE id=?", (pkg_id,)
            ).fetchone()
            return dict(row) if row else None

    def update_package_price(self, pkg_id, new_price):
        with self._conn() as conn:
            conn.execute(
                "UPDATE packages SET price=? WHERE id=?", (new_price, pkg_id)
            )

    # ── STATS & MISC ────────────────────────────────────────────────────────────

    def get_all_users(self):
        with self._conn() as conn:
            rows = conn.execute("SELECT user_id FROM users").fetchall()
            return [dict(r) for r in rows]

    def get_stats(self):
        with self._conn() as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            today_users = conn.execute(
                "SELECT COUNT(*) FROM users WHERE joined_date=date('now')"
            ).fetchone()[0]
            total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            pending_orders = conn.execute(
                "SELECT COUNT(*) FROM orders WHERE status='pending'"
            ).fetchone()[0]
            rev_row = conn.execute("""
                SELECT COALESCE(SUM(p.price),0) as rev
                FROM orders o JOIN packages p ON o.pkg_id=p.id
                WHERE o.status='approved'
            """).fetchone()
            return {
                "total_users": total_users,
                "today_users": today_users,
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "total_revenue": rev_row["rev"]
            }

    def get_leaderboard(self):
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT full_name, referrals
                FROM users
                ORDER BY referrals DESC
                LIMIT 5
            """).fetchall()
            return [dict(r) for r in rows]
