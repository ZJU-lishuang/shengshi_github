import base64
import json
import os.path

from . import logger
from . import PY2
from . import utils
from ._version import __version__


class LabelFileError(Exception):
    pass


class LabelFile(object):

    suffix = '.json'

    def __init__(self, filename=None,imagePath = None,output_dir = None):
        self.shapes = ()
        self.imagePath = imagePath
        self.imageData = None
        self.filename = filename
        self.output_dir = output_dir
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        keys = [
            'imageData',
            'filename',
            'lineColor',
            'fillColor',
            'objects',  # polygonal annotations
            'flags',   # image level flags
            'imgHeight',
            'imgWidth',
        ]
        try:
            with open(filename, 'rb' if PY2 else 'r') as f:
                data = json.load(f)
            try:
                if data['imageData'] is not None:
                    imageData = base64.b64decode(data['imageData'])
                else:
                    # imagePath = os.path.join(os.path.dirname(self.imagePath) ,
                    #                          data['filename'])
                    imagePath = self.imagePath
                    with open(imagePath, 'rb') as f:
                        imageData = f.read()
            except:
                # relative path from label file to relative path from cwd
                imagePath = self.imagePath
                with open(imagePath, 'rb') as f:
                    imageData = f.read()
            flags = data.get('flags')
            imagePath = data['filename']
            self._check_image_height_and_width(
                base64.b64encode(imageData).decode('utf-8'),
                data.get('imgHeight'),
                data.get('imgWidth'),
            )
            lineColor = [
                            0,
                            255,
                            0,
                            128
                          ]
            fillColor = [
                            255,
                            0,
                            0,
                            128
                          ]
            if 'lineColor' in data.keys():
                lineColor = data['lineColor']
            if 'fillColor' in data.keys():
                fillColor = data['fillColor']
            shapes = []
            for s in data['objects']:
                if 'lineColor' not in s.keys():
                    s['line_color'] = None
                if 'fillColor' not in s.keys():
                    s['fill_color'] = None
                if s['shape_type'] == "POLYGON":
                    shapes.append (
                        (
                            s['label'],
                            s['polygon'],
                            s['line_color'],
                            s['fill_color'],
                            s.get('shape_type', 'polygon'),
                        )
                    )
                elif s['shape_type'] == "RECT":
                    shapes.append (
                        (
                            s['label'],
                            s['bbox'],
                            s['line_color'],
                            s['fill_color'],
                            s.get('shape_type', 'polygon'),
                        )
                    )
                elif s['shape_type'] == "KEYPOINTS":
                    shapes.append (
                        (
                            s['label'],
                            s['keypoints'],
                            s['line_color'],
                            s['fill_color'],
                            s.get('shape_type', 'polygon'),
                        )
                    )
                elif s['shape_type']=="PERSONKEYPOINTS": #读取新模块格式  #ls
                    shapes.append(
                        (
                            s['label'],
                            s['keypoints'],
                            s['line_color'],
                            s['fill_color'],
                            s.get('shape_type', 'polygon'),
                        )
                    )
                else:
                    shapes.append (
                        (
                            s['label'],
                            s['points'],
                            s['line_color'],
                            s['fill_color'],
                            s.get('shape_type', 'polygon'),
                        )
                    )
        except Exception as e:
            raise LabelFileError(e)

        otherData = {}
        for key, value in data.items():
            if key not in keys:
                otherData[key] = value

        # Only replace data after everything is loaded.
        self.flags = flags
        self.shapes = shapes
        self.imagePath = imagePath
        self.imageData = imageData
        self.lineColor = lineColor
        self.fillColor = fillColor
        self.filename = filename
        self.otherData = otherData

    @staticmethod
    def _check_image_height_and_width(imageData, imgHeight, imgWidth):
        img_arr = utils.img_b64_to_arr(imageData)
        if imgHeight is not None and img_arr.shape[0] != imgHeight:
            logger.error(
                'imgHeight does not match with imageData or imagePath filename, '
                'so getting imgHeight from actual image.'
            )
            imgHeight = img_arr.shape[0]
        if imgWidth is not None and img_arr.shape[1] != imgWidth:
            logger.error(
                'imgWidth does not match with imageData or imagePath filename, '
                'so getting imgWidth from actual image.'
            )
            imgWidth = img_arr.shape[1]
        return imgHeight, imgWidth

    def save(
        self,
        filename,
        shapes,
        imagePath,
        imgHeight,
        imgWidth,
        imageData=None,
        lineColor=None,
        fillColor=None,
        otherData=None,
        flags=None,
    ):
        if imageData is not None:
            imageData = base64.b64encode(imageData).decode('utf-8')
            imgHeight, imgWidth = self._check_image_height_and_width(
                imageData, imgHeight, imgWidth
            )
        if otherData is None:
            otherData = {}
        if flags is None:
            flags = {}
        data = dict(
            version=__version__,
            flags=flags,
            objects=shapes,
            lineColor=lineColor,
            fillColor=fillColor,
            filename=os.path.basename(imagePath),
            imageData=imageData,
            imgHeight=imgHeight,
            imgWidth=imgWidth,
        )
        for key, value in otherData.items():
            data[key] = value
        try:
            with open(filename, 'wb' if PY2 else 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.filename = filename
        except Exception as e:
            raise LabelFileError(e)

    @staticmethod
    def isLabelFile(filename):
        return os.path.splitext(filename)[1].lower() == LabelFile.suffix
