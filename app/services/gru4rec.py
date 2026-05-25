"""
app/services/gru4rec.py — GRU4Rec model and training agent.

Architecture: Two-layer GRU over BGE-M3 content embeddings.
Scores candidates by dot product of the last hidden state with projected
candidate embeddings. No category stream, no auxiliary losses.

Key design choices:
  - ContentProjector: reduces BGE-M3 1024-dim → 256-dim hidden space (shared
    between sequence encoder and candidate projector so scores are comparable)
  - GRU: captures order-aware sequential patterns with fewer parameters than
    self-attention — serves as the recurrent baseline in the comparison table
  - Sampled softmax loss: same objective and negative-sampling protocol as
    DIFSASRec for a fair architectural comparison

Usage:
    agent = GRU4RecAgent(retriever)
    scores = agent.get_candidate_scores(click_asins, candidate_asins)
    loss   = agent.train_step_batch(seqs, targets, neg_pool_vecs)
"""
import copy
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from app.config import settings

# ── Constants ─────────────────────────────────────────────────────────────────
TEXT_EMBED_DIM  = settings.TEXT_EMBED_DIM       # 1024 — BGE-M3 output dim
HIDDEN_DIM      = 256                            # GRU hidden size (fixed baseline)
GRU_NUM_LAYERS  = 2
GRU_DROPOUT     = 0.2
LR              = settings.SASREC_LR            # 1e-3
WEIGHT_DECAY    = settings.SASREC_WEIGHT_DECAY  # 0.01
NUM_NEGATIVES   = settings.SASREC_NUM_NEGATIVES # 512
MAX_SEQ_LEN     = settings.MAX_SEQ_LEN          # 50


# ─────────────────────────────────────────────────────────────────────────────
# Model
# ─────────────────────────────────────────────────────────────────────────────

class ContentProjector(nn.Module):
    """Projects BGE-M3 1024-dim → 256-dim. Shape: [*, 1024] → [*, 256]"""

    def __init__(self, in_dim: int = TEXT_EMBED_DIM, out_dim: int = HIDDEN_DIM):
        super().__init__()
        self.proj = nn.Linear(in_dim, out_dim)
        self.norm = nn.LayerNorm(out_dim)
        self.drop = nn.Dropout(GRU_DROPOUT)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.drop(self.norm(self.proj(x)))


class GRU4RecModel(nn.Module):
    """
    GRU4Rec: two-layer GRU over projected BGE-M3 item embeddings.

    Intent = GRU hidden state at the last valid sequence position.
    Candidates are scored via dot product with a shared ContentProjector.
    """

    def __init__(self, hidden_dim: int = HIDDEN_DIM, num_layers: int = GRU_NUM_LAYERS,
                 max_len: int = MAX_SEQ_LEN):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.max_len    = max_len

        self.content_proj   = ContentProjector(TEXT_EMBED_DIM, hidden_dim)
        # dropout applies between GRU layers (not on the final output layer)
        self.gru            = nn.GRU(
            input_size=hidden_dim, hidden_size=hidden_dim, num_layers=num_layers,
            batch_first=True, dropout=GRU_DROPOUT,
        )
        self.final_norm     = nn.LayerNorm(hidden_dim)
        self.candidate_proj = ContentProjector(TEXT_EMBED_DIM, hidden_dim)

    def forward(self, bge_seqs: torch.Tensor,
                lengths: torch.Tensor):
        """
        Args:
            bge_seqs: [B, T, 1024]  BGE-M3 embeddings (valid items at 0..L-1, zeros after)
            lengths:  [B]           actual sequence lengths
        Returns:
            output  [B, T, hidden_dim]
            intent  [B, hidden_dim]   hidden state at last valid position
        """
        B  = bge_seqs.size(0)
        x  = self.content_proj(bge_seqs)        # [B, T, hidden_dim]
        output, _ = self.gru(x)                 # [B, T, hidden_dim]
        output    = self.final_norm(output)

        idx    = (lengths - 1).clamp(min=0)
        intent = output[torch.arange(B, device=bge_seqs.device), idx]  # [B, hidden_dim]
        return output, intent

    def score_candidates(self, intent: torch.Tensor,
                         candidate_bge: torch.Tensor) -> torch.Tensor:
        """
        Args:
            intent:        [B, hidden_dim]
            candidate_bge: [N, 1024]
        Returns:
            scores [B, N]
        """
        cand_proj = self.candidate_proj(candidate_bge)  # [N, hidden_dim]
        return intent @ cand_proj.T                      # [B, N]


# ─────────────────────────────────────────────────────────────────────────────
# Agent (training + inference interface)
# ─────────────────────────────────────────────────────────────────────────────

