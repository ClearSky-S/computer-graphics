from OpenGL.GL import *
from glfw.GLFW import *
import glm
import ctypes
import numpy as np
from camera import *
from gameobject import GameObject, read_bvh
initial_viewport_size = (1200, 800)
screen_pos_prev = (0,0)
screen_pos = (0,0)
camera = Camera(initial_viewport_size)
is_panning = False
is_orbiting = False
is_wireframe = False
g_triangle_translation = glm.vec3()
is_line_render_mode = True
root_gameobject = read_bvh("walk_rough.bvh")
object_scale_multiplier = 30
object_scale = root_gameobject.children[0].transform.position[1] * object_scale_multiplier
# print(object_scale)
camera.distance = object_scale
is_animation_active = False
prev_time = 0



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


g_vertex_shader_src_lighting = '''
#version 330 core

layout (location = 0) in vec3 vin_pos; 
layout (location = 1) in vec3 vin_normal; 

out vec3 vout_surface_pos;
out vec3 vout_normal;

uniform mat4 MVP;
uniform mat4 M;

void main()
{
    vec4 p3D_in_hcoord = vec4(vin_pos.xyz, 1.0);
    gl_Position = MVP * p3D_in_hcoord;

    vout_surface_pos = vec3(M * vec4(vin_pos, 1));
    vout_normal = normalize( mat3(inverse(transpose(M)) ) * vin_normal);
}
'''

