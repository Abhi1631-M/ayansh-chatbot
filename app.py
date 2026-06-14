"""
Ayansh Infocom Private Limited -- Web Chat & Admin Server
==========================================================
FastAPI backend serving the chat UI, admin panel, and all
API endpoints that power the LangGraph chatbot.

Run:  python app.py
Open: http://localhost:8000         (Chat UI)
      http://localhost:8000/admin   (Admin Panel)
"""

from __future__ import annotations

import sys
import io
import uvicorn

# Force UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
import secrets
import hashlib
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from graph.builder import chatbot_graph
from database.db import get_connection

# ── Auth config ───────────────────────────────────────────
_ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")
_TOKEN_TTL_HOURS = 8   # tokens expire after 8 hours

# In-memory token store: {token: expiry_datetime}
_active_tokens: dict[str, datetime] = {}


def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _create_token() -> str:
    return secrets.token_urlsafe(32)


def _validate_token(token: str | None) -> bool:
    """Return True if token exists and has not expired."""
    if not token:
        return False
    expiry = _active_tokens.get(token)
    if not expiry:
        return False
    if datetime.utcnow() > expiry:
        del _active_tokens[token]
        return False
    return True


def _require_auth(request: Request):
    """FastAPI dependency — raises 401 if token invalid."""
    token = request.cookies.get("admin_token") or request.headers.get("X-Admin-Token")
    if not _validate_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")

app = FastAPI(title="Ayansh Infocom Chatbot")

# Serve static files
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the chat interface."""
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/admin-login", response_class=HTMLResponse)
async def serve_login():
    """Serve the login page."""
    html_path = STATIC_DIR / "login.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/admin", response_class=HTMLResponse)
async def serve_admin(request: Request):
    """Serve the admin panel — redirect to login if not authenticated."""
    token = request.cookies.get("admin_token")
    if not _validate_token(token):
        return RedirectResponse(url="/admin-login", status_code=302)
    html_path = STATIC_DIR / "admin.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """Process a chat message through the LangGraph pipeline."""
    body = await request.json()
    user_message = body.get("message", "").strip()
    chat_history = body.get("history", [])

    if not user_message:
        return JSONResponse(
            content={"error": "Empty message"},
            status_code=400,
        )

    try:
        result = chatbot_graph.invoke({
            "user_input": user_message,
            "chat_history": chat_history,
            "retrieved_context": "",
            "router_decision": "",
            "final_response": "",
        })

        response_text = result.get("final_response", "Sorry, I couldn't generate a response.")
        route_taken = result.get("router_decision", "unknown")

        # Intercept Lead Capture JSON
        import re
        from database.db import save_lead
        
        lead_match = re.search(r"\[LEAD_CAPTURE\](.*?)\[/LEAD_CAPTURE\]", response_text, re.DOTALL)
        if lead_match:
            try:
                import json
                lead_data = json.loads(lead_match.group(1).strip())
                save_lead(
                    customer_name=lead_data.get("name", "Unknown"),
                    contact_info=lead_data.get("phone", "Unknown"),
                    product_interest=lead_data.get("product", "Unknown")
                )
                # Remove the block from the user's visible text
                response_text = re.sub(r"\[LEAD_CAPTURE\].*?\[/LEAD_CAPTURE\]", "", response_text, flags=re.DOTALL).strip()
            except Exception as e:
                print(f"Error parsing lead capture data: {e}")

        # Log to Supabase PostgreSQL
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO chat_logs (user_query, bot_response, route_decision) VALUES (%s, %s, %s)",
                (user_message, response_text, route_taken)
            )
            conn.commit()
            conn.close()
        except Exception as log_e:
            print(f"Error logging chat to DB: {log_e}")

        return JSONResponse(content={
            "response": response_text,
            "route": route_taken,
        })

    except Exception as e:
        return JSONResponse(
            content={"error": f"An error occurred: {str(e)}"},
            status_code=500,
        )

# ═══════════════════════════════════════════════════════════
#  WHATSAPP WEBHOOK (TWILIO)
# ═══════════════════════════════════════════════════════════

@app.post("/api/whatsapp")
async def whatsapp_endpoint(request: Request):
    """Process incoming WhatsApp messages from Twilio."""
    body = await request.form()
    user_message = body.get("Body", "").strip()
    phone_number = body.get("From", "").strip()

    if not user_message:
        return Response(content="<Response></Response>", media_type="application/xml")

    from database.db import get_whatsapp_history, update_whatsapp_history
    chat_history = get_whatsapp_history(phone_number)

    try:
        result = chatbot_graph.invoke({
            "user_input": user_message,
            "chat_history": chat_history,
            "retrieved_context": "",
            "router_decision": "",
            "final_response": "",
        })

        response_text = result.get("final_response", "Sorry, I couldn't generate a response.")
        route_taken = result.get("router_decision", "unknown")

        # Intercept Lead Capture JSON
        import re
        from database.db import save_lead
        
        lead_match = re.search(r"\[LEAD_CAPTURE\](.*?)\[/LEAD_CAPTURE\]", response_text, re.DOTALL)
        if lead_match:
            try:
                import json
                lead_data = json.loads(lead_match.group(1).strip())
                save_lead(
                    customer_name=lead_data.get("name", "Unknown"),
                    contact_info=lead_data.get("phone", "Unknown"),
                    product_interest=lead_data.get("product", "Unknown")
                )
                # Remove the block from the user's visible text
                response_text = re.sub(r"\[LEAD_CAPTURE\].*?\[/LEAD_CAPTURE\]", "", response_text, flags=re.DOTALL).strip()
            except Exception as e:
                print(f"Error parsing lead capture data: {e}")

        # Update History
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": response_text})
        if len(chat_history) > 10:
            chat_history = chat_history[-10:]
        update_whatsapp_history(phone_number, chat_history)

        # Log to Supabase PostgreSQL
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO chat_logs (user_query, bot_response, route_decision) VALUES (%s, %s, %s)",
                (f"[WA] {user_message}", response_text, route_taken)
            )
            conn.commit()
            conn.close()
        except Exception as log_e:
            print(f"Error logging WA chat to DB: {log_e}")

        # Return TwiML XML
        xml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message><![CDATA[{response_text}]]></Message>
</Response>"""
        return Response(content=xml_response, media_type="application/xml")
    except Exception as e:
        print(f"Error processing WhatsApp message: {e}")
        return Response(content="<Response></Response>", media_type="application/xml")



