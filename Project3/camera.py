from OpenGL.GL import *
from glfw.GLFW import *
import glm
import ctypes
import numpy as np


class Camera:

    def __init__(self, viewport_size=(800,800), origin=glm.vec3(0, 0, 0), distance=500, xz_angle=np.radians(45), y_angle=np.radians(45),
                 up=glm.vec3(0, 1, 0), is_perspective=True):
        self.viewport_height = 1.
        self.viewport_width = self.viewport_height * viewport_size[0] / viewport_size[1]  # initial width/height
        # g_P = glm.ortho(-viewport_width * .5, viewport_width * .5, -viewport_width * .5, viewport_height * .5, -10, 10)
        self.origin = origin
        self.distance = distance
        self.xz_angle = xz_angle
        self.y_angle = y_angle
        self.up = up
        self.isPerspective = is_perspective

    def camera_position(self):
        if self.isPerspective:
            distance = self.distance
        else:
            distance = 0.1
        return self.origin + \
            glm.vec3(distance * np.sin(self.y_angle) * np.sin(self.xz_angle),
                     distance * np.cos(self.y_angle),
                     distance * np.sin(self.y_angle) * np.cos(self.xz_angle))

    def get_view_matrix(self):
        if self.isPerspective:
            return glm.perspective(45, self.viewport_width/self.viewport_height, 0.001, 20000) * glm.lookAt(self.camera_position(), self.origin, self.up)
        else:
            d = self.distance
            return glm.ortho(-d*self.viewport_width, d*self.viewport_width, -d*self.viewport_height, d*self.viewport_height, -d, d) * glm.lookAt(self.camera_position(), self.origin, self.up)

    def get_view_matrix_raw(self):
        return glm.lookAt(self.camera_position(), self.origin, self.up)

    def set_viewport_size(self, width, height):
        self.viewport_width = self.viewport_height * width / height
    def get_viewport_ratio(self):
        return self.viewport_width / self.viewport_height