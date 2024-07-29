import sys
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtCore import Qt
from OpenGL.GL import *
from OpenGL.GLU import *
import fbx


class MeshViewer(QOpenGLWidget):
    def __init__(self, parent=None):
        super(MeshViewer, self).__init__(parent)
        self.last_pos = None
        self.x_rot = 0
        self.y_rot = 0
        self.z_rot = 0
        self.zoom = -5
        self.meshes = []

        # FBXファイルのパスを指定
        self.load_fbx("1M_Cube.fbx")

    def load_fbx(self, file_path):
        manager = fbx.FbxManager.Create()
        if not manager:
            print("Failed to create FBX Manager.")
            return

        ios = fbx.FbxIOSettings.Create(manager, fbx.IOSROOT)
        manager.SetIOSettings(ios)

        importer = fbx.FbxImporter.Create(manager, "")
        if not importer:
            print("Failed to create FBX Importer.")
            return

        if not importer.Initialize(file_path, -1, manager.GetIOSettings()):
            status = importer.GetStatus()
            print("Failed to initialize the FBX importer:")
            print(f"Error: {status.GetErrorString()}")
            return

        scene = fbx.FbxScene.Create(manager, "myScene")
        if not importer.Import(scene):
            status = importer.GetStatus()
            print("Failed to import FBX scene:")
            print(f"Error: {status.GetErrorString()}")
            return

        print("FBX file loaded successfully")
        self.process_scene(scene)
        manager.Destroy()

    def process_scene(self, scene):
        root_node = scene.GetRootNode()
        if root_node:
            self.process_node(root_node)

    def process_node(self, node):
        for i in range(node.GetChildCount()):
            child = node.GetChild(i)
            if child.GetNodeAttribute():
                attr_type = child.GetNodeAttribute().GetAttributeType()
                if attr_type == fbx.FbxNodeAttribute.eMesh:
                    self.process_mesh(child.GetMesh())
            self.process_node(child)

    def process_mesh(self, mesh):
        control_points = mesh.GetControlPoints()
        num_polygons = mesh.GetPolygonCount()

        vertices = []
        for i in range(num_polygons):
            num_vertices = mesh.GetPolygonSize(i)
            polygon_vertices = []
            for j in range(num_vertices):
                index = mesh.GetPolygonVertex(i, j)
                point = control_points[index]
                polygon_vertices.append((point[0], point[1], point[2]))

            # ポリゴンを適切な描画モードで描画
            if num_vertices == 3:
                # 三角形として処理
                vertices.append(('TRIANGLES', polygon_vertices))
            elif num_vertices == 4:
                # 四角形として処理
                vertices.append(('QUADS', polygon_vertices))
            else:
                # その他のポリゴンとして処理
                vertices.append(('POLYGON', polygon_vertices))

        print(f"Processed mesh with {num_polygons} polygons")
        self.meshes.append(vertices)

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glShadeModel(GL_SMOOTH)
        glClearColor(0.0, 0.0, 0.0, 1.0)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, width / float(height), 1.0, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, self.zoom)
        glRotatef(self.x_rot / 16.0, 1.0, 0.0, 0.0)
        glRotatef(self.y_rot / 16.0, 0.0, 1.0, 0.0)
        glRotatef(self.z_rot / 16.0, 0.0, 0.0, 1.0)

        self.draw_meshes()

    def draw_meshes(self):
        # # テスト用
        # glBegin(GL_TRIANGLES)
        # glColor3f(1.0, 0.0, 0.0)
        # glVertex3f(-1.0, -1.0, 0.0)
        # glColor3f(0.0, 1.0, 0.0)
        # glVertex3f(1.0, -1.0, 0.0)
        # glColor3f(0.0, 0.0, 1.0)
        # glVertex3f(0.0, 1.0, 0.0)
        # glEnd()

        for mesh in self.meshes:
            for mode, vertices in mesh:
                if mode == 'TRIANGLES':
                    glBegin(GL_TRIANGLES)
                elif mode == 'QUADS':
                    glBegin(GL_QUADS)
                else:
                    glBegin(GL_POLYGON)

                for vertex in vertices:
                    glVertex3f(*vertex)

                glEnd()

    def mousePressEvent(self, event):
        self.last_pos = event.position()

    def mouseMoveEvent(self, event):
        dx = event.position().x() - self.last_pos.x()
        dy = event.position().y() - self.last_pos.y()

        if event.buttons() & Qt.MouseButton.LeftButton:
            self.set_x_rotation(self.x_rot + 8 * dy)
            self.set_y_rotation(self.y_rot + 8 * dx)
        elif event.buttons() & Qt.MouseButton.RightButton:
            self.set_x_rotation(self.x_rot + 8 * dy)
            self.set_z_rotation(self.z_rot + 8 * dx)

        self.last_pos = event.position()

    def wheelEvent(self, event):
        num_degrees = event.angleDelta().y() / 8
        num_steps = num_degrees / 15
        self.zoom += num_steps
        self.update()

    def set_x_rotation(self, angle):
        self.x_rot = angle
        self.update()

    def set_y_rotation(self, angle):
        self.y_rot = angle
        self.update()

    def set_z_rotation(self, angle):
        self.z_rot = angle
        self.update()


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.viewer = MeshViewer(self)
        self.setCentralWidget(self.viewer)
        self.setWindowTitle("Mesh Viewer")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    fmt = QSurfaceFormat()
    fmt.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(fmt)

    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