# ═══════════════════════════════════════════════════════════
#  AUTH ENDPOINTS
# ═══════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/admin/login")
async def admin_login(body: LoginRequest):
    """Validate credentials and issue a session token."""
    if (body.username != _ADMIN_USERNAME or
            body.password != _ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token  = _create_token()
    expiry = datetime.utcnow() + timedelta(hours=_TOKEN_TTL_HOURS)
    _active_tokens[token] = expiry

    response = JSONResponse(content={"token": token, "expires_in_hours": _TOKEN_TTL_HOURS})
    response.set_cookie(
        key="admin_token", value=token,
        httponly=True, samesite="lax",
        max_age=_TOKEN_TTL_HOURS * 3600,
    )
    return response


@app.post("/api/admin/logout")
async def admin_logout(request: Request):
    """Invalidate the current session token."""
    token = request.cookies.get("admin_token")
    if token and token in _active_tokens:
        del _active_tokens[token]
    response = JSONResponse(content={"status": "ok", "message": "Logged out."})
    response.delete_cookie("admin_token")
    return response


@app.get("/api/admin/chat-logs")
async def get_chat_logs(request: Request):
    """Return recent chat logs for the admin panel."""
    token = request.cookies.get("admin_token")
    if not _validate_token(token):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    from database.db import get_chat_logs as db_get_chat_logs
    logs = db_get_chat_logs(limit=50)
    return {"logs": logs}

@app.get("/api/admin/leads")
async def get_leads_api(request: Request):
    """Return all captured leads for the admin panel."""
    token = request.cookies.get("admin_token")
    if not _validate_token(token):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    from database.db import get_all_leads
    leads = get_all_leads()
    return {"leads": leads}


@app.get("/api/admin/me")
async def admin_me(request: Request):
    """Check if current session is valid."""
    token = request.cookies.get("admin_token")
    if not _validate_token(token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return JSONResponse(content={"authenticated": True, "username": _ADMIN_USERNAME})


# ═══════════════════════════════════════════════════════════
#  ADMIN API — Products
# ═══════════════════════════════════════════════════════════

class ProductModel(BaseModel):
    product_id: str
    name: str
    brand: str
    category: str
    unit_price_inr: float
    stock_qty: int
    warehouse: str
    std_shipping_days: int = 5
    exp_shipping_days: int = 2
    exp_surcharge_inr: float = 0.0
    weight_kg: Optional[float] = None
    restock_date: Optional[str] = None
    alternative_product: Optional[str] = None
    keywords: Optional[str] = None


class OfferModel(BaseModel):
    code: str
    description: str
    discount_pct: float
    valid_until: str


class KnowledgeModel(BaseModel):
    category: str
    title: str
    content: str
    keywords: Optional[str] = None


@app.get("/api/admin/products", dependencies=[Depends(_require_auth)])
async def admin_get_products():
    """Return all products with their offers."""
    conn = get_connection()
    try:
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM products ORDER BY category, name")
        rows = cur.fetchall()
        products = []
        for row in rows:
            p = dict(row)
            cur.execute(
                "SELECT * FROM offers WHERE product_id = %s", (p["product_id"],)
            )
            offer = cur.fetchone()
            p["offer"] = dict(offer) if offer else None
            products.append(p)
        return JSONResponse(content={"products": products})
    finally:
        conn.close()


@app.post("/api/admin/products", dependencies=[Depends(_require_auth)])
async def admin_add_product(product: ProductModel):
    """Add a new product."""
    
    # Auto-generate keywords separated by commas so the Chatbot can always find it!
    if not product.keywords:
        words = set(f"{product.name} {product.brand} {product.category}".lower().split())
        product.keywords = ",".join(words)
        
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO products
              (product_id, name, brand, category, unit_price_inr, stock_qty,
               warehouse, std_shipping_days, exp_shipping_days, exp_surcharge_inr,
               weight_kg, restock_date, alternative_product, keywords)
            VALUES
              (%(product_id)s, %(name)s, %(brand)s, %(category)s, %(unit_price_inr)s, %(stock_qty)s,
               %(warehouse)s, %(std_shipping_days)s, %(exp_shipping_days)s, %(exp_surcharge_inr)s,
               %(weight_kg)s, %(restock_date)s, %(alternative_product)s, %(keywords)s)
            """,
            product.model_dump(),
        )
        conn.commit()
        return JSONResponse(content={"status": "ok", "message": "Product added."})
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.put("/api/admin/products/{product_id}", dependencies=[Depends(_require_auth)])
async def admin_update_product(product_id: str, product: ProductModel):
    """Update an existing product."""
    conn = get_connection()
    try:
        data = product.model_dump()
        data["_id"] = product_id
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE products SET
              name=%(name)s, brand=%(brand)s, category=%(category)s, unit_price_inr=%(unit_price_inr)s,
              stock_qty=%(stock_qty)s, warehouse=%(warehouse)s, std_shipping_days=%(std_shipping_days)s,
              exp_shipping_days=%(exp_shipping_days)s, exp_surcharge_inr=%(exp_surcharge_inr)s,
              weight_kg=%(weight_kg)s, restock_date=%(restock_date)s,
              alternative_product=%(alternative_product)s, keywords=%(keywords)s
            WHERE product_id=%(_id)s
            """,
            data,
        )
        conn.commit()
        return JSONResponse(content={"status": "ok", "message": "Product updated."})
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.delete("/api/admin/products/{product_id}", dependencies=[Depends(_require_auth)])
async def admin_delete_product(product_id: str):
    """Delete a product and its offer."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM offers WHERE product_id = %s", (product_id,))
        cur.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        conn.commit()
        return JSONResponse(content={"status": "ok", "message": "Product deleted."})
    finally:
        conn.close()


# ── Offers ──────────────────────────────────────────────────

@app.post("/api/admin/products/{product_id}/offer", dependencies=[Depends(_require_auth)])
async def admin_set_offer(product_id: str, offer: OfferModel):
    """Add or replace the offer for a product."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM offers WHERE product_id = %s", (product_id,))
        cur.execute(
            "INSERT INTO offers (product_id, code, description, discount_pct, valid_until) VALUES (%s,%s,%s,%s,%s)",
            (product_id, offer.code, offer.description, offer.discount_pct, offer.valid_until),
        )
        conn.commit()
        return JSONResponse(content={"status": "ok", "message": "Offer saved."})
    finally:
        conn.close()


