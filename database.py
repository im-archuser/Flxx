import aiosqlite
import time

DB_NAME = "users.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                access_token TEXT,
                refresh_token TEXT,
                expires_at INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ticket_configs (
                guild_id TEXT PRIMARY KEY,
                category_id TEXT,
                support_role_id TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ticket_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT,
                label TEXT,
                description TEXT,
                emoji TEXT,
                value TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS role_panels (
                panel_id TEXT PRIMARY KEY,
                guild_id TEXT,
                channel_id TEXT,
                message_id TEXT,
                title TEXT,
                description TEXT,
                color INTEGER,
                thumbnail TEXT,
                footer TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS role_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                panel_id TEXT,
                role_id TEXT,
                emoji TEXT,
                label TEXT,
                FOREIGN KEY (panel_id) REFERENCES role_panels (panel_id) ON DELETE CASCADE
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS panel_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                panel_id TEXT,
                content TEXT,
                type TEXT DEFAULT 'text', -- 'text' or 'field'
                field_name TEXT, -- only for 'field' type
                position INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS auto_responses (
                guild_id TEXT,
                trigger TEXT,
                title TEXT,
                description TEXT,
                color INTEGER,
                image TEXT,
                footer TEXT,
                PRIMARY KEY (guild_id, trigger)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS drops (
                message_id TEXT PRIMARY KEY,
                guild_id TEXT,
                channel_id TEXT,
                file_path TEXT,
                display_name TEXT,
                download_count INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT,
                user_id TEXT,
                moderator_id TEXT,
                reason TEXT,
                timestamp INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                channel_id TEXT,
                message_id TEXT,
                message TEXT,
                remind_at INTEGER,
                status INTEGER DEFAULT 0 -- 0: Pending, 1: Expired (in 10m grace), 2: Completed/Deleted
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS generator_usage (
                user_id TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            )
        """)
        # Migration: Add footer to role_panels if not exists
        try:
            await db.execute("ALTER TABLE role_panels ADD COLUMN footer TEXT")
        except:
            pass # Already exists
            
        await db.commit()

async def delete_role_panel(panel_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM role_panels WHERE panel_id = ?", (panel_id,))
        await db.execute("DELETE FROM role_options WHERE panel_id = ?", (panel_id,))
        await db.execute("DELETE FROM panel_content WHERE panel_id = ?", (panel_id,))
        await db.commit()

async def add_panel_content(panel_id, content, type='text', field_name=None):
    async with aiosqlite.connect(DB_NAME) as db:
        # Get current max position
        async with db.execute("SELECT MAX(position) FROM panel_content WHERE panel_id = ?", (panel_id,)) as cursor:
            row = await cursor.fetchone()
            pos = (row[0] or 0) + 1
        
        await db.execute("""
            INSERT INTO panel_content (panel_id, content, type, field_name, position)
            VALUES (?, ?, ?, ?, ?)
        """, (panel_id, content, type, field_name, pos))
        await db.commit()

async def get_panel_content(panel_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM panel_content WHERE panel_id = ? ORDER BY position ASC", (panel_id,)) as cursor:
            return await cursor.fetchall()

async def clear_panel_content(panel_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM panel_content WHERE panel_id = ?", (panel_id,))
        await db.commit()

async def save_role_panel(panel_id, guild_id, channel_id, message_id, title, description, color, thumbnail, footer):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR REPLACE INTO role_panels (panel_id, guild_id, channel_id, message_id, title, description, color, thumbnail, footer)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (panel_id, str(guild_id), str(channel_id), str(message_id), title, description, color, thumbnail, footer))
        await db.commit()

async def add_role_option(panel_id, role_id, emoji, label):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO role_options (panel_id, role_id, emoji, label)
            VALUES (?, ?, ?, ?)
        """, (panel_id, str(role_id), emoji, label))
        await db.commit()

async def get_role_panel(panel_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM role_panels WHERE panel_id = ?", (panel_id,)) as cursor:
            return await cursor.fetchone()

async def get_role_options(panel_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM role_options WHERE panel_id = ?", (panel_id,)) as cursor:
            return await cursor.fetchall()

async def add_ticket_category(guild_id, label, description, emoji, value):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO ticket_categories (guild_id, label, description, emoji, value)
            VALUES (?, ?, ?, ?, ?)
        """, (str(guild_id), label, description, emoji, value))
        await db.commit()

async def remove_ticket_category(guild_id, value):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM ticket_categories WHERE guild_id = ? AND value = ?", (str(guild_id), value))
        await db.commit()

async def get_ticket_categories(guild_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM ticket_categories WHERE guild_id = ?", (str(guild_id),)) as cursor:
            return await cursor.fetchall()

async def save_ticket_config(guild_id, category_id, support_role_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR REPLACE INTO ticket_configs (guild_id, category_id, support_role_id)
            VALUES (?, ?, ?)
        """, (
            str(guild_id), 
            str(category_id) if category_id else None, 
            str(support_role_id) if support_role_id else None
        ))
        await db.commit()

async def get_ticket_config(guild_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM ticket_configs WHERE guild_id = ?", (str(guild_id),)) as cursor:
            return await cursor.fetchone()

async def save_user(user_id, access_token, refresh_token, expires_at):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR REPLACE INTO users (user_id, access_token, refresh_token, expires_at)
            VALUES (?, ?, ?, ?)
        """, (str(user_id), access_token, refresh_token, expires_at))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cursor:
            return await cursor.fetchall()

async def get_user_count():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0

async def save_auto_response(guild_id, trigger, title, description, color, image, footer):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR REPLACE INTO auto_responses (guild_id, trigger, title, description, color, image, footer)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (str(guild_id), trigger.lower(), title, description, color, image, footer))
        await db.commit()

async def get_auto_responses(guild_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM auto_responses WHERE guild_id = ?", (str(guild_id),)) as cursor:
            return await cursor.fetchall()

async def delete_auto_response(guild_id, trigger):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM auto_responses WHERE guild_id = ? AND trigger = ?", (str(guild_id), trigger.lower()))
        await db.commit()

async def save_drop(message_id, guild_id, channel_id, file_path, display_name):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO drops (message_id, guild_id, channel_id, file_path, display_name)
            VALUES (?, ?, ?, ?, ?)
        """, (str(message_id), str(guild_id), str(channel_id), file_path, display_name))
        await db.commit()

async def increment_download_count(message_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE drops SET download_count = download_count + 1 WHERE message_id = ?", (str(message_id),))
        await db.commit()
        async with db.execute("SELECT download_count FROM drops WHERE message_id = ?", (str(message_id),)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def get_drop(message_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM drops WHERE message_id = ?", (str(message_id),)) as cursor:
            return await cursor.fetchone()

# Warning System
async def add_warning(guild_id, user_id, moderator_id, reason):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (str(guild_id), str(user_id), str(moderator_id), reason, int(time.time())))
        await db.commit()

async def get_warnings(guild_id, user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM warnings WHERE guild_id = ? AND user_id = ?", (str(guild_id), str(user_id))) as cursor:
            return await cursor.fetchall()

# Reminder System
async def add_reminder(user_id, channel_id, message_id, message, remind_at):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO reminders (user_id, channel_id, message_id, message, remind_at, status)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (str(user_id), str(channel_id), str(message_id), message, int(remind_at)))
        await db.commit()

async def get_due_reminders():
    now = int(time.time())
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        # Status 0: Time reached -> notify
        # Status 1: Time + 10m reached -> delete
        async with db.execute("SELECT * FROM reminders WHERE (status = 0 AND remind_at <= ?) OR (status = 1 AND remind_at + 600 <= ?)", (now, now)) as cursor:
            return await cursor.fetchall()

async def update_reminder_status(reminder_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE reminders SET status = ? WHERE id = ?", (status, reminder_id))
        await db.commit()

async def delete_reminder(reminder_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        await db.commit()

# Leaderboard System
async def log_generator_usage(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO generator_usage (user_id, count)
            VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET count = count + 1
        """, (str(user_id),))
        await db.commit()

async def get_top_users(limit=10):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM generator_usage ORDER BY count DESC LIMIT ?", (limit,)) as cursor:
            return await cursor.fetchall()
