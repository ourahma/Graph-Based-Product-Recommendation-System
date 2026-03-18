# Graph-Based Product Recommendation System

A backend API for product recommendations and customer segmentation powered by **Neo4j Graph Database** and the **Graph Data Science (GDS)** plugin. Customers and products are modeled as nodes; purchases, reviews, and similarities are modeled as relationships.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Running the API](#running-the-api)
- [Pipeline: How It Works](#pipeline-how-it-works)
- [API Reference](#api-reference)
- [Graph Algorithms Used](#graph-algorithms-used)
- [Troubleshooting](#troubleshooting)

---

## Overview

This system builds a **knowledge graph** of customers and products in Neo4j, then runs graph algorithms to:

- Identify customers with similar purchasing behavior (**Node Similarity → `SIMILAR_TO`**)
- Identify similar products bought by the same customers (**Node Similarity → `PRODUCT_SIMILAR`**)
- Rank products by influence (**PageRank**, **Degree Centrality**, **Betweenness**)
- Segment customers into communities (**Louvain**)

The results are exposed through a **FastAPI REST API** for consumption by any frontend.

---

## Tech Stack

| Layer          | Technology              |
| -------------- | ----------------------- |
| Graph Database | Neo4j 5.x + GDS Plugin  |
| Backend        | Python 3.10+ / FastAPI  |
| Driver         | neo4j-python-driver 5.x |
| Server         | Uvicorn                 |
| Config         | python-dotenv           |

---

## Project Structure

```
project/
├── main.py                  # FastAPI app entry point
├── config/
│   └── database.py          # Neo4j singleton client
├── routers/
│   ├── algorithms.py        # POST /algorithms/run_all, GET /algorithms/status
│   ├── recommendations.py   # GET /recommendations/client, /product, /top
│   └── customers.py         # GET /customers/segments, /top
├── services/
│   ├── gds.py               # GDS projections + algorithm execution
│   └── recommendation.py    # Cypher queries for recommendations
├── utils/
│   └── cache.py             # In-memory TTL cache
├── .env                     # Environment variables (not committed)
└── requirements.txt
```

---

## Setup & Installation

### 1. Prerequisites

- Python 3.10+
- Neo4j Desktop (or Neo4j AuraDB) with the **GDS plugin** installed
- Your CSV datasets imported into Neo4j (`customers.csv`, `products.csv`, `purchases_1M.csv`, `reviews_1M.csv`)

### 2. Clone & install dependencies

```bash
git clone <your-repo-url>
cd project

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure Neo4j

Make sure your Neo4j instance is **running** before starting the API.

In Neo4j Desktop: open your project → click **Start**.

> **Important:** Use `bolt://` not `neo4j://` in your URI for standalone instances.
> Using `neo4j://` on a non-cluster instance causes `Unable to retrieve routing information`.

---

## Environment Variables

Create a `.env` file at the project root:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

---

## Running the API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs available at: **http://localhost:8000/docs**

---

## Pipeline: How It Works

The recommendation engine requires a **one-time pre-computation step** before any endpoint returns data. This is done by calling the pipeline endpoint.

### Step 1 — Trigger the pipeline

```
POST /api/v1/algorithms/run_all?limit=100
```

The pipeline runs **in the background**. Response is immediate:

```json
{ "status": "started", "message": "Pipeline GDS launched on 100 clients." }
```

> `limit` controls how many customers are included in the computation.
> Start with `100` for testing, increase progressively for production.

### Step 2 — Wait for completion

Poll this endpoint until `running` is `false`:

```
GET /api/v1/algorithms/status
```

```json
{
  "pipeline": {
    "running": false,
    "last_run": "2026-03-18T00:37:56",
    "last_report": {
      "tagging": { "subset_customers": 100, "subset_products": 46 },
      "louvain": { "communityCount": 4, "nodePropertiesWritten": 100 },
      "pagerank": { "nodePropertiesWritten": 146, "ranIterations": 20 },
      "similarity_customers": {
        "nodesCompared": 95,
        "relationshipsWritten": 312
      },
      "similarity_products": {
        "nodesCompared": 46,
        "relationshipsWritten": 180
      }
    },
    "error": null
  }
}
```

### Step 3 — Call recommendation endpoints

```
GET /api/v1/recommendations/client/C0001?top_k=5
```

### What the pipeline does internally

```
0. Tag N customers as SubCustomer + their products as SubProduct
1. Build CO_PURCHASED graph (Cypher projection) → run Louvain → writes c.community
2. Global projection (SubCustomer + SubProduct) → PageRank, Degree, Betweenness
3. Node Similarity (clients) → writes SIMILAR_TO relationships
4. Node Similarity (products) → writes PRODUCT_SIMILAR relationships
5. Clean up in-memory GDS projections
```

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

### Recommendations

#### `GET /recommendations/client/{client_id}`

Returns the top-K recommended products for a customer.

Combines three signals:

- **Collaborative Filtering** (50%) — products bought by similar customers
- **Community-based** (30%) — popular products within the same Louvain community
- **PageRank** (20%) — overall product influence in the graph

| Parameter   | Type            | Default | Description                      |
| ----------- | --------------- | ------- | -------------------------------- |
| `client_id` | string (path)   | —       | Customer ID (e.g. `C0001`)       |
| `top_k`     | integer (query) | `5`     | Number of recommendations (1–50) |

**Example response:**

```json
{
  "client_id": "C0001",
  "top_k": 5,
  "count": 5,
  "recommendations": [
    {
      "product_id": "P0042",
      "product_name": "Wireless Headphones Pro",
      "category": "Electronics",
      "brand": "SoundMax",
      "price": 129.99,
      "score": 0.7821,
      "method": "collaborative_filtering",
      "cf_score": 0.85,
      "community_score": 0.62,
      "pagerank_score": 0.71,
      "supporter_count": 8
    }
  ]
}
```

> **404** means either the client does not exist or the pipeline has not been run yet.

---

#### `GET /recommendations/product/{product_id}`

Returns similar products ("You might also like"). Combines Node Similarity (60%) and co-purchase frequency (40%).

| Parameter    | Type            | Default | Description               |
| ------------ | --------------- | ------- | ------------------------- |
| `product_id` | string (path)   | —       | Product ID (e.g. `P0042`) |
| `top_k`      | integer (query) | `5`     | Number of results (1–50)  |

---

#### `GET /recommendations/top`

Pre-computed ranking of top products. Cached for 5 minutes. Ideal for a homepage or trending widget.

| Parameter  | Type    | Default    | Description                                           |
| ---------- | ------- | ---------- | ----------------------------------------------------- |
| `method`   | string  | `pagerank` | `pagerank` \| `degree` \| `betweenness` \| `combined` |
| `limit`    | integer | `50`       | Number of results (1–200)                             |
| `category` | string  | `null`     | Filter by category                                    |
| `brand`    | string  | `null`     | Filter by brand                                       |

---

### Customer Segmentation

#### `GET /customers/segments`

Lists all Louvain communities with statistics.

| Parameter | Type    | Default | Description                   |
| --------- | ------- | ------- | ----------------------------- |
| `limit`   | integer | `20`    | Max segments returned (1–100) |

---

#### `GET /customers/segments/{segment_id}`

Returns customers belonging to a specific segment, ordered by purchase count.

| Parameter    | Type           | Default | Description                 |
| ------------ | -------------- | ------- | --------------------------- |
| `segment_id` | integer (path) | —       | Segment ID from `/segments` |
| `limit`      | integer        | `20`    | Max customers returned      |

---

#### `GET /customers/top`

Top customers by total amount spent.

| Parameter | Type    | Default | Description                    |
| --------- | ------- | ------- | ------------------------------ |
| `limit`   | integer | `20`    | Max customers returned (1–100) |

---

### Analytics

#### `GET /analytics/categories`

Aggregated statistics per product category: purchase volume, revenue, average rating, review count. Cached for 5 minutes.

---

### Pipeline Administration

#### `POST /algorithms/run_all`

Triggers the full GDS pipeline in the background.

| Parameter | Type    | Default | Description                    |
| --------- | ------- | ------- | ------------------------------ |
| `limit`   | integer | `100`   | Number of customers to include |

#### `GET /algorithms/status`

Returns pipeline state and cache statistics.

---

## Graph Algorithms Used

| Algorithm             | GDS Procedure              | Output                         | Used For                  |
| --------------------- | -------------------------- | ------------------------------ | ------------------------- |
| **Node Similarity**   | `gds.nodeSimilarity.write` | `SIMILAR_TO` relationship      | Finding similar customers |
| **Node Similarity**   | `gds.nodeSimilarity.write` | `PRODUCT_SIMILAR` relationship | Finding similar products  |
| **PageRank**          | `gds.pageRank.write`       | `p.pagerank` property          | Product influence score   |
| **Degree Centrality** | `gds.degree.write`         | `p.degree` property            | Product popularity        |
| **Betweenness**       | `gds.betweenness.write`    | `p.betweenness` property       | Cross-community products  |
| **Louvain**           | `gds.louvain.write`        | `c.community` property         | Customer segmentation     |

---

## Troubleshooting

### `Unable to retrieve routing information`

Neo4j is not running, or your `NEO4J_URI` uses `neo4j://` instead of `bolt://`.
Fix: Start Neo4j Desktop and set `NEO4J_URI=bolt://localhost:7687` in `.env`.

### `404` on recommendation endpoints

The pipeline has not been run yet, or it failed.
Fix: Call `POST /algorithms/run_all` and wait for `GET /algorithms/status` to return `running: false`.

### `MemoryPoolOutOfMemoryError`

Neo4j's transaction memory limit is too low.
Fix: In Neo4j Desktop → Settings → `neo4j.conf`, set:

```
dbms.memory.transaction.total.max=2g
server.memory.heap.max_size=2g
```

Then restart Neo4j.

### `nodesCompared: 0, relationshipsWritten: 0` after Node Similarity

The customers in your subset share no common products.
Fix: Increase `limit` when calling `/run_all` (e.g. `?limit=500`).

### `modularity: null` in Louvain report

Louvain found no edges between customers (no co-purchases).
This is normal with a small `limit` — increase it for meaningful communities.

### `Out of range float values are not JSON compliant`

A `NaN` value leaked into the API response.
Fix: Already handled in `gds.py` (`_safe_float`) and `algorithms.py` (json sanitization). Restart the server if the issue persists.
