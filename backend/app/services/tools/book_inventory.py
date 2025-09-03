# E.g. Whether a book is available in the inventory
# ❗️Simulated false data
def search_books(query: str):
    demo = [
        {"title": "Designing with AI", "author": "Kim Lee", "status": "available"},
        {"title": "Climate & Design", "author": "R. Gray", "status": "checked out"},
        {"title": "AI for Libraries", "author": "M. Chen", "status": "available"},
    ]
    q = (query or "").lower()
    return [b for b in demo if q in b["title"].lower() or q in b["author"].lower()]
