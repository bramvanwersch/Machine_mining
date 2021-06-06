import pygame

import utility.constants as con


# thanks to https://stackoverflow.com/questions/14354171/add-scrolling-to-a-platformer-in-pygame
class CameraAwareLayeredUpdates(pygame.sprite.LayeredUpdates):
    def __init__(self, target, world_size, cam=None):
        pygame.sprite.LayeredUpdates.__init__(self)
        self.target = target
        self.cam = pygame.Vector2(*cam) if cam else pygame.Vector2(0, 0)
        self.world_size = world_size
        if self.target:
            self.add(target)

    def update(self, *args, paused=False):
        for sprite in self.sprites():
            if paused and sprite.pausable:
                continue
            sprite.update(*args)
        if self.target:
            x = -self.target.rect.center[0] + con.SCREEN_SIZE.width / 2
            y = -self.target.rect.center[1] + con.SCREEN_SIZE.height / 2
            self.cam += (pygame.Vector2((x, y)) - self.cam)
            self.cam.x = max(-(self.world_size.width - con.SCREEN_SIZE.width), min(0.0, self.cam.x))
            self.cam.y = max(-(self.world_size.height - con.SCREEN_SIZE.height), min(0.0, self.cam.y))

    def draw(self, surface):
        spritedict = self.spritedict
        surface_blit = surface.blit
        dirty = self.lostsprites
        self.lostsprites = []
        dirty_append = dirty.append
        init_rect = self._init_rect
        for spr in self.sprites():
            if not spr.is_showing():
                continue
            rec = spritedict[spr]
            if spr.static:
                newrect = surface_blit(spr.surface, spr.rect.move(self.cam))
            else:
                newrect = surface_blit(spr.surface, spr.rect)
            if rec is init_rect:
                dirty_append(newrect)
            else:
                if newrect.colliderect(rec):
                    dirty_append(newrect.union(rec))
                else:
                    dirty_append(newrect)
                    dirty_append(rec)
            spritedict[spr] = newrect
        return dirty


class ShowToggleLayerUpdates(pygame.sprite.LayeredUpdates):

    def draw(self, surface):
        spritedict = self.spritedict
        surface_blit = surface.blit
        dirty = self.lostsprites
        self.lostsprites = []
        dirty_append = dirty.append
        init_rect = self._init_rect
        for spr in self.sprites():
            if not spr.is_showing():
                continue
            rec = spritedict[spr]
            newrect = surface_blit(spr.surface, spr.rect)
            if rec is init_rect:
                dirty_append(newrect)
            else:
                if newrect.colliderect(rec):
                    dirty_append(newrect.union(rec))
                else:
                    dirty_append(newrect)
                    dirty_append(rec)
            spritedict[spr] = newrect
        return dirty
