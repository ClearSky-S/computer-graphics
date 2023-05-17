import glm
import numpy as np


class GameObject:
    def __init__(self, name="gameobject", parent=None):
        self.name = name
        self.transform = Transform()  # 애니메이션이 적용되지 않은 joint transform
        self.link_transform = Transform()  # 애니메이션을 위한 link transform
        self.chanel_index = ChanelIndex()
        self.is_visible = True  # 메쉬가 눈에 보이는 지
        self.mesh_transform = Transform()  # (0, 0, 0)에 위치한 단위 Cube를 이동시키기 위한 데이터
        self.end = None  # 자식이 없는 마지막 joint

        self.children = []  # 자식 게임 오브젝트
        self.parent = parent  # 부모 게임 오브젝트

        self.animation = None
        self.mesh = None
        if parent is not None:
            parent.children.append(self)
            # self.animation = Animation()
            # 애니메이션은 필요할 경우에 외부에서 붙혀주는 걸로

    def get_world_transform_mat(self):
        if self.parent is None:
            return self.transform.get_local_transform_mat() * self.link_transform.get_local_transform_mat()
        else:
            return self.parent.get_world_transform_mat() * self.transform.get_local_transform_mat()

    def print_recursive(self, depth=0):
        print("  " * depth + self.name)
        print("  " * depth + "  - pos: " + self.transform.position.__str__())
        print("  " * depth + "  - childs: " + self.children.__str__())
        if self.end is not None:
            print("  " * depth + "  - end: " + self.end.__str__())

        # print("  " * depth + " - childs: " + str(len(self.children)))
        for child in self.children:
            child.print_recursive(depth + 1)
    def __str__(self):
        return self.name + "\n"

    def __repr__(self):
        return self.name

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

class ChanelIndex:
    def __init__(self):
        self.position = [-1,-1,-1]
        self.rotation = [-1,-1,-1]

class Animation:
    def __init__(self, filepath):
        self.frames = 0
        self.current_frame = 0
        self.frame_time = 0.1
        self.animation_data = []


        f = open(filepath, 'r')
        file = f.read().split('\n')
        f.close()
        index = 0
        while file[index] != "MOTION":
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

        for line in file[index:]:
            self.animation_data.append(line.split(' '))

    def __str__(self):
        return "Frames: " + str(self.frames) + "\nFrame Time: " + str(self.frame_time) + "\nAnimation Data: " + str(self.animation_data)

    @property
    def current_anim_data(self):
        return self.animation_data[self.current_frame]

    def set_time(self, time):
        self.current_frame = int(time / self.frame_time)
        if self.current_frame >= self.frames:
            self.current_frame = self.current_frame % self.frames

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
    for i in range(2, 2+int(words[1])):
        if words[i] == "Xposition":
            root.chanel_index.position[0] = channel_index
            channel_index += 1
        elif words[i] == "Yposition":
            root.chanel_index.position[1] = channel_index
            channel_index += 1
        elif words[i] == "Zposition":
            root.chanel_index.position[2] = channel_index
            channel_index += 1
        elif words[i] == "Xrotation":
            root.chanel_index.rotation[0] = channel_index
            channel_index += 1
        elif words[i] == "Yrotation":
            root.chanel_index.rotation[1] = channel_index
            channel_index += 1
        elif words[i] == "Zrotation":
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
                if words[i] == "Xposition":
                    game_object.chanel_index.position[0] = channel_index
                    channel_index += 1
                elif words[i] == "Yposition":
                    game_object.chanel_index.position[1] = channel_index
                    channel_index += 1
                elif words[i] == "Zposition":
                    game_object.chanel_index.position[2] = channel_index
                    channel_index += 1
                elif words[i] == "Xrotation":
                    game_object.chanel_index.rotation[0] = channel_index
                    channel_index += 1
                elif words[i] == "Yrotation":
                    game_object.chanel_index.rotation[1] = channel_index
                    channel_index += 1
                elif words[i] == "Zrotation":
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

    return root






if __name__ =="__main__":
    root = read_bvh("walk_rough.bvh")
    root.print_recursive()


