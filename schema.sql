CREATE TABLE IF NOT EXISTS prefix (
    user_id BIGINT,
    prefix TEXT
);

CREATE TABLE IF NOT EXISTS guilds (
    guild_id BIGINT PRIMARY KEY,
    prefix TEXT
);

CREATE TABLE IF NOT EXISTS afk (
    user_id BIGINT PRIMARY KEY,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS todo (
    user_id BIGINT,
    task TEXT,
    jump_url TEXT
);

CREATE TABLE IF NOT EXISTS blacklist (
    user_id BIGINT PRIMARY KEY,
    reason TEXT
)