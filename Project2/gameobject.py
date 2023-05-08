import glm
import numpy as np

class GameObject:
    def __init__(self, name="gameobject", parent=None, obj_loc=None):
        self.name = name
        self.transform = Transform()
        self.children = []
        self.parent = parent
        if parent is not None:
            parent.children.append(self)
        if obj_loc == None:
            self.mesh = None
        else:
            self.mesh = Mesh(obj_loc)

    def get_world_transform_mat(self):
        if self.parent is None:
            return self.transform.get_local_transform_mat()
        else:
            return self.parent.get_world_transform_mat() * self.transform.get_local_transform_mat()

class Transform:
    def __init__(self):
        self.position = [0, 0, 0]
        self.rotation = [0, 0, 0]
        self.scale = [1.0, 1.0, 1.0]
    def get_local_transform_mat(self):
        return glm.translate(glm.mat4(1.0), self.position) * \
               glm.rotate(glm.mat4(1.0), np.radians(self.rotation[0]), glm.vec3(1.0, 0.0, 0.0)) * \
               glm.rotate(glm.mat4(1.0), np.radians(self.rotation[1]), glm.vec3(0.0, 1.0, 0.0)) * \
               glm.rotate(glm.mat4(1.0), np.radians(self.rotation[2]), glm.vec3(0.0, 0.0, 1.0)) * \
               glm.scale(glm.mat4(1.0), self.scale)

class Mesh:
    def __init__(self, filepath):
        """Loads a Wavefront OBJ file. """
        self.filepath = filepath
        self.filename = filepath.split('\\')[-1]
        # print(filename)
        self.pivot = [0, 0, 0]
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.vao = None
        self.gl_vertex=[] # postion and normal
        material = None
        for line in open(filepath, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue
            if values[0] == 'v':
                v = tuple(map(float, values[1:4]))
                self.vertices.append(v)
            elif values[0] == 'vn':
                v = tuple(map(float, values[1:4]))
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
            else:
                pass
        for element in self.faces:
            for i in range(3):
                self.gl_vertex.append(self.vertices[element[0][i]-1][0])
                self.gl_vertex.append(self.vertices[element[0][i]-1][1])
                self.gl_vertex.append(self.vertices[element[0][i]-1][2])
                if len(self.normals) == 0:
                    self.gl_vertex.append(1)
                    self.gl_vertex.append(1)
                    self.gl_vertex.append(1)
                else:
                    self.gl_vertex.append(self.normals[element[1][i]-1][0])
                    self.gl_vertex.append(self.normals[element[1][i]-1][1])
                    self.gl_vertex.append(self.normals[element[1][i]-1][2])
    def __str__(self):
        face_3vertex = 0
        face_4vertex = 0
        face_5upvertex = 0
        for element in self.faces:
            if len(element[0]) == 3:
                face_3vertex += 1
            elif len(element[0]) == 4:
                face_4vertex += 1
            else:
                face_5upvertex += 1

        info = self.filename + '\n'
        info += "faces: " + str(len(self.faces)) + '\n'
        info += "faces with 3 vertices: " + str(face_3vertex) + '\n'
        info += "faces with 4 vertices: " + str(face_4vertex) + '\n'
        info += "faces with 5+ vertices: " + str(face_5upvertex) + '\n'
        return info

