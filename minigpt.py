"""
A minimal character-level GPT in PyTorch — a learning example.

This is the SAME architecture as real GPT, just tiny:
  - it reads text one character at a time,
  - learns to predict the next character,
  - and can then generate new text by sampling one char at a time.

The whole model is a stack of "transformer blocks". Each block does two things:
  1. Self-attention  -> lets each position look at earlier positions.
  2. A small MLP      -> processes what attention gathered.

Run:  python minigpt.py
(No downloads needed — it trains on the embedded text below.)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

torch.manual_seed(1337)

# ---------------------------------------------------------------------------
# Hyperparameters (deliberately tiny so it runs on a CPU).
# ---------------------------------------------------------------------------
block_size = 32     # context length: how many chars the model sees at once
batch_size = 16     # sequences per training step
n_embd     = 64     # size of each token's vector ("width" of the model)
n_head     = 4      # number of attention heads
n_layer    = 3      # number of transformer blocks ("depth")
dropout    = 0.1
lr         = 1e-3
max_iters  = 3000
device     = "cuda" if torch.cuda.is_available() else "cpu"

# ---------------------------------------------------------------------------
# Data: any plain text works. Swap this for open("input.txt").read() to train
# on something bigger (e.g. tiny-shakespeare). Here we embed a short sample.
# ---------------------------------------------------------------------------
text = (
    "To be, or not to be, that is the question:\n"
    "Whether 'tis nobler in the mind to suffer\n"
    "The slings and arrows of outrageous fortune,\n"
    "Or to take arms against a sea of troubles\n"
    "And by opposing end them. To die-to sleep,\n"
    "No more; and by a sleep to say we end\n"
    "The heart-ache and the thousand natural shocks\n"
    "That flesh is heir to: 'tis a consummation\n"
    "Devoutly to be wish'd. To die, to sleep;\n"
    "To sleep, perchance to dream-ay, there's the rub.\n"
) * 50  # repeat so there's enough to train on

# Build the vocabulary: every unique character gets an integer id.
chars = sorted(set(text))
vocab_size = len(chars)
stoi = {c: i for i, c in enumerate(chars)}   # char -> id
itos = {i: c for i, c in enumerate(chars)}   # id   -> char
encode = lambda s: [stoi[c] for c in s]
decode = lambda ids: "".join(itos[i] for i in ids)

data = torch.tensor(encode(text), dtype=torch.long)


def get_batch():
    """Grab a random batch of (input, target) sequences.
    The target is just the input shifted one char to the right —
    i.e. 'predict the next character'."""
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([data[i:i + block_size] for i in ix])
    y = torch.stack([data[i + 1:i + block_size + 1] for i in ix])
    return x.to(device), y.to(device)


# ---------------------------------------------------------------------------
# One attention head: the heart of the transformer.
# Each position emits a query, a key, and a value.
#   - query · key  -> "how much should I attend to that position?"
#   - the masked softmax of those scores weights the values.
# The mask stops a position from peeking at FUTURE characters (causal).
# ---------------------------------------------------------------------------
class Head(nn.Module):
    def __init__(self, head_size):
        super().__init__()
        self.key   = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        # lower-triangular matrix used to mask out the future
        self.register_buffer("tril", torch.tril(torch.ones(block_size, block_size)))
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        B, T, C = x.shape
        k = self.key(x)      # (B, T, head_size)
        q = self.query(x)
        # attention scores, scaled by 1/sqrt(head_size) for stability
        wei = q @ k.transpose(-2, -1) * k.shape[-1] ** -0.5   # (B, T, T)
        wei = wei.masked_fill(self.tril[:T, :T] == 0, float("-inf"))  # causal mask
        wei = F.softmax(wei, dim=-1)
        wei = self.dropout(wei)
        v = self.value(x)
        return wei @ v       # weighted sum of values -> (B, T, head_size)


class MultiHead(nn.Module):
    """Several attention heads run in parallel and get concatenated.
    Different heads can learn to attend to different things."""
    def __init__(self, n_head, head_size):
        super().__init__()
        self.heads = nn.ModuleList([Head(head_size) for _ in range(n_head)])
        self.proj = nn.Linear(n_embd, n_embd)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        out = torch.cat([h(x) for h in self.heads], dim=-1)
        return self.dropout(self.proj(out))


class FeedForward(nn.Module):
    """A small per-position MLP. This is where most 'thinking' happens."""
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_embd, 4 * n_embd),
            nn.ReLU(),
            nn.Linear(4 * n_embd, n_embd),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        return self.net(x)


class Block(nn.Module):
    """One transformer block: attention + feed-forward, each wrapped in a
    residual connection (x + ...) and LayerNorm. Stack N of these = GPT."""
    def __init__(self):
        super().__init__()
        head_size = n_embd // n_head
        self.sa = MultiHead(n_head, head_size)
        self.ff = FeedForward()
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)

    def forward(self, x):
        x = x + self.sa(self.ln1(x))   # "+" = residual connection
        x = x + self.ff(self.ln2(x))
        return x


# ---------------------------------------------------------------------------
# The full model.
# ---------------------------------------------------------------------------
class MiniGPT(nn.Module):
    def __init__(self):
        super().__init__()
        # token embedding: each char id -> a vector
        self.token_emb = nn.Embedding(vocab_size, n_embd)
        # position embedding: tells the model WHERE in the sequence a token is
        self.pos_emb = nn.Embedding(block_size, n_embd)
        self.blocks = nn.Sequential(*[Block() for _ in range(n_layer)])
        self.ln_f = nn.LayerNorm(n_embd)
        self.head = nn.Linear(n_embd, vocab_size)   # -> score per possible next char

    def forward(self, idx, targets=None):
        B, T = idx.shape
        tok = self.token_emb(idx)                                   # (B, T, n_embd)
        pos = self.pos_emb(torch.arange(T, device=device))          # (T, n_embd)
        x = tok + pos
        x = self.blocks(x)
        x = self.ln_f(x)
        logits = self.head(x)                                       # (B, T, vocab_size)

        loss = None
        if targets is not None:
            # reshape so cross-entropy compares every position's prediction
            loss = F.cross_entropy(logits.view(B * T, -1), targets.view(B * T))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens):
        """Generate text one character at a time."""
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -block_size:]          # only the last block_size chars fit
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :]                # focus on the last position
            probs = F.softmax(logits, dim=-1)
            next_id = torch.multinomial(probs, 1)    # sample (not just argmax) for variety
            idx = torch.cat([idx, next_id], dim=1)
        return idx


# ---------------------------------------------------------------------------
# Train (same loop shape as the MNIST script: forward -> loss -> backward -> step).
# ---------------------------------------------------------------------------
model = MiniGPT().to(device)
print(f"Model has {sum(p.numel() for p in model.parameters()) / 1e3:.0f}K parameters")
optimizer = torch.optim.AdamW(model.parameters(), lr=lr)

for it in range(max_iters):
    xb, yb = get_batch()
    _, loss = model(xb, yb)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    if it % 300 == 0:
        print(f"step {it:4d}  loss {loss.item():.4f}")

# ---------------------------------------------------------------------------
# Generate a sample starting from a single newline character.
# ---------------------------------------------------------------------------
print("\n----- generated text -----")
start = torch.zeros((1, 1), dtype=torch.long, device=device)
print(decode(model.generate(start, max_new_tokens=400)[0].tolist()))