class GRU4RecAgent:
    """
    High-level interface for GRU4Rec — recurrent sequential recommendation
    baseline using BGE-M3 content embeddings and sampled softmax training.

    Mirrors DIFSASRecAgent's interface (no category stream or auxiliary losses).
    """

    def __init__(self, retriever, pretrained_path: str = None):
        self.retriever    = retriever
        self.device       = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.model     = GRU4RecModel().to(self.device)
        self.optimizer = optim.AdamW(self.model.parameters(), lr=LR,
                                     weight_decay=WEIGHT_DECAY)

        self._amp_enabled = self.device.type == "cuda"
        self.scaler       = torch.cuda.amp.GradScaler(enabled=self._amp_enabled)
        self.scheduler    = None

        self._step        = 0
        self.loss_history = []
        self._emb_cache: dict = {}

        self._all_asins = list(retriever.asin_to_idx.keys()) if retriever else []

        if pretrained_path and os.path.exists(pretrained_path):
            self.load(pretrained_path)
        else:
            param_count = sum(p.numel() for p in self.model.parameters())
            print(f"[GRU4RecAgent] Initialized fresh model — "
                  f"{param_count:,} params  device={self.device}")

        self._pretrained_state        = copy.deepcopy(self.model.state_dict())
        self._pretrained_opt_state    = copy.deepcopy(self.optimizer.state_dict())
        self._pretrained_step         = self._step
        self._pretrained_loss_history = list(self.loss_history)

    # ── Per-user weight helpers ───────────────────────────────────────────────

    @staticmethod
    def _user_path(data_dir: str, user_id: str) -> str:
        profiles_dir = os.path.join(data_dir, "profiles")
        os.makedirs(profiles_dir, exist_ok=True)
        safe_id = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in user_id)
        return os.path.join(profiles_dir, f"{safe_id}_gru4rec.pt")

    def load_user(self, user_id: str, data_dir: str):
        """Load per-user weights, or reset to pretrained baseline for new users."""
        path = self._user_path(data_dir, user_id)
        if os.path.exists(path):
            self.load(path)
        else:
            self.model.load_state_dict(self._pretrained_state)
            self.optimizer.load_state_dict(self._pretrained_opt_state)
            self._step        = self._pretrained_step
            self.loss_history = list(self._pretrained_loss_history)
            self.model.eval()

    def save_user(self, user_id: str, data_dir: str):
        """Persist current weights as the user's personal checkpoint."""
        self.save(self._user_path(data_dir, user_id))

    # ── Tensor building ───────────────────────────────────────────────────────

    def _build_tensors(self, click_seq_asins: list):
        """
        Reconstruct BGE-M3 embeddings for a single click sequence.

        Returns:
            bge_t [1, MAX_SEQ_LEN, 1024], len_t [1]  or  (None, None) on empty
        """
        seq      = click_seq_asins[-MAX_SEQ_LEN:]
        bge_list = []

        for asin in seq:
            if asin not in self.retriever.asin_to_idx:
                continue
            idx = self.retriever.asin_to_idx[asin]
            vec = self.retriever.text_flat.reconstruct(idx)
            bge_list.append(vec)

        T = len(bge_list)
        if T == 0:
            return None, None

        bge_arr       = np.zeros((MAX_SEQ_LEN, TEXT_EMBED_DIM), dtype=np.float32)
        bge_arr[:T]   = np.array(bge_list)
        bge_t         = torch.FloatTensor(bge_arr).unsqueeze(0).to(self.device)
        len_t         = torch.tensor([T], device=self.device)
        return bge_t, len_t

    def set_embedding_cache(self, cache: dict):
        """
        Inject a pre-loaded {asin: np.ndarray[1024]} cache.
        When set, _get_asin_vec serves from RAM instead of FAISS mmap.
        """
        self._emb_cache = cache

    def configure_scheduler(self, total_steps: int, warmup_steps: int):
        """Attach a linear-warmup + cosine-decay LR scheduler."""
        import math
        from torch.optim.lr_scheduler import LambdaLR

        def _lr_lambda(step: int) -> float:
            if step < warmup_steps:
                return step / max(1, warmup_steps)
            progress = (step - warmup_steps) / max(1, total_steps - warmup_steps)
            return max(0.05, 0.5 * (1.0 + math.cos(math.pi * progress)))

        self.scheduler = LambdaLR(self.optimizer, _lr_lambda)
        print(f"[GRU4RecAgent] Scheduler: linear warmup {warmup_steps:,} steps "
              f"-> cosine decay to {total_steps:,} steps")

    def _get_asin_vec(self, asin: str):
        """Return BGE-M3 vector [1024] for an ASIN, or None."""
        if self._emb_cache and asin in self._emb_cache:
            return self._emb_cache[asin]
        if asin not in self.retriever.asin_to_idx:
            return None
        idx = self.retriever.asin_to_idx[asin]
        return self.retriever.text_flat.reconstruct(idx)

    # ── Inference ─────────────────────────────────────────────────────────────

    def get_intent_vector(self, click_seq_asins: list) -> np.ndarray | None:
        """Encode a click sequence into a 256-dim intent vector."""
        bge_t, len_t = self._build_tensors(click_seq_asins)
        if bge_t is None:
            return None
        self.model.eval()
        with torch.no_grad():
            _, intent = self.model(bge_t, len_t)
        return intent.squeeze(0).cpu().numpy()

    def get_candidate_scores(self, click_seq_asins: list,
                              candidate_asins: list) -> dict:
        """
        Score a list of candidate ASINs against the user's current intent.

        Args:
            click_seq_asins: user's click history
            candidate_asins: ASINs to score

        Returns:
            {asin: float_score}
        """
        if not click_seq_asins or not candidate_asins:
            return {asin: 0.0 for asin in candidate_asins}

        bge_t, len_t = self._build_tensors(click_seq_asins)
        if bge_t is None:
            return {asin: 0.0 for asin in candidate_asins}

        self.model.eval()
        with torch.no_grad():
            _, intent = self.model(bge_t, len_t)    # [1, 256]

        valid_asins, cand_vecs = [], []
        for asin in candidate_asins:
            vec = self._get_asin_vec(asin)
            if vec is not None:
                valid_asins.append(asin)
                cand_vecs.append(vec)

        if not valid_asins:
            return {}

        cand_t = torch.FloatTensor(np.array(cand_vecs)).to(self.device)
        with torch.no_grad():
            scores = self.model.score_candidates(intent, cand_t)    # [1, N]
        scores_np = scores.squeeze(0).cpu().numpy()
        return {asin: float(s) for asin, s in zip(valid_asins, scores_np)}

    # ── Training ──────────────────────────────────────────────────────────────

    def _build_batch_tensors(self, batch_seqs: list):
        """
        Build padded batch tensors from multiple sequences (all from emb_cache).

        Returns:
            bge_t [B, MAX_SEQ_LEN, 1024], len_t [B]
        """
        B       = len(batch_seqs)
        bge_arr = np.zeros((B, MAX_SEQ_LEN, TEXT_EMBED_DIM), dtype=np.float32)
        lengths = np.zeros(B, dtype=np.int64)

        for i, seq in enumerate(batch_seqs):
            truncated = seq[-MAX_SEQ_LEN:]
            vecs      = [v for a in truncated
                         if (v := self._get_asin_vec(a)) is not None]
            T = len(vecs)
            if T > 0:
                bge_arr[i, :T] = vecs
            lengths[i] = T

        bge_t = torch.FloatTensor(bge_arr).to(self.device)
        len_t = torch.tensor(lengths, device=self.device)
        return bge_t, len_t

    def train_step_batch(self, batch_seqs: list, target_asins: list,
                         neg_pool_vecs: np.ndarray) -> float | None:
        """
        Batched training step using shared-negative sampled softmax.

        Uses shared negatives across the batch (standard in large-scale rec systems):
          logits = [B, 1+K]  where col 0 is the positive score, cols 1..K are shared negatives.
          target = [0, 0, ..., 0]  (positive is always index 0 for every sample)

        Args:
            batch_seqs:    list of B ASIN sequences (input, before target)
            target_asins:  list of B target ASIN strings
            neg_pool_vecs: [M, 1024] numpy array of pre-loaded negative embeddings

        Returns:
            mean loss over the batch, or None if batch has no valid sequences
        """
        valid = [(seq, tgt) for seq, tgt in zip(batch_seqs, target_asins)
                 if self._get_asin_vec(tgt) is not None]
        if not valid:
            return None

        seqs, tgt_asins = zip(*valid)
        seqs = list(seqs)

        bge_t, len_t = self._build_batch_tensors(seqs)
        valid_mask   = (len_t > 0)
        if not valid_mask.any():
            return None

        bge_t     = bge_t[valid_mask]
        len_t     = len_t[valid_mask]
        tgt_asins = [a for a, m in zip(tgt_asins, valid_mask.cpu().tolist()) if m]
        B         = len(tgt_asins)

        pos_vecs = np.array([self._get_asin_vec(a) for a in tgt_asins], dtype=np.float32)
        pos_t    = torch.FloatTensor(pos_vecs).to(self.device)          # [B, 1024]

        K       = min(NUM_NEGATIVES, len(neg_pool_vecs))
        neg_idx = np.random.choice(len(neg_pool_vecs), K, replace=False)
        neg_t   = torch.FloatTensor(neg_pool_vecs[neg_idx]).to(self.device)

        self.model.train()
        with torch.autocast(device_type=self.device.type, enabled=self._amp_enabled):
            _, intent  = self.model(bge_t, len_t)                      # [B, 256]

            pos_proj   = self.model.candidate_proj(pos_t)               # [B, 256]
            neg_proj   = self.model.candidate_proj(neg_t)               # [K, 256]

            scores_pos = (intent * pos_proj).sum(dim=1, keepdim=True)   # [B, 1]
            scores_neg = intent @ neg_proj.T                             # [B, K]
            logits     = torch.cat([scores_pos, scores_neg], dim=1)     # [B, 1+K]
            targets    = torch.zeros(B, dtype=torch.long, device=self.device)
            loss       = F.cross_entropy(logits, targets)

        self.optimizer.zero_grad()
        self.scaler.scale(loss).backward()
        self.scaler.unscale_(self.optimizer)
        nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        scale_before = self.scaler.get_scale()
        self.scaler.step(self.optimizer)
        self.scaler.update()

        if self.scheduler is not None and self.scaler.get_scale() >= scale_before:
            self.scheduler.step()

        self._step += 1
        loss_val = float(loss.item())
        self.loss_history.append(loss_val)
        if len(self.loss_history) > 500:
            self.loss_history = self.loss_history[-500:]
        return loss_val

    def train_step(self, click_seq_asins: list, target_asin: str,
                   neg_pool_asins: list,
                   neg_pool_vecs: np.ndarray = None) -> float | None:
        """
        Single online training step using sampled softmax.

        Args:
            click_seq_asins: input sequence (items seen before target)
            target_asin:     next item the user clicked
            neg_pool_asins:  pool for negative sampling (online training)
            neg_pool_vecs:   [M, 1024] optional pre-loaded negatives (fast path)

        Returns:
            loss as float, or None if sequence has no valid ASINs
        """
        target_vec = self._get_asin_vec(target_asin)
        if target_vec is None:
            return None

        bge_t, len_t = self._build_tensors(click_seq_asins)
        if bge_t is None:
            return None

        if neg_pool_vecs is not None:
            n_neg    = min(NUM_NEGATIVES, len(neg_pool_vecs))
            neg_idx  = np.random.choice(len(neg_pool_vecs), size=n_neg, replace=False)
            neg_vecs = [neg_pool_vecs[i] for i in neg_idx]
        else:
            neg_pool  = [a for a in neg_pool_asins if a != target_asin]
            n_neg     = min(NUM_NEGATIVES, len(neg_pool))
            neg_asins = np.random.choice(neg_pool, size=n_neg, replace=False).tolist()
            neg_vecs  = [v for a in neg_asins
                         if (v := self._get_asin_vec(a)) is not None]
        if not neg_vecs:
            return None

        pos_t = torch.FloatTensor(target_vec).unsqueeze(0).to(self.device)
        neg_t = torch.FloatTensor(np.array(neg_vecs)).to(self.device)
        all_t = torch.cat([pos_t, neg_t], dim=0)                        # [1+K, 1024]

        self.model.train()
        _, intent = self.model(bge_t, len_t)                             # [1, 256]
        scores    = self.model.score_candidates(intent, all_t).squeeze(0)  # [1+K]
        target_idx = torch.zeros(1, dtype=torch.long, device=self.device)
        loss       = F.cross_entropy(scores.unsqueeze(0), target_idx)

        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        self.optimizer.step()

        self._step += 1
        loss_val = float(loss.item())
        self.loss_history.append(loss_val)
        if len(self.loss_history) > 200:
            self.loss_history = self.loss_history[-200:]
        return loss_val

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: str):
        """Save model state, optimizer state, and step counter."""
        torch.save({
            "arch":            "gru4rec_v1",
            "model_state":     self.model.state_dict(),
            "optimizer_state": self.optimizer.state_dict(),
            "step":            self._step,
            "loss_history":    self.loss_history,
        }, path)
        print(f"[GRU4RecAgent] Saved checkpoint to {path} (step={self._step})")

    def load(self, path: str):
        """Load checkpoint from disk. Skips if arch key mismatches."""
        if not os.path.exists(path):
            return
        ckpt = torch.load(path, map_location=self.device, weights_only=False)
        if ckpt.get("arch") != "gru4rec_v1":
            print(f"[GRU4RecAgent] Skipping {path} — arch mismatch "
                  f"(expected 'gru4rec_v1', got '{ckpt.get('arch')}')")
            return
        self.model.load_state_dict(ckpt["model_state"])
        self.optimizer.load_state_dict(ckpt["optimizer_state"])
        self._step        = ckpt.get("step", 0)
        self.loss_history = ckpt.get("loss_history", [])
        self.model.eval()
        print(f"[GRU4RecAgent] Loaded from {path} (step={self._step})")
