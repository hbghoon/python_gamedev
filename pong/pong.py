import pygame, random
from pygame.locals import *

"""
while True:
    events()
    loop()
    render()


__name__ -> on_execute
         -> on_init (where everything gets initialised and all objects are created)
         -> loop (after initialization, we enter the loop where the game runs)
                -> on_event() gets the events
                -> on_loop() makes iterations that
                -> on_render() renders
                -> goes on until we stop (quit) the game

"""

class App:
    def __init__ (self):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 640, 400

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode (self.size, HWSURFACE | pygame.DOUBLEBUF)
        self.paddle = pygame.Rect (25, 160, 6, 80)
        self.paddle2 = pygame.Rect (609, 160, 6, 80)
        self.reset_ball()
        self.score1 = 0
        self.score2 = 0
        self.font = pygame.font.Font(None, 50)
        self.clock = pygame.time.Clock()
        self._running = True
        return True

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

    def reset_ball (self):
        self.ball = pygame.Rect (315, 195, 10, 10)
        self.ball_vx = 4 * random.choice([-1, 1])
        self.ball_vy = 4 * random.choice([-1, 1])
        self.ball_pause = 60
        
    
    def on_loop(self):
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
            if (self.ball.colliderect(self.paddle) and self.ball_vx < 0) or (self.ball.colliderect(self.paddle2) and self.ball_vx > 0):
                self.ball_vx = -self.ball_vx
        
        #if self.score1 == 10 or self.score2 == 10:
            
            
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.paddle.y -= 5
        if keys[pygame.K_s]:
            self.paddle.y += 5
        if self.paddle.y < 0:
            self.paddle.y = 0
        if self.paddle.y > 320:
            self.paddle.y = 320
        if keys[pygame.K_UP]:
            self.paddle2.y -= 5
        if keys[pygame.K_DOWN]:
            self.paddle2.y += 5
        if self.paddle2.y < 0:
            self.paddle2.y = 0
        if self.paddle2.y > 320:
            self.paddle2.y = 320

    def on_render(self):
        self._display_surf.fill ((0, 0, 0))
        pygame.draw.rect (self._display_surf, (255, 0, 255), self.paddle)
        pygame.draw.rect (self._display_surf, (0, 255, 255), self.paddle2)
        pygame.draw.rect (self._display_surf, (255, 255, 255), self.ball)
        text1 = self.font.render(str(self.score1), True, (255, 255, 255))
        text2 = self.font.render(str(self.score2), True, (255, 255, 255))
        self._display_surf.blit (text1, (self.width // 4, 20))
        self._display_surf.blit (text2, (3*self.width // 4, 20))
        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()
    
    def on_execute(self):
        if self.on_init() == False:
            self._running = False

        while (self._running):
            for event in pygame.event.get():
                self.on_event (event)
            self.on_loop()
            self.on_render()
            self.clock.tick(60)
        self.on_cleanup()


if __name__ == "__main__":
    theApp = App()
    theApp.on_execute()

