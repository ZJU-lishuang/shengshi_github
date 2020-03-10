import functools
import io
import os
import os.path as osp
import re
import webbrowser

import PIL.Image

from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy import QtGui
from qtpy import QtWidgets

from labelme import __appname__
from labelme import PY2
from labelme import QT5

from labelme.config import get_config
from labelme.label_file import LabelFile
from labelme.label_file import LabelFileError
from labelme import logger
from labelme.shape import DEFAULT_FILL_COLOR
from labelme.shape import DEFAULT_LINE_COLOR
from labelme.shape import Shape
from labelme.utils import addActions
from labelme.utils import fmtShortcut
from labelme.utils import newAction
from labelme.utils import newIcon
from labelme.utils import struct
from labelme.widgets import Canvas
from labelme.widgets import ColorDialog
from labelme.widgets import EscapableQListWidget
from labelme.widgets import LabelDialog
from labelme.widgets import LabelQListWidget
from labelme.widgets import ToolBar
from labelme.widgets import ZoomWidget


# FIXME
# - [medium] Set max zoom value to something big enough for FitWidth/Window

# TODO(unknown):
# - [high] Add polygon movement with arrow keys
# - [high] Deselect shape when clicking and already selected(?)
# - [low,maybe] Open images with drag & drop.
# - [low,maybe] Preview images on file dialogs.
# - Zoom is too "steppy".


class WindowMixin(object):
    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        if actions:
            addActions(menu, actions)
        return menu

    def toolbar(self, title, actions=None):
        toolbar = ToolBar(title)
        toolbar.setObjectName('%sToolBar' % title)
        # toolbar.setOrientation(Qt.Vertical)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        if actions:
            addActions(toolbar, actions)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)
        return toolbar


