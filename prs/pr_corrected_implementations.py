"""
Corrected implementations for PR #1 (bulk purchase) and PR #2 (list stats).

Written as part of the code review to demonstrate concrete fixes for every
issue logged in review_template.md. Each function follows the same pattern
established by mark_purchased() in services/list_service.py:
  - check that referenced entities (list) exist before mutating/reading,
    raising ValueError so the route can map it to a clean 404
  - never touch state outside the scope the operation is meant to affect
  - return values that mean what the caller will assume they mean
"""

from datetime import datetime, timezone
from extensions import db
from models import GroceryList, Item


# ---------------------------------------------------------------------------
# PR #1 — corrected purchase_all_items()
# ---------------------------------------------------------------------------

def purchase_all_items(list_id: str, user_id: str) -> int:
    """
    Mark all unpurchased items in a list as purchased.

    Args:
        list_id: ID of the grocery list.
        user_id: ID of the user performing the bulk purchase.

    Returns:
        The number of items newly marked as purchased by this call.

    Raises:
        ValueError: If the list does not exist.
    """
    grocery_list = db.session.get(GroceryList, list_id)
    if not grocery_list:
        raise ValueError(f"List {list_id!r} not found")

    items = Item.query.filter_by(list_id=list_id, is_purchased=False).all()
    now = datetime.now(timezone.utc)
    for item in items:
        item.is_purchased = True
        item.purchased_by = user_id
        item.purchased_at = now
    db.session.commit()
    return len(items)


# routes/lists.py addition — validates user_id the same way add_item/mark_purchased do
"""
@lists_bp.route("/<list_id>/purchase-all", methods=["POST"])
def purchase_all(list_id):
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing required field: user_id"}), 400

    try:
        count = list_service.purchase_all_items(list_id, user_id)
        return jsonify({"purchased": count}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
"""


# ---------------------------------------------------------------------------
# PR #2 — corrected get_list_stats()
# ---------------------------------------------------------------------------

def get_list_stats(list_id: str) -> dict:
    """
    Compute summary statistics for a grocery list.

    by_category counts only items still remaining (unpurchased), matching
    the frontend's stated use case: navigating the store by what's left.

    Raises:
        ValueError: If the list does not exist.
    """
    grocery_list = db.session.get(GroceryList, list_id)
    if not grocery_list:
        raise ValueError(f"List {list_id!r} not found")

    items = Item.query.filter_by(list_id=list_id).all()

    total = len(items)
    purchased = sum(1 for item in items if item.is_purchased)
    remaining = total - purchased

    by_category = {}
    for item in items:
        if item.is_purchased:
            continue
        cat = item.category or "uncategorized"
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "list_id": list_id,
        "total_items": total,
        "purchased": purchased,
        "remaining": remaining,
        "by_category": by_category,
    }


# routes/lists.py addition
"""
@lists_bp.route("/<list_id>/stats", methods=["GET"])
def list_stats(list_id):
    try:
        stats = list_service.get_list_stats(list_id)
        return jsonify(stats), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
"""