@app.delete("/api/admin/products/{product_id}/offer", dependencies=[Depends(_require_auth)])
async def admin_delete_offer(product_id: str):
    """Remove the offer from a product."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM offers WHERE product_id = %s", (product_id,))
        conn.commit()
        return JSONResponse(content={"status": "ok", "message": "Offer removed."})
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════
#  ADMIN API — Knowledge Chunks
# ═══════════════════════════════════════════════════════════

@app.get("/api/admin/knowledge", dependencies=[Depends(_require_auth)])
async def admin_get_knowledge():
    """Return all knowledge chunks."""
    conn = get_connection()
    try:
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM knowledge_chunks ORDER BY category, id")
        return JSONResponse(content={"chunks": [dict(r) for r in cur.fetchall()]})
    finally:
        conn.close()


@app.post("/api/admin/knowledge", dependencies=[Depends(_require_auth)])
async def admin_add_knowledge(chunk: KnowledgeModel):
    """Add a new knowledge chunk."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO knowledge_chunks (category, title, content, keywords) VALUES (%s,%s,%s,%s) RETURNING id",
            (chunk.category, chunk.title, chunk.content, chunk.keywords),
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        
        from database.vector_db import upsert_knowledge_chunk
        upsert_knowledge_chunk(
            chunk_id=new_id, 
            title=chunk.title, 
            content=chunk.content, 
            category=chunk.category
        )
        
        return JSONResponse(content={"status": "ok", "message": "Chunk added."})
    finally:
        conn.close()


