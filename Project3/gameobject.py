import glm
import numpy as np
from OpenGL.GL import *
from glfw.GLFW import *
import glm
import ctypes
from camera import *
import os

class GameObject:
    def __init__(self, name="gameobject", parent=None):
        self.name = name
        self.transform = Transform(self)  # 애니메이션이 적용되지 않은 joint transform
        self.link_transform = Transform(self, True)  # 애니메이션을 위한 link transform
        self.chanel_index = ChanelIndex()
        self.is_visible = True  # 메쉬가 눈에 보이는 지
        self.mesh_transform_mat = glm.mat4()  # (0, 0, 0)에 위치한 단위 Cube를 이동시키기 위한 데이터
        self.end = None  # 자식이 없는 마지막 joint

        self.children = []  # 자식 게임 오브젝트
        self.parent = parent  # 부모 게임 오브젝트

        self.animation = None
        # self.mesh = None
        if parent is not None:
            parent.children.append(self)
            # self.animation = Animation()
            # 애니메이션은 필요할 경우에 외부에서 붙혀주는 걸로

    def get_world_transform_mat(self):
        if self.parent is None:
            return self.transform.get_local_transform_mat() * self.link_transform.get_local_transform_mat()
        else:
            return self.parent.get_world_transform_mat() * self.transform.get_local_transform_mat() * self.link_transform.get_local_transform_mat()

    def print_recursive(self, depth=0):
        print("  " * depth + self.name)
        # print("  " * depth + "  - pos: " + self.transform.position.__str__())
        # print("  " * depth + "  - childs: " + self.children.__str__())
        # print("  " * depth + "  - link rotation index: " + self.chanel_index.rotation.__str__())
        # if self.end is not None:
        #     print("  " * depth + "  - end: " + self.end.__str__())

        # print("  " * depth + " - childs: " + str(len(self.children)))
        for child in self.children:
            child.print_recursive(depth + 1)

    def draw_recusive_line(self, unif_locs_color, camera):
        # print(self.name)
        # M = self.get_world_transform_mat()*self.mesh_transform.get_local_transform_mat()
        # MVP = camera.get_view_matrix() * M
        # # print(MVP*glm.vec4(0,0,0,1))
        # glUniformMatrix4fv(unif_locs_color['MVP'], 1, GL_FALSE, glm.value_ptr(MVP))
        # # glUniformMatrix4fv(unif_locs_color['M'], 1, GL_FALSE, glm.value_ptr(M))
        # # glUniform3f(unif_locs_color['material_color'], 1., 1., 1.)
        # # glUniform3f(unif_locs_color['view_pos'], camera.camera_position().x, camera.camera_position().y,
        # #             camera.camera_position().z)
        # glDrawArrays(GL_LINES, 2, 2)
        if self.children == []:
            a = glm.vec3(0, 1, 0)
            b = glm.vec3(self.end)
            v = glm.cross(a, b)
            if v == glm.vec3(0, 0, 0):
                v = glm.vec3(1, 0, 0)
            angle = glm.acos(glm.dot(b, a) / (glm.length(a) * glm.length(b)))
            scale = glm.vec3(1, glm.length(b), 1)
            M = self.get_world_transform_mat() * glm.rotate(angle, v) * glm.scale(scale)
            MVP = camera.get_view_matrix() * M
            glUniformMatrix4fv(unif_locs_color['MVP'], 1, GL_FALSE, glm.value_ptr(MVP))
            glDrawArrays(GL_LINES, 2, 2)

        for child in self.children:
            a = glm.vec3(0, 1, 0)
            b = glm.vec3(child.transform.position)
            v = glm.cross(a, b)
            if v == glm.vec3(0, 0, 0):
                v = glm.vec3(1, 0, 0)
            angle = glm.acos(glm.dot(b, a) / (glm.length(a) * glm.length(b)))
            scale = glm.vec3(1, glm.length(b), 1)
            M = self.get_world_transform_mat() * glm.rotate(angle, v) * glm.scale(scale)
            MVP = camera.get_view_matrix() * M
            glUniformMatrix4fv(unif_locs_color['MVP'], 1, GL_FALSE, glm.value_ptr(MVP))
            glDrawArrays(GL_LINES, 2, 2)
            child.draw_recusive_line(unif_locs_color, camera)

    def draw_mesh_recursive(self, unif_locs, camera):
        if self.is_visible:
            M = self.get_world_transform_mat() * self.mesh_transform_mat
            MVP = camera.get_view_matrix() * M
            glUniformMatrix4fv(unif_locs['MVP'], 1, GL_FALSE, glm.value_ptr(MVP))
            glUniformMatrix4fv(unif_locs['M'], 1, GL_FALSE, glm.value_ptr(M))
            glUniform3f(unif_locs['material_color'], 1., 1., 1.)
            glUniform3f(unif_locs['view_pos'], camera.camera_position().x, camera.camera_position().y,
                        camera.camera_position().z)
            glDrawArrays(GL_TRIANGLES, 0, 36)

        for child in self.children:
            child.draw_mesh_recursive(unif_locs, camera)

    def reset_link_transform(self):
        self.link_transform = Transform(self, True)
        for child in self.children:
            child.reset_link_transform()

    def update_animation(self, animation=None):
        # print(self.name)
        if animation is None:
            animation = self.animation

        if animation is not None:
            for i in range(0,3):
                if self.chanel_index.position[i] != -1:
                    self.link_transform.position[i] = animation.current_anim_data[self.chanel_index.position[i]]
            for i in range(0,3):
                if self.chanel_index.rotation[i] != -1:
                    self.link_transform.rotation[i] = animation.current_anim_data[self.chanel_index.rotation[i]]


        for child in self.children:
            child.update_animation(animation)


    def __str__(self):
        return self.name + "\n"

    def __repr__(self):
        return self.name



class Transform:
    def __init__(self, gameobject, is_link=False):
        self.gameobject = gameobject
        self.position = [0, 0, 0]
        self.rotation = [0, 0, 0]
        self.scale = [1.0, 1.0, 1.0]
        self.is_link = is_link

    def get_local_transform_mat(self):
        if not self.is_link:
            return glm.translate(glm.mat4(1.0), self.position) * \
                glm.rotate(glm.mat4(1.0), np.radians(self.rotation[0]), glm.vec3(1.0, 0.0, 0.0)) * \
                glm.rotate(glm.mat4(1.0), np.radians(self.rotation[1]), glm.vec3(0.0, 1.0, 0.0)) * \
                glm.rotate(glm.mat4(1.0), np.radians(self.rotation[2]), glm.vec3(0.0, 0.0, 1.0)) * \
                glm.scale(glm.mat4(1.0), self.scale)
        else:
            # apply rotation with small index first
            x = glm.rotate(glm.mat4(1.0), np.radians(self.rotation[0]), glm.vec3(1.0, 0.0, 0.0))
            y = glm.rotate(glm.mat4(1.0), np.radians(self.rotation[1]), glm.vec3(0.0, 1.0, 0.0))
            z = glm.rotate(glm.mat4(1.0), np.radians(self.rotation[2]), glm.vec3(0.0, 0.0, 1.0))
            l = [(self.gameobject.chanel_index.rotation[0], x), (self.gameobject.chanel_index.rotation[1], y),
                 (self.gameobject.chanel_index.rotation[2], z)]
            l.sort(key=lambda e: e[0])
            return glm.translate(glm.mat4(1.0), self.position) * \
                l[0][1] * l[1][1] * l[2][1] * \
                glm.scale(glm.mat4(1.0), self.scale)


class ChanelIndex:
    def __init__(self):
        self.position = [-1, -1, -1]
        self.rotation = [-1, -1, -1]


class Animation:
    def __init__(self, filepath):
        self.frames = 0
        self.current_frame = 0
        self.frame_time = 0.1
        self.animation_data = []
        self.time = 0.0

        joint_cnt = 0

        f = open(filepath, 'r')
        file = f.read().split('\n')
        f.close()
        index = 0
        while file[index] != "MOTION":
            if file[index].strip().split()[0] == "JOINT":
                joint_cnt += 1
            index += 1
        index += 1
        # print(file[index])

        if file[index].split(':')[0] != "Frames":  # Frames: 1
            print("Error: Frames is not defined")
            exit()
        self.frames = int(file[index].split(':')[1])
        index += 1

        # print(file[index])
        if file[index].split(':')[0] != "Frame Time":
            print("Error: Frame Time is not defined")
            exit()
        self.frame_time = float(file[index].split(':')[1])
        index += 1

        for line in file[index:-1]:
            self.animation_data.append(list(map(float, line.strip().split())))

        # 파일정보 출력
        print("1. File name: " + os.path.split(filepath)[1])
        print("2. Number of frames: " + str(self.frames))
        print("3. Frame time: " + str(1/self.frame_time))
        print("4. Number of joint: " + str(joint_cnt))



    def __str__(self):
        return "Frames: " + str(self.frames) + "\nFrame Time: " + str(self.frame_time) + "\nAnimation Data: " + str(
            self.animation_data)

    @property
    def current_anim_data(self):
        return self.animation_data[self.current_frame]

    def set_time(self, time):
        self.time = time
        self.current_frame = int(self.time / self.frame_time) % self.frames
    def add_time(self, delta_time):
        self.time += delta_time
        self.current_frame = int(self.time / self.frame_time) % self.frames
        # print(self.current_frame)
        # print(self.current_anim_data[0])


