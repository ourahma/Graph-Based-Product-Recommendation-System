# Graph-Based Product Recommendation System
## Backend API

A production-ready FastAPI backend for intelligent product recommendations and customer segmentation powered by **Neo4j Graph Database** and **Graph Data Science (GDS)** algorithms. 

This system models your e-commerce ecosystem as a knowledge graph where customers and products are nodes, and relationships (purchases, reviews, similarities) represent behavioral and transactional patterns.

**Key Features:**
- 🎯 Personalized product recommendations using collaborative filtering
- 👥 Customer segmentation via Louvain community detection
- 📊 Graph-based ranking (PageRank, Betweenness, Degree Centrality)
- ⚡ Production-ready REST API with full documentation
- 🔄 Hybrid scoring combining 4 graph algorithms
- 📈 Real-time analytics dashboards
- 🛡️ Type-safe Python 3.10+ with FastAPI

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Running the API](#running-the-api)
- [Pipeline: How It Works](#pipeline-how-it-works)
- [API Reference](#api-reference)
- [Graph Algorithms Used](#graph-algorithms-used)
- [Troubleshooting](#troubleshooting)
- [Performance & Optimization](#performance--optimization)
- [Contributing](#contributing)

---

## Overview

This system builds a **knowledge graph** of customers and products in Neo4j, then runs graph algorithms to:

- Identify customers with similar purchasing behavior (**Node Similarity → `SIMILAR_TO`**)
- Identify similar products bought by the same customers (**Node Similarity → `PRODUCT_SIMILAR`**)
- Rank products by influence (**PageRank**, **Degree Centrality**, **Betweenness**)
- Segment customers into communities (**Louvain Community Detection**)

The results are exposed through a **FastAPI REST API** with automatic interactive documentation.

### Key Capabilities

- **Hybrid Recommendations**: Combines 70% collaborative filtering + 30% PageRank scoring
- **Real-time Insights**: Category analytics, customer segmentation, top products
- **Scalable**: Tested with 1M+ transactions and 100K+ customers/products
- **Type-Safe**: Full Python type hints with FastAPI validation
- **Well-Documented**: OpenAPI/Swagger docs, comprehensive markdown guides

---

## Tech Stack

| Layer          | Technology              | Version |
| -------------- | ----------------------- | ------- |
| Graph Database | Neo4j 5.20+ GDS         | 5.20.0+ |
| Backend        | FastAPI                 | 0.111.0 |
| Server         | Uvicorn                 | 0.30.0  |
| Python Driver  | neo4j-python-driver     | 5.20.0+ |
| Language       | Python                  | 3.10+   |
| Config         | python-dotenv           | 1.0.0+  |

---

## Architecture

### System Components

```
Frontend Layer
    ↓
REST API (FastAPI)
    ├─ Routers (endpoints)
    ├─ Services (business logic)
    └─ Utils (caching, helpers)
    ↓
Database Layer (Neo4j 5.20)
    ├─ Customer nodes
    ├─ Product nodes
    ├─ Relationships (PURCHASED, REVIEWED, SIMILAR_TO, PRODUCT_SIMILAR)
    └─ Properties (community, pagerank, degree, betweenness)
    ↓
GDS (Graph Data Science)
    ├─ Louvain (community detection)
    ├─ PageRank (ranking)
    ├─ Node Similarity (customer/product similarity)
    └─ Projections (in-memory graphs)
```

### Data Model

```
(:Customer {
  client_id: string,
  name: string,
  country: string,
  community: integer,
  pagerank: float
})

(:Product {
  product_id: string,
  product_name: string,
  category: string,
  brand: string,
  price: float,
  pagerank: float,
  degree: integer,
  betweenness: float
})

Relationships:
  (c:Customer)-[:PURCHASED {quantity, price_at_purchase}]->(p:Product)
  (c:Customer)-[:REVIEWED {rating}]->(p:Product)
  (c:Customer)-[:SIMILAR_TO {similarity}]->(c2:Customer)
  (p:Product)-[:PRODUCT_SIMILAR {similarity}]->(p2:Product)
```

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

---

## Architecture

### System Design

```
┌─────────────────────┐
│   Frontend (React)  │
│   Pages & Charts    │
└──────────┬──────────┘
           │ HTTP/REST
┌──────────▼──────────┐
│   FastAPI Backend   │
│  (main.py)          │
├─────────────────────┤
│ • Routers (KPIs)    │
│ • Services (Logic)  │
│ • Utils (Cache)     │
└──────────┬──────────┘
           │ Bolt Protocol
┌──────────▼──────────┐
│   Neo4j (5.20)      │
│  • Customer nodes   │
│  • Product nodes    │
│  • Relationships    │
│  • GDS Projections  │
└─────────────────────┘
```

### Data Flow: Recommendation Pipeline

```
1. Customer tagging (SubCustomer property)
   ↓
2. Louvain community detection (c.community)
   ↓
3. Global projection build + PageRank
   ↓
4. Node Similarity for customers (SIMILAR_TO)
   ↓
5. Node Similarity for products (PRODUCT_SIMILAR)
   ↓
6. Scoring: CF (70%) + PageRank (30%)
   ↓
7. Results cached for 5 minutes TTL
```

### Recommendation Scoring Formula

**For Customer Recommendations:**
```
score = 0.70 × CF_score + 0.30 × PageRank_score

where:
  CF_score = Σ(similarity × quantity) / Σ(similarity)
  PageRank_score = pr / (1 + pr)
```

**For Product Recommendations:**
```
score = 0.80 × Node_Similarity + 0.20 × Popularity_score
```

---

## Performance & Optimization

### Caching Strategy

- **Recommendations**: 300 seconds (5 min) TTL
- **Top Products**: 300 seconds TTL
- **Category Analytics**: 300 seconds TTL
- **Segments**: 300 seconds TTL

To clear cache at runtime, restart the server.

### Database Indexing

Ensure Neo4j has these indexes for query performance:

```cypher
CREATE INDEX customer_id IF NOT EXISTS FOR (c:Customer) ON (c.client_id);
CREATE INDEX product_id IF NOT EXISTS FOR (p:Product) ON (p.product_id);
CREATE INDEX customer_community IF NOT EXISTS FOR (c:Customer) ON (c.community);
```

### Best Practices

1. **Subset customers for testing**: Use `?limit=100` initially
2. **Scale up gradually**: Move to `limit=1000`, then `limit=10000`
3. **Monitor memory**: Keep Neo4j heap at 2GB+ for production
4. **Set proper constraints**: Unique constraints on `client_id` and `product_id`
5. **Version your GDS**: Always use the same GDS version for reproducibility

### Load Testing

For load testing, use tools like Apache JMeter or k6:

```bash
# Example with k6
k6 run --vus 100 --duration 30s load_test.js
```

---

## Contributing

### Development Setup

```bash
git clone <repo>
cd project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Code Style

- Follow PEP 8
- Use type hints (Python 3.10+)
- Run Black for formatting: `black .`
- Use Pylint: `pylint routers/ services/`

### Adding New Endpoints

1. Create a new router in `routers/new_feature.py`
2. Add business logic in `services/service_name.py`
3. Include Cypher queries with proper error handling
4. Add unit tests
5. Update this README with endpoint documentation

### Testing

```bash
pytest tests/
pytest --cov=.
```

---

## Deployment

### Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes

See [DEPLOYMENT.md](./DEPLOYMENT.md) for Kubernetes manifest examples.

### Environment Secrets

Never commit `.env`. Use your deployment platform's secret management:
- **Docker Compose**: Use `.env.local` (in .gitignore)
- **Kubernetes**: Use Secrets resource
- **Cloud platforms**: Use managed secret stores (AWS Secrets Manager, Azure KeyVault, etc.)

---

## Support & Documentation

- **API Docs**: Visit `http://localhost:8000/docs` (Swagger UI)
- **ReDoc**: Visit `http://localhost:8000/redoc` (Alternative API docs)
- **Full Documentation**: See [BACKEND_DOCUMENTATION.md](./BACKEND_DOCUMENTATION.md)
- **Neo4j Queries**: See [CYPHER_QUERIES_COMPLETE.md](./CYPHER_QUERIES_COMPLETE.md)

---

## License

MIT License - See LICENSE file for details

## Authors

Built with ❤️ for intelligent recommendation systems

Last Updated: March 2026
