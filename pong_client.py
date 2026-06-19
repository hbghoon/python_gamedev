import pygame, socket, json
from pygame.locals import *

HOST = "127.0.0.1"
PORT = 5555

class App:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 640, 400
    
    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, HWSURFACE | pygame.DOUBLEBUF)
        self.paddle = pygame.Rect(25, 160, 6, 80)
        self.paddle2 = pygame.Rect(609, 160, 6, 80)
        self.ball = pygame.Rect(315, 195, 10, 10)
        self.font = pygame.font.Font(None, 50)
        self.clock = pygame.time.Clock()

        #network setup
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((HOST, PORT))

        self._running = True
        return True
    
    def on_event (self, event):
        if event.type == pygame.QUIT:
            self._running = False
    
    def on_loop (self):
        keys = pygame.key.get_pressed()
        intent = 0
        if keys[pygame.K_DOWN]:
            intent = 1
        if keys[pygame.K_UP]:
            intent = -1
        
        intent_send = f"{intent}\n"
        try:
            self.s.send(intent_send.encode())
        except OSError:
            self._running = False
            return
        
        #recieve:

        try:
            msg = self.s.recv (1024).decode()
            if msg == "":
                self._running = False
                return
            latest = msg.strip().split("\n")[-1]
            state = json.loads(latest)          # JSON text -> dict
            self.ball.x = state["ball_x"]
            self.ball.y = state["ball_y"]
            self.paddle.y = state["p1y"]
            self.paddle2.y = state["p2y"]
            self.s1 = state["s1"]
            self.s2 = state["s2"]
        except (ConnectionResetError, ValueError, OSError):
            self._running = False
        


    def on_render (self):
        self._display_surf.fill((0, 0, 0))
        pygame.draw.rect(self._display_surf, (255, 0, 255), self.paddle)
        pygame.draw.rect(self._display_surf, (0, 255, 255), self.paddle2)
        pygame.draw.rect(self._display_surf, (255, 255, 255), self.ball)
        text1 = self.font.render(str(self.s1), True, (255, 255, 255))
        text2 = self.font.render(str(self.s2), True, (255, 255, 255))
        self._display_surf.blit(text1, (self.width // 4, 20))
        self._display_surf.blit(text2, (3 * self.width // 4, 20))
        pygame.display.flip()

    def on_cleanup (self):
        if self.s:
            self.s.close()

        pygame.quit()

    def on_execute (self):
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
