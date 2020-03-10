# coding： utf8
import copy
import math

from qtpy import QtCore
from qtpy import QtGui

import labelme.utils


# TODO(unknown):
# - [opt] Store paths instead of creating new ones at each paint.


DEFAULT_LINE_COLOR = QtGui.QColor(0, 255, 0, 128)
DEFAULT_FILL_COLOR = QtGui.QColor(255, 0, 0, 128)
DEFAULT_SELECT_LINE_COLOR = QtGui.QColor(255, 255, 255)
DEFAULT_SELECT_FILL_COLOR = QtGui.QColor(0, 128, 255, 155)
DEFAULT_VERTEX_FILL_COLOR = QtGui.QColor(0, 255, 0, 255)
DEFAULT_HVERTEX_FILL_COLOR = QtGui.QColor(255, 0, 0)

DEFAULT_KEYPOINT_COLOR=[QtGui.QColor(192, 192, 192),QtGui.QColor(255, 0, 255),
                        QtGui.QColor(0, 255, 64),QtGui.QColor(128, 180, 0),QtGui.QColor(255, 128, 128),QtGui.QColor(255, 255, 0),QtGui.QColor(0, 255, 255),QtGui.QColor(218, 112, 214),
                        QtGui.QColor(0, 64, 0),QtGui.QColor(128, 64, 64),QtGui.QColor(255, 0, 0),QtGui.QColor(255, 128, 0),QtGui.QColor(0, 0, 255),QtGui.QColor(128, 0, 128)]



_keypoints=['_head','_neck',  \
             '_right_shoulder','_right_elbow','_right_hand','_right_buttocks','_right_knee','_right_foot',  \
             '_left_shoulder','_left_elbow','_left_hand','_left_buttocks','_left_knee','_left_foot']
_keypointsname=['头部','脖子',  \
             '右肩','右肘','右手','右臀','右膝','右脚',  \
             '左肩','左肘','左手','左臀','左膝','左脚']


