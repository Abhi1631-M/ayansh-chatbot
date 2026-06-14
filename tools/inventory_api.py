"""
Inventory / ERP API Tool — Database-backed
==========================================
Queries the SQLite database (ayansh.db) for live product data:
price, stock quantity, tax, shipping dates, and offers.

To add/edit products, run:  python database/seed.py
or edit the database directly using any SQLite client.
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta

from database.db import query_product


def _resolve_gst(pin_code: str) -> tuple[float, str] | tuple[None, None]:
    """Return (rate, region_label) for a 6-digit Indian PIN code."""
    if re.match(r"^\d{6}$", pin_code):
        return 0.18, "India (GST 18%)"
    return None, None


# ═══════════════════════════════════════════════════════════
#  PUBLIC API — called by the LangGraph tool node
# ═══════════════════════════════════════════════════════════

def query_inventory_api(user_query: str, pin_code: str | None = None) -> str:
    """
    Query the SQLite database for a matching product and return
    a JSON string with pricing, stock status, shipping estimates,
    and any active promotional offers.

    Parameters
    ----------
    user_query : str
        The natural-language product query from the user.
    pin_code : str | None
        Optional 6-digit Indian PIN code for GST calculation.
    """
    product = query_product(user_query)

    if product is None:
        return json.dumps({
            "status": "not_found",
            "message": (
                "No matching product found in the Ayansh Infocom catalogue. "
                "Please refine your search or visit https://ayanshinfo.com."
            ),
        }, indent=2)

    # ── Pricing & GST ────────────────────────────────────
    unit_price = product["unit_price_inr"]
    tax_rate, region = (
        _resolve_gst(pin_code) if pin_code else (None, None)
    )

    pricing: dict = {"unit_price_inr": unit_price, "currency": "INR"}

    if tax_rate is not None:
        tax_amount = round(unit_price * tax_rate, 2)
        total      = round(unit_price + tax_amount, 2)
        pricing.update({
            "tax_region":        region,
            "tax_rate_pct":      f"{tax_rate * 100:.0f}%",
            "tax_amount_inr":    tax_amount,
            "total_with_tax_inr": total,
        })
    else:
        pricing["tax_note"] = (
            "GST not calculated — provide your 6-digit PIN code for an accurate total."
        )

    # ── Stock & Shipping ────────────────────────────────
    in_stock = product["stock_qty"] > 0
    today    = date.today()

    shipping: dict = {
        "in_stock":  in_stock,
        "stock_qty": product["stock_qty"],
        "warehouse": product["warehouse"],
    }

    if in_stock:
        std_arrival = today + timedelta(days=product["std_shipping_days"])
        exp_arrival = today + timedelta(days=product["exp_shipping_days"])
        shipping.update({
            "standard_shipping": {
                "estimated_arrival": std_arrival.isoformat(),
                "cost": "FREE",
            },
            "express_shipping": {
                "estimated_arrival": exp_arrival.isoformat(),
                "surcharge_inr":     product["exp_surcharge_inr"],
            },
        })
    else:
        shipping["restock_date"] = product.get("restock_date") or "TBD"
        if product.get("alternative_product"):
            shipping["suggested_alternative"] = product["alternative_product"]

    # ── Active Offer ────────────────────────────────────
    offer = product.get("offer")  # None or dict from DB

    # ── Assemble response ───────────────────────────────
    result = {
        "status": "found",
        "product": {
            "product_id": product["product_id"],
            "name":       product["name"],
            "brand":      product["brand"],
            "category":   product["category"],
        },
        "pricing":      pricing,
        "shipping":     shipping,
        "active_offer": offer,
    }

    return json.dumps(result, indent=2)
