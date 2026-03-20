# Graph-Based Product Recommendation System

A full-stack recommendation engine that uses a **graph database** to model relationships between customers and products, discover purchasing patterns, and serve personalized recommendations through a REST API and interactive dashboard.

---

## What the System Does

The system turns a dataset of customers, products, purchases, and reviews into a living knowledge graph. It continuously analyses how customers interact with products to:

- Recommend the most relevant products to each customer
- Surface similar products based on shared buyer behavior
- Group customers into meaningful segments based on purchasing overlap
- Rank products by their influence and popularity across the entire graph
- Provide actionable analytics on categories, revenue, and network structure

---

## Tech Stack

| Layer | Technology |
|---|---|
| Graph Database | Neo4j 5.x |
| Graph Algorithms | Neo4j Graph Data Science (GDS) Plugin |
| Backend API | FastAPI (Python 3.10+) |
| Frontend | Next.js 14 with TypeScript |
| Data Visualization | Recharts |

---

## Graph Algorithms

The system runs six graph algorithms that enrich every node and relationship with computed intelligence:

| Algorithm | What it does |
|---|---|
| **Louvain** | Groups customers into communities based on shared purchasing behavior |
| **PageRank** | Scores each product by its overall influence in the purchase network |
| **Degree Centrality** | Measures how many distinct customers have purchased each product |
| **Betweenness Centrality** | Identifies products that connect otherwise unrelated customer groups |
| **Node Similarity (customers)** | Finds pairs of customers with the most similar purchase histories |
| **Node Similarity (products)** | Finds pairs of products frequently bought by the same customers |

---

## How Recommendations Work

**For a customer** — the system finds customers with the most similar purchase histories, identifies products those customers bought that the target has not yet purchased, and ranks them by combining similarity signals, community trends, and product influence. If a customer is new or has very few purchases, the system falls back to globally influential products.

**For a product** — the system identifies other products frequently bought by the same customers and ranks them by the strength of that co-purchase signal.

**For the catalog** — products are ranked by their computed graph metrics (PageRank, popularity, or betweenness) with optional filters by category or brand.

---

## API Endpoints

Base URL: `http://localhost:8000/api/v1`

### Recommendations

| Method | Endpoint | Role |
|---|---|---|
| GET | `/recommendations/client/{client_id}` | Returns personalized product recommendations for a customer |
| GET | `/recommendations/product/{product_id}` | Returns products similar to a given product |
| GET | `/recommendations/top` | Returns top-ranked products across the entire catalog |

### Customer Segmentation

| Method | Endpoint | Role |
|---|---|---|
| GET | `/customers/segments` | Lists all customer communities with size and geographic breakdown |
| GET | `/customers/segments/{segment_id}` | Returns the customers belonging to a specific community |
| GET | `/customers/top` | Returns the highest-spending customers |

### Analytics

| Method | Endpoint | Role |
|---|---|---|
| GET | `/analytics/categories` | Aggregated purchase volume, revenue, and ratings by product category |
| GET | `/analytics/graph-stats` | Global graph metrics including node counts, density, average degree, average shortest path, and diameter |

### Pipeline Administration

| Method | Endpoint | Role |
|---|---|---|
| POST | `/algorithms/run_all` | Triggers the full graph algorithm pipeline as a background task |
| GET | `/algorithms/status` | Returns the current pipeline state and the report from the last run |

---

## Frontend

| Page | Description |
|---|---|
| **Dashboard** | Overview of key metrics, top products, top customers, and category revenue |
| **Recommendations** | Look up personalized recommendations for any customer by ID |
| **Products** | Explore products similar to a given product, with category and brand filters |
| **Segments** | Browse customer communities and explore the members of each segment |
| **Analytics** | Visual breakdown of category performance including purchases, revenue, and ratings |
| **Admin** | Trigger the algorithm pipeline, monitor its status, and inspect graph diagnostics |

---

## Acknowledgements

This project was developed as part of the **Master Big Data** program. It would not have been possible without the following open-source projects and their communities:

- [Neo4j](https://neo4j.com) and the [Graph Data Science library](https://neo4j.com/docs/graph-data-science/) for the graph database engine and algorithms
- [FastAPI](https://fastapi.tiangolo.com) for the backend framework
- [Next.js](https://nextjs.org) for the frontend framework
- [Recharts](https://recharts.org) for data visualization components
- [neo4j-python-driver](https://github.com/neo4j/neo4j-python-driver) for the official Python driver

---

## License

This project is released under the **MIT License**.
