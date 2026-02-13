import logging
import os
import psycopg2
import numpy as np
import time
from urllib.parse import quote_plus
from sentence_transformers import SentenceTransformer

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)

model = SentenceTransformer("jinaai/jina-clip-v2", trust_remote_code=True)

database_url = os.getenv("DATABASE_URL")
if not database_url:
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_sslmode = os.getenv("DB_SSLMODE", "disable")

    required = {
        "DB_HOST": db_host,
        "DB_PORT": db_port,
        "DB_NAME": db_name,
        "DB_USER": db_user,
        "DB_PASSWORD": db_password,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise RuntimeError(
            "DATABASE_URL is not set and missing DB params: " + ", ".join(missing)
        )

    database_url = (
        "postgresql://"
        f"{quote_plus(db_user)}:{quote_plus(db_password)}@"
        f"{db_host}:{db_port}/{db_name}?sslmode={db_sslmode}"
    )

conn = psycopg2.connect(database_url)
cur = conn.cursor()

cur.execute("""
    SELECT pad.product_id, p.name, p.description
    FROM product_ai_data pad
    JOIN product p ON p.id = pad.product_id
""")
rows = cur.fetchall()
logger.info("Total products: %d", len(rows))

product_ids = [r[0] for r in rows]
names = [r[1] or "" for r in rows]
descriptions = [r[2] or "" for r in rows]

BATCH_SIZE = 64

start = time.time()

logger.info("Encoding names...")
name_embeddings = model.encode(
    names, batch_size=BATCH_SIZE, show_progress_bar=True, normalize_embeddings=True
)

logger.info("Encoding descriptions...")
desc_embeddings = model.encode(
    descriptions,
    batch_size=BATCH_SIZE,
    show_progress_bar=True,
    normalize_embeddings=True,
)

elapsed = time.time() - start
logger.info("Encoding done in %.1fs", elapsed)

test_emb = model.encode([names[0]], normalize_embeddings=True)[0]
cosine = np.dot(name_embeddings[0], test_emb)
logger.info("Self-check cosine: %.6f (має бути ~1.0)", cosine)

logger.info("Updating database...")
update_count = 0
for i, pid in enumerate(product_ids):
    name_vec = name_embeddings[i].tolist()
    desc_vec = desc_embeddings[i].tolist()
    cur.execute(
        """
        UPDATE product_ai_data
        SET jina_v2_clip_name_embedding = %s::vector,
            jina_v2_clip_description_embedding = %s::vector
        WHERE product_id = %s
    """,
        (str(name_vec), str(desc_vec), pid),
    )
    update_count += 1
    if update_count % 500 == 0:
        logger.info("Updated %d/%d", update_count, len(product_ids))

conn.commit()
conn.close()
logger.info("Done! Updated %d products.", update_count)
