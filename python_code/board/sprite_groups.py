import pygame

from utility.constants import SCREEN_SIZE
from utility.utilities import Serializer, Size
import entities


# thanks to https://stackoverflow.com/questions/14354171/add-scrolling-to-a-platformer-in-pygame
class CameraAwareLayeredUpdates(pygame.sprite.LayeredUpdates, Serializer):
    def __init__(self, target, world_size, cam=None):
        pygame.sprite.LayeredUpdates.__init__(self)
        self.target = target
        self.cam = pygame.Vector2(*cam) if cam else pygame.Vector2(0, 0)
        self.world_size = world_size
        if self.target:
            self.add(target)

    def update(self, *args):
        super().update(*args)
        if self.target:
            x = -self.target.rect.center[0] + SCREEN_SIZE.width / 2
            y = -self.target.rect.center[1] + SCREEN_SIZE.height / 2
            self.cam += (pygame.Vector2((x, y)) - self.cam)
            self.cam.x = max(-(self.world_size.width-SCREEN_SIZE.width), min(0.0, self.cam.x))
            self.cam.y = max(-(self.world_size.height-SCREEN_SIZE.height), min(0.0, self.cam.y))

    def to_dict(self):
        return {
            "cam": (self.cam.x, self.cam.y),
            "world_size": self.world_size.to_dict(),
            "entities": [sprite.to_dict() for sprite in self.sprites() if sprite is not self.target]
        }

    @classmethod
    def from_dict(cls, target=None, **arguments):
        arguments["world_size"] = Size.from_dict(**arguments["world_size"]),
        ents = arguments.pop("entities")
        new_instance = super().from_dict(target=target, **arguments)
        new_instance.add(getattr(entities, dct["type"]).from_dict(sprite_group=[],
                                                                  **dct) for dct in ents)
        return new_instance

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
                newrect = surface_blit(spr.image, spr.rect.move(self.cam))
            else:
                newrect = surface_blit(spr.image, spr.rect)
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
            newrect = surface_blit(spr.image, spr.rect)
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