class Shape(object):

    P_SQUARE, P_ROUND = 0, 1

    MOVE_VERTEX, NEAR_VERTEX = 0, 1

    # The following class variables influence the drawing of all shape objects.
    line_color = DEFAULT_LINE_COLOR
    fill_color = DEFAULT_FILL_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    select_fill_color = DEFAULT_SELECT_FILL_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    hvertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    point_type = P_ROUND
    point_size = 8
    scale = 1.0

    def __init__(self, label=None, line_color=None, shape_type=None):
        self.label = label
        self.points = []
        self.fill = False
        self.selected = False
        self.shape_type = shape_type
        self.paintrect=False   #添加信号  #ls
        self.paintpoint=False
        #if shape_type == 'PERSONKEYPOINTS':
        self.bodyvisible=[]   #关键点属性和点的连接关系
        self.skeleton=[[1,0],[2,1],[3,2],[4,3],[5,2],[6,5],[7,6],[8,1],[9,8],[10,9],[11,5],[11,8],[12,11],[13,12]]

        self._highlightIndex = None
        self._highlightMode = self.NEAR_VERTEX
        self._highlightSettings = {
            self.NEAR_VERTEX: (4, self.P_ROUND),
            self.MOVE_VERTEX: (1.5, self.P_SQUARE),
        }

        self._closed = False

        if line_color is not None:
            # Override the class line_color attribute
            # with an object attribute. Currently this
            # is used for drawing the pending line a different color.
            self.line_color = line_color

        self.shape_type = shape_type

    @property
    def shape_type(self):
        return self._shape_type

    @shape_type.setter
    def shape_type(self, value):
        if value is None:
            value = 'POLYGON'
        if value not in ['POLYGON', 'RECT', 'POINT','PERSONKEYPOINTS',
           'LINE', 'CIRCLE', 'KEYPOINTS']:
            raise ValueError('Unexpected shape_type: {}'.format(value))
        self._shape_type = value

    def close(self):
        self._closed = True

    def addPoint(self, point):
        if self.points and point == self.points[0]:
            self.close()
        else:
            self.points.append(point)

    def popPoint(self):
        if self.points:
            return self.points.pop()
        return None

    def insertPoint(self, i, point):
        self.points.insert(i, point)

    def isClosed(self):
        return self._closed

    def setOpen(self):
        self._closed = False

    def getRectFromLine(self, pt1, pt2):
        x1, y1 = pt1.x(), pt1.y()
        x2, y2 = pt2.x(), pt2.y()
        return QtCore.QRectF(x1, y1, x2 - x1, y2 - y1)

    def head_to_neck(self,line_path):
        if self.bodyvisible[0] != 0 and self.bodyvisible[1] !=0:
            line_path.moveTo(self.points[2])
            line_path.lineTo(self.points[3])
            line_path.addPath(line_path)
    def right_buttocks_to_right_knee(self,line_path):
        if self.bodyvisible[5] != 0 and self.bodyvisible[6] !=0:
            line_path.moveTo(self.points[7])
            line_path.lineTo(self.points[8])
            line_path.addPath(line_path)

    def paint(self, painter):
        if self.points:
            color = self.select_line_color \
                if self.selected else self.line_color
            pen = QtGui.QPen(color)
            # Try using integer sizes for smoother drawing(?)
            pen.setWidth(max(1, int(round(2.0 / self.scale))))
            painter.setPen(pen)

            line_path = QtGui.QPainterPath()
            vrtx_path = QtGui.QPainterPath()
            if self.shape_type == 'PERSONKEYPOINTS':
                _head = QtGui.QPainterPath()
                _neck = QtGui.QPainterPath()
                _right_shoulder = QtGui.QPainterPath()
                _right_elbow = QtGui.QPainterPath()
                _right_hand = QtGui.QPainterPath()
                _right_buttocks = QtGui.QPainterPath()
                _right_knee = QtGui.QPainterPath()
                _right_foot = QtGui.QPainterPath()
                _left_shoulder = QtGui.QPainterPath()
                _left_elbow = QtGui.QPainterPath()
                _left_hand = QtGui.QPainterPath()
                _left_buttocks = QtGui.QPainterPath()
                _left_knee = QtGui.QPainterPath()
                _left_foot = QtGui.QPainterPath()


            if self.shape_type == 'RECT':
                assert len(self.points) in [1, 2]
                if len(self.points) == 2:
                    rectangle = self.getRectFromLine(*self.points)
                    line_path.addRect(rectangle)
                for i in range(len(self.points)):
                    self.drawVertex(vrtx_path, i)
            elif self.shape_type == "CIRCLE":
                assert len(self.points) in [1, 2]
                if len(self.points) == 2:
                    rectangle = self.getCircleRectFromLine(self.points)
                    line_path.addEllipse(rectangle)
                for i in range(len(self.points)):
                    self.drawVertex(vrtx_path, i)
            elif self.shape_type == "KEYPOINTS":
                line_path.moveTo(self.points[0])
                for i, p in enumerate(self.points):
                    line_path.lineTo(p)
                    self.drawVertex(vrtx_path, i)
            elif self.shape_type == 'PERSONKEYPOINTS':  #添加自定义模块画图模式
                if self.paintrect and not self.paintpoint:#画框不画点
                    assert len(self.points) in [1, 2]
                    if len(self.points) == 2:
                        rectangle = self.getRectFromLine(*self.points)
                        line_path.addRect(rectangle)
                    for i in range(len(self.points)):
                        self.drawVertex(vrtx_path, i)
                elif self.paintpoint and not self.paintrect: #画点不画框
                    # line_path.moveTo(self.points[0])
                    # for i, p in enumerate(self.points):
                    #     line_path.lineTo(p)
                    #     self.drawVertex(vrtx_path, i)

                    #self.drawVertex(vrtx_path, 1)
                    # if self.points[1].x() == 0:
                    #     print('error')
                    self.drawVertex(eval(_keypoints[len(self.bodyvisible)]), 1)
                elif (self.paintpoint and self.paintrect) or len(self.points)==16: #点和框都画
                    rectpoints=self.points[:2]
                    if len(rectpoints) == 2:  #矩形框
                        rectangle = self.getRectFromLine(*rectpoints)
                        line_path.addRect(rectangle)

                    #line_path.moveTo(self.points[0])  #连线 ls

                    # Uncommenting the following line will draw 2 paths
                    # for the 1st vertex, and make it non-filled, which
                    # may be desirable.
                    # self.drawVertex(vrtx_path, 0)

                    for i, p in enumerate(self.points):
                        #line_path.lineTo(p) #连线 ls
                        if i>1:
                            if self.bodyvisible[i-2] == 0:#无标定点不画,进入此条件意味着开始画关键点了
                                continue
                            else:
                                self.drawVertex(eval(_keypoints[i - 2]), i)#不同关键点对应不同颜色
                        else:
                            self.drawVertex(vrtx_path, i)



                        #self.drawVertex(vrtx_path, i) #画点

                        #self.drawVertex(globals()[_keypoints[i-2]], i)

                    # if len(self.points) >3: #总共四个点才开始画线。  实时画点,速度过慢，注释掉 #ls
                    #     if len(self.points) <13:
                    #         currentskeleton=self.skeleton[:len(self.points)-3]
                    #     else:
                    #         currentskeleton=self.skeleton[:len(self.points)-2]
                    #     for i,j in currentskeleton:
                    #         if self.bodyvisible[i] != 0 and self.bodyvisible[j] != 0:
                    #             line_path.moveTo(self.points[i+2])
                    #             line_path.lineTo(self.points[j+2])
                    #             line_path.addPath(line_path)

                    # if len(self.points)  == 16:  #只画完整的骨架  #ls
                    #     for i,j in self.skeleton:
                    #         if self.bodyvisible[i] != 0 and self.bodyvisible[j] != 0:
                    #             line_path.moveTo(self.points[i+2])
                    #             line_path.lineTo(self.points[j+2])
                    #             line_path.addPath(line_path)

                    # if len(self.points) == 4:  #使用内部函数连接，未完工，选择上面画骨架的方式 #ls
                    #     self.head_to_neck(line_path)
                    #
                    # if len(self.points) == 9:
                    #     self.head_to_neck(line_path)
                    #     self.right_buttocks_to_right_knee(line_path)


            else:
                line_path.moveTo(self.points[0])
                # Uncommenting the following line will draw 2 paths
                # for the 1st vertex, and make it non-filled, which
                # may be desirable.
                # self.drawVertex(vrtx_path, 0)

                for i, p in enumerate(self.points):
                    line_path.lineTo(p)
                    self.drawVertex(vrtx_path, i)
                if self.isClosed():
                    line_path.lineTo(self.points[0])

            painter.drawPath(line_path)
            painter.drawPath(vrtx_path)
            painter.fillPath(vrtx_path, self.vertex_fill_color)
            if self.shape_type == 'PERSONKEYPOINTS':#标注人体关键点时颜色标定添加步骤显示不同点颜色
                if (self.paintpoint and self.paintrect) or len(self.points)==16:
                    for i, p in enumerate(self.points):
                        if i>1 and self.bodyvisible[i-2] == 0:  #无标定点不画,进入此条件意味着开始画关键点了
                            continue
                        painter.drawPath(eval(_keypoints[i-2]))
                        painter.fillPath(eval(_keypoints[i-2]), DEFAULT_KEYPOINT_COLOR[i-2])#不同关键点对应不同颜色 #ls
                elif self.paintpoint and not self.paintrect:
                    painter.drawPath(eval(_keypoints[len(self.bodyvisible)]))
                    painter.fillPath(eval(_keypoints[len(self.bodyvisible)]), DEFAULT_KEYPOINT_COLOR[len(self.bodyvisible)])  # 不同关键点对应不同颜色 #ls
            if self.fill:
                color = self.select_fill_color \
                    if self.selected else self.fill_color
                painter.fillPath(line_path, color)

    def drawVertex(self, path, i):
        d = self.point_size / self.scale
        shape = self.point_type
        point = self.points[i]
        if i == self._highlightIndex:
            size, shape = self._highlightSettings[self._highlightMode]
            d *= size
        if self._highlightIndex is not None:
            self.vertex_fill_color = self.hvertex_fill_color
        else:
            self.vertex_fill_color = Shape.vertex_fill_color
        if shape == self.P_SQUARE:
            path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)
        elif shape == self.P_ROUND:
            if self.shape_type == 'PERSONKEYPOINTS':
                if i>1:
                    path.addText(point, QtGui.QFont(), '{}'.format(_keypointsname[i-2]))
                    if self.bodyvisible[i-2] == 1:
                        path.addEllipse(point, d, d)  # 不可见点显示为圆环，可见点显示为实心圆  #ls
                elif i==1 and len(self.bodyvisible) != 14 and self.paintpoint and not self.paintrect:#绘画当前点时添加的条件,显示标定的当前点属性
                    path.addText(point, QtGui.QFont(), '{}'.format(_keypointsname[len(self.bodyvisible)]))
            #     if i > 1 and self.bodyvisible[i-2] == 1:
            #         path.addEllipse(point, d , d ) #不可见点显示为圆环，可见点显示为实心圆  #ls
            # path.addText(point, QtGui.QFont(), 'test')
            path.addEllipse(point, d / 2.0, d / 2.0)
        else:
            assert False, "unsupported vertex shape"

    def nearestVertex(self, point, epsilon):
        min_distance = float('inf')
        min_i = None
        for i, p in enumerate(self.points):
            dist = labelme.utils.distance(p - point)
            if dist <= epsilon and dist < min_distance:
                min_distance = dist
                min_i = i
        return min_i

    def nearestEdge(self, point, epsilon):
        min_distance = float('inf')
        post_i = None
        for i in range(len(self.points)):
            line = [self.points[i - 1], self.points[i]]
            dist = labelme.utils.distancetoline(point, line)
            if dist <= epsilon and dist < min_distance:
                min_distance = dist
                post_i = i
        return post_i

    def containsPoint(self, point):
        return self.makePath().contains(point)

    def getCircleRectFromLine(self, line):
        """Computes parameters to draw with `QPainterPath::addEllipse`"""
        if len(line) != 2:
            return None
        (c, point) = line
        r = line[0] - line[1]
        d = math.sqrt(math.pow(r.x(), 2) + math.pow(r.y(), 2))
        rectangle = QtCore.QRectF(c.x() - d, c.y() - d, 2 * d, 2 * d)
        return rectangle

    def makePath(self):
        if self.shape_type == 'RECT':
            path = QtGui.QPainterPath()
            if len(self.points) == 2:
                rectangle = self.getRectFromLine(*self.points)
                path.addRect(rectangle)
        elif self.shape_type == "CIRCLE":
            path = QtGui.QPainterPath()
            if len(self.points) == 2:
                rectangle = self.getCircleRectFromLine(self.points)
                path.addEllipse(rectangle)
        elif self.shape_type == 'PERSONKEYPOINTS':  #目前只利用了矩形框
            path = QtGui.QPainterPath()
            rectpoints = self.points[:2]
            rectangle = self.getRectFromLine(*rectpoints)
            path.addRect(rectangle)

            path.moveTo(self.points[2])   #此为使用所有的标注点，此关键点连线暂未发现用途
            for i,p in enumerate(self.points[2:]):
                if self.bodyvisible[i] == 0:
                    continue
                path.lineTo(p)

        else:
            path = QtGui.QPainterPath(self.points[0])
            for p in self.points[1:]:
                path.lineTo(p)
        return path

    def boundingRect(self):
        return self.makePath().boundingRect()

    def moveBy(self, offset):
        self.points = [p + offset for p in self.points]

    def moveVertexBy(self, i, offset):
        self.points[i] = self.points[i] + offset

    def highlightVertex(self, i, action):
        self._highlightIndex = i
        self._highlightMode = action

    def highlightClear(self):
        self._highlightIndex = None

    def copy(self):
        shape = Shape(label=self.label, shape_type=self.shape_type)
        shape.points = [copy.deepcopy(p) for p in self.points]
        shape.fill = self.fill
        shape.selected = self.selected
        shape._closed = self._closed
        shape.line_color = copy.deepcopy(self.line_color)
        shape.fill_color = copy.deepcopy(self.fill_color)
        return shape

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value