@app.put("/api/admin/knowledge/{chunk_id}", dependencies=[Depends(_require_auth)])
async def admin_update_knowledge(chunk_id: int, chunk: KnowledgeModel):
    """Update a knowledge chunk."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE knowledge_chunks SET category=%s, title=%s, content=%s, keywords=%s WHERE id=%s",
            (chunk.category, chunk.title, chunk.content, chunk.keywords, chunk_id),
        )
        conn.commit()
        
        from database.vector_db import upsert_knowledge_chunk
        upsert_knowledge_chunk(
            chunk_id=chunk_id, 
            title=chunk.title, 
            content=chunk.content, 
            category=chunk.category
        )

        return JSONResponse(content={"status": "ok", "message": "Chunk updated."})
    finally:
        conn.close()


@app.delete("/api/admin/knowledge/{chunk_id}", dependencies=[Depends(_require_auth)])
async def admin_delete_knowledge(chunk_id: int):
    """Delete a knowledge chunk."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM knowledge_chunks WHERE id = %s", (chunk_id,))
        conn.commit()
        
        from database.vector_db import delete_knowledge_chunk
        delete_knowledge_chunk(chunk_id)

        return JSONResponse(content={"status": "ok"})
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════
#  ADMIN API — Analytics & Logs
# ═══════════════════════════════════════════════════════════

@app.get("/api/admin/chat-logs", dependencies=[Depends(_require_auth)])
async def admin_get_chat_logs(limit: int = 100):
    """Return recent chat interactions."""
    conn = get_connection()
    try:
        import psycopg2.extras
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM chat_logs ORDER BY timestamp DESC LIMIT %s", 
            (limit,)
        )
        logs = []
        for r in cur.fetchall():
            d = dict(r)
            # Convert timestamp to string for JSON serialization
            if d.get('timestamp'):
                d['timestamp'] = str(d['timestamp'])
            logs.append(d)
        return JSONResponse(content={"logs": logs})
    finally:
        conn.close()


if __name__ == "__main__":
    print("\n  Ayansh Infocom Chatbot Server")
    print("  Chat UI:    http://localhost:8000")
    print("  Admin Panel: http://localhost:8000/admin\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