class MainWindow(QtWidgets.QMainWindow, WindowMixin):
    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = 0, 1, 2

    def __init__(
        self,
        config=None,
        filename=None,
        output=None,
        output_file=None,
        output_dir=None,
    ):
        if output is not None:
            logger.warning(
                'argument output is deprecated, use output_file instead'
            )
            if output_file is None:
                output_file = output

        # see labelme/config/default_config.yaml for valid configuration
        if config is None:
            config = get_config()
        self._config = config

        super(MainWindow, self).__init__()
        self.setWindowTitle(__appname__)

        # Whether we need to save or not.
        self.dirty = False

        self._noSelectionSlot = False

        # Main widgets and related state.
        self.labelDialog = LabelDialog(
            parent=self,
            labels=self._config['labels'],
            sort_labels=self._config['sort_labels'],
            show_text_field=self._config['show_label_text_field'],
            completion=self._config['label_completion'],
            fit_to_content=self._config['fit_to_content'],
        )

        self.labelList = LabelQListWidget()
        self.lastOpenDir = self._config['open_dir']  #默认打开路径

        #self.lastOpenDir = None

        self.flag_dock = self.flag_widget = None
        self.flag_dock = QtWidgets.QDockWidget('Flags', self)
        self.flag_dock.setObjectName('Flags')
        self.flag_widget = QtWidgets.QListWidget()
        if config['flags']:
            self.loadFlags({k: False for k in config['flags']})
        self.flag_dock.setWidget(self.flag_widget)
        self.flag_widget.itemChanged.connect(self.setDirty)  #connect的槽机制


        self.key_flag_dock = self.key_flag_widget = None
        self.key_flag_dock = QtWidgets.QDockWidget('key_Flags', self)
        self.key_flag_dock.setObjectName('key_Flags')
        self.key_flag_widget = QtWidgets.QListWidget()
        if config['keyflags']:
            self.loadkeyFlags({k: False for k in config['keyflags']})
        #self.key_flag_widget.itemSelectionChanged.connect(self.keyflagSelectionChanged)
        self.key_flag_dock.setWidget(self.key_flag_widget)
        self.key_flag_widget.itemChanged.connect(self.keyflagChanged)
        self.key_flag_widget.itemChanged.connect(self.setDirty)  #connect的槽机制

        self.labelList.itemActivated.connect(self.labelSelectionChanged)
        self.labelList.itemSelectionChanged.connect(self.labelSelectionChanged)
        self.labelList.itemDoubleClicked.connect(self.editLabel)
        # Connect to itemChanged to detect checkbox changes.
        self.labelList.itemChanged.connect(self.labelItemChanged)
        self.labelList.setDragDropMode(
            QtWidgets.QAbstractItemView.InternalMove)
        self.labelList.setParent(self)
        self.shape_dock = QtWidgets.QDockWidget('Polygon Labels', self)
        self.shape_dock.setObjectName('Labels')
        self.shape_dock.setWidget(self.labelList)

        self.uniqLabelList = EscapableQListWidget()
        self.uniqLabelList.setToolTip(
            "Select label to start annotating for it. "
            "Press 'Esc' to deselect.")
        if self._config['labels']:
            self.uniqLabelList.addItems(self._config['labels'])
            self.uniqLabelList.sortItems()
        self.label_dock = QtWidgets.QDockWidget(u'Label List', self)
        self.label_dock.setObjectName(u'Label List')
        self.label_dock.setWidget(self.uniqLabelList)

        self.fileSearch = QtWidgets.QLineEdit()
        self.fileSearch.setPlaceholderText('Search Filename')
        self.fileSearch.textChanged.connect(self.fileSearchChanged)
        self.fileListWidget = QtWidgets.QListWidget()
        self.fileListWidget.itemSelectionChanged.connect(
            self.fileSelectionChanged
        )
        fileListLayout = QtWidgets.QVBoxLayout()
        fileListLayout.setContentsMargins(0, 0, 0, 0)
        fileListLayout.setSpacing(0)
        fileListLayout.addWidget(self.fileSearch)
        fileListLayout.addWidget(self.fileListWidget)
        self.file_dock = QtWidgets.QDockWidget(u'File List', self)
        self.file_dock.setObjectName(u'Files')
        fileListWidget = QtWidgets.QWidget()
        fileListWidget.setLayout(fileListLayout)
        self.file_dock.setWidget(fileListWidget)

        self.zoomWidget = ZoomWidget()
        self.colorDialog = ColorDialog(parent=self)

        self.canvas = self.labelList.canvas = Canvas(
            epsilon=self._config['epsilon'],
        )
        self.canvas.zoomRequest.connect(self.zoomRequest)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidget(self.canvas)
        scrollArea.setWidgetResizable(True)
        self.scrollBars = {
            Qt.Vertical: scrollArea.verticalScrollBar(),
            Qt.Horizontal: scrollArea.horizontalScrollBar(),
        }
        self.canvas.scrollRequest.connect(self.scrollRequest)

        self.canvas.newShape.connect(self.newShape)
        self.canvas.shapeMoved.connect(self.setDirty)
        self.canvas.selectionChanged.connect(self.shapeSelectionChanged)  #selectionChanged触发shapeSelectionChanged操作
        self.canvas.drawingPolygon.connect(self.toggleDrawingSensitive)

        self.setCentralWidget(scrollArea)

        features = QtWidgets.QDockWidget.DockWidgetFeatures()
        for dock in ['key_flag_dock','flag_dock', 'label_dock', 'shape_dock', 'file_dock']:
            if self._config[dock]['closable']:
                features = features | QtWidgets.QDockWidget.DockWidgetClosable
            if self._config[dock]['floatable']:
                features = features | QtWidgets.QDockWidget.DockWidgetFloatable
            if self._config[dock]['movable']:
                features = features | QtWidgets.QDockWidget.DockWidgetMovable
            getattr(self, dock).setFeatures(features)
            if self._config[dock]['show'] is False:
                getattr(self, dock).setVisible(False)

        self.addDockWidget(Qt.RightDockWidgetArea, self.key_flag_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.flag_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.label_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.shape_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.file_dock)

        # Actions
        #操作
        action = functools.partial(newAction, self)
        shortcuts = self._config['shortcuts']
        quit = action('&Quit', self.close, shortcuts['quit'], 'quit',
                      'Quit application')
        open_ = action('&Open', self.openFile, shortcuts['open'], 'open',
                       'Open image or label file')
        opendir = action('&Open Dir', self.openDirDialog,
                         shortcuts['open_dir'], 'open', u'Open Dir')
        openNextImg = action(
            '&Next Image',
            self.openNextImg,
            shortcuts['open_next'],
            'next',
            u'Open next (hold Ctl+Shift to copy labels)',
            enabled=False,
        )
        openPrevImg = action(
            '&Prev Image',
            self.openPrevImg,
            shortcuts['open_prev'],
            'prev',
            u'Open prev (hold Ctl+Shift to copy labels)',
            enabled=False,
        )
        save = action('&Save', self.saveFile, shortcuts['save'], 'save',
                      'Save labels to file', enabled=False)
        saveAs = action('&Save As', self.saveFileAs, shortcuts['save_as'],
                        'save-as', 'Save labels to a different file',
                        enabled=False)
        changeOutputDir = action(
            '&Change Output Dir',
            slot=self.changeOutputDirDialog,
            shortcut=shortcuts['save_to'],
            icon='open',
            tip=u'Change where annotations are loaded/saved'
        )

        saveAuto = action(
            text='Save &Automatically',
            slot=lambda x: self.actions.saveAuto.setChecked(x),
            icon='save',
            tip='Save automatically',
            checkable=True,
            enabled=True,
        )
        saveAuto.setChecked(self._config['auto_save'])

        close = action('&Close', self.closeFile, shortcuts['close'], 'close',
                       'Close current file')
        color1 = action('Polygon &Line Color', self.chooseColor1,
                        shortcuts['edit_line_color'], 'color_line',
                        'Choose polygon line color')
        color2 = action('Polygon &Fill Color', self.chooseColor2,
                        shortcuts['edit_fill_color'], 'color',
                        'Choose polygon fill color')

        toggle_keep_prev_mode = action(
            'Keep Previous Annotation',
            self.toggleKeepPrevMode,
            shortcuts['toggle_keep_prev_mode'], None,
            'Toggle "keep pevious annotation" mode',
            checkable=True)
        toggle_keep_prev_mode.setChecked(self._config['keep_prev'])

        createMode = action(
            'Create Polygons',
            lambda: self.toggleDrawMode(False, createMode='POLYGON'),
            shortcuts['create_polygon'],
            'objects',
            'Start drawing polygons',
            enabled=False,
        )
        createRectangleMode = action(
            'Create Rectangle',
            lambda: self.toggleDrawMode(False, createMode='RECT'),
            shortcuts['create_rectangle'],
            'objects',
            'Start drawing rectangles',
            enabled=False,
        )
        createCircleMode = action(
            'Create Circle',
            lambda: self.toggleDrawMode(False, createMode='CIRCLE'),
            shortcuts['create_circle'],
            'objects',
            'Start drawing circles',
            enabled=False,
        )
        createLineMode = action(
            'Create Line',
            lambda: self.toggleDrawMode(False, createMode='LINE'),
            shortcuts['create_line'],
            'objects',
            'Start drawing lines',
            enabled=False,
        )
        createPointMode = action(
            'Create Point',
            lambda: self.toggleDrawMode(False, createMode='POINT'),
            shortcuts['create_point'],
            'objects',
            'Start drawing points',
            enabled=False,
        )
        createPersonKeyPointMode = action(
            'Create Person KeyPoint',
            lambda: self.toggleDrawMode(False, createMode='PERSONKEYPOINTS'),
            shortcuts['create_personkeypoint'],
            'objects',
            'Start drawing personkeypoints',
            enabled=False,
        )
        createLineStripMode = action(
            'Create LineStrip(KEYPOINTS)',
            lambda: self.toggleDrawMode(False, createMode='KEYPOINTS'),
            shortcuts['create_linestrip_KEYPOINTS'],
            'objects',
            'Start drawing linestrip(KEYPOINTS). Ctrl+LeftClick ends creation.',
            enabled=False,
        )
        editMode = action('Edit Polygons', self.setEditMode,
                          shortcuts['edit_polygon'], 'edit',
                          'Move and edit polygons', enabled=False)

        delete = action('Delete Polygon', self.deleteSelectedShape,
                        shortcuts['delete_polygon'], 'cancel',
                        'Delete', enabled=False)
        copy = action('Duplicate Polygon', self.copySelectedShape,
                      shortcuts['duplicate_polygon'], 'copy',
                      'Create a duplicate of the selected polygon',
                      enabled=False)
        undoLastPoint = action('Undo last point', self.canvas.undoLastPoint,
                               shortcuts['undo_last_point'], 'undo',
                               'Undo last drawn point', enabled=False)
        createnolabelpoint = action('Create a No Label Key Point', self.canvas.createnolabelpoint,
                               shortcuts['no_label_point'], 'color-line',
                               'Create no label point', enabled=False)
        addPoint = action('Add Point to Edge', self.canvas.addPointToEdge,
                          None, 'edit', 'Add point to the nearest edge',
                          enabled=False)

        undo = action('Undo', self.undoShapeEdit, shortcuts['undo'], 'undo',
                      'Undo last add and edit of shape', enabled=False)

        hideAll = action('&Hide\nPolygons',
                         functools.partial(self.togglePolygons, False),
                         icon='eye', tip='Hide all polygons', enabled=False)
        showAll = action('&Show\nPolygons',
                         functools.partial(self.togglePolygons, True),
                         icon='eye', tip='Show all polygons', enabled=False)

        help = action('&Tutorial', self.tutorial, icon='help',
                      tip='Show tutorial page')
        #缩放操作
        zoom = QtWidgets.QWidgetAction(self)
        zoom.setDefaultWidget(self.zoomWidget)
        self.zoomWidget.setWhatsThis(
            "Zoom in or out of the image. Also accessible with"
            " %s and %s from the canvas." %
            (fmtShortcut('%s,%s' % (shortcuts['zoom_in'],
                                    shortcuts['zoom_out'])),
             fmtShortcut("Ctrl+Wheel")))
        self.zoomWidget.setEnabled(False)

        zoomIn = action('Zoom &In', functools.partial(self.addZoom, 10),
                        shortcuts['zoom_in'], 'zoom-in',
                        'Increase zoom level', enabled=False)
        zoomOut = action('&Zoom Out', functools.partial(self.addZoom, -10),
                         shortcuts['zoom_out'], 'zoom-out',
                         'Decrease zoom level', enabled=False)
        zoomOrg = action('&Original size',
                         functools.partial(self.setZoom, 100),
                         shortcuts['zoom_to_original'], 'zoom',
                         'Zoom to original size', enabled=False)
        fitWindow = action('&Fit Window', self.setFitWindow,
                           shortcuts['fit_window'], 'fit-window',
                           'Zoom follows window size', checkable=True,
                           enabled=False)
        fitWidth = action('Fit &Width', self.setFitWidth,
                          shortcuts['fit_width'], 'fit-width',
                          'Zoom follows window width',
                          checkable=True, enabled=False)
        # Group zoom controls into a list for easier toggling.
        #放进zoomActions这个元组里面
        zoomActions = (self.zoomWidget, zoomIn, zoomOut, zoomOrg,
                       fitWindow, fitWidth)
        self.zoomMode = self.FIT_WINDOW
        fitWindow.setChecked(Qt.Checked)
        self.scalers = {
            self.FIT_WINDOW: self.scaleFitWindow,
            self.FIT_WIDTH: self.scaleFitWidth,
            # Set to one to scale to 100% when loading files.
            self.MANUAL_ZOOM: lambda: 1,
        }

        edit = action('&Edit Label', self.editLabel, shortcuts['edit_label'],
                      'edit', 'Modify the label of the selected polygon',
                      enabled=False)

        #TODO:编辑的时候改变对应关键点的属性，可见，不可见，不存在，删除四个功能
        visible=action('&visible Label（Unfinished）', self.editLabel, #shortcuts['visible_label'],
                      icon='edit', tip='Modify the label to visible',
                      enabled=False)

        invisible=action('&invisible Label（Unfinished）', self.editLabel, #shortcuts['invisible_label'],
                      icon='edit', tip='Modify the label to invisible',
                      enabled=False)
        
        inexistent=action('&inexistent Label（Unfinished）', self.editLabel, #shortcuts['inexistent_label'],
                      icon='edit', tip='Modify the label to inexistent',
                      enabled=False)


        shapeLineColor = action(
            'Shape &Line Color', self.chshapeLineColor, icon='color-line',
            tip='Change the line color for this specific shape', enabled=False)
        shapeFillColor = action(
            'Shape &Fill Color', self.chshapeFillColor, icon='color',
            tip='Change the fill color for this specific shape', enabled=False)
        fill_drawing = action(
            'Fill Drawing Polygon',
            lambda x: self.canvas.setFillDrawing(x),
            None,
            'color',
            'Fill polygon while drawing',
            checkable=True,
            enabled=True,
        )
        fill_drawing.setChecked(True)  #pyqt中用setChecked设置状态

        # Lavel list context menu.
        labelMenu = QtWidgets.QMenu()
        addActions(labelMenu, (edit, delete))
        self.labelList.setContextMenuPolicy(Qt.CustomContextMenu)  #设置右键属性
        self.labelList.customContextMenuRequested.connect(
            self.popLabelListMenu)
        
        keylabelMenu = QtWidgets.QMenu()
        addActions(keylabelMenu, (visible,invisible,inexistent))
        self.key_flag_dock.setContextMenuPolicy(Qt.CustomContextMenu) 
        self.key_flag_dock.customContextMenuRequested.connect(
            self.popkey_flag_dockMenu)

        # Store actions for further handling.
        self.actions = struct(
            saveAuto=saveAuto,
            changeOutputDir=changeOutputDir,
            save=save, saveAs=saveAs, open=open_, close=close,
            lineColor=color1, fillColor=color2,
            toggleKeepPrevMode=toggle_keep_prev_mode,
            delete=delete, edit=edit, copy=copy,
            undoLastPoint=undoLastPoint, undo=undo,
            createnolabelpoint=createnolabelpoint,
            addPoint=addPoint,
            createMode=createMode, editMode=editMode,
            createRectangleMode=createRectangleMode,
            createCircleMode=createCircleMode,
            createLineMode=createLineMode,
            createPointMode=createPointMode,
            createPersonKeyPointMode=createPersonKeyPointMode,
            createLineStripMode=createLineStripMode,
            shapeLineColor=shapeLineColor, shapeFillColor=shapeFillColor,
            zoom=zoom, zoomIn=zoomIn, zoomOut=zoomOut, zoomOrg=zoomOrg,
            fitWindow=fitWindow, fitWidth=fitWidth,
            zoomActions=zoomActions,
            openNextImg=openNextImg, openPrevImg=openPrevImg,
            fileMenuActions=(open_, opendir, save, saveAs, close, quit),
            tool=(),
            editMenu=(edit, copy, delete, None, undo, undoLastPoint,createnolabelpoint,
                      None, color1, color2, None, toggle_keep_prev_mode),
            # menu shown at right click
            #右键菜单
            menu=(
                createMode,
                createRectangleMode,
                createCircleMode,
                createLineMode,
                createPointMode,
                createPersonKeyPointMode,
                createLineStripMode,
                editMode,
                edit,
                copy,
                delete,
                shapeLineColor,
                shapeFillColor,
                undo,
                addPoint,
            ),
            onLoadActive=(
                close,
                createMode,
                createRectangleMode,
                createCircleMode,
                createLineMode,
                createPointMode,
                createPersonKeyPointMode,
                createLineStripMode,
                editMode,
            ),
            onShapesPresent=(saveAs, hideAll, showAll),
        )

        self.canvas.edgeSelected.connect(self.actions.addPoint.setEnabled)
        #顶部菜单栏
        self.menus = struct(
            file=self.menu('&File'),
            edit=self.menu('&Edit'),
            view=self.menu('&View'),
            help=self.menu('&Help'),
            recentFiles=QtWidgets.QMenu('Open &Recent'),
            labelList=labelMenu,
            key_flag_dock=keylabelMenu,
        )

        addActions(self.menus.file, (open_, openNextImg, openPrevImg, opendir,
                                     self.menus.recentFiles,
                                     save, saveAs, saveAuto, changeOutputDir,
                                     close,
                                     None,
                                     quit))
        addActions(self.menus.help, (help,))
        addActions(self.menus.view, (
            self.key_flag_dock.toggleViewAction(),
            self.flag_dock.toggleViewAction(),
            self.label_dock.toggleViewAction(),
            self.shape_dock.toggleViewAction(),
            self.file_dock.toggleViewAction(),
            None,
            fill_drawing,
            None,
            hideAll,
            showAll,
            None,
            zoomIn,
            zoomOut,
            zoomOrg,
            None,
            fitWindow,
            fitWidth,
            None,
        ))

        self.menus.file.aboutToShow.connect(self.updateFileMenu)

        # Custom context menu for the canvas widget:
        addActions(self.canvas.menus[0], self.actions.menu)
        addActions(self.canvas.menus[1], (
            action('&Copy here', self.copyShape),
            action('&Move here', self.moveShape)))

        self.tools = self.toolbar('Tools')
        # Menu buttons on Left
        #左边的菜单栏
        self.actions.tool = (
           # open_,
            opendir,
            changeOutputDir,
            openNextImg,
            openPrevImg,
            save,
            None,
            createMode,
            createRectangleMode,
            createPersonKeyPointMode,
            editMode,
            copy,
            delete,
            undo,
            createnolabelpoint,
            None,
            zoomIn,
            zoom,
            zoomOut,
            fitWindow,
            fitWidth,
        )

        self.statusBar().showMessage('%s started.' % __appname__)
        self.statusBar().show()

        if output_file is not None and self._config['auto_save']:
            logger.warn(
                'If `auto_save` argument is True, `output_file` argument '
                'is ignored and output filename is automatically '
                'set as IMAGE_BASENAME.json.'
            )
        self.output_file = output_file
        self.output_dir = self._config['output_dir']  #保存路径
        if output_dir != None:
            self.output_dir = output_dir

        # Application state.
        self.image = QtGui.QImage()
        self.imagePath = None
        self.recentFiles = []
        self.maxRecent = 7
        self.lineColor = None
        self.fillColor = None
        self.otherData = None
        self.zoom_level = 100
        self.fit_window = False

        if filename is not None and osp.isdir(filename):
            self.importDirImages(filename, load=False)
        elif self.lastOpenDir and osp.exists(self.lastOpenDir):  #ls
            self.importDirImages(self.lastOpenDir, load=False)
            self.filename = self._config['open_imagename']
            self.filename = osp.join(self.lastOpenDir, self.filename)
        else:
            self.filename = filename



        if config['file_search']:
            self.fileSearch.setText(config['file_search'])
            self.fileSearchChanged()

        # XXX: Could be completely declarative.
        # Restore application settings.
        #保存程序设置
        self.settings = QtCore.QSettings('labelme', 'labelme')
        # FIXME: QSettings.value can return None on PyQt4
        self.recentFiles = self.settings.value('recentFiles', []) or []
        size = self.settings.value('window/size', QtCore.QSize(600, 500))
        position = self.settings.value('window/position', QtCore.QPoint(0, 0))
        self.resize(size)
        self.move(position)
        # or simply:
        # self.restoreGeometry(settings['window/geometry']
        self.restoreState(
            self.settings.value('window/state', QtCore.QByteArray()))
        self.lineColor = QtGui.QColor(
            self.settings.value('line/color', Shape.line_color))
        self.fillColor = QtGui.QColor(
            self.settings.value('fill/color', Shape.fill_color))
        Shape.line_color = self.lineColor
        Shape.fill_color = self.fillColor

        # Populate the File menu dynamically.
        self.updateFileMenu()
        # Since loading the file may take some time,
        # make sure it runs in the background.
        if self.filename is not None:
            self.queueEvent(functools.partial(self.loadFile, self.filename))

        # Callbacks:
        self.zoomWidget.valueChanged.connect(self.paintCanvas)

        self.populateModeActions()

        # self.firstStart = True
        # if self.firstStart:
        #    QWhatsThis.enterWhatsThisMode()

    # Support Functions
    #判断是否有itemsToShapes
    def noShapes(self):
        return not self.labelList.itemsToShapes
    #编辑选项菜单，在里面添加功能
    def populateModeActions(self):
        tool, menu = self.actions.tool, self.actions.menu
        self.tools.clear()
        addActions(self.tools, tool)
        self.canvas.menus[0].clear()
        addActions(self.canvas.menus[0], menu)
        self.menus.edit.clear()
        actions = (
            self.actions.createMode,
            self.actions.createRectangleMode,
            self.actions.createCircleMode,
            self.actions.createLineMode,
            self.actions.createPointMode,
            self.actions.createPersonKeyPointMode,
            self.actions.createLineStripMode,
            self.actions.editMode,
        )
        addActions(self.menus.edit, actions + self.actions.editMenu)
    #编辑，更改时
    def setDirty(self):
        if self._config['auto_save'] or self.actions.saveAuto.isChecked():
            label_file = osp.splitext(self.imagePath)[0] + '.json'
            basename = os.path.basename(self.imagePath)
            basename = osp.splitext(basename)[0]
            if self.output_dir:
                label_file = osp.join(
                    self.output_dir, basename + LabelFile.suffix
                )
            # if self.output_dir:
            #     label_file = osp.join(self.output_dir, label_file)
            self.saveLabels(label_file)
            return
        self.dirty = True
        self.actions.save.setEnabled(True)
        self.actions.undo.setEnabled(self.canvas.isShapeRestorable)

        title = __appname__
        if self.filename is not None:
            title = '{} - {}*'.format(title, self.filename)
        self.setWindowTitle(title)
    #新建
    def setClean(self):
        self.dirty = False
        self.actions.save.setEnabled(False)
        self.actions.createMode.setEnabled(True)
        self.actions.createRectangleMode.setEnabled(True)
        self.actions.createCircleMode.setEnabled(True)
        self.actions.createLineMode.setEnabled(True)
        self.actions.createPointMode.setEnabled(True)
        self.actions.createPersonKeyPointMode.setEnabled(True)
        self.actions.createLineStripMode.setEnabled(True)
        title = __appname__
        if self.filename is not None:
            title = '{} - {}'.format(title, self.filename)
        self.setWindowTitle(title)
    #设置某些功能是否可用
    def toggleActions(self, value=True):
        """Enable/Disable widgets which depend on an opened image."""
        for z in self.actions.zoomActions:
            z.setEnabled(value)
        for action in self.actions.onLoadActive:
            action.setEnabled(value)
    #触发一次函数，无延时（一张一张读取图片）
    def queueEvent(self, function):
        QtCore.QTimer.singleShot(0, function)
    #显示临时信息，时间默认5秒钟.
    def status(self, message, delay=5000):
        self.statusBar().showMessage(message, delay)

    def resetState(self):
        self.labelList.clear()
        self.filename = None
        self.imagePath = None
        self.imageData = None
        self.labelFile = None
        self.otherData = None
        self.canvas.resetState()
    #取出当前图片
    def currentItem(self):
        items = self.labelList.selectedItems()  #selectedItems() → List[QListWidgetItem]
        if items:
            return items[0]
        return None
    #最近打开的文档痕迹open recent
    def addRecentFile(self, filename):
        if filename in self.recentFiles:
            self.recentFiles.remove(filename)
        elif len(self.recentFiles) >= self.maxRecent:
            self.recentFiles.pop()
        self.recentFiles.insert(0, filename)

    # Callbacks

    def undoShapeEdit(self):
        self.canvas.restoreShape()
        self.labelList.clear()
        self.loadShapes(self.canvas.shapes)
        self.actions.undo.setEnabled(self.canvas.isShapeRestorable)

    def tutorial(self):
        url = 'https://github.com/wkentaro/labelme/tree/master/examples/tutorial'  # NOQA
        webbrowser.open(url)
    # no use
    def toggleAddPointEnabled(self, enabled):
        self.actions.addPoint.setEnabled(enabled)
    #画图时禁用一些功能，防止发生异常
    def toggleDrawingSensitive(self, drawing=True):
        """Toggle drawing sensitive.

        In the middle of drawing, toggling between modes should be disabled.
        """
        self.actions.editMode.setEnabled(not drawing)
        self.actions.undoLastPoint.setEnabled(drawing)
        self.actions.createnolabelpoint.setEnabled(drawing)
        self.actions.undo.setEnabled(not drawing)
        self.actions.delete.setEnabled(not drawing)
    #画图模式切换
    def toggleDrawMode(self, edit=True, createMode='POLYGON'):
        self.canvas.setEditing(edit)
        self.canvas.createMode = createMode
        if edit:
            self.actions.createMode.setEnabled(True)
            self.actions.createRectangleMode.setEnabled(True)
            self.actions.createCircleMode.setEnabled(True)
            self.actions.createLineMode.setEnabled(True)
            self.actions.createPointMode.setEnabled(True)
            self.actions.createPersonKeyPointMode.setEnabled(True)
            self.actions.createLineStripMode.setEnabled(True)
        else:
            if createMode == 'POLYGON':
                self.actions.createMode.setEnabled(False)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createPersonKeyPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)
            elif createMode == 'RECT':
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(False)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createPersonKeyPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)
            elif createMode == 'LINE':
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(False)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createPersonKeyPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)
            elif createMode == 'POINT':
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(False)
                self.actions.createPersonKeyPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)
            elif createMode == 'CIRCLE':
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(False)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createPersonKeyPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(True)
            elif createMode == 'KEYPOINTS':
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createPersonKeyPointMode.setEnabled(True)
                self.actions.createLineStripMode.setEnabled(False)
            elif createMode == 'PERSONKEYPOINTS':
                self.actions.createMode.setEnabled(True)
                self.actions.createRectangleMode.setEnabled(True)
                self.actions.createCircleMode.setEnabled(True)
                self.actions.createLineMode.setEnabled(True)
                self.actions.createPointMode.setEnabled(True)
                self.actions.createPersonKeyPointMode.setEnabled(False)
                self.actions.createLineStripMode.setEnabled(True)
            else:
                raise ValueError('Unsupported createMode: %s' % createMode)
        self.actions.editMode.setEnabled(not edit)
    #设置默认的画图模式
    def setEditMode(self):
        self.toggleDrawMode(True)
    #更新open recent里面文件目录
    def updateFileMenu(self):
        current = self.filename

        def exists(filename):
            return osp.exists(str(filename))

        menu = self.menus.recentFiles
        menu.clear()
        files = [f for f in self.recentFiles if f != current and exists(f)]
        for i, f in enumerate(files):
            icon = newIcon('labels')  #图标
            action = QtWidgets.QAction(
                icon, '&%d %s' % (i + 1, QtCore.QFileInfo(f).fileName()), self)
            action.triggered.connect(functools.partial(self.loadRecent, f))
            menu.addAction(action)
    #右键点击，修改或删除存在的标签
    def popLabelListMenu(self, point):
        self.menus.labelList.exec_(self.labelList.mapToGlobal(point))   #pWidget->mapToGlobal(QPoint(0,0)) ;将当前控件的相对位置转换为屏幕绝对位置

    def popkey_flag_dockMenu(self, point):
        self.menus.key_flag_dock.exec_(self.key_flag_dock.mapToGlobal(point))   #pWidget->mapToGlobal(QPoint(0,0)) ;将当前控件的相对位置转换为屏幕绝对位置
    #设置验证标签（可锁死可选标签,不增加新标签）
    def validateLabel(self, label):
        # no validation
        if self._config['validate_label'] is None:
            return True

        for i in range(self.uniqLabelList.count()):
            label_i = self.uniqLabelList.item(i).text()
            if self._config['validate_label'] in ['exact', 'instance']:
                if label_i == label:
                    return True
            if self._config['validate_label'] == 'instance':
                m = re.match(r'^{}-[0-9]*$'.format(label_i), label)
                if m:
                    return True
        return False
    #编辑标签
    def editLabel(self, item=None):
        if not self.canvas.editing():
            return
        item = item if item else self.currentItem()
        text = self.labelDialog.popUp(item.text())
        if text is None:
            return
        if not self.validateLabel(text):  #锁死label
            self.errorMessage('Invalid label',
                              "Invalid label '{}' with validation type '{}'"
                              .format(text, self._config['validate_label']))
            return
        item.setText(text)
        self.setDirty()
        if not self.uniqLabelList.findItems(text, Qt.MatchExactly):  #添加label
            self.uniqLabelList.addItem(text)
            self.uniqLabelList.sortItems()
    #路径改变，重新加载路径下图片
    def fileSearchChanged(self):
        self.importDirImages(
            self.lastOpenDir,
            pattern=self.fileSearch.text(),
            load=False,
        )
    #选择文件改变,加载关联
    def fileSelectionChanged(self):
        items = self.fileListWidget.selectedItems()
        if not items:
            return
        item = items[0]

        if not self.mayContinue():
            return

        currIndex = self.imageList.index(str(item.text()))
        if currIndex < len(self.imageList):
            filename = self.imageList[currIndex]

            # yaml #ls
            print (os.getcwd())
            config_file = osp.join('config', 'default_config.yaml')
            config_file='/home/lishuang/Disk/shengshi_github/code/labelme_nightly/labelme/config/default_config.yaml'
            file_data = ""
            with open(config_file) as f:
                for line in f:
                    if 'open_imagename: "' in line:
                        # line=line.replace(defaultOpenDirPath,targetDirPath)
                        line = line[:17] + osp.basename(filename) + line[-2:]
                    file_data += line
            with open(config_file, "w") as f:
                f.write(file_data)

            if filename:
                self.loadFile(filename)

    # React to canvas signals.
    #标定改变，加载关联项
    def shapeSelectionChanged(self, selected=False):
        #print('shapeSelectionChanged')
        if self._noSelectionSlot:
            self._noSelectionSlot = False
        else:
            shape = self.canvas.selectedShape
            if shape:
                #print('    shapeSelectionChanged:shape.shape_type=',shape.shape_type)
                #if shape.shape_type == 'RECT' and shape.label.encode('utf-8') if PY2 else shape.label == 'person':
                #    print('---------------yes-------------')
                item = self.labelList.get_item_from_shape(shape)
                item.setSelected(True) #item激活  self.labelList.itemActivated
            else:
                self.labelList.clearSelection()
        self.actions.delete.setEnabled(selected)
        self.actions.copy.setEnabled(selected)
        self.actions.edit.setEnabled(selected)
        self.actions.shapeLineColor.setEnabled(selected)
        self.actions.shapeFillColor.setEnabled(selected)

    def addLabel(self, shape):
        item = QtWidgets.QListWidgetItem(shape.label)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked)
        self.labelList.itemsToShapes.append((item, shape))
        self.labelList.addItem(item)
        if not self.uniqLabelList.findItems(shape.label, Qt.MatchExactly):
            self.uniqLabelList.addItem(shape.label)
            self.uniqLabelList.sortItems()
        self.labelDialog.addLabelHistory(item.text())
        for action in self.actions.onShapesPresent:
            action.setEnabled(True)

    def remLabel(self, shape):
        item = self.labelList.get_item_from_shape(shape)
        self.labelList.takeItem(self.labelList.row(item))   # takeItem  删除item

    def loadShapes(self, shapes):
        for shape in shapes:
            self.addLabel(shape)
        self.canvas.loadShapes(shapes)

    def loadLabels(self, shapes):
        s = []
        for label, points, line_color, fill_color, shape_type in shapes:
            shape = Shape(label=label, shape_type=shape_type)
            if shape_type == 'PERSONKEYPOINTS':   #新模块加载标签 #ls
                for i,p in enumerate(points):
                    if i < 2:
                        shape.addPoint(QtCore.QPoint(p[0], p[1]))
                    else:
                        shape.addPoint(QtCore.QPoint(p[0], p[1]))
                        shape.bodyvisible.append(p[2])
            else:
                for x, y in points:
                    shape.addPoint(QtCore.QPoint(x, y))
            shape.close()
            s.append(shape)
            if line_color:
                shape.line_color = QtGui.QColor(*line_color)
            if fill_color:
                shape.fill_color = QtGui.QColor(*fill_color)
        self.loadShapes(s)

    
    def loadkeyFlags(self, flags):
        self.key_flag_widget.clear()
        for key, flag in flags.items():
            item = QtWidgets.QListWidgetItem(key)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if flag else Qt.Unchecked)
            self.key_flag_widget.addItem(item)

    def loadFlags(self, flags):
        self.flag_widget.clear()
        for key, flag in flags.items():
            item = QtWidgets.QListWidgetItem(key)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if flag else Qt.Unchecked)
            self.flag_widget.addItem(item)
    #保存格式，添加时间和用户名
    def saveLabels(self, filename):
        lf = LabelFile(output_dir = self.output_dir)

        def format_shape(s):
            import getpass
            import time
            if s.shape_type == "POLYGON":
                return dict(
                    label=s.label.encode('utf-8') if PY2 else s.label,
                    line_color=s.line_color.getRgb()
                    if s.line_color != self.lineColor else None,
                    fill_color=s.fill_color.getRgb()
                    if s.fill_color != self.fillColor else None,
                    polygon=[(p.x(), p.y()) for p in s.points],
                    shape_type=s.shape_type,
                    draw=True,
                    user= getpass.getuser(),
                    date=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                )
            elif s.shape_type == "RECT":
                return dict(
                    label=s.label.encode('utf-8') if PY2 else s.label,
                    line_color=s.line_color.getRgb()
                    if s.line_color != self.lineColor else None,
                    fill_color=s.fill_color.getRgb()
                    if s.fill_color != self.fillColor else None,
                    bbox=[(p.x(), p.y()) for p in s.points],
                    shape_type=s.shape_type,
                    draw=True,
                    user= getpass.getuser(),
                    date=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                )
            elif s.shape_type == "KEYPOINTS":
                return dict(
                    label=s.label.encode('utf-8') if PY2 else s.label,
                    line_color=s.line_color.getRgb()
                    if s.line_color != self.lineColor else None,
                    fill_color=s.fill_color.getRgb()
                    if s.fill_color != self.fillColor else None,
                    keypoints=[(p.x(), p.y()) for p in s.points],
                    shape_type=s.shape_type,
                    draw=True,
                    user= getpass.getuser(),
                    date=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                )
            elif s.shape_type == "PERSONKEYPOINTS":
                tmpkeypoints=[]  #关键点存储格式 #ls

                for i,p in enumerate(s.points):
                    if i>1:
                        if s.bodyvisible[i-2] == 0:#存储时，属性为无标定的关键点坐标归零
                            tmpkeypoints.append((0, 0,s.bodyvisible[i-2]))
                        else:
                            tmpkeypoints.append((p.x(), p.y(),s.bodyvisible[i-2]))
                    else:
                        tmpkeypoints.append((p.x(), p.y()))
                return dict(
                    label=s.label.encode('utf-8') if PY2 else s.label,
                    line_color=s.line_color.getRgb()
                    if s.line_color != self.lineColor else None,
                    fill_color=s.fill_color.getRgb()
                    if s.fill_color != self.fillColor else None,
                    keypoints=tmpkeypoints,
                    #keypoints=[(p.x(), p.y(),s.bodyvisible[i-2]) for i,p in enumerate(s.points) if i > 1 ],
                    #keypoints=[(p.x(), p.y()) for i,p in enumerate(s.points) if i < 2 (p.x(), p.y(),s.bodyvisible[i]) for i,p in enumerate(s.points) if i > 2],
                    shape_type=s.shape_type,
                    draw=True,
                    user= getpass.getuser(),
                    date=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                )
            else:
                return dict(
                    label=s.label.encode('utf-8') if PY2 else s.label,
                    line_color=s.line_color.getRgb()
                    if s.line_color != self.lineColor else None,
                    fill_color=s.fill_color.getRgb()
                    if s.fill_color != self.fillColor else None,
                    points=[(p.x(), p.y()) for p in s.points],
                    shape_type=s.shape_type,
                    draw=True,
                    user= getpass.getuser(),
                    date=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                )

        shapes = [format_shape(shape) for shape in self.labelList.shapes]
        flags = {}
        for i in range(self.flag_widget.count()):
            item = self.flag_widget.item(i)
            key = item.text()
            flag = item.checkState() == Qt.Checked
            flags[key] = flag
        try:

            imagePath = osp.relpath(
                self.imagePath, osp.dirname(filename))
            imageData = self.imageData if self._config['store_data'] else None
            if osp.dirname(filename) and not osp.exists(osp.dirname(filename)):
                os.makedirs(osp.dirname(filename))
            #imagePath保存文件名，无路径
            lf.save(
                filename=filename,
                shapes=shapes,
                imagePath=imagePath,
                imageData=imageData,
                imgHeight=self.image.height(),
                imgWidth=self.image.width(),
                lineColor=self.lineColor.getRgb(),
                fillColor=self.fillColor.getRgb(),
                otherData=self.otherData,
                flags=flags,
            )
            self.labelFile = lf
            items = self.fileListWidget.findItems(
                self.imagePath, Qt.MatchExactly
            )
            if len(items) > 0:
                if len(items) != 1:
                    raise RuntimeError('There are duplicate files.')
                items[0].setCheckState(Qt.Checked)
            # disable allows next and previous image to proceed
            # self.filename = filename
            return True
        except LabelFileError as e:
            self.errorMessage('Error saving label data', '<b>%s</b>' % e)
            return False
    #复制框功能
    def copySelectedShape(self):
        self.addLabel(self.canvas.copySelectedShape())
        # fix copy and delete
        self.shapeSelectionChanged(True)
    #选定标签改变，跟踪
    def labelSelectionChanged(self):
        item = self.currentItem()
        if item and self.canvas.editing():
            self._noSelectionSlot = True
            shape = self.labelList.get_shape_from_item(item)
            if shape.shape_type=='PERSONKEYPOINTS':  #优化显示，在右侧显示标定的关键点
                self.loadkeyFlags({k: shape.bodyvisible[i]!=0 for i,k in enumerate(self._config['keyflags'])})
            self.canvas.selectShape(shape)

    def keyflagSelectionChanged(self): #暂时废弃
        if self.key_flag_widget.selectedItems():
            keyname=self.key_flag_widget.selectedItems()[0].text()
            print("keyname=",keyname)
    #更改目标标签
    def labelItemChanged(self, item):
        shape = self.labelList.get_shape_from_item(item)
        label = str(item.text())
        if label != shape.label:
            shape.label = str(item.text())
            self.setDirty()
        else:  # User probably changed item visibility
            self.canvas.setShapeVisible(shape, item.checkState() == Qt.Checked)

    def keyflagChanged(self,item):
        keyname=item.text()
        keystate=item.checkState()
        idx = self._config['keyflags'].index(keyname) if keyname in self._config['keyflags'] else None
        if self.canvas.selectedShape and keystate==2 and idx is not None:
            xmin=self.canvas.selectedShape.points[0].x()
            ymin=self.canvas.selectedShape.points[0].y()
            xmax = self.canvas.selectedShape.points[1].x()
            ymax = self.canvas.selectedShape.points[1].y()

            self.canvas.selectedShape.bodyvisible[idx]=2
            self.canvas.selectedShape.points[idx+2].setX((xmin+xmax)/2)
            self.canvas.selectedShape.points[idx + 2].setY((ymin+ymax)/2)
        elif self.canvas.selectedShape and keystate==0 and idx is not None:
            self.canvas.selectedShape.bodyvisible[idx] = 0
            self.canvas.selectedShape.points[idx + 2].setX(0)
            self.canvas.selectedShape.points[idx + 2].setY(0)

    # Callback functions:
    #新建标签
    def newShape(self):
        """Pop-up and give focus to the label editor.

        position MUST be in global coordinates.
        """
        items = self.uniqLabelList.selectedItems()
        text = None
        # if self.canvas.selectedPerson:   #人体关键点信号流程 ,应该使下面两个失效 #ls
        #     if self.canvas.prevKeyPoint == None:
        #         self.canvas.prevKeyPoint=self.uniqLabelList.item(0).text()
        #     elif self.canvas.prevKeyPoint == self.uniqLabelList.item(0).text():
        #         self.canvas.prevKeyPoint = self.uniqLabelList.item(1).text()
        #     elif self.canvas.prevKeyPoint == self.uniqLabelList.item(1).text():
        #         self.canvas.prevKeyPoint = self.uniqLabelList.item(2).text()
        #     elif self.canvas.prevKeyPoint == self.uniqLabelList.item(2).text():
        #         self.canvas.prevKeyPoint = self.uniqLabelList.item(3).text()
        #     elif self.canvas.prevKeyPoint == self.uniqLabelList.item(3).text():
        #         self.canvas.prevKeyPoint = self.uniqLabelList.item(4).text()
        #     elif self.canvas.prevKeyPoint == self.uniqLabelList.item(4).text():
        #         self.canvas.prevKeyPoint = self.uniqLabelList.item(5).text()
        #     text=self.canvas.prevKeyPoint#开始14个人体关键点标签
        #     if self.canvas.prevKeyPoint == self.uniqLabelList.item(5).text(): #一轮关键点用完，初始化信号 #ls
        #         self.canvas.prevKeyPoint==None
        #         self.canvas.deSelectPerson()
        if items:# and not text:  #兼容上面的情况，判断text的状态 #ls
            text = items[0].text()
        if self._config['display_label_popup'] or not text:
            text = self.labelDialog.popUp(text)
        if text is not None and not self.validateLabel(text):#标签检查
            self.errorMessage('Invalid label',
                              "Invalid label '{}' with validation type '{}'"
                              .format(text, self._config['validate_label']))
            text = None
        if text is None:
            self.canvas.undoLastLine()
            self.canvas.shapesBackups.pop()
        else:
            self.addLabel(self.canvas.setLastLabel(text))
            self.actions.editMode.setEnabled(True)
            self.actions.undoLastPoint.setEnabled(False)
            self.actions.createnolabelpoint.setEnabled(False)
            self.actions.undo.setEnabled(True)
            self.setDirty()  #保存
    #滚动
    def scrollRequest(self, delta, orientation):
        units = - delta * 0.1  # natural scroll
        bar = self.scrollBars[orientation]
        bar.setValue(bar.value() + bar.singleStep() * units)

    def setZoom(self, value):
        self.actions.fitWidth.setChecked(False)
        self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.MANUAL_ZOOM
        self.zoomWidget.setValue(value)

    def addZoom(self, increment=10):
        self.setZoom(self.zoomWidget.value() + increment)

    # 缩放
    def zoomRequest(self, delta, pos):
        canvas_width_old = self.canvas.width()

        units = delta * 0.1
        self.addZoom(units)

        canvas_width_new = self.canvas.width()
        if canvas_width_old != canvas_width_new:
            canvas_scale_factor = canvas_width_new / canvas_width_old

            x_shift = round(pos.x() * canvas_scale_factor) - pos.x()
            y_shift = round(pos.y() * canvas_scale_factor) - pos.y()

            self.scrollBars[Qt.Horizontal].setValue(
                self.scrollBars[Qt.Horizontal].value() + x_shift)
            self.scrollBars[Qt.Vertical].setValue(
                self.scrollBars[Qt.Vertical].value() + y_shift)

    # 缩放
    def setFitWindow(self, value=True):
        if value:
            self.actions.fitWidth.setChecked(False)
        self.zoomMode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
        self.adjustScale()

    # 缩放
    def setFitWidth(self, value=True):
        if value:
            self.actions.fitWindow.setChecked(False)
        self.zoomMode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
        self.adjustScale()
    #隐藏或显示标定
    def togglePolygons(self, value):
        for item, shape in self.labelList.itemsToShapes:
            item.setCheckState(Qt.Checked if value else Qt.Unchecked)

    def convertImageDataToPng(self, imageData):
        if imageData is None:
            return
        img = PIL.Image.open(io.BytesIO(imageData))
        with io.BytesIO() as imgBytesIO:
            img.save(imgBytesIO, "PNG")
            imgBytesIO.seek(0)
            data = imgBytesIO.read()
        return data
    #打开图片文件
    def loadFile(self, filename=None):
        """Load the specified file, or the last opened file if None."""
        # changing fileListWidget loads file
        if (filename in self.imageList and
                self.fileListWidget.currentRow() !=
                self.imageList.index(filename)):
            self.fileListWidget.setCurrentRow(self.imageList.index(filename))
            self.fileListWidget.repaint()
            return

        self.resetState()
        self.canvas.setEnabled(False)
        if filename is None:
            filename = self.settings.value('filename', '')
        filename = str(filename)
        if not QtCore.QFile.exists(filename):
            self.errorMessage(
                'Error opening file', 'No such file: <b>%s</b>' % filename)
            return False
        # assumes same name, but json extension
        self.status("Loading %s..." % osp.basename(str(filename)))
        label_file = osp.splitext(filename)[0] + '.json'
        if self.output_dir:
            label_file = osp.splitext(osp.basename(str(filename)))[0] + '.json'
            label_file = osp.join(self.output_dir,label_file)
        if QtCore.QFile.exists(label_file) and \
                LabelFile.isLabelFile(label_file):
            try:
                self.labelFile = LabelFile(filename=label_file, imagePath=filename, output_dir=self.output_dir)
                # FIXME: PyQt4 installed via Anaconda fails to load JPEG
                # and JSON encoded images.
                # https://github.com/ContinuumIO/anaconda-issues/issues/131
                if QtGui.QImage.fromData(self.labelFile.imageData).isNull():
                    # tries to read image with PIL and convert it to PNG
                    self.labelFile.imageData = self.convertImageDataToPng(
                        self.labelFile.imageData)
                if QtGui.QImage.fromData(self.labelFile.imageData).isNull():
                    raise LabelFileError(
                        'Failed loading image data from label file.\n'
                        'Maybe this is a known issue of PyQt4 built on'
                        ' Anaconda, and may be fixed by installing PyQt5.')
            except LabelFileError as e:
                self.errorMessage(
                    'Error opening file',
                    "<p><b>%s</b></p>"
                    "<p>Make sure <i>%s</i> is a valid label file."
                    % (e, label_file))
                self.status("Error reading %s" % label_file)
                return False
            self.imageData = self.labelFile.imageData
            self.imagePath = osp.join(
                osp.dirname(label_file),
                self.labelFile.imagePath,
            )
            self.lineColor = QtGui.QColor(*self.labelFile.lineColor)
            self.fillColor = QtGui.QColor(*self.labelFile.fillColor)
            self.otherData = self.labelFile.otherData
        else:
            # Load image:
            # read data first and store for saving into label file.
            self.imageData = read(filename, None)
            if self.imageData is not None:
                # the filename is image not JSON
                self.imagePath = filename
                if QtGui.QImage.fromData(self.imageData).isNull():
                    self.imageData = self.convertImageDataToPng(self.imageData)
            self.labelFile = None
        image = QtGui.QImage.fromData(self.imageData)
        if image.isNull():
            formats = ['*.{}'.format(fmt.data().decode())
                       for fmt in QtGui.QImageReader.supportedImageFormats()]
            self.errorMessage(
                'Error opening file',
                '<p>Make sure <i>{0}</i> is a valid image file.<br/>'
                'Supported image formats: {1}</p>'
                .format(filename, ','.join(formats)))
            self.status("Error reading %s" % filename)
            return False
        self.image = image
        self.filename = filename
        if self._config['keep_prev']:
            prev_shapes = self.canvas.shapes
        self.canvas.loadPixmap(QtGui.QPixmap.fromImage(image))
        if self._config['flags']:
            self.loadFlags({k: False for k in self._config['flags']})
        if self._config['keep_prev']:
            self.loadShapes(prev_shapes)
        if self.labelFile:
            self.loadLabels(self.labelFile.shapes)
            if self.labelFile.flags is not None:
                self.loadFlags(self.labelFile.flags)
        self.setClean()
        self.canvas.setEnabled(True)
        self.adjustScale(initial=True)
        self.paintCanvas()
        self.addRecentFile(self.filename)
        self.toggleActions(True)
        self.status("Loaded %s" % osp.basename(str(filename)))
        return True
    #自适应
    def resizeEvent(self, event):
        if self.canvas and not self.image.isNull()\
           and self.zoomMode != self.MANUAL_ZOOM:
            self.adjustScale()
        super(MainWindow, self).resizeEvent(event)

    def paintCanvas(self):
        assert not self.image.isNull(), "cannot paint null image"
        self.canvas.scale = 0.01 * self.zoomWidget.value()
        self.canvas.adjustSize()
        self.canvas.update()

    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]()
        self.zoomWidget.setValue(int(100 * value))
    #图片适应窗口功能
    def scaleFitWindow(self):
        """Figure out the size of the pixmap to fit the main widget."""
        e = 2.0  # So that no scrollbars are generated.
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1 / h1
        # Calculate a new scale value based on the pixmap's aspect ratio.
        w2 = self.canvas.pixmap.width() - 0.0
        h2 = self.canvas.pixmap.height() - 0.0
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2

    # 图片适应宽度
    def scaleFitWidth(self):
        # The epsilon does not seem to work too well here.
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()
    #下一张图
    def closeEvent(self, event):
        if not self.mayContinue():
            event.ignore()
        self.settings.setValue(
            'filename', self.filename if self.filename else '')
        self.settings.setValue('window/size', self.size())
        self.settings.setValue('window/position', self.pos())
        self.settings.setValue('window/state', self.saveState())
        self.settings.setValue('line/color', self.lineColor)
        self.settings.setValue('fill/color', self.fillColor)
        self.settings.setValue('recentFiles', self.recentFiles)
        # ask the use for where to save the labels
        # self.settings.setValue('window/geometry', self.saveGeometry())

    # User Dialogs #

    def loadRecent(self, filename):
        if self.mayContinue():
            self.loadFile(filename)

    def openPrevImg(self, _value=False):
        keep_prev = self._config['keep_prev']
        if QtGui.QGuiApplication.keyboardModifiers() == \
                (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
            self._config['keep_prev'] = True

        if not self.mayContinue():
            return

        if len(self.imageList) <= 0:
            return

        if self.filename is None:
            return

        currIndex = self.imageList.index(self.filename)
        if currIndex - 1 >= 0:
            filename = self.imageList[currIndex - 1]
            if filename:
                self.loadFile(filename)

        self._config['keep_prev'] = keep_prev

    def openNextImg(self, _value=False, load=True):
        keep_prev = self._config['keep_prev']
        if QtGui.QGuiApplication.keyboardModifiers() == \
                (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
            self._config['keep_prev'] = True

        if not self.mayContinue():
            return

        if len(self.imageList) <= 0:
            return

        filename = None
        if self.filename is None:
            filename = self.imageList[0]
        else:
            currIndex = self.imageList.index(self.filename)
            if currIndex + 1 < len(self.imageList):
                filename = self.imageList[currIndex + 1]
            else:
                filename = self.imageList[-1]
        self.filename = filename

        if self.filename and load:
            self.loadFile(self.filename)

        self._config['keep_prev'] = keep_prev

    def openFile(self, _value=False):
        if not self.mayContinue():
            return
        path = osp.dirname(str(self.filename)) if self.filename else '.'
        formats = ['*.{}'.format(fmt.data().decode())
                   for fmt in QtGui.QImageReader.supportedImageFormats()]
        filters = "Image & Label files (%s)" % ' '.join(
            formats + ['*%s' % LabelFile.suffix])
        filename = QtWidgets.QFileDialog.getOpenFileName(
            self, '%s - Choose Image or Label file' % __appname__,
            path, filters)
        if QT5:
            filename, _ = filename
        filename = str(filename)
        if filename:
            self.loadFile(filename)

    def changeOutputDirDialog(self, _value=False):
        default_output_dir = self.output_dir
        if default_output_dir is None and self.filename:
            default_output_dir = osp.dirname(self.filename)
        if default_output_dir is None:
            default_output_dir = self.currentPath()

        output_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, '%s - Save/Load Annotations in Directory' % __appname__,
            default_output_dir,
            QtWidgets.QFileDialog.ShowDirsOnly |
            QtWidgets.QFileDialog.DontResolveSymlinks,
        )
        output_dir = str(output_dir)

        if not output_dir:
            return

        self.output_dir = output_dir

        self.statusBar().showMessage(
            '%s . Annotations will be saved/loaded in %s' %
            ('Change Annotations Dir', self.output_dir))
        self.statusBar().show()

        current_filename = self.filename
        self.importDirImages(self.lastOpenDir, load=False)

        if current_filename in self.imageList:
            # retain currently selected file
            self.fileListWidget.setCurrentRow(
                self.imageList.index(current_filename))
            self.fileListWidget.repaint()

        # yaml #ls
        config_file = osp.join('config', 'default_config.yaml')
        config_file='/home/lishuang/Disk/shengshi_github/code/labelme_nightly/labelme/config/default_config.yaml'
        file_data = ""
        with open(config_file) as f:
            for line in f:
                if 'output_dir: "' in line:
                    # line=line.replace(defaultOpenDirPath,targetDirPath)
                    line = line[:13] + output_dir + line[-2:]
                file_data += line
        with open(config_file, "w") as f:
            f.write(file_data)

    def saveFile(self, _value=False):
        assert not self.image.isNull(), "cannot save empty image"
        if self._config['flags'] or self.hasLabels():
            if self.labelFile:
                # DL20180323 - overwrite when in directory
                self._saveFile(self.labelFile.filename)
            elif self.output_file:
                self._saveFile(self.output_file)
                self.close()
            else:
                self._saveFile(self.saveFileDialog())

    def saveFileAs(self, _value=False):
        assert not self.image.isNull(), "cannot save empty image"
        if self.hasLabels():
            self._saveFile(self.saveFileDialog())
    #保存文件对话框
    def saveFileDialog(self):
        caption = '%s - Choose File' % __appname__
        filters = 'Label files (*%s)' % LabelFile.suffix
        if self.output_dir:
            dlg = QtWidgets.QFileDialog(
                self, caption, self.output_dir, filters
            )
        else:
            dlg = QtWidgets.QFileDialog(
                self, caption, self.currentPath(), filters
            )
        dlg.setDefaultSuffix(LabelFile.suffix[1:])
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dlg.setOption(QtWidgets.QFileDialog.DontConfirmOverwrite, False)
        dlg.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, False)
        #basename = osp.splitext(self.filename)[0]
        basename = os.path.basename(self.filename)
        basename = osp.splitext(basename)[0]
        if self.output_dir:
            default_labelfile_name = osp.join(
                self.output_dir, basename + LabelFile.suffix
            )
        else:
            default_labelfile_name = osp.join(
                self.currentPath(), basename + LabelFile.suffix
            )
        filename = dlg.getSaveFileName(
            self, 'Choose File', default_labelfile_name,
            'Label files (*%s)' % LabelFile.suffix)
        if QT5:
            filename, _ = filename
        filename = str(filename)
        return filename

    def _saveFile(self, filename):
        if filename and self.saveLabels(filename):
            self.addRecentFile(filename)
            self.setClean()
    #退出当前图片
    def closeFile(self, _value=False):
        if not self.mayContinue():
            return
        self.resetState()
        self.setClean()
        self.toggleActions(False)
        self.canvas.setEnabled(False)
        self.actions.saveAs.setEnabled(False)

    # Message Dialogs. #
    def hasLabels(self):
        if not self.labelList.itemsToShapes:
            self.errorMessage(
                'No objects labeled',
                'You must label at least one object to save the file.')
            return False
        return True

    def mayContinue(self):
        if not self.dirty:
            return True
        mb = QtWidgets.QMessageBox
        msg = 'Save annotations to "{}" before closing?'.format(self.filename)
        answer = mb.question(self,
                             'Save annotations?',
                             msg,
                             mb.Save | mb.Discard | mb.Cancel,
                             mb.Save)
        if answer == mb.Discard:
            return True
        elif answer == mb.Save:
            self.saveFile()
            return True
        else:  # answer == mb.Cancel
            return False

    def errorMessage(self, title, message):
        return QtWidgets.QMessageBox.critical(
            self, title, '<p><b>%s</b></p>%s' % (title, message))

    def currentPath(self):
        return osp.dirname(str(self.filename)) if self.filename else '.'
    #部分功能实现
    def chooseColor1(self):
        color = self.colorDialog.getColor(
            self.lineColor, 'Choose line color', default=DEFAULT_LINE_COLOR)
        if color:
            self.lineColor = color
            # Change the color for all shape lines:
            Shape.line_color = self.lineColor
            self.canvas.update()
            self.setDirty()

    def chooseColor2(self):
        color = self.colorDialog.getColor(
            self.fillColor, 'Choose fill color', default=DEFAULT_FILL_COLOR)
        if color:
            self.fillColor = color
            Shape.fill_color = self.fillColor
            self.canvas.update()
            self.setDirty()

    def toggleKeepPrevMode(self):
        self._config['keep_prev'] = not self._config['keep_prev']

    def deleteSelectedShape(self):
        yes, no = QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No
        msg = 'You are about to permanently delete this polygon, ' \
              'proceed anyway?'
        if yes == QtWidgets.QMessageBox.warning(self, 'Attention', msg,
                                                yes | no):
            self.remLabel(self.canvas.deleteSelected())
            self.setDirty()
            if self.noShapes():
                for action in self.actions.onShapesPresent:
                    action.setEnabled(False)
    #右键功能
    def chshapeLineColor(self):
        color = self.colorDialog.getColor(
            self.lineColor, 'Choose line color', default=DEFAULT_LINE_COLOR)
        if color:
            self.canvas.selectedShape.line_color = color
            self.canvas.update()
            self.setDirty()
    #右键功能
    def chshapeFillColor(self):
        color = self.colorDialog.getColor(
            self.fillColor, 'Choose fill color', default=DEFAULT_FILL_COLOR)
        if color:
            self.canvas.selectedShape.fill_color = color
            self.canvas.update()
            self.setDirty()

    def copyShape(self):
        self.canvas.endMove(copy=True)
        self.addLabel(self.canvas.selectedShape)
        self.setDirty()

    def moveShape(self):
        self.canvas.endMove(copy=False)
        self.setDirty()

    def openDirDialog(self, _value=False, dirpath=None):
        if not self.mayContinue():
            return

        defaultOpenDirPath = dirpath if dirpath else '.'
        if self.lastOpenDir and osp.exists(self.lastOpenDir):
            defaultOpenDirPath = self.lastOpenDir
        else:
            defaultOpenDirPath = osp.dirname(self.filename) \
                if self.filename else '.'

        targetDirPath = str(QtWidgets.QFileDialog.getExistingDirectory(
            self, '%s - Open Directory' % __appname__, defaultOpenDirPath,
            QtWidgets.QFileDialog.ShowDirsOnly |
            QtWidgets.QFileDialog.DontResolveSymlinks))
        self.importDirImages(targetDirPath)


        #yaml #ls
        config_file = osp.join('config', 'default_config.yaml')
        config_file='/home/lishuang/Disk/shengshi_github/code/labelme_nightly/labelme/config/default_config.yaml'
        file_data = ""
        with open(config_file) as f:
            for line in f:
                if 'open_dir: "' in line:
                    # line=line.replace(defaultOpenDirPath,targetDirPath)
                    line = line[:11] + targetDirPath+line[-2:]
                file_data += line
        with open(config_file,"w") as f:
            f.write(file_data)




    @property
    def imageList(self):
        lst = []
        for i in range(self.fileListWidget.count()):
            item = self.fileListWidget.item(i)
            lst.append(item.text())
        return lst

    def importDirImages(self, dirpath, pattern=None, load=True):
        self.actions.openNextImg.setEnabled(True)
        self.actions.openPrevImg.setEnabled(True)

        if not self.mayContinue() or not dirpath:
            return

        self.lastOpenDir = dirpath
        self.filename = None
        self.fileListWidget.clear()
        for filename in self.scanAllImages(dirpath):
            if pattern and pattern not in filename:
                continue
            label_file = osp.splitext(filename)[0] + '.json'
            if self.output_dir:
                label_file = osp.join(self.output_dir, label_file)
            item = QtWidgets.QListWidgetItem(filename)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            if QtCore.QFile.exists(label_file) and \
                    LabelFile.isLabelFile(label_file):
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.fileListWidget.addItem(item)
        self.openNextImg(load=load)

    def scanAllImages(self, folderPath):
        extensions = ['.%s' % fmt.data().decode("ascii").lower()
                      for fmt in QtGui.QImageReader.supportedImageFormats()]
        images = []

        for root, dirs, files in os.walk(folderPath):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    relativePath = osp.join(root, file)
                    images.append(relativePath)
        images.sort(key=lambda x: x.lower())
        return images


def read(filename, default=None):
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except Exception:
        return default
