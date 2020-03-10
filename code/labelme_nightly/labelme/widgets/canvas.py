from qtpy import QtCore
from qtpy import QtGui
from qtpy import QtWidgets

from labelme import QT5
from labelme import PY2
from labelme.shape import Shape
import labelme.utils


# TODO(unknown):
# - [maybe] Find optimal epsilon value.


CURSOR_DEFAULT = QtCore.Qt.ArrowCursor
CURSOR_POINT = QtCore.Qt.PointingHandCursor
CURSOR_DRAW = QtCore.Qt.CrossCursor
CURSOR_MOVE = QtCore.Qt.ClosedHandCursor
CURSOR_GRAB = QtCore.Qt.OpenHandCursor

keypointbodyname=['head',
                  'right_shoulder','right_elbow','right_hand','right_buttocks','right_knee','right_foot',
                  'left_shoulder','left_elbow','left_hand','left_buttocks','left_knee','left_foot',]



class Canvas(QtWidgets.QWidget):

    zoomRequest = QtCore.Signal(int, QtCore.QPoint)
    scrollRequest = QtCore.Signal(int, int)
    newShape = QtCore.Signal()
    selectionChanged = QtCore.Signal(bool)
    shapeMoved = QtCore.Signal()
    drawingPolygon = QtCore.Signal(bool)
    edgeSelected = QtCore.Signal(bool)

    CREATE, EDIT = 0, 1

    # polygon, rectangle, line, or point
    _createMode = 'POLYGON'

    _fill_drawing = False

    def __init__(self, *args, **kwargs):
        self.epsilon = kwargs.pop('epsilon', 11.0)
        super(Canvas, self).__init__(*args, **kwargs)
        # Initialise local state.
        self.mode = self.EDIT
        self.shapes = []
        self.shapesBackups = []
        self.current = None
        self.selectedShape = None  # save the selected shape here
        self.isLeftButtonPressed=False
        self.selectedPerson = None # save the selected person here for key points  #ls
        self.prevKeyPoint=None #save the previous key point for auto choose next one  #ls
        self.selectedShapeCopy = None
        self.lineColor = QtGui.QColor(0, 0, 255)
        # self.line represents:
        #   - createMode == 'POLYGON': edge from last point to current
        #   - createMode == 'RECT': diagonal line of the rectangle
        #   - createMode == 'LINE': the line
        #   - createMode == 'POINT': the point
        self.line = Shape(line_color=self.lineColor)
        self.prevPoint = QtCore.QPoint()
        self.prevMovePoint = QtCore.QPoint()
        self.offsets = QtCore.QPoint(), QtCore.QPoint()
        self.scale = 1.0
        self.pixmap = QtGui.QPixmap()
        self.visible = {}
        self._hideBackround = False
        self.hideBackround = False
        self.hShape = None
        self.hVertex = None
        self.hEdge = None
        self.movingShape = False
        self._painter = QtGui.QPainter()
        self._cursor = CURSOR_DEFAULT
        # Menus:
        self.menus = (QtWidgets.QMenu(), QtWidgets.QMenu())
        # Set widget options.
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.WheelFocus)

    def fillDrawing(self):
        return self._fill_drawing

    def setFillDrawing(self, value):
        self._fill_drawing = value

    @property
    def createMode(self):
        return self._createMode

    @createMode.setter
    def createMode(self, value):
        if value not in ['POLYGON', 'RECT', 'POINT','PERSONKEYPOINTS',
           'LINE', 'CIRCLE', 'KEYPOINTS']:
            raise ValueError('Unsupported createMode: %s' % value)
        self._createMode = value

    def storeShapes(self):
        shapesBackup = []
        for shape in self.shapes:
            shapesBackup.append(shape.copy())
        if len(self.shapesBackups) >= 10:
            self.shapesBackups = self.shapesBackups[-9:]
        self.shapesBackups.append(shapesBackup)

    @property
    def isShapeRestorable(self):
        if len(self.shapesBackups) < 2:
            return False
        return True

    def restoreShape(self):
        if not self.isShapeRestorable:
            return
        self.shapesBackups.pop()  # latest
        shapesBackup = self.shapesBackups.pop()
        self.shapes = shapesBackup
        self.storeShapes()
        self.repaint()

    def enterEvent(self, ev):
        self.overrideCursor(self._cursor)

    def leaveEvent(self, ev):
        self.restoreCursor()

    def focusOutEvent(self, ev):
        self.restoreCursor()

    def isVisible(self, shape):
        return self.visible.get(shape, True)

    def drawing(self):
        return self.mode == self.CREATE

    def editing(self):
        return self.mode == self.EDIT

    def setEditing(self, value=True):
        self.mode = self.EDIT if value else self.CREATE
        if not value:  # Create
            self.unHighlight()
            self.deSelectShape()

    def unHighlight(self):
        if self.hShape:
            self.hShape.highlightClear()
        self.hVertex = self.hShape = None

    def selectedVertex(self):
        return self.hVertex is not None

    def errorMessage_ls(self, title, message):#报错
        return QtWidgets.QMessageBox.critical(
            self, title, '<p><b>%s</b></p>%s' % (title, message))

    def mouseMoveEvent(self, ev): #鼠标移动事件
        """Update line with last point and current coordinates."""
        if QT5:
            pos = self.transformPos(ev.pos())
        else:
            pos = self.transformPos(ev.posF())

        self.prevMovePoint = pos
        self.restoreCursor()


        # Polygon drawing.
        if self.drawing():

            self.line.shape_type = self.createMode

            self.overrideCursor(CURSOR_DRAW)

            if self.selectedPerson and not self.current:  #新模块初始化  兼容以前的矩形模块#ls
                self.current = Shape(shape_type=self.createMode)
                self.current.addPoint(self.selectedPerson.points[0])
                self.current.addPoint(self.selectedPerson.points[1])
                self.line.points = [pos, pos]
                self.current.paintpoint = True
                self.current.paintrect = True
                self.line.paintpoint = True
                self.line.paintrect = False
                self.setHiding()
                self.drawingPolygon.emit(True)
                self.update()
                return

            if not self.current:
                return

            color = self.lineColor
            if self.outOfPixmap(pos):
                # Don't allow the user to draw outside the pixmap.
                # Project the point to the pixmap's edges.
                pos = self.intersectionPoint(self.current[-1], pos)
            elif len(self.current) > 1 and self.createMode == 'POLYGON' and\
                    self.closeEnough(pos, self.current[0]):
                # Attract line to starting point and
                # colorise to alert the user.
                pos = self.current[0]
                color = self.current.line_color
                self.overrideCursor(CURSOR_POINT)
                self.current.highlightVertex(0, Shape.NEAR_VERTEX)
            if self.createMode in ['POLYGON', 'KEYPOINTS']:
                self.line[0] = self.current[-1]
                self.line[1] = pos
            elif self.createMode == 'RECT':
                self.line.points = [self.current[0], pos]
                self.line.close()
            elif self.createMode == 'CIRCLE':
                self.line.points = [self.current[0], pos]
                self.line.shape_type = 'CIRCLE'
            elif self.createMode == 'LINE':
                self.line.points = [self.current[0], pos]
                self.line.close()
            elif self.createMode == 'POINT':  #点模式下鼠标移动处理
                self.line.points = [self.current[0]]
                self.line.close()
            elif self.createMode == 'PERSONKEYPOINTS':
                if self.current.paintpoint:   #画关键点  #ls
                    self.line[0] = self.current[-1]
                    self.line[1] = pos
                    self.line.close()
                else:  #画矩形框  #ls
                    self.line.points = [self.current[0], pos]
                    self.line.close()
            self.line.line_color = color
            self.repaint()
            self.current.highlightClear()
            return

        # Polygon copy moving.
        if QtCore.Qt.RightButton & ev.buttons():
            if self.selectedShapeCopy and self.prevPoint:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShape(self.selectedShapeCopy, pos)
                self.repaint()
            elif self.selectedShape:
                self.selectedShapeCopy = self.selectedShape.copy()
                self.repaint()
            return

        # Polygon/Vertex moving.
        self.movingShape = False
        if QtCore.Qt.LeftButton & ev.buttons():
            if self.selectedVertex():
                self.boundedMoveVertex(pos)
                self.repaint()
                self.movingShape = True
            elif self.selectedShape and self.prevPoint:
                self.overrideCursor(CURSOR_MOVE)
                self.boundedMoveShape(self.selectedShape, pos)
                self.repaint()
                self.movingShape = True
            return

        # Just hovering over the canvas, 2 posibilities:
        # - Highlight shapes
        # - Highlight vertex
        # Update shape/vertex fill and tooltip value accordingly.
        self.setToolTip("Image")
        for shape in reversed([s for s in self.shapes if self.isVisible(s)]):
            # Look for a nearby vertex to highlight. If that fails,
            # check if we happen to be inside a shape.
            index = shape.nearestVertex(pos, self.epsilon)
            index_edge = shape.nearestEdge(pos, self.epsilon)
            if index is not None:
                if self.selectedVertex():
                    self.hShape.highlightClear()
                self.hVertex = index
                self.hShape = shape
                self.hEdge = index_edge
                shape.highlightVertex(index, shape.MOVE_VERTEX)
                self.overrideCursor(CURSOR_POINT)
                if self.hShape.shape_type == 'PERSONKEYPOINTS' and index > 1 and self.hShape.bodyvisible[index- 2] != 0: #关键点属性显示
                    self.setToolTip("Click & drag to move point:{}".format(keypointbodyname[index-2]))
                else:
                    self.setToolTip("Click & drag to move point")
                self.setStatusTip(self.toolTip())
                self.update()
                break
            elif shape.containsPoint(pos):
                if self.selectedVertex():
                    self.hShape.highlightClear()
                self.hVertex = None
                self.hShape = shape
                self.hEdge = index_edge
                self.setToolTip(
                    "Click & drag to move shape '%s'" % shape.label)
                self.setStatusTip(self.toolTip())
                self.overrideCursor(CURSOR_GRAB)
                self.update()
                break
        else:  # Nothing found, clear highlights, reset state.
            if self.hShape:
                self.hShape.highlightClear()
                self.update()
            self.hVertex, self.hShape, self.hEdge = None, None, None
        self.edgeSelected.emit(self.hEdge is not None)

    def addPointToEdge(self):
        if (self.hShape is None and
                self.hEdge is None and
                self.prevMovePoint is None):
            return
        shape = self.hShape
        index = self.hEdge
        point = self.prevMovePoint
        shape.insertPoint(index, point)
        shape.highlightVertex(index, shape.MOVE_VERTEX)
        self.hShape = shape
        self.hVertex = index
        self.hEdge = None
    #按下鼠标
    def mousePressEvent(self, ev):
        if QT5:
            pos = self.transformPos(ev.pos())
        else:
            pos = self.transformPos(ev.posF())
        if ev.button() == QtCore.Qt.LeftButton:
            if self.drawing():
                # if self.createMode == 'PERSONKEYPOINTS' and self.selectedPerson: #关键点状态时，已选中矩形框,初始化部分参数  #转移到前一步鼠标移动mouseMoveEvent
                #     self.current = Shape(shape_type=self.createMode)
                #     self.current.addPoint(self.selectedPerson.points[0])
                #     self.current.addPoint(self.selectedPerson.points[1])
                #     self.line.points = [pos, pos]
                #     self.setHiding()
                #     self.drawingPolygon.emit(True)
                #     self.update()
                if self.current:
                    # Add point to existing shape.
                    if self.createMode == 'POLYGON':
                        self.current.addPoint(self.line[1])
                        self.line[0] = self.current[-1]
                        if self.current.isClosed():
                            self.finalise()
                    elif self.createMode in ['RECT', 'CIRCLE', 'LINE']:
                        assert len(self.current.points) == 1
                        self.current.points = self.line.points
                        self.finalise()
                    elif self.createMode == 'KEYPOINTS':
                        self.current.addPoint(self.line[1])
                        self.line[0] = self.current[-1]
                        if int(ev.modifiers()) == QtCore.Qt.ControlModifier:
                            self.finalise()
                    elif self.createMode == 'PERSONKEYPOINTS':  #新模块 PERSONKEYPOINTS   #ls
                        if len(self.current.points) > 1 and not self.inPerson(pos) and not(int(ev.modifiers()) == QtCore.Qt.AltModifier): #不在矩形框内,异常，无标注时例外
                            self.errorMessage_ls('Invalid Point','the key point of human body is out of the person')
                            return
                        self.current.addPoint(self.line[1])
                        self.line[0] = self.current[-1]
                        if len(self.current.points) == 2 or self.selectedPerson:  #点完两点后，转换画图模式
                            self.current.paintpoint=True
                            self.current.paintrect = True
                            self.line.paintpoint=True
                            self.line.paintrect=False
                            self.deSelectPerson()  #使用完矩形框，清除数据，同时也是初始化完毕的信号
                        if len(self.current.points) > 2 :   #标注可见，不可见点操作
                            if int(ev.modifiers()) == QtCore.Qt.ControlModifier:
                                self.current.bodyvisible.append(1)  #不可见
                            # elif int(ev.modifiers()) == QtCore.Qt.AltModifier:
                            #     self.current.bodyvisible.append(0)   #无标注
                            #     self.current[-1].setX(0)
                            #     self.current[-1].setY(0)
                            else:
                                self.current.bodyvisible.append(2)  #可见
                        self.line.bodyvisible=self.current.bodyvisible
                        if len(self.current.points) == 2+len(keypointbodyname): #点完16个点结束
                            self.finalise()
                elif not self.outOfPixmap(pos):
                    # Create new shape.
                    self.current = Shape(shape_type=self.createMode)
                    self.current.addPoint(pos)
                    if self.createMode == 'POINT':                         #origin  #ls
                       self.finalise()
                    else:
                        if self.createMode == 'CIRCLE':
                            self.current.shape_type = 'CIRCLE'
                        if self.createMode =='PERSONKEYPOINTS':
                            self.line.paintrect=True    #激活画框
                            self.current.paintrect=True
                            self.line.paintpoint=False
                            self.current.paintrect=False
                        self.line.points = [pos, pos]
                        self.setHiding()
                        self.drawingPolygon.emit(True)
                        self.update()
            else:
                #print('----------LeftButton and no drawing')
                self.isLeftButtonPressed=True     #区分左右键按下信号  #ls
                self.selectShapePoint(pos)
                self.isLeftButtonPressed = False  #复原信号 #ls
                if self.editing() and self.selectedVertex() and self.hShape.shape_type == 'PERSONKEYPOINTS' and self.hVertex > 1 and self.hShape.bodyvisible != 0:
                    if int(ev.modifiers()) == QtCore.Qt.ControlModifier:#鼠标左键加ctrl键，将关键点属性转为不存在
                        self.hShape.points[self.hVertex].setX(0)
                        self.hShape.points[self.hVertex].setY(0)
                        self.hShape.bodyvisible[self.hVertex - 2]=0
                        self.storeShapes()
                        self.shapeMoved.emit()
                    elif int(ev.modifiers()) == QtCore.Qt.AltModifier:
                        self.hShape.bodyvisible[self.hVertex - 2]=1
                        self.storeShapes()
                        self.shapeMoved.emit()
                self.prevPoint = pos
                self.repaint()
        elif ev.button() == QtCore.Qt.RightButton and self.editing():
            #print('------------RightButton and editing')
            self.selectShapePoint(pos)
            self.prevPoint = pos
            self.repaint()
    #释放鼠标
    def mouseReleaseEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            menu = self.menus[bool(self.selectedShapeCopy)]
            self.restoreCursor()
            if not menu.exec_(self.mapToGlobal(ev.pos()))\
               and self.selectedShapeCopy:
                # Cancel the move by deleting the shadow copy.
                self.selectedShapeCopy = None
                self.repaint()
        elif ev.button() == QtCore.Qt.LeftButton and self.selectedShape:
            self.overrideCursor(CURSOR_GRAB)
        if self.movingShape:
            self.storeShapes()
            self.shapeMoved.emit()

    def endMove(self, copy=False):
        assert self.selectedShape and self.selectedShapeCopy
        shape = self.selectedShapeCopy
        # del shape.fill_color
        # del shape.line_color
        if copy:
            self.shapes.append(shape)
            self.selectedShape.selected = False
            self.selectedShape = shape
            self.repaint()
        else:
            shape.label = self.selectedShape.label
            self.deleteSelected()
            self.shapes.append(shape)
        self.storeShapes()
        self.selectedShapeCopy = None

    def hideBackroundShapes(self, value):
        self.hideBackround = value
        if self.selectedShape:
            # Only hide other shapes if there is a current selection.
            # Otherwise the user will not be able to select a shape.
            self.setHiding(True)
            self.repaint()

    def setHiding(self, enable=True):
        self._hideBackround = self.hideBackround if enable else False

    def canCloseShape(self):
        return self.drawing() and self.current and len(self.current) > 2

    def mouseDoubleClickEvent(self, ev):
        # We need at least 4 points here, since the mousePress handler
        # adds an extra one before this handler is called.
        if self.canCloseShape() and len(self.current) > 3 and self.current.shape_type != 'PERSONKEYPOINTS': #鼠标双击事件结束标定，此时要把新模块排除在外 #ls
            self.current.popPoint()
            self.finalise()

    def selectShape(self, shape):
        #print('selectShape')
        self.deSelectShape()#启动deSelectShape，更新，如果self.selectedShape 存在
        shape.selected = True
        self.selectedShape = shape
        self.setHiding()
        self.selectionChanged.emit(True)  #触发selectionChanged信号
        self.update()

    def selectShapePoint(self, point):
        """Select the first shape created which contains this point."""
        self.deSelectShape()#去除前一个，更新，如果self.selectedShape 存在
        if self.isLeftButtonPressed:#左键清除人物信息，右键不清除
            self.deSelectPerson() #清除旧有的人物框信息  #ls
        if self.selectedVertex():  # A vertex is marked for selection.
            index, shape = self.hVertex, self.hShape
            shape.highlightVertex(index, shape.MOVE_VERTEX)
            return
        for shape in reversed(self.shapes):
            if self.isVisible(shape) and shape.containsPoint(point):
                #print('selectShapePoint')
                shape.selected = True
                if self.isLeftButtonPressed and (shape.shape_type == 'RECT') :#and (shape.label.encode('utf-8') if PY2 else shape.label == 'person'): #左键选中矩形框时，且为目标属性时，获取保存人物框 #ls
                    #print('selectedPerson')
                    self.deSelectPerson()
                    self.line = Shape(line_color=self.lineColor)
                    self.selectedPerson=shape
                self.selectedShape = shape
                self.calculateOffsets(shape, point)
                self.setHiding()
                self.selectionChanged.emit(True)
                return

    def calculateOffsets(self, shape, point):
        rect = shape.boundingRect()
        x1 = rect.x() - point.x()
        y1 = rect.y() - point.y()
        x2 = (rect.x() + rect.width() - 1) - point.x()
        y2 = (rect.y() + rect.height() - 1) - point.y()
        self.offsets = QtCore.QPoint(x1, y1), QtCore.QPoint(x2, y2)

    def boundedMoveVertex(self, pos):
        index, shape = self.hVertex, self.hShape
        point = shape[index]
        # if self.outOfPixmap(pos):    #原代码
        #     pos = self.intersectionPoint(point, pos)
        #人体关键点超出人物框的情况  #ls
        if self.hShape.shape_type == 'PERSONKEYPOINTS' and self.hVertex > 1 and self.hShape.bodyvisible[self.hVertex - 2] != 0 and self.outofPerson(pos):
            pos=self.intersectionkeyPoint(point, pos)
        #人物框不能小于关键点范围   #ls
        elif self.hShape.shape_type == 'PERSONKEYPOINTS' and self.hVertex < 2 and self.rectInkeypoint(point,pos):
            pos = self.intersectionrect(point, pos)
        elif self.outOfPixmap(pos):#原越界条件不适合新模块PERSONKEYPOINTS  #ls
            pos = self.intersectionPoint(point, pos)
        shape.moveVertexBy(index, pos - point)

    def boundedMoveShape(self, shape, pos):
        if self.outOfPixmap(pos):
            return False  # No need to move
        o1 = pos + self.offsets[0]
        if self.outOfPixmap(o1):
            pos -= QtCore.QPoint(min(0, o1.x()), min(0, o1.y()))
        o2 = pos + self.offsets[1]
        if self.outOfPixmap(o2):
            pos += QtCore.QPoint(min(0, self.pixmap.width() - o2.x()),
                                 min(0, self.pixmap.height() - o2.y()))
        # XXX: The next line tracks the new position of the cursor
        # relative to the shape, but also results in making it
        # a bit "shaky" when nearing the border and allows it to
        # go outside of the shape's area for some reason.
        # self.calculateOffsets(self.selectedShape, pos)
        dp = pos - self.prevPoint
        if dp:
            shape.moveBy(dp)
            self.prevPoint = pos
            return True
        return False

    def deSelectPerson(self):  #删除人物  #ls
        if self.selectedPerson:
            #print('deSelectPerson')
            self.selectedPerson.selected = False
            self.selectedPerson = None

    def deSelectShape(self):
        if self.selectedShape:
            #print('deSelectShape')
            self.selectedShape.selected = False
            self.selectedShape = None
            self.setHiding(False)
            self.selectionChanged.emit(False)
            self.update()  #更新重绘窗口

    def deleteSelected(self):
        if self.selectedShape:
            shape = self.selectedShape
            self.shapes.remove(self.selectedShape)
            self.storeShapes()
            self.selectedShape = None
            self.update()
            return shape

    def copySelectedShape(self):
        if self.selectedShape:
            shape = self.selectedShape.copy()
            self.deSelectShape()
            self.shapes.append(shape)
            self.storeShapes()
            shape.selected = True
            self.selectedShape = shape
            self.boundedShiftShape(shape)
            return shape

    def boundedShiftShape(self, shape):
        # Try to move in one direction, and if it fails in another.
        # Give up if both fail.
        point = shape[0]
        offset = QtCore.QPoint(2.0, 2.0)
        self.calculateOffsets(shape, point)
        self.prevPoint = point
        if not self.boundedMoveShape(shape, point - offset):
            self.boundedMoveShape(shape, point + offset)

    def paintEvent(self, event):
        if not self.pixmap:
            return super(Canvas, self).paintEvent(event)

        p = self._painter
        p.begin(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        p.setRenderHint(QtGui.QPainter.HighQualityAntialiasing)
        p.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

        p.scale(self.scale, self.scale)
        p.translate(self.offsetToCenter())

        p.drawPixmap(0, 0, self.pixmap)
        Shape.scale = self.scale
        for shape in self.shapes:
            if (shape.selected or not self._hideBackround) and \
                    self.isVisible(shape):
                shape.fill = shape.selected or shape == self.hShape
                shape.paint(p)
        if self.current:
            self.current.paint(p)
            self.line.paint(p)
        if self.selectedShapeCopy:
            self.selectedShapeCopy.paint(p)

        if (self.fillDrawing() and self.createMode == 'POLYGON' and
                self.current is not None and len(self.current.points) >= 2):
            drawing_shape = self.current.copy()
            drawing_shape.addPoint(self.line[1])
            drawing_shape.fill = True
            drawing_shape.fill_color.setAlpha(64)
            drawing_shape.paint(p)

        p.end()

    def transformPos(self, point):
        """Convert from widget-logical coordinates to painter-logical ones."""
        return point / self.scale - self.offsetToCenter()

    def offsetToCenter(self):
        s = self.scale
        area = super(Canvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QtCore.QPoint(x, y)


    def rectInkeypoint(self,point,p):#导入待更新点和更新后的坐标判断  #ls
        xmin=self.pixmap.width()
        xmax=0
        ymin=self.pixmap.height()
        ymax=0
        w, h = self.pixmap.width(), self.pixmap.height()
        for i in range(13):#关键点外接矩形框
            if self.hShape.bodyvisible[i] != 0:
                xmin=min(self.hShape.points[i+2].x(),xmin)
                xmax=max(self.hShape.points[i+2].x(),xmax)
                ymin=min(self.hShape.points[i+2].y(),ymin)
                ymax=max(self.hShape.points[i+2].y(),ymax)

        if point.x() >= xmax:
            if p.x() < xmax:
                return 1
        elif point.x() <= xmin:
            if p.x() > xmin:
                return 1

        if point.y() >= ymax:
            if p.y() < ymax:
                return 1
        elif point.y() <= ymin:
            if p.y() > ymin:
                return 1

        return not (0 <= p.x() < w and 0 <= p.y() < h)   #超出图像边界
        #return xmin<p.x()<xmax or ymin<p.y()<ymax

    def outofPerson(self,p):#点超出人物框，编辑点的时候使用 #ls
        x1=self.hShape.points[0].x()
        y1 = self.hShape.points[0].y()
        x2 = self.hShape.points[1].x()
        y2 = self.hShape.points[1].y()
        xmin = min(x1, x2)
        xmax = max(x1, x2)
        ymin = min(y1, y2)
        ymax = max(y1, y2)
        return not(xmin<p.x()<xmax and ymin<p.y()<ymax)

    def inPerson(self,p):   #点在人物框内,标定关键点的时候使用 #ls
        x1 = self.current[0].x()
        y1 = self.current[0].y()
        x2 = self.current[1].x()
        y2 = self.current[1].y()
        xmin=min(x1,x2)
        xmax=max(x1,x2)
        ymin=min(y1,y2)
        ymax=max(y1,y2)
        return xmin<p.x()<xmax and ymin<p.y()<ymax

    def outOfPixmap(self, p):
        w, h = self.pixmap.width(), self.pixmap.height()
        return not (0 <= p.x() < w and 0 <= p.y() < h)

    def finalise(self):
        assert self.current
        self.current.close()
        self.shapes.append(self.current)
        self.storeShapes()
        self.current = None
        self.setHiding(False)
        self.newShape.emit()
        self.update()

    def closeEnough(self, p1, p2):
        # d = distance(p1 - p2)
        # m = (p1-p2).manhattanLength()
        # print "d %.2f, m %d, %.2f" % (d, m, d - m)
        return labelme.utils.distance(p1 - p2) < self.epsilon


    def intersectionrect(self,p1,p2):  #人体关键点中矩形框编辑限制  #ls
        xmin = self.pixmap.width()
        xmax = 0
        ymin = self.pixmap.height()
        ymax = 0

        w, h = self.pixmap.width(), self.pixmap.height()#使更新点坐标在点内,超出图像的移到边界上  #ls
        if p2.x() < 0:
            p2.setX(0)
        elif p2.x() >= w:
            p2.setX(w - 1)

        if p2.y() < 0:
            p2.setY(0)
        elif p2.y() >= h:
            p2.setY(h - 1)

        for i in range(13):#关键点的外接矩形框
            if self.hShape.bodyvisible[i] != 0:
                xmin = min(self.hShape.points[i + 2].x(), xmin)
                xmax = max(self.hShape.points[i + 2].x(), xmax)
                ymin = min(self.hShape.points[i + 2].y(), ymin)
                ymax = max(self.hShape.points[i + 2].y(), ymax)
        if self.hVertex == 0:
            xmin = min(self.hShape.points[1].x(), xmin)
            xmax = max(self.hShape.points[1].x(), xmax)
            ymin = min(self.hShape.points[1].y(), ymin)
            ymax = max(self.hShape.points[1].y(), ymax)
            if self.hShape.points[1].x() == xmin and p2.x() < xmax:
                p2.setX(xmax)
            if self.hShape.points[1].x() == xmax and p2.x() > xmin:
                p2.setX(xmin)
            if self.hShape.points[1].y() == ymin and p2.y() < ymax:
                p2.setY(ymax)
            if self.hShape.points[1].y() == ymax and p2.y() > ymin:
                p2.setY(ymin)
        elif self.hVertex == 1:
            xmin = min(self.hShape.points[0].x(), xmin)
            xmax = max(self.hShape.points[0].x(), xmax)
            ymin = min(self.hShape.points[0].y(), ymin)
            ymax = max(self.hShape.points[0].y(), ymax)
            if self.hShape.points[0].x() == xmin and p2.x() < xmax:
                p2.setX(xmax)
            if self.hShape.points[0].x() == xmax and p2.x() > xmin:
                p2.setX(xmin)
            if self.hShape.points[0].y() == ymin and p2.y() < ymax:
                p2.setY(ymax)
            if self.hShape.points[0].y() == ymax and p2.y() > ymin:
                p2.setY(ymin)

        return QtCore.QPoint(p2.x(), p2.y())



    def intersectionkeyPoint(self, p1, p2):  #关键点的时候异常处理  #ls
        # Cycle through each image edge in clockwise fashion,
        # and find the one intersecting the current line segment.
        # http://paulbourke.net/geometry/lineline2d/
        #人体矩形框关键点编辑
        xmin=min(self.hShape.points[0].x(),self.hShape.points[1].x())
        xmax=max(self.hShape.points[0].x(),self.hShape.points[1].x())
        ymin = min(self.hShape.points[0].y(), self.hShape.points[1].y())
        ymax = max(self.hShape.points[0].y(), self.hShape.points[1].y())
        if p2.x() > xmax:
            p2.setX(xmax)
        elif p2.x() <xmin:
            p2.setX(xmin)
        if p2.y()>ymax:
            p2.setY(ymax)
        elif p2.y()<ymin:
            p2.setY(ymin)

        return QtCore.QPoint(p2.x(), p2.y())


    def intersectionPoint(self, p1, p2):
        # Cycle through each image edge in clockwise fashion,
        # and find the one intersecting the current line segment.
        # http://paulbourke.net/geometry/lineline2d/
        size = self.pixmap.size()
        points = [(0, 0),
                  (size.width() - 1, 0),
                  (size.width() - 1, size.height() - 1),
                  (0, size.height() - 1)]
        x1, y1 = p1.x(), p1.y()
        x2, y2 = p2.x(), p2.y()
        d, i, (x, y) = min(self.intersectingEdges((x1, y1), (x2, y2), points))
        x3, y3 = points[i]
        x4, y4 = points[(i + 1) % 4]
        if (x, y) == (x1, y1):
            # Handle cases where previous point is on one of the edges.
            if x3 == x4:
                return QtCore.QPoint(x3, min(max(0, y2), max(y3, y4)))
            else:  # y3 == y4
                return QtCore.QPoint(min(max(0, x2), max(x3, x4)), y3)
        return QtCore.QPoint(x, y)

    def intersectingEdges(self, point1, point2, points):
        """Find intersecting edges.

        For each edge formed by `points', yield the intersection
        with the line segment `(x1,y1) - (x2,y2)`, if it exists.
        Also return the distance of `(x2,y2)' to the middle of the
        edge along with its index, so that the one closest can be chosen.
        """
        (x1, y1) = point1
        (x2, y2) = point2
        for i in range(4):
            x3, y3 = points[i]
            x4, y4 = points[(i + 1) % 4]
            denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
            nua = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
            nub = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)
            if denom == 0:
                # This covers two cases:
                #   nua == nub == 0: Coincident
                #   otherwise: Parallel
                continue
            ua, ub = nua / denom, nub / denom
            if 0 <= ua <= 1 and 0 <= ub <= 1:
                x = x1 + ua * (x2 - x1)
                y = y1 + ua * (y2 - y1)
                m = QtCore.QPoint((x3 + x4) / 2, (y3 + y4) / 2)
                d = labelme.utils.distance(m - QtCore.QPoint(x2, y2))
                yield d, i, (x, y)

    # These two, along with a call to adjustSize are required for the
    # scroll area.
    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.pixmap:
            return self.scale * self.pixmap.size()
        return super(Canvas, self).minimumSizeHint()

    def wheelEvent(self, ev):
        if QT5:
            mods = ev.modifiers()
            delta = ev.angleDelta()
            if QtCore.Qt.ControlModifier == int(mods):
                # with Ctrl/Command key
                # zoom
                self.zoomRequest.emit(delta.y(), ev.pos())
            else:
                # scroll
                self.scrollRequest.emit(delta.x(), QtCore.Qt.Horizontal)
                self.scrollRequest.emit(delta.y(), QtCore.Qt.Vertical)
        else:
            if ev.orientation() == QtCore.Qt.Vertical:
                mods = ev.modifiers()
                if QtCore.Qt.ControlModifier == int(mods):
                    # with Ctrl/Command key
                    self.zoomRequest.emit(ev.delta(), ev.pos())
                else:
                    self.scrollRequest.emit(
                        ev.delta(),
                        QtCore.Qt.Horizontal
                        if (QtCore.Qt.ShiftModifier == int(mods))
                        else QtCore.Qt.Vertical)
            else:
                self.scrollRequest.emit(ev.delta(), QtCore.Qt.Horizontal)
        ev.accept()

    def keyPressEvent(self, ev):
        key = ev.key()
        # if int(ev.modifiers()) == QtCore.Qt.AltModifier:
        #     print('press AltModifier')
        # if key == QtCore.Qt.Key_Alt:
        #     print('press Key_Alt')
        if key == QtCore.Qt.Key_Escape and self.current:
            self.current = None
            self.drawingPolygon.emit(False)
            self.update()
        elif key == QtCore.Qt.Key_Return and self.canCloseShape():
            self.finalise()


    def createnolabelpoint(self):
        if self.current and self.current.shape_type == 'PERSONKEYPOINTS' and self.drawing():#新模块下，按下某个键，不标注当前点
            if len(self.current) > 1:  # 添加无标定点
                if len(self.current) == 2:  # 第一个点为不可见时
                    self.current.paintpoint = True
                    self.current.paintrect = True
                    self.line.paintpoint = True
                    self.line.paintrect = False

                self.current.addPoint(QtCore.QPoint(0, 0))
                self.current.bodyvisible.append(0)  # 无标注

                self.line.bodyvisible = self.current.bodyvisible
                if len(self.current.points) == 2+len(keypointbodyname):  # 点完16个点结束，最后一个点为不可见点
                    self.finalise()
                else:
                    self.update()


    def setLastLabel(self, text):
        assert text
        self.shapes[-1].label = text
        self.shapesBackups.pop()
        self.storeShapes()
        return self.shapes[-1]

    def undoLastLine(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.setOpen()
        if self.createMode in ['POLYGON', 'KEYPOINTS']:
            self.line.points = [self.current[-1], self.current[0]]
        elif self.createMode in ['RECT', 'LINE', 'CIRCLE']:
            self.current.points = self.current.points[0:1]
        elif self.createMode == 'POINT':
            self.current = None
        elif self.createMode == 'PERSONKEYPOINTS':  #新模块的撤销操作,点撤销的同时，属性也要撤销  #ls
            self.line.points = [self.current[-1], self.current[0]]
            self.current.popPoint()
            self.current.bodyvisible.pop()
        self.drawingPolygon.emit(True)

    def undoLastPoint(self):
        if not self.current or self.current.isClosed():
            return
        self.current.popPoint()
        if self.current.bodyvisible:  #新模块的撤销操作,点撤销的同时，属性也要撤销  #ls
            self.current.bodyvisible.pop()
        if len(self.current) > 0:
            self.line[0] = self.current[-1]
        else:
            self.current = None
            self.drawingPolygon.emit(False)
        self.repaint()

    def loadPixmap(self, pixmap):
        self.pixmap = pixmap
        self.shapes = []
        self.repaint()

    def loadShapes(self, shapes):
        self.shapes = list(shapes)
        self.storeShapes()
        self.current = None
        self.repaint()

    def setShapeVisible(self, shape, value):
        self.visible[shape] = value
        self.repaint()

    def overrideCursor(self, cursor):
        self.restoreCursor()
        self._cursor = cursor
        QtWidgets.QApplication.setOverrideCursor(cursor)

    def restoreCursor(self):
        QtWidgets.QApplication.restoreOverrideCursor()

    def resetState(self):
        self.restoreCursor()
        self.pixmap = None
        self.shapesBackups = []
        self.update()
