# python_gamedev

Small Python experiments: a networked Pong game and a couple of from-scratch ML learning scripts.

## Pong (LAN multiplayer)

<video src="pongrec.mp4" controls width="640"></video>

*(if the video doesn't render above, it's [pongrec.mp4](pongrec.mp4) in the repo root)*

Two-player Pong over a LAN socket connection, plus a single-player local version.

- [pong.py](pong.py) — single-player/local, both paddles on one keyboard (W/S and Up/Down).
- [pong_server.py](pong_server.py) — host. Controls the left paddle (W/S), listens on port `5555`, and simulates the game (ball physics, scoring, paddle spin).
- [pong_client.py](pong_client.py) — client. Connects to the host, controls the right paddle (Up/Down), and just renders the state it receives.
- [server_test.py](server_test.py) / [client_test.py](client_test.py) — minimal raw-socket send/receive scripts used to sanity-check the networking before wiring it into the game.

### Running it

Requires `pygame`:

```bash
pip install pygame
```

On the host machine:

```bash
python pong_server.py
```

It prints "Waiting for Player 2 to connect..." and blocks until a client connects.

On the client machine (edit `HOST` in [pong_client.py](pong_client.py) to the host's LAN IP if not running on the same machine):

```bash
python pong_client.py
```

Controls:
- Host (left paddle): `W` / `S`
- Client (right paddle): `Up` / `Down`

## ML learning scripts

Small, heavily-commented PyTorch scripts written to learn the fundamentals — not meant to be production code.

- [mnist.py](mnist.py) — a small CNN trained on MNIST digit classification (downloads the dataset, trains a few epochs, saves weights to `mnist_cnn.pt`).
- [minigpt.py](minigpt.py) — a tiny character-level GPT (self-attention, transformer blocks, autoregressive generation) trained on a short embedded text sample, no dataset download needed.

```bash
python mnist.py
python minigpt.py
```
