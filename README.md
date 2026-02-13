# 🔍 Product Search API

> Semantic product search service built with **FastAPI** + **Jina CLIP v2** embeddings + **PostgreSQL**

The API returns ordered arrays of product IDs (`best match → worst match`) and supports hard filters for selected categories.

---

## ✨ Features

### 🎯 Semantic Search
Search by text query across product categories:
- `/faucets`
- `/tiles`
- `/vanities`
- and more...

### 🔧 Hard Filters

| Category | Filter | Values |
|----------|--------|--------|
| `lightings`, `shower-glasses`, `tub-doors`, `vanities` | `lengthMax` | Maximum length |
| `mirrors` | `widthMax` | Maximum width |
| `shower-systems` | `hasTubSpout` | Tub spout availability |
| `faucets` | `holeSpacingCompatibility` | `Single Hole` \| `Widespread` \| `Centerset` |
| `tiles` | `locations` | `wall` \| `floor` \| `shower_wall` \| `shower_floor` |

### 📄 Pagination
- **10 product IDs per page**
- Controlled via `page` parameter in request body

### ⚡ Performance Features
- LRU query embedding cache (configurable)
- Infrastructure as code via **Terraform** (DigitalOcean Droplet + Managed Postgres)

---

## 📋 API Contract

### Request
JSON body with at least:
- `query: string`
- `page: int` (default `1`)

### Response
`string[]` — array of product IDs, max **10 IDs per page**

### 📚 Documentation
Swagger: **`GET /docs`**

---

## 🏗️ Design Decisions

### 1️⃣ Why I regenerated embeddings

I regenerated product embeddings with the same model used at runtime (`jinaai/jina-clip-v2`) and with `normalize_embeddings=True` to keep one consistent vector space for both stored product vectors and incoming query vectors.

**Without this step:** old vectors (different model or normalization) can produce unstable cosine similarity and worse ranking quality.

---

### 2️⃣ Why embeddings are kept in memory

At startup, the service loads product IDs, names, and embeddings into RAM (NumPy arrays) and serves search directly from memory.

**Why:**
- ⚡ Much lower latency than querying vectors from DB on every request
- 📊 Predictable performance for benchmark traffic
- 💾 Dataset size is small enough to fit comfortably in memory

**Tradeoff:**
- Higher startup time and RAM usage, but **significantly faster** per-request search

---

### 3️⃣ How thresholding works

The API uses a **hybrid ranking strategy**:

#### Process Steps
1. Encode incoming query with `jinaai/jina-clip-v2` (`normalize_embeddings=True`)
2. Compute vector similarity against preloaded product name embeddings
3. Apply lexical boosts (exact substring + token overlap)
4. Apply endpoint-specific hard filters (when provided)
5. Sort by final score and return paginated IDs

#### Scoring Formula
```
score = 0.70 × vector_similarity + 0.20 × exact_match + 0.10 × token_overlap
```

#### Thresholding
After sorting, weak matches are removed with:
```python
top_score = best score
threshold = max(0.10, top_score × 0.25)
# keep only results where score >= threshold
```

---

### 4️⃣ How search works end-to-end

```
1. Receive request (query, optional filter fields, page)
                    ↓
2. Encode query with Jina CLIP v2 (with LRU cache for repeated queries)
                    ↓
3. Compute vector similarity against in-memory category embeddings
   (dot product on normalized vectors)
                    ↓
4. Apply lexical boosts:
   • exact substring match
   • token overlap
                    ↓
5. Apply hard filters (if provided by endpoint)
                    ↓
6. Sort by final score (best to worst)
                    ↓
7. Apply threshold (remove weak matches)
                    ↓
8. Apply pagination (10 IDs per page)
                    ↓
9. Return JSON array of product IDs
```

---

## 🛠️ Preprocessing and Indexing

I performed the following preprocessing/indexing steps:

### 1. Embedding Regeneration
- Regenerated product embeddings in `product_ai_data` using the same runtime model (`jinaai/jina-clip-v2`)
- Normalized vectors to keep one consistent vector space

### 2. Startup In-Memory Index
- On startup, load product IDs, category IDs, names, and embeddings from DB
- Group by category and store embeddings as NumPy arrays in RAM for fast scoring

### 3. In-Memory Filter Metadata
Preload filter/dimension data used for hard filters:
- **Faucets:** hole spacing compatibility
- **Tiles:** location availability
- **Shower systems:** `has_tub_spout`
- **Vanities/lightings/shower-glasses/tub-doors:** `length`
- **Mirrors:** `width`

### 4. Synthetic Flooring Category
- Build a synthetic `flooring` index by combining LVP products + tiles available for floor usage

### 5. Query Embedding LRU Cache
- Cache query embeddings to avoid recomputation and reduce latency on repeated queries

---

<p align="center">Made with ❤️</p>