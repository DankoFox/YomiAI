# Graph Report - app  (2026-05-21)

## Corpus Check
- Corpus is ~14,385 words - fits in a single context window. You may not need a graph.

## Summary
- 310 nodes · 374 edges · 39 communities (26 shown, 13 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_LLM Context Enrichment|LLM Context Enrichment]]
- [[_COMMUNITY_DIF-SASRec Agent|DIF-SASRec Agent]]
- [[_COMMUNITY_User Profile Repository|User Profile Repository]]
- [[_COMMUNITY_DIF Attention Layers|DIF Attention Layers]]
- [[_COMMUNITY_App Lifecycle & Container|App Lifecycle & Container]]
- [[_COMMUNITY_FAISS & Cleora Index|FAISS & Cleora Index]]
- [[_COMMUNITY_Category Encoder|Category Encoder]]
- [[_COMMUNITY_ML Model Encoders|ML Model Encoders]]
- [[_COMMUNITY_Agent Pool|Agent Pool]]
- [[_COMMUNITY_Translation & Language Detection|Translation & Language Detection]]
- [[_COMMUNITY_Passive Recommendation Engine|Passive Recommendation Engine]]
- [[_COMMUNITY_Metadata Repository|Metadata Repository]]
- [[_COMMUNITY_MongoDB Database Layer|MongoDB Database Layer]]
- [[_COMMUNITY_Recommendation Routes|Recommendation Routes]]
- [[_COMMUNITY_FastAPI Dependencies|FastAPI Dependencies]]
- [[_COMMUNITY_API Request Schemas|API Request Schemas]]
- [[_COMMUNITY_Auth Routes|Auth Routes]]
- [[_COMMUNITY_LLM Chat Routes|LLM Chat Routes]]
- [[_COMMUNITY_Profile Routes|Profile Routes]]
- [[_COMMUNITY_Search Routes|Search Routes]]
- [[_COMMUNITY_Health Check Route|Health Check Route]]
- [[_COMMUNITY_Interact Routes|Interact Routes]]
- [[_COMMUNITY_App Config|App Config]]
- [[_COMMUNITY_FastAPI App Factory|FastAPI App Factory]]
- [[_COMMUNITY_DB Connect Lifecycle|DB Connect Lifecycle]]
- [[_COMMUNITY_DB Disconnect Lifecycle|DB Disconnect Lifecycle]]
- [[_COMMUNITY_Interaction Log Push|Interaction Log Push]]
- [[_COMMUNITY_Profile Retrieval|Profile Retrieval]]
- [[_COMMUNITY_Profile Upsert|Profile Upsert]]
- [[_COMMUNITY_Agent Context Manager|Agent Context Manager]]
- [[_COMMUNITY_Agent Pool Stats|Agent Pool Stats]]
- [[_COMMUNITY_Category Leaf Extractor|Category Leaf Extractor]]