def read_bvh(filepath):
    f = open(filepath, 'r')
    file = f.read().split('\n')
    f.close()
    index = 1
    channel_index = 0

    words = file[index].strip().split(' ')
    stack = []
    root = GameObject(words[1].strip())
    stack.append(root)

    # set root offset
    index += 2
    words = file[index].strip().split(' ')
    root.transform.position = [float(words[1]), float(words[2]), float(words[3])]

    # set channel index
    index += 1
    words = file[index].strip().split(' ')
    for i in range(2, 2 + int(words[1])):
        if words[i].upper() == "Xposition".upper():
            root.chanel_index.position[0] = channel_index
            channel_index += 1
        elif words[i].upper() == "Yposition".upper():
            root.chanel_index.position[1] = channel_index
            channel_index += 1
        elif words[i].upper() == "Zposition".upper():
            root.chanel_index.position[2] = channel_index
            channel_index += 1
        elif words[i].upper() == "Xrotation".upper():
            root.chanel_index.rotation[0] = channel_index
            channel_index += 1
        elif words[i].upper() == "Yrotation".upper():
            root.chanel_index.rotation[1] = channel_index
            channel_index += 1
        elif words[i].upper() == "Zrotation".upper():
            root.chanel_index.rotation[2] = channel_index
            channel_index += 1
    while True:
        index += 1
        # print(file[index])
        words = file[index].strip().split(' ')
        if words[0] == "JOINT":
            game_object = GameObject(words[1].strip(), stack[-1])
            stack.append(game_object)
            # set offset
            index += 2
            words = file[index].strip().split(' ')
            game_object.transform.position = [float(words[1]), float(words[2]), float(words[3])]
            # set channel index
            index += 1
            words = file[index].strip().split(' ')
            for i in range(2, 2 + int(words[1])):
                words[i] = words[i].upper()
                if words[i] == "Xposition".upper():
                    game_object.chanel_index.position[0] = channel_index
                    channel_index += 1
                elif words[i] == "Yposition".upper():
                    game_object.chanel_index.position[1] = channel_index
                    channel_index += 1
                elif words[i] == "Zposition".upper():
                    game_object.chanel_index.position[2] = channel_index
                    channel_index += 1
                elif words[i] == "Xrotation".upper():
                    game_object.chanel_index.rotation[0] = channel_index
                    channel_index += 1
                elif words[i] == "Yrotation".upper():
                    game_object.chanel_index.rotation[1] = channel_index
                    channel_index += 1
                elif words[i] == "Zrotation".upper():
                    game_object.chanel_index.rotation[2] = channel_index
                    channel_index += 1
        elif words[0] == "End":
            index += 2
            words = file[index].strip().split(' ')
            stack[-1].end = [float(words[1]), float(words[2]), float(words[3])]
            index += 1
        elif words[0] == "}":
            # index += 1
            stack.pop()
            # print(stack)
            # print(stack.pop())

            if not stack:
                # print("end")
                break
        elif words[0] == "MOTION":
            break
    root.animation = Animation(filepath)
    # print(root.children[0].transform.position[1]/20)
    set_mesh_recursive(root, root.children[0].transform.position[1]/20)
    print("5. List all joint names")
    root.print_recursive()

    return root

def set_mesh_recursive(gameobject : GameObject, object_scale = 1):
    # print(object_scale)
    if gameobject.children == []:
        a = glm.vec3(0, 1, 0)
        b = glm.vec3(gameobject.end)
        v = glm.cross(a, b)
        if v == glm.vec3(0, 0, 0):
            v = glm.vec3(1, 0, 0)
        angle = glm.acos(glm.dot(b, a) / (glm.length(a) * glm.length(b)))
        scale = glm.vec3(object_scale, glm.length(b)*0.5, object_scale)
        gameobject.mesh_transform_mat = glm.rotate(angle, v) * glm.translate(glm.vec3(0, glm.length(b)*0.5, 0)) * glm.scale(scale)


    for child in gameobject.children:
        if child != gameobject.children[0]:
            set_mesh_recursive(child, object_scale)
            continue
        a = glm.vec3(0, 1, 0)
        b = glm.vec3(child.transform.position)
        v = glm.cross(a, b)
        if v == glm.vec3(0, 0, 0):
            v = glm.vec3(1, 0, 0)
        angle = glm.acos(glm.dot(b, a) / (glm.length(a) * glm.length(b)))
        scale = glm.vec3(object_scale, glm.length(b)*0.5, object_scale)
        gameobject.mesh_transform_mat = glm.rotate(angle, v) * glm.translate(glm.vec3(0, glm.length(b)*0.5, 0)) * glm.scale(scale)
        set_mesh_recursive(child, object_scale)

if __name__ == "__main__":
    root = read_bvh("walk_rough.bvh")
    root.print_recursive()
