-- ============================================================
-- Ayansh Infocom Private Limited — PostgreSQL Schema (Supabase)
-- ============================================================

-- Leads Table (Lead Generation & Sales)
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    customer_name TEXT NOT NULL,
    contact_info TEXT NOT NULL,
    product_interest TEXT NOT NULL,
    status TEXT DEFAULT 'New',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WhatsApp Sessions Table (Chat History)
CREATE TABLE IF NOT EXISTS whatsapp_sessions (
    phone_number TEXT PRIMARY KEY,
    history JSONB NOT NULL DEFAULT '[]',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products Table
CREATE TABLE IF NOT EXISTS products (
    id                    SERIAL PRIMARY KEY,
    product_id            TEXT    NOT NULL UNIQUE,
    name                  TEXT    NOT NULL,
    brand                 TEXT    NOT NULL,
    category              TEXT    NOT NULL,
    unit_price_inr        DOUBLE PRECISION NOT NULL,
    stock_qty             INTEGER NOT NULL DEFAULT 0,
    warehouse             TEXT    NOT NULL,
    std_shipping_days     INTEGER NOT NULL DEFAULT 5,
    exp_shipping_days     INTEGER NOT NULL DEFAULT 2,
    exp_surcharge_inr     DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    weight_kg             DOUBLE PRECISION,
    restock_date          TEXT,
    alternative_product   TEXT,
    keywords              TEXT    -- comma-separated keywords for matching
);

-- Offers Table (one per product, can be NULL)
CREATE TABLE IF NOT EXISTS offers (
    id            SERIAL PRIMARY KEY,
    product_id    TEXT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    code          TEXT NOT NULL,
    description   TEXT NOT NULL,
    discount_pct  DOUBLE PRECISION NOT NULL,
    valid_until   TEXT NOT NULL
);

-- Knowledge Chunks Table (FAQ + Specs)
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id        SERIAL PRIMARY KEY,
    category  TEXT NOT NULL,
    title     TEXT NOT NULL,
    content   TEXT NOT NULL,
    keywords  TEXT
);

-- Company Info Table (key-value store)
CREATE TABLE IF NOT EXISTS company_info (
    id    SERIAL PRIMARY KEY,
    key   TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL
);

-- Chat Logs Table (Analytics)
CREATE TABLE IF NOT EXISTS chat_logs (
    id             SERIAL PRIMARY KEY,
    timestamp      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_query     TEXT NOT NULL,
    bot_response   TEXT NOT NULL,
    route_decision TEXT NOT NULL
);
