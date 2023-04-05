from OpenGL.GL import *
from glfw.GLFW import *
import glm
import ctypes
import numpy as np

PROJECTION_MATRIX = glm.ortho(-1, 1, -1, 1, -1, 1)


class Camera:

    def __init__(self, origin=glm.vec3(0, 0, 0), distance=1, xz_angle=np.radians(45), y_angle=np.radians(45),
                 up=glm.vec3(0, 1, 0), is_perspective=True):
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
            return glm.perspective(45, 1, 0.1, 10) * glm.lookAt(self.camera_position(), self.origin, self.up)
        else:
            return PROJECTION_MATRIX * glm.lookAt(self.camera_position(), self.origin, self.up)

    def get_view_matrix_raw(self):
        return glm.lookAt(self.camera_position(), self.origin, self.up)
