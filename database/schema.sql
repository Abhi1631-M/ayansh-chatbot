-- ============================================================
-- Ayansh Infocom Private Limited — SQLite Schema
-- ============================================================

-- Products Table
CREATE TABLE IF NOT EXISTS products (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id            TEXT    NOT NULL UNIQUE,
    name                  TEXT    NOT NULL,
    brand                 TEXT    NOT NULL,
    category              TEXT    NOT NULL,
    unit_price_inr        REAL    NOT NULL,
    stock_qty             INTEGER NOT NULL DEFAULT 0,
    warehouse             TEXT    NOT NULL,
    std_shipping_days     INTEGER NOT NULL DEFAULT 5,
    exp_shipping_days     INTEGER NOT NULL DEFAULT 2,
    exp_surcharge_inr     REAL    NOT NULL DEFAULT 0.0,
    weight_kg             REAL,
    restock_date          TEXT,
    alternative_product   TEXT,
    keywords              TEXT    -- comma-separated keywords for matching
);

-- Offers Table (one per product, can be NULL)
CREATE TABLE IF NOT EXISTS offers (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id    TEXT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    code          TEXT NOT NULL,
    description   TEXT NOT NULL,
    discount_pct  REAL NOT NULL,
    valid_until   TEXT NOT NULL
);

-- Knowledge Chunks Table (FAQ + Specs)
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    category  TEXT NOT NULL,  -- e.g. 'fortigate_40f', 'general_faq', 'company_info'
    title     TEXT NOT NULL,
    content   TEXT NOT NULL,
    keywords  TEXT            -- comma-separated keywords for matching
);

-- Company Info Table (key-value store)
CREATE TABLE IF NOT EXISTS company_info (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    key   TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL
);

-- Chat Logs Table (Analytics)
CREATE TABLE IF NOT EXISTS chat_logs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp      DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_query     TEXT NOT NULL,
    bot_response   TEXT NOT NULL,
    route_decision TEXT NOT NULL
);
