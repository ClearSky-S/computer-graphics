from OpenGL.GL import *
from glfw.GLFW import *
import glm
import ctypes
import numpy as np
from camera import Camera
screen_pos_prev = (0,0)
screen_pos = (0,0)
camera = Camera()
is_panning = False
is_orbiting = False
g_triangle_translation = glm.vec3()
g_cam_ang = 0.
g_cam_height = .1
g_vertex_shader_src = '''

#version 330 core

layout (location = 0) in vec3 vin_pos; 
layout (location = 1) in vec3 vin_color; 

out vec4 vout_color;

uniform mat4 MVP;

void main()
{
    // 3D points in homogeneous coordinates
    vec4 p3D_in_hcoord = vec4(vin_pos.xyz, 1.0);

    gl_Position = MVP * p3D_in_hcoord;

    vout_color = vec4(vin_color, 1.);
}
'''

g_fragment_shader_src = '''
#version 330 core

in vec4 vout_color;

out vec4 FragColor;

void main()
{
    FragColor = vout_color;
}
'''


def load_shaders(vertex_shader_source, fragment_shader_source):
    # build and compile our shader program
    # ------------------------------------

    # vertex shader
    vertex_shader = glCreateShader(GL_VERTEX_SHADER)  # create an empty shader object
    glShaderSource(vertex_shader, vertex_shader_source)  # provide shader source code
    glCompileShader(vertex_shader)  # compile the shader object

    # check for shader compile errors
    success = glGetShaderiv(vertex_shader, GL_COMPILE_STATUS)
    if (not success):
        infoLog = glGetShaderInfoLog(vertex_shader)
        print("ERROR::SHADER::VERTEX::COMPILATION_FAILED\n" + infoLog.decode())

    # fragment shader
    fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)  # create an empty shader object
    glShaderSource(fragment_shader, fragment_shader_source)  # provide shader source code
    glCompileShader(fragment_shader)  # compile the shader object

    # check for shader compile errors
    success = glGetShaderiv(fragment_shader, GL_COMPILE_STATUS)
    if (not success):
        infoLog = glGetShaderInfoLog(fragment_shader)
        print("ERROR::SHADER::FRAGMENT::COMPILATION_FAILED\n" + infoLog.decode())

    # link shaders
    shader_program = glCreateProgram()  # create an empty program object
    glAttachShader(shader_program, vertex_shader)  # attach the shader objects to the program object
    glAttachShader(shader_program, fragment_shader)
    glLinkProgram(shader_program)  # link the program object

    # check for linking errors
    success = glGetProgramiv(shader_program, GL_LINK_STATUS)
    if (not success):
        infoLog = glGetProgramInfoLog(shader_program)
        print("ERROR::SHADER::PROGRAM::LINKING_FAILED\n" + infoLog.decode())

    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)

    return shader_program  # return the shader program


def key_callback(window, key, scancode, action, mods):
    global g_cam_ang, g_cam_height
    if key == GLFW_KEY_ESCAPE and action == GLFW_PRESS:
        glfwSetWindowShouldClose(window, GLFW_TRUE);
    else:
        if action == GLFW_PRESS:
            if key == GLFW_KEY_V:
                camera.isPerspective = not camera.isPerspective

        # if action == GLFW_PRESS or action == GLFW_REPEAT:
            # if key == GLFW_KEY_1:
            #     g_cam_ang += np.radians(-10)
            #     camera.xz_angle += np.radians(10)
            # elif key == GLFW_KEY_3:
            #     g_cam_ang += np.radians(10)
            #     camera.xz_angle -= np.radians(10)
            # elif key == GLFW_KEY_2:
            #     # height limit
            #     camera.y_angle += np.radians(10)
            #     if (g_cam_height < 0.5):
            #         g_cam_height += .05
            # elif key == GLFW_KEY_W:
            #     # height limit
            #     camera.y_angle -= np.radians(10)
            #     if (g_cam_height > - 0.5):
            #         g_cam_height += -.05
            # elif key == GLFW_KEY_Q:
            #     g_triangle_translation.x += .01
            # elif key == GLFW_KEY_A:
            #     g_triangle_translation.x -= .01
            # elif key == GLFW_KEY_E:
            #     g_triangle_translation.y += .01
            # elif key == GLFW_KEY_D:
            #     g_triangle_translation.y -= .01
            # elif key == GLFW_KEY_Z:
            #     g_triangle_translation.z += .01
            # elif key == GLFW_KEY_X:
            #     g_triangle_translation.z -= .01

def scroll_callback(window, xoffset, yoffset):
    if yoffset < 0:
        camera.distance += 0.05
    elif yoffset > 0:
        if camera.distance>0.06:
            camera.distance -= 0.05
    # offset = glm.vec4(0, 0, yoffset*0.01, 0)
    # if (glm.determinant(camera.get_view_matrix_raw()) != 0):
    #     offset = glm.inverse(camera.get_view_matrix_raw()) * offset
    # else:
    #     offset = glm.vec3(0, 0, 0)
    # offset = glm.vec3(offset)
    # camera.origin = glm.vec3(glm.translate(offset) * glm.vec4(camera.origin, 1))
def mouse_button_callback(window, button, action, mods):
    global is_panning, is_orbiting
    if (button == GLFW_MOUSE_BUTTON_RIGHT) & (action == GLFW_PRESS):
        if (glfwRawMouseMotionSupported()):
            is_panning= True
            glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            glfwSetInputMode(window, GLFW_RAW_MOUSE_MOTION, GLFW_TRUE)

    if (button == GLFW_MOUSE_BUTTON_RIGHT) & (action == GLFW_RELEASE):
        is_panning= False
        glfwSetInputMode(window, GLFW_CURSOR,  GLFW_CURSOR_NORMAL)
        glfwSetInputMode(window, GLFW_RAW_MOUSE_MOTION, GLFW_FALSE)

    if (button == GLFW_MOUSE_BUTTON_LEFT) & (action == GLFW_PRESS):
        if (glfwRawMouseMotionSupported()):
            is_orbiting= True
            glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED)
            glfwSetInputMode(window, GLFW_RAW_MOUSE_MOTION, GLFW_TRUE)

    if (button == GLFW_MOUSE_BUTTON_LEFT) & (action == GLFW_RELEASE):
        is_orbiting= False
        glfwSetInputMode(window, GLFW_CURSOR,  GLFW_CURSOR_NORMAL)
        glfwSetInputMode(window, GLFW_RAW_MOUSE_MOTION, GLFW_FALSE)

def cursor_position_callback(window, xpos, ypos):
    # print(xpos, ypos)
    pass

def prepare_vao_triangle():
    # prepare vertex data (in main memory)
    vertices = glm.array(glm.float32,
                         # position        # color
                         0.0, 0.0, 0.0, 1.0, 0.0, 0.0,  # v0
                         0.5, 0.0, 0.0, 0.0, 1.0, 0.0,  # v1
                         0.0, 0.5, 0.0, 0.0, 0.0, 1.0,  # v2
                         )

    # create and activate VAO (vertex array object)
    VAO = glGenVertexArrays(1)  # create a vertex array object ID and store it to VAO variable
    glBindVertexArray(VAO)  # activate VAO

    # create and activate VBO (vertex buffer object)
    VBO = glGenBuffers(1)  # create a buffer object ID and store it to VBO variable
    glBindBuffer(GL_ARRAY_BUFFER, VBO)  # activate VBO as a vertex buffer object

    # copy vertex data to VBO
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr,
                 GL_STATIC_DRAW)  # allocate GPU memory for and copy vertex data to the currently bound vertex buffer

    # configure vertex positions
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), None)
    glEnableVertexAttribArray(0)

    # configure vertex colors
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32),
                          ctypes.c_void_p(3 * glm.sizeof(glm.float32)))
    glEnableVertexAttribArray(1)

    return VAO


def prepare_vao_frame():
    # prepare vertex data (in main memory)
    vertices = glm.array(glm.float32,
                         # position        # color
                         0.0, 0.0, 0.0, 1.0, 0.0, 0.0,  # x-axis start
                         1.0, 0.0, 0.0, 1.0, 0.0, 0.0,  # x-axis end
                         0.0, 0.0, 0.0, 0.0, 1.0, 0.0,  # y-axis start
                         0.0, 1.0, 0.0, 0.0, 1.0, 0.0,  # y-axis end
                         0.0, 0.0, 0.0, 0.0, 0.0, 1.0,  # z-axis start
                         0.0, 0.0, 1.0, 0.0, 0.0, 1.0,  # z-axis end
                         -1.0, 0.0, 0.0, 0.3, 0.3, 0.3,  # x-axis grid start
                         1.0, 0.0, 0.0, 0.3, 0.3, 0.3,  # x-axis grid end
                         0.0, 0.0, -1.0, 0.3, 0.3, 0.3,  # z-axis grid start
                         0.0, 0.0, 1.0, 0.3, 0.3, 0.3,  # z-axis grid end
                         )

    # create and activate VAO (vertex array object)
    VAO = glGenVertexArrays(1)  # create a vertex array object ID and store it to VAO variable
    glBindVertexArray(VAO)  # activate VAO

    # create and activate VBO (vertex buffer object)
    VBO = glGenBuffers(1)  # create a buffer object ID and store it to VBO variable
    glBindBuffer(GL_ARRAY_BUFFER, VBO)  # activate VBO as a vertex buffer object

    # copy vertex data to VBO
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.ptr,
                 GL_STATIC_DRAW)  # allocate GPU memory for and copy vertex data to the currently bound vertex buffer

    # configure vertex positions
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32), None)
    glEnableVertexAttribArray(0)

    # configure vertex colors
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32),
                          ctypes.c_void_p(3 * glm.sizeof(glm.float32)))
    glEnableVertexAttribArray(1)

    return VAO


def draw_grid(MVP_loc, camera, vao_frame):
    glBindVertexArray(vao_frame)
    # draw grid
    for i in range(-5, 6):
        I = glm.translate(glm.vec3(0, 0, i * 0.2))
        MVP = camera.get_view_matrix() * I
        glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
        glDrawArrays(GL_LINES, 6, 2)
        I = glm.translate(glm.vec3(i * 0.2, 0, 0))
        MVP = camera.get_view_matrix() * I
        glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
        glDrawArrays(GL_LINES, 8, 2)

    # draw world frame
    I = glm.mat4()
    MVP = camera.get_view_matrix() * I
    glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
    glDrawArrays(GL_LINES, 0, 6)
    # Draw Screen Frame
    I = glm.mat4(0.03, 0.03, 0.03, 1)
    glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(I))
    glDrawArrays(GL_LINES, 0, 4)


def main():
    global screen_pos, screen_pos_prev, is_panning, is_orbiting
    # initialize glfw
    if not glfwInit():
        return
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3)  # OpenGL 3.3
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3)
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)  # Do not allow legacy OpenGl API calls
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE)  # for macOS

    # create a window and OpenGL context
    window = glfwCreateWindow(800, 800, '2021038131 장준혁', None, None)
    if not window:
        glfwTerminate()
        return
    glfwMakeContextCurrent(window)

    # register event callbacks
    glfwSetKeyCallback(window, key_callback)
    glfwSetScrollCallback(window, scroll_callback)
    glfwSetMouseButtonCallback(window, mouse_button_callback)
    glfwSetCursorPosCallback(window, cursor_position_callback)

    # load shaders
    shader_program = load_shaders(g_vertex_shader_src, g_fragment_shader_src)
    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_ALWAYS)
    # get uniform locations
    MVP_loc = glGetUniformLocation(shader_program, 'MVP')

    # prepare vaos
    vao_triangle = prepare_vao_triangle()
    vao_frame = prepare_vao_frame()


    # loop until the user closes the window
    while not glfwWindowShouldClose(window):
        # render

        # enable depth test (we'll see details later)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        glUseProgram(shader_program)

        draw_grid(MVP_loc, camera, vao_frame)

        # animating
        t = glfwGetTime()

        # rotation
        th = np.radians(t * 90)
        R = glm.rotate(th, glm.vec3(0, 0, 1))

        # tranlation
        T = glm.translate(glm.vec3(np.sin(t), .2, 0.))

        # scaling
        S = glm.scale(glm.vec3(np.sin(t), np.sin(t), np.sin(t)))

        M = glm.translate(g_triangle_translation)*R
        # M = T
        # M = S
        # M = R @ T
        # M = T @ R

        # current frame: P*V*M

        MVP = camera.get_view_matrix() * M

        glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))

        # draw triangle w.r.t. the current frame
        glBindVertexArray(vao_triangle)
        glDrawArrays(GL_TRIANGLES, 0, 3)

        # draw current frame

        
        glBindVertexArray(vao_frame)
        glDrawArrays(GL_LINES, 0, 6)

        # swap front and back buffers
        glfwSwapBuffers(window)

        # poll events
        glfwPollEvents()

        screen_pos_prev = screen_pos
        screen_pos = glfwGetCursorPos(window)

        if is_panning:
            offset = np.subtract(screen_pos, screen_pos_prev)*0.0003
            offset = glm.vec4(-offset[0], offset[1], 0, 0)
            if (glm.determinant(camera.get_view_matrix_raw()) != 0):
                offset = glm.inverse(camera.get_view_matrix_raw()) * offset
            else:
                offset = glm.vec3(0, 0, 0)
            offset = glm.vec3(offset)
            camera.origin = glm.vec3(glm.translate(offset)*glm.vec4(camera.origin,1))
        if is_orbiting:
            offset = np.subtract(screen_pos, screen_pos_prev) * 0.0001
            camera.xz_angle -= offset[0]*5
            camera.y_angle -= offset[1]*5
            if camera.y_angle > np.radians(179):
                camera.y_angle = np.radians(179)
            if camera.y_angle < np.radians(1):
                camera.y_angle = np.radians(1)

    # terminate glfw
    glfwTerminate()


if __name__ == "__main__":
    main()