g_fragment_shader_src_lighting = '''
#version 330 core

in vec3 vout_surface_pos;
in vec3 vout_normal;

out vec4 FragColor;

uniform vec3 view_pos;
uniform vec3 material_color;

void main()
{
    // light and material properties
    vec3 light_pos = vec3(200,250,150);
    vec3 light_color = vec3(1,1,1);
    float material_shininess = 32.0;

    // light components
    vec3 light_ambient = 0.1*light_color;
    vec3 light_diffuse = light_color;
    vec3 light_specular = light_color;

    // material components
    vec3 material_ambient = material_color;
    vec3 material_diffuse = material_color;
    vec3 material_specular = light_color;  // for non-metal material

    // ambient
    vec3 ambient = light_ambient * material_ambient;

    // for diffiuse and specular
    vec3 normal = normalize(vout_normal);
    vec3 surface_pos = vout_surface_pos;
    vec3 light_dir = normalize(light_pos - surface_pos);

    // diffuse
    float diff = max(dot(normal, light_dir), 0);
    vec3 diffuse = diff * light_diffuse * material_diffuse;

    // specular
    vec3 view_dir = normalize(view_pos - surface_pos);
    vec3 reflect_dir = reflect(-light_dir, normal);
    float spec = pow( max(dot(view_dir, reflect_dir), 0.0), material_shininess);
    vec3 specular = spec * light_specular * material_specular;

    vec3 color = ambient + diffuse + specular;
    FragColor = vec4(color, 1.);
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
    global g_cam_ang, g_cam_height, is_wireframe, is_line_render_mode, is_animation_active
    if key == GLFW_KEY_ESCAPE and action == GLFW_PRESS:
        glfwSetWindowShouldClose(window, GLFW_TRUE);
    else:
        if action == GLFW_PRESS:
            if key == GLFW_KEY_V:
                camera.isPerspective = not camera.isPerspective
            if key == GLFW_KEY_R:
                # reset camera view target
                camera.origin = glm.vec3(0, 0, 0)
            if key == GLFW_KEY_Z:
                if is_wireframe:
                    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

                else:
                    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
                is_wireframe = not is_wireframe
            if key == GLFW_KEY_1:
                is_line_render_mode = True
            if key == GLFW_KEY_2:
                is_line_render_mode = False
            if key == GLFW_KEY_SPACE:
                # set animation flag
                is_animation_active = not is_animation_active
                if not is_animation_active:
                    # reset animation
                    root_gameobject.reset_link_transform()
                    root_gameobject.animation.set_time(0)


def scroll_callback(window, xoffset, yoffset):
    if yoffset < 0:
        camera.distance += object_scale / 3
    elif yoffset > 0:
        if camera.distance > object_scale / 3+0.000001:
            camera.distance -= object_scale / 3
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

def drop_callback(window, paths):
    # print(paths[0])
    global root_gameobject, camera, object_scale, is_animation_active
    is_animation_active = False
    root_gameobject = read_bvh(paths[0])
    object_scale = root_gameobject.children[0].transform.position[1] * object_scale_multiplier
    camera.distance = object_scale
    camera.origin = glm.vec3(0, 0, 0)

def framebuffer_size_callback(window, width, height):
    glViewport(0, 0, width, height)
    camera.set_viewport_size(width, height)

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
    global object_scale
    glBindVertexArray(vao_frame)
    # draw grid
    for i in range(-5, 6):
        I = glm.translate(glm.vec3(0, 0, i *0.2))
        grid_scale = glm.scale(glm.vec3(object_scale))
        MVP = camera.get_view_matrix() * grid_scale * I
        glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
        glDrawArrays(GL_LINES, 6, 2)
        I = glm.translate(glm.vec3(i*0.2 , 0, 0))
        MVP = camera.get_view_matrix()* grid_scale * I
        glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
        glDrawArrays(GL_LINES, 8, 2)

    # draw world frame
    I = glm.mat4()
    MVP = camera.get_view_matrix()* grid_scale * I
    glUniformMatrix4fv(MVP_loc, 1, GL_FALSE, glm.value_ptr(MVP))
    glDrawArrays(GL_LINES, 0, 6)


def prepare_vao_cube():
    # prepare vertex data (in main memory)
    # 36 vertices for 12 triangles
    vertices = glm.array(glm.float32,
                         # position      normal
                         -1, 1, 1, 0, 0, 1,  # v0
                         1, -1, 1, 0, 0, 1,  # v2
                         1, 1, 1, 0, 0, 1,  # v1

                         -1, 1, 1, 0, 0, 1,  # v0
                         -1, -1, 1, 0, 0, 1,  # v3
                         1, -1, 1, 0, 0, 1,  # v2

                         -1, 1, -1, 0, 0, -1,  # v4
                         1, 1, -1, 0, 0, -1,  # v5
                         1, -1, -1, 0, 0, -1,  # v6

                         -1, 1, -1, 0, 0, -1,  # v4
                         1, -1, -1, 0, 0, -1,  # v6
                         -1, -1, -1, 0, 0, -1,  # v7

                         -1, 1, 1, 0, 1, 0,  # v0
                         1, 1, 1, 0, 1, 0,  # v1
                         1, 1, -1, 0, 1, 0,  # v5

                         -1, 1, 1, 0, 1, 0,  # v0
                         1, 1, -1, 0, 1, 0,  # v5
                         -1, 1, -1, 0, 1, 0,  # v4

                         -1, -1, 1, 0, -1, 0,  # v3
                         1, -1, -1, 0, -1, 0,  # v6
                         1, -1, 1, 0, -1, 0,  # v2

                         -1, -1, 1, 0, -1, 0,  # v3
                         -1, -1, -1, 0, -1, 0,  # v7
                         1, -1, -1, 0, -1, 0,  # v6

                         1, 1, 1, 1, 0, 0,  # v1
                         1, -1, 1, 1, 0, 0,  # v2
                         1, -1, -1, 1, 0, 0,  # v6

                         1, 1, 1, 1, 0, 0,  # v1
                         1, -1, -1, 1, 0, 0,  # v6
                         1, 1, -1, 1, 0, 0,  # v5

                         -1, 1, 1, -1, 0, 0,  # v0
                         -1, -1, -1, -1, 0, 0,  # v7
                         -1, -1, 1, -1, 0, 0,  # v3

                         -1, 1, 1, -1, 0, 0,  # v0
                         -1, 1, -1, -1, 0, 0,  # v4
                         -1, -1, -1, -1, 0, 0,  # v7
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

    # configure vertex normals
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 6 * glm.sizeof(glm.float32),
                          ctypes.c_void_p(3 * glm.sizeof(glm.float32)))
    glEnableVertexAttribArray(1)

    return VAO

def main():
    global screen_pos, screen_pos_prev, is_panning, is_orbiting, root_gameobject, is_line_render_mode, is_animation_active
    # initialize glfw
    if not glfwInit():
        return
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3)  # OpenGL 3.3
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3)
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE)  # Do not allow legacy OpenGl API calls
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE)  # for macOS

    # create a window and OpenGL context
    window = glfwCreateWindow(initial_viewport_size[0],initial_viewport_size[1], '2021038131 장준혁', None, None)
    if not window:
        glfwTerminate()
        return
    glfwMakeContextCurrent(window)

    # register event callbacks
    glfwSetKeyCallback(window, key_callback)
    glfwSetScrollCallback(window, scroll_callback)
    glfwSetMouseButtonCallback(window, mouse_button_callback)
    glfwSetFramebufferSizeCallback(window, framebuffer_size_callback)
    glfwSetDropCallback(window, drop_callback)

    # load shaders
    shader_program = load_shaders(g_vertex_shader_src, g_fragment_shader_src)
    shader_lighting = load_shaders(g_vertex_shader_src_lighting, g_fragment_shader_src_lighting)





    # glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LESS)

    # get uniform locations
    # MVP_loc = glGetUniformLocation(shader_program, 'MVP')

    unif_names = ['MVP']
    unif_locs_color = {}
    for name in unif_names:
        unif_locs_color[name] = glGetUniformLocation(shader_program, name)

    unif_names = ['MVP', 'M', 'view_pos', 'material_color']
    unif_locs_lighting = {}
    for name in unif_names:
        unif_locs_lighting[name] = glGetUniformLocation(shader_lighting, name)

    # prepare vaos
    vao_frame = prepare_vao_frame()
    vao_cube = prepare_vao_cube()
    prev_time = glfwGetTime()

    # loop until the user closes the window
    while not glfwWindowShouldClose(window):
        # render

        # enable depth test (we'll see details later)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)

        delta_time = glfwGetTime() - prev_time
        prev_time = glfwGetTime()

        if is_animation_active:
            root_gameobject.animation.add_time(delta_time)
            root_gameobject.update_animation()
        if is_line_render_mode:
            glUseProgram(shader_program)
            glBindVertexArray(vao_frame)
            root_gameobject.draw_recusive_line(unif_locs_color, camera)
        else:
            glUseProgram(shader_lighting)
            glBindVertexArray(vao_cube)
            root_gameobject.draw_mesh_recursive(unif_locs_lighting, camera)


        glUseProgram(shader_lighting)


        # Draw Screen Frame
        glUseProgram(shader_program)
        glBindVertexArray(vao_frame)
        I = glm.scale(glm.vec3(1/camera.get_viewport_ratio(),1,1))* glm.mat4(0.03, 0.03, 0.03, 1)
        glUniformMatrix4fv(unif_locs_color['MVP'], 1, GL_FALSE, glm.value_ptr(I))
        glDrawArrays(GL_LINES, 0, 4)

        draw_grid(unif_locs_color['MVP'], camera, vao_frame)

        # swap front and back buffers
        glfwSwapBuffers(window)
        # poll events
        glfwPollEvents()

        # camera movement
        screen_pos_prev = screen_pos
        screen_pos = glfwGetCursorPos(window)
        if is_panning:
            offset = np.subtract(screen_pos, screen_pos_prev)*0.005 * object_scale/5
            offset = glm.vec4(-offset[0], offset[1], 0, 0)
            if (glm.determinant(camera.get_view_matrix_raw()) != 0):
                offset = glm.inverse(camera.get_view_matrix_raw()) * offset
            else:
                offset = glm.vec3(0, 0, 0)
            offset = glm.vec3(offset)
            camera.origin = glm.vec3(glm.translate(offset)*glm.vec4(camera.origin,1))
        if is_orbiting:
            offset = np.subtract(screen_pos, screen_pos_prev) * 0.0003
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
