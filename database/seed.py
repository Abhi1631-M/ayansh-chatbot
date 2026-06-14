"""
Database Seed Script — Supabase PostgreSQL
==========================================
Run this ONCE to create tables and populate them with initial data
in the Supabase PostgreSQL database.

Usage
-----
    python -m database.seed

Running again will REPLACE all existing data (safe for re-seeding).
"""

from __future__ import annotations

import sys
import io
import os
from datetime import date, timedelta
from pathlib import Path

# Fix Unicode on Windows terminals
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Load .env so DATABASE_URL is available
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from database.db import get_connection, _dict_cursor

_SQL_PATH = Path(__file__).resolve().parent / "schema.sql"


def create_tables(conn) -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    print("  [OK] Tables created.")


def seed_products(conn) -> None:
    """Insert all products and their offers."""

    today = date.today()

    products = [
        {
            "product_id":         "FG-40F-WIFI",
            "name":               "FortiGate FortiWifi 40F",
            "brand":              "Fortinet / FortiGate",
            "category":           "Network Firewalls",
            "unit_price_inr":     80_000.00,
            "stock_qty":          5,
            "warehouse":          "Delhi Warehouse",
            "std_shipping_days":  3,
            "exp_shipping_days":  1,
            "exp_surcharge_inr":  1500.00,
            "weight_kg":          1.5,
            "restock_date":       None,
            "alternative_product": None,
            "keywords":           "fortigate,fortiwifi,firewall,40f,fortigate 40f,network firewall",
            "offer":              None,
        },
        {
            "product_id":         "SR-42U-600X1000",
            "name":               "42U 600x1000mm Floor Standing Networking Server Rack",
            "brand":              "Ayansh Infocom",
            "category":           "Server Racks",
            "unit_price_inr":     42_000.00,
            "stock_qty":          12,
            "warehouse":          "Mumbai Warehouse",
            "std_shipping_days":  5,
            "exp_shipping_days":  2,
            "exp_surcharge_inr":  3500.00,
            "weight_kg":          85.0,
            "restock_date":       None,
            "alternative_product": None,
            "keywords":           "42u,server rack,floor standing,rack,floor rack,networking rack",
            "offer": {
                "code":         "RACK26K",
                "description":  "Special promotional price - limited period offer",
                "discount_pct": 0.938,
                "valid_until":  (today + timedelta(days=30)).isoformat(),
            },
        },
        {
            "product_id":         "WR-15U-400X550",
            "name":               "15U Rack 400x550 Wall Mount",
            "brand":              "Ayansh Infocom",
            "category":           "Wall Mount Racks",
            "unit_price_inr":     4_500.00,
            "stock_qty":          25,
            "warehouse":          "Delhi Warehouse",
            "std_shipping_days":  3,
            "exp_shipping_days":  1,
            "exp_surcharge_inr":  500.00,
            "weight_kg":          15.0,
            "restock_date":       None,
            "alternative_product": None,
            "keywords":           "15u,wall rack,wall mount,wall mount rack,small rack",
            "offer": {
                "code":         "WALL3200",
                "description":  "Special discounted price: Rs.3,200 (MRP Rs.4,500)",
                "discount_pct": 0.289,
                "valid_until":  (today + timedelta(days=15)).isoformat(),
            },
        },
        {
            "product_id":         "MT-RB750Gr3",
            "name":               "Mikrotik RouterBoard hEX (RB750Gr3)",
            "brand":              "Mikrotik",
            "category":           "Routerboards & Routers",
            "unit_price_inr":     5_500.00,
            "stock_qty":          45,
            "warehouse":          "Bangalore Warehouse",
            "std_shipping_days":  4,
            "exp_shipping_days":  2,
            "exp_surcharge_inr":  400.00,
            "weight_kg":          0.5,
            "restock_date":       None,
            "alternative_product": None,
            "keywords":           "mikrotik,routerboard,hex,rb750,router,mikrotik router",
            "offer":              None,
        },
        {
            "product_id":         "AR-1930-24G",
            "name":               "Aruba Instant On 1930 24-Port Gigabit Switch",
            "brand":              "Aruba",
            "category":           "Network Switches",
            "unit_price_inr":     18_500.00,
            "stock_qty":          0,
            "warehouse":          "Mumbai Warehouse",
            "std_shipping_days":  5,
            "exp_shipping_days":  2,
            "exp_surcharge_inr":  800.00,
            "weight_kg":          2.5,
            "restock_date":       (today + timedelta(days=10)).isoformat(),
            "alternative_product": "TP-Link 24-Port Gigabit Switch (In stock)",
            "keywords":           "aruba,switch,1930,24 port,aruba switch,network switch",
            "offer":              None,
        },
    ]

    cur = conn.cursor()

    # Clear existing data (offers first due to FK)
    cur.execute("DELETE FROM offers")
    cur.execute("DELETE FROM products")

    for p in products:
        offer = p.pop("offer")

        cur.execute(
            """
            INSERT INTO products
              (product_id, name, brand, category, unit_price_inr, stock_qty,
               warehouse, std_shipping_days, exp_shipping_days,
               exp_surcharge_inr, weight_kg, restock_date,
               alternative_product, keywords)
            VALUES
              (%(product_id)s, %(name)s, %(brand)s, %(category)s, %(unit_price_inr)s, %(stock_qty)s,
               %(warehouse)s, %(std_shipping_days)s, %(exp_shipping_days)s,
               %(exp_surcharge_inr)s, %(weight_kg)s, %(restock_date)s,
               %(alternative_product)s, %(keywords)s)
            """,
            p,
        )

        if offer:
            cur.execute(
                """
                INSERT INTO offers (product_id, code, description, discount_pct, valid_until)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (p["product_id"], offer["code"], offer["description"],
                 offer["discount_pct"], offer["valid_until"]),
            )

    conn.commit()
    print(f"  [OK] {len(products)} products seeded.")


def seed_knowledge(conn) -> None:
    """Insert all knowledge base chunks."""

    chunks = [
        # -- Company Info
        {
            "category": "company_info",
            "title":    "About Ayansh Infocom Private Limited & Contact Info",
            "content":  (
                "Established in 2025, Ayansh Infocom Private Limited is a premier Trader and Retailer "
                "of high-performance Network Switches, Mikrotik Routerboards, Server Racks, and Wireless Equipment. "
                "Founded by Mr. Devendra Tripathi.\n\n"
                "**Contact Information**\n"
                "- **Address:** 301 Padama Place, Nehru Place\n"
                "- **Phone:** +91 98996 81017\n"
                "- **Email:** devendra@ayanshinfo.com"
            ),
            "keywords": "ayansh,infocom,company,about,founder,devendra,tripathi,contact,address,phone,email,location,nehru place",
        },
        {
            "category": "company_info",
            "title":    "Authorized Brand Partnerships",
            "content":  (
                "We are an authorized retailer for:\n"
                "- Mikrotik: Advanced routing solutions for ISPs and enterprises.\n"
                "- Ubiquiti: High-performance wireless broadband and WiFi.\n"
                "- Grandstream: Unified communications and networking.\n"
                "- Aruba & TP-Link: Enterprise-grade switching and access points.\n"
                "- Huawei & FortiGate: Robust network infrastructure and firewall solutions."
            ),
            "keywords": "brand,partner,authorized,mikrotik,ubiquiti,grandstream,aruba,tp-link,huawei,fortigate",
        },
        # -- FortiGate
        {
            "category": "fortigate_40f",
            "title":    "FortiGate FortiWifi 40F - Technical Specifications",
            "content":  (
                "- Product Type: Network Firewall / Secure SD-WAN\n"
                "- Ports: 5 x GE RJ45 ports (1 x WAN, 4 x LAN)\n"
                "- Wireless: Built-in Dual Band WiFi 6 (2.4GHz / 5GHz)\n"
                "- Firewall Throughput: 5 Gbps\n"
                "- IPS Throughput: 1 Gbps\n"
                "- NGFW Throughput: 800 Mbps\n"
                "- Threat Protection: 600 Mbps\n"
                "- Features: FortiGuard AI/ML threat intelligence, ZTNA, SD-WAN\n"
                "- Form Factor: Desktop"
            ),
            "keywords": "fortigate,fortiwifi,firewall,40f,specs,specification,throughput,ips,ngfw",
        },
        # -- 42U Server Rack
        {
            "category": "42u_server_rack",
            "title":    "42U 600x1000mm Floor Standing Server Rack - Specifications",
            "content":  (
                "- External Dimensions: 600 mm (W) x 1000 mm (D) x 2055 mm (H)\n"
                "- Internal Usable Height: 42U\n"
                "- Load Capacity: Up to 800 kg static load\n"
                "- Material: Heavy-duty Cold-rolled steel\n"
                "- Doors: Perforated front & rear doors for maximum airflow\n"
                "- Cable Management: Integrated vertical cable managers on both sides\n"
                "- Accessories: Leveling feet, casters, mounting hardware included"
            ),
            "keywords": "42u,server rack,floor standing,dimension,weight,load capacity,specification,rack specs",
        },
        # -- 15U Wall Rack
        {
            "category": "15u_wall_rack",
            "title":    "15U Rack 400x550 Wall Mount - Specifications",
            "content":  (
                "- External Dimensions: 600 mm (W) x 400/550 mm (D) x ~770 mm (H)\n"
                "- Internal Usable Height: 15U\n"
                "- Load Capacity: Up to 60 kg\n"
                "- Door: Toughened glass front door with key lock\n"
                "- Ventilation: Top and bottom cooling vents\n"
                "- Mounting: Wall mountable with heavy-duty anchor slots"
            ),
            "keywords": "15u,wall rack,wall mount,dimension,load capacity,small rack,specification",
        },
        # -- Mikrotik
        {
            "category": "mikrotik_routerboard",
            "title":    "Mikrotik RouterBoard hEX (RB750Gr3) - Specifications",
            "content":  (
                "- CPU: Dual Core 880 MHz MMIPS\n"
                "- RAM: 256 MB\n"
                "- Storage: 16 MB Flash (microSD slot available)\n"
                "- Ports: 5 x 10/100/1000 Gigabit Ethernet\n"
                "- OS: RouterOS L4 license\n"
                "- Hardware IPsec: ~470 Mbps encryption throughput\n"
                "- Power: 8-30V DC, max 5W consumption"
            ),
            "keywords": "mikrotik,routerboard,hex,specification,rb750,specs,cpu,ram",
        },
        # -- Aruba Switch
        {
            "category": "aruba_switch",
            "title":    "Aruba Instant On 1930 24G - Specifications",
            "content":  (
                "- Ports: 24 x Gigabit RJ45, 4 x 1/10GbE SFP/SFP+\n"
                "- Switching Capacity: 128 Gbps\n"
                "- Throughput: 95.23 Mpps\n"
                "- Management: Cloud web portal, mobile app, local web GUI\n"
                "- Form Factor: 1U Rack-mountable\n"
                "- Warranty: Limited Lifetime with 90-day phone support"
            ),
            "keywords": "aruba,switch,1930,specification,24 port,gigabit,specs",
        },
        # -- General FAQ
        {
            "category": "general_faq",
            "title":    "Ayansh Guarantee - Authenticity & Support",
            "content":  (
                "In a market flooded with counterfeit electronics, trust is paramount.\n"
                "- Genuine Products: Every item comes with verified authenticity certificates.\n"
                "- Warranty Support: We facilitate smooth warranty claims to minimize downtime.\n"
                "- Transparent Pricing: No hidden costs - crystal clear transparency in every quote."
            ),
            "keywords": "guarantee,authentic,genuine,trust,quality,support,warranty",
        },
        {
            "category": "general_faq",
            "title":    "Return & Refund Policy",
            "content":  (
                "- 30-day return window from delivery date for unused products in original packaging.\n"
                "- Opened or installed products may incur a 15% restocking fee.\n"
                "- Defective items covered under manufacturer warranty - free replacement or repair.\n"
                "- Return shipping prepaid for defective items; buyer pays for change-of-mind returns."
            ),
            "keywords": "return,refund,policy,replacement,restocking",
        },
        {
            "category": "general_faq",
            "title":    "Shipping & Delivery",
            "content":  (
                "- Standard shipping: 3-7 business days across India.\n"
                "- Express shipping: Available at checkout for an additional fee (1-3 business days).\n"
                "- All products are insured during transit.\n"
                "- For bulk/enterprise orders, contact us for dedicated logistics support."
            ),
            "keywords": "shipping,delivery,transit,express,standard,days",
        },
        {
            "category": "general_faq",
            "title":    "Warranty Information",
            "content":  (
                "- Network Firewalls: 1-year hardware warranty (Fortinet).\n"
                "- Mikrotik Routerboards: 15-month limited warranty.\n"
                "- Server Racks & Wall Racks: 1-year structural warranty.\n"
                "- Aruba Switches: Limited Lifetime Warranty.\n"
                "- Claims: Email support@ayanshinfo.com or visit our website."
            ),
            "keywords": "warranty,guarantee,claim,hardware warranty,support",
        },
    ]

    cur = conn.cursor()
    cur.execute("DELETE FROM knowledge_chunks")
    for c in chunks:
        cur.execute(
            """
            INSERT INTO knowledge_chunks (category, title, content, keywords)
            VALUES (%(category)s, %(title)s, %(content)s, %(keywords)s)
            """,
            c,
        )
    conn.commit()
    print(f"  [OK] {len(chunks)} knowledge chunks seeded.")


def seed_company_info(conn) -> None:
    """Insert key-value company info."""
    info = [
        ("company_name",    "Ayansh Infocom Private Limited"),
        ("founded_year",    "2025"),
        ("founder",         "Mr. Devendra Tripathi"),
        ("website",         "https://ayanshinfo.com"),
        ("business_type",   "Trader and Retailer"),
        ("specialization",  "Networking Hardware, Server Racks, Mikrotik Routerboards, Wireless Equipment"),
        ("contact_email",   "support@ayanshinfo.com"),
    ]
    cur = conn.cursor()
    cur.execute("DELETE FROM company_info")
    for key, value in info:
        cur.execute(
            "INSERT INTO company_info (key, value) VALUES (%s, %s)",
            (key, value),
        )
    conn.commit()
    print(f"  [OK] {len(info)} company info entries seeded.")


def main() -> None:
    print("\n  Ayansh Infocom -- Database Seed Script (Supabase PostgreSQL)")
    print("  " + "-" * 50)

    conn = get_connection()
    try:
        create_tables(conn)
        seed_products(conn)
        seed_knowledge(conn)
        seed_company_info(conn)
        print("\n  [OK] Database seeded successfully on Supabase!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
