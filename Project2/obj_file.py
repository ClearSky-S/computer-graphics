import sys, pygame
from pygame.locals import *
from pygame.constants import *
from OpenGL.GL import *
from OpenGL.GLU import *

# global vertices
# global normals
# global texcoords
# global faces

# vertices = []
# normals = []
# texcoords = []
# faces = []

def MTL(filename):
    contents = {}
    mtl = None
    for line in open(filename, "r"):
        if line.startswith('#'): continue
        values = line.split()
        if not values: continue
        if values[0] == 'newmtl':
            mtl = contents[values[1]] = {}
        elif mtl is None:
            raise ValueError
        elif values[0] == 'map_Kd':
            # load the texture referred to by this declaration
            # mtl[values[0]] = values[1]
            surf = pygame.image.load(mtl['map_Kd'])
            image = pygame.image.tostring(surf, 'RGBA', 1)
            ix, iy = surf.get_rect().size
            texid = mtl['texture_Kd'] = glGenTextures(1)

        else:
            mtl[values[0]] = map(float, values[1:])
    return contents

class OBJ:
    def __init__(self, filename, swapyz=False):
        """Loads a Wavefront OBJ file. """
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        material = None
        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'v':
                v = tuple(map(float, values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = tuple(map(float, values[1:4]))
                if swapyz:
                    v = v[0], v[2], v[1]
                self.normals.append(v)
            elif values[0] == 'vt':
                self.texcoords.append(tuple(map(float, values[1:3])))
            elif values[0] in ('usemtl', 'usemat'):
                material = values[1]
            elif values[0] == 'mtllib':
                pass
                # self.mtl = MTL(values[1])
            elif values[0] == 'f':
                face = []
                texcoords = []
                norms = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]))
                    if len(w) >= 2 and len(w[1]) > 0:
                        texcoords.append(int(w[1]))
                    else:
                        texcoords.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norms.append(int(w[2]))
                    else:
                        norms.append(0)
                self.faces.append((face, norms, texcoords, material))
        # for face in self.faces:
        #     vertices, normals, texture_coords, material = face
        #     # vertices, normals, texcoords
        #     # mtl = self.mtl[material]
        #     # if 'texture_Kd' in mtl:
        #     #     # use diffuse texmap
        #     #     glBindTexture(GL_TEXTURE_2D, mtl['texture_Kd'])
        #     # else:
        #     #     # just use diffuse colour
        #     #     glColor(*mtl['Kd'])
        #     glBegin(GL_POLYGON)
        #     for i in range(len(vertices)):
        #         if normals[i] > 0:
        #             glNormal3fv(normals[normals[i] - 1])
        #         # if texture_coords[i] > 0:
        #         #     glTexCoord2fv(self.texcoords[texture_coords[i] - 1])
        #         glVertex3fv(vertices[vertices[i] - 1])
        #     glEnd()





if __name__ == "__main__":
    obj = OBJ("Kazusa.obj", swapyz=True)
    print(obj.faces)