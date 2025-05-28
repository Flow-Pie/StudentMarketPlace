# 🛍️ StudentMarketPlace

**StudentMarketPlace** is a user-friendly web application that allows university students to **list**, **search**, and **purchase** second-hand items like electronics, books, clothing, and furniture.

---

## 📌 Features

- 📋 Post items for sale (title, description, price, category, condition)
- 🔍 Search and filter listings
- 🧾 View item details
- 🔐 JWT-based authentication for sellers and buyers
- 🎨 Clean and responsive UI

---

## 📚 Tech Stack

- **Backend**: Python, Flask, SQLAlchemy, Marshmallow, JWT
- **Database**: PostgreSQL / SQLite
- **Frontend**: HTML, CSS, JavaScript
- **API**: RESTful API design

---

## 🧠 System Call Graph

This diagram gives a quick overview of how different parts of the system interact:

![Student Market Place Call Graph](MartketPlaceCallGraph.drawio.svg)

---

## 🧠 Sequence diagram
The shows image upload API error handling (invalid token, permission denied)

```mermaid
sequenceDiagram
    Client->>API: POST /items/123/images (invalid token)
    API->>Client: 401 Unauthorized (TOKEN_INVALID)
    Client->>API: POST /items/123/images (valid token)
    API->>DB: Check item ownership
    DB->>API: Item belongs to user B
    API->>Client: 403 Forbidden (PERMISSION_DENIED)
```


## 🚀 Getting Started

1. **Clone the repo**  
   ```bash
   git clone https://github.com/Flow-Pie/StudentMarketPlace.git
   cd StudentMarketPlace