## God Nodes (most connected - your core abstractions)
1. `UserProfileManager` - 20 edges
2. `DIFSASRecAgent` - 18 edges
3. `Retriever` - 12 edges
4. `lifespan()` - 11 edges
5. `CategoryEncoder` - 10 edges
6. `PassiveRecommendationEngine` - 10 edges
7. `AgentPool` - 9 edges
8. `generate_stream()` - 9 edges
9. `ActiveSearchEngine` - 8 edges
10. `fetch_wikipedia_summary()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `lifespan()` --calls--> `Retriever`  [INFERRED]
  core/lifespan.py → repository/faiss_repo.py
- `lifespan()` --calls--> `MetadataRepository`  [INFERRED]
  core/lifespan.py → repository/metadata_repo.py
- `lifespan()` --calls--> `CategoryEncoder`  [INFERRED]
  core/lifespan.py → services/category_encoder.py
- `lifespan()` --calls--> `UserProfileManager`  [INFERRED]
  core/lifespan.py → repository/profile_repo.py
- `lifespan()` --calls--> `PassiveRecommendationEngine`  [INFERRED]
  core/lifespan.py → services/passive_recommend.py

## Communities (39 total, 13 thin omitted)

### Community 0 - "LLM Context Enrichment"
Cohesion: 0.10
Nodes (31): _books_request(), _build_wiki_queries(), ensure_loaded(), _extract_series_name(), _extract_vol_number(), fetch_book_context(), _fetch_google_books(), fetch_wikipedia_summary() (+23 more)

### Community 1 - "DIF-SASRec Agent"
Cohesion: 0.09
Nodes (17): DIFSASRecAgent, Score candidates against the user intent vector.          Args:             i, High-level interface for DIF-SASRec — drop-in replacement for RLSequentialFilter, Load per-user weights, or reset to pretrained baseline for new users., Persist this agent's current weights as the user's personal checkpoint., Reconstruct BGE-M3 embeddings from FAISS and build model-ready tensors., Inject a pre-loaded {asin: np.ndarray[1024]} cache.         When set, _get_asin, Attach a linear-warmup + cosine-decay LR scheduler.          Call this once be (+9 more)

### Community 2 - "User Profile Repository"
Cohesion: 0.16
Nodes (5): app/repository/profile_repo.py — User profile management.  Moved from src/user, Manages all user profiles: creates, updates, and persists them.     Primary sto, Return (asin_list, category_id_list) for the DIF-SASRec model.          Both l, UserBehaviorProfile, UserProfileManager

### Community 3 - "DIF Attention Layers"
Cohesion: 0.12
Nodes (12): ContentProjector, DIFAttentionLayer, DIFSASRecBlock, DIFSASRecModel, app/services/dif_sasrec.py — DIF-SASRec model and online training agent.  Arch, [B, T, D] → [B, n_heads, T, head_dim], Args:             content:    [B, T, hidden_dim]  projected BGE-M3 embeddings, One transformer block using DIF attention.      Pre-norm architecture (LayerNo (+4 more)

### Community 4 - "App Lifecycle & Container"
Cohesion: 0.11
Nodes (13): AppContainer, app/core/container.py — Typed dependency container (replaces _state dict).  Bu, Holds every runtime dependency the routes need.      All fields are set during, lifespan(), _log_worker(), app/core/lifespan.py — FastAPI lifespan: startup, background worker, shutdown., Load all ML models and infrastructure once at startup., Export delta hyperedges → retrain Cleora → hot-reload FAISS index. (+5 more)

### Community 5 - "FAISS & Cleora Index"
Cohesion: 0.13
Nodes (9): app/repository/faiss_repo.py — FAISS + Cleora index access layer.  Index file, Layer 1: Nearest neighbours in Cleora behavioural space., Layer 2: Text + CLIP similarity scores for a list of candidates., Return (text_vec, clip_vec) tuple for the given ASIN, or None., Hot-swap the Cleora FAISS index without restarting the API.          Safe unde, Loads and provides access to FAISS indices (text encoder, CLIP) and the     Cle, Personal Pipeline candidate generation via HNSW KNN search.          Uses self, Load the text (semantic) FAISS index.          Priority:           1. Primary (+1 more)

### Community 6 - "Category Encoder"
Cohesion: 0.12
Nodes (10): CategoryEncoder, _parse_leaf_category(), app/services/category_encoder.py — Category Vocabulary for DIF-SASRec  Parses, Return the category ID for an ASIN. Returns UNK_ID if not found., Reverse lookup: int_id → category string., Convert a list of ASINs into a list of category IDs., Save vocabulary to JSON., Load vocabulary from JSON. (+2 more)

### Community 7 - "ML Model Encoders"
Cohesion: 0.14
Nodes (15): _cached_encode(), encode_image_b64(), encode_text(), load_clip(), load_text_encoder(), proxy_query_vecs(), app/core/models.py — ML model loading and encoding helpers.  Extracted from ap, Load CLIP model + processor. Returns (model, processor) or (None, None). (+7 more)

### Community 8 - "Agent Pool"
Cohesion: 0.15
Nodes (8): AgentPool, borrow(), app/services/agent_pool.py — Pool of DIFSASRecAgent instances for concurrent use, Fixed-size pool of DIFSASRecAgent instances.      Thread-safety model: asyncio, Synchronously instantiate N agents and return them as a list.          Run in, Build all agents in a thread, then populate the asyncio.Queue from the, Block until an agent is available, then remove it from the pool., Return agent to the pool after use.

### Community 9 - "Translation & Language Detection"
Cohesion: 0.21
Nodes (13): _cached_translate(), detect_language(), _get_lingua_detector(), _has_untranslated_words(), _load_nllb(), app/infrastructure/translation.py — Multilingual → EN translation via NLLB-200., Return True if significant words from `source` survived into `translation`, Translate `text` (in `nllb_src_lang`) to English.      Strategy:       1. Fas (+5 more)

### Community 10 - "Passive Recommendation Engine"
Cohesion: 0.19
Nodes (6): PassiveRecommendationEngine, app/services/passive_recommend.py — Mode 2: Dual-Pipeline NBA Recommendation Fun, DIF-SASRec intent → HNSW KNN → content veto → DIF-SASRec scoring.          Use, Train the DIF-SASRec model on the latest click event., System-initiated recommendations split into two independent pipelines.      Ta, Generate personalised recommendations split into two pools.          Returns N

### Community 11 - "Metadata Repository"
Cohesion: 0.25
Nodes (4): MetadataRepository, app/repository/metadata_repo.py — Parquet metadata access layer.  Extracted fr, Loads item_metadata.parquet and provides per-ASIN detail lookups., Return a fully-hydrated item dict for the given ASIN.

### Community 13 - "Recommendation Routes"
Cohesion: 0.33
Nodes (6): _cold_start(), GET /recommend and GET /rl_metrics., Return real-time DIF-SASRec model metrics., Mode 2: 3-Layer NBA Funnel.     Cold-start users receive random catalogue items, recommend(), rl_metrics()

### Community 14 - "FastAPI Dependencies"
Cohesion: 0.40
Nodes (5): get_container(), app/api/dependencies.py — FastAPI Depends() helpers.  Routes call Depends(get_, Return the AppContainer built during lifespan startup., Return the container, raising 503 if the system is still initializing., require_ready()

### Community 15 - "API Request Schemas"
Cohesion: 0.47
Nodes (5): AskLLMRequest, InteractRequest, app/api/schemas.py — Pydantic request/response models.  Moved from api.py (Sea, SearchRequest, BaseModel

### Community 16 - "Auth Routes"
Cohesion: 0.33
Nodes (5): auth_check(), auth_create(), POST /auth/check and POST /auth/create — password-free identity endpoints., Check whether a user_id exists in MongoDB.      Body: { "username": str }, Create a new user profile in MongoDB.      Body: { "username": str }     Retu

### Community 17 - "LLM Chat Routes"
Cohesion: 0.33
Nodes (5): ask_llm(), ask_llm_stream(), POST /ask_llm — Qwen2.5 grounded book assistant., Generates a conversational response about a book using Qwen2.5 (Sync)., Streams a conversational response about a book token-by-token.

### Community 18 - "Profile Routes"
Cohesion: 0.50
Nodes (3): get_profile(), GET /profile — user stats and hydrated recent history., Return aggregated user stats and hydrated recent history for the UI bar.

### Community 19 - "Search Routes"
Cohesion: 0.67
Nodes (3): POST /search — Mode 1: Multimodal Active Search., _run_pipeline(), search()

## Knowledge Gaps
- **2 isolated node(s):** `Settings`, `Database`
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `lifespan()` connect `App Lifecycle & Container` to `User Profile Repository`, `FAISS & Cleora Index`, `Category Encoder`, `Agent Pool`, `Passive Recommendation Engine`, `Metadata Repository`?**
  _High betweenness centrality (0.247) - this node is a cross-community bridge._
- **Why does `AgentPool` connect `Agent Pool` to `DIF-SASRec Agent`, `App Lifecycle & Container`?**
  _High betweenness centrality (0.165) - this node is a cross-community bridge._
- **Why does `DIFSASRecAgent` connect `DIF-SASRec Agent` to `Agent Pool`, `DIF Attention Layers`?**
  _High betweenness centrality (0.152) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `DIFSASRecAgent` (e.g. with `AgentPool` and `._build_agents()`) actually correct?**
  _`DIFSASRecAgent` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `lifespan()` (e.g. with `AppContainer` and `Retriever`) actually correct?**
  _`lifespan()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Settings`, `app/config.py — Typed settings for the NBA Recommendation System.  All constan`, `app/main.py — FastAPI application factory.  Entry point:  uvicorn app.main:app` to the rest of the system?**
  _125 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `LLM Context Enrichment` be split into smaller, more focused modules?**
  _Cohesion score 0.09659090909090909 - nodes in this community are weakly interconnected._