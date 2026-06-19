import pygame, random, socket, json, threading
from pygame.locals import *

# ---- network settings ----
HOST = "0.0.0.0"   # "0.0.0.0" = accept connections on ALL network interfaces,
                # so other machines on the LAN can reach us (not just this PC).
PORT = 5555


class App:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 640, 400
        self.conn = None      # the socket dedicated to our one client (set in on_init)
        self.server_sock = None

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, HWSURFACE | pygame.DOUBLEBUF)
        self.paddle = pygame.Rect(25, 160, 6, 80)     # Player 1 (host, left)
        self.paddle2 = pygame.Rect(609, 160, 6, 80)   # Player 2 (client, right)
        self.reset_ball()
        self.score1 = 0
        self.score2 = 0
        self.client_intent = 0
        self.font = pygame.font.Font(None, 50)
        self.clock = pygame.time.Clock()

        # ---- set up networking: wait for Player 2 to connect ----
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((HOST, PORT))
        self.server_sock.listen()
        print("Waiting for Player 2 to connect...")
        self.conn, addr = self.server_sock.accept()   # BLOCKS here until the client dials in
        print("Player 2 connected from", addr)

        self.net_thread = threading.Thread(target=self.network_loop, daemon=True)
        self.net_thread.start()

        self._running = True
        return True

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

    def reset_ball(self):
        self.ball = pygame.Rect(315, 195, 10, 10)
        self.ball_vx = 4 * random.choice([-1, 1])
        self.ball_vy = 4 * random.choice([-1, 1])
        self.ball_pause = 60
    
    def network_loop (self):
        while self._running:
            try:
                msg = self.conn.recv (1024).decode()
                if msg == "":
                    self._running = False
                    return
                self.client_intent = int(msg.strip().split("\n")[-1])
                state = {
                    "ball_x": self.ball.x,
                    "ball_y": self.ball.y,
                    "p1y": self.paddle.y,
                    "p2y": self.paddle2.y,
                    "s1": self.score1,
                    "s2": self.score2
                }
                self.conn.send((json.dumps(state) + "\n").encode())
            except (ConnectionResetError, ValueError, OSError):
                self._running = False
                return

    def on_loop(self):
        # --- 1. host's own input (Player 1, W/S) ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.paddle.y -= 5
        if keys[pygame.K_s]:
            self.paddle.y += 5
        if self.paddle.y < 0:
            self.paddle.y = 0
        if self.paddle.y > 320:
            self.paddle.y = 320

        #2. apply intent recieved from thread 
        self.paddle2.y += self.client_intent * 5
        if self.paddle2.y < 0:
            self.paddle2.y = 0
        if self.paddle2.y > 320:
            self.paddle2.y = 320

        # --- 3. run the physics (unchanged from single-player) ---
        if self.ball_pause > 0:
            self.ball_pause -= 1
        else:
            self.ball.x += self.ball_vx
            self.ball.y += self.ball_vy
            if self.ball.top <= 0 or self.ball.bottom >= self.height:
                self.ball_vy = -self.ball_vy
            if self.ball.left < 0:
                self.score2 += 1
                self.reset_ball()
            if self.ball.right > self.width:
                self.score1 += 1
                self.reset_ball()
            if (self.ball.colliderect(self.paddle) and self.ball_vx < 0) or \
            (self.ball.colliderect(self.paddle2) and self.ball_vx > 0):
                self.ball_vx = -self.ball_vx

    def on_render(self):
        self._display_surf.fill((0, 0, 0))
        pygame.draw.rect(self._display_surf, (255, 0, 255), self.paddle)
        pygame.draw.rect(self._display_surf, (0, 255, 255), self.paddle2)
        pygame.draw.rect(self._display_surf, (255, 255, 255), self.ball)
        text1 = self.font.render(str(self.score1), True, (255, 255, 255))
        text2 = self.font.render(str(self.score2), True, (255, 255, 255))
        self._display_surf.blit(text1, (self.width // 4, 20))
        self._display_surf.blit(text2, (3 * self.width // 4, 20))
        pygame.display.flip()

    def on_cleanup(self):
        if self.conn:
            self.conn.close()
        if self.server_sock:
            self.server_sock.close()
        pygame.quit()

    def on_execute(self):
        if self.on_init() == False:
            self._running = False

        while (self._running):
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
            self.clock.tick(60)
        self.on_cleanup()


if __name__ == "__main__":
    theApp = App()
    theApp.on_execute()
