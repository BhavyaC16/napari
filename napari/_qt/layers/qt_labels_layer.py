from qtpy.QtGui import QPainter, QColor
from qtpy.QtWidgets import (
    QButtonGroup,
    QWidget,
    QPushButton,
    QSlider,
    QCheckBox,
    QLabel,
    QSpinBox,
    QHBoxLayout,
)
from qtpy.QtCore import Qt

import numpy as np
from .qt_base_layer import QtLayerControls
from ...layers.labels._constants import Mode
from ..qt_mode_buttons import QtModeRadioButton
from ..utils import disable_with_opacity


class QtLabelsControls(QtLayerControls):
    """Qt view and controls for the napari Labels layer.

    Parameters
    ----------
    layer : napari.layers.Labels
        An instance of a napari Labels layer.

    Attributes
    ----------
    button_group : qtpy.QtWidgets.QButtonGroup
        Button group of labels layer modes: PAN_ZOOM, PICKER, PAINT, or FILL.
    colormapUpdate : qtpy.QtWidgets.QPushButton
        Button to update colormap of label layer.
    contigCheckBox : qtpy.QtWidgets.QCheckBox
        Checkbox to control if label layer is contiguous.
    fill_button : qtpy.QtWidgets.QtModeRadioButton
        Button to select FILL mode on Labels layer.
    grid_layout : qtpy.QtWidgets.QGridLayout
        Layout of Qt widget controls for the layer.
    layer : napari.layers.Labels
        An instance of a napari Labels layer.
    ndimCheckBox : qtpy.QtWidgets.QCheckBox
        Checkbox to control if label layer is n-dimensional.
    paint_button : qtpy.QtWidgets.QtModeRadioButton
        Button to select PAINT mode on Labels layer.
    panzoom_button : qtpy.QtWidgets.QtModeRadioButton
        Button to select PAN_ZOOM mode on Labels layer.
    pick_button : qtpy.QtWidgets.QtModeRadioButton
        Button to select PICKER mode on Labels layer.
    selectionSpinBox : qtpy.QtWidgets.QSpinBox
        Widget to select a specfic label by its index.

    Raises
    ------
    ValueError
        Raise error if label mode is not PAN_ZOOM, PICKER, PAINT, or FILL.
    """

    def __init__(self, layer):
        super().__init__(layer)

        self.layer.events.mode.connect(self._on_mode_change)
        self.layer.events.selected_label.connect(self._on_selection_change)
        self.layer.events.brush_size.connect(self._on_brush_size_change)
        self.layer.events.contiguous.connect(self._on_contig_change)
        self.layer.events.n_dimensional.connect(self._on_n_dim_change)
        self.layer.events.editable.connect(self._on_editable_change)

        # shuffle colormap button
        self.colormapUpdate = QPushButton('shuffle colors')
        self.colormapUpdate.setObjectName('shuffleButton')
        self.colormapUpdate.clicked.connect(self.changeColor)

        # selection spinbox
        self.selectionSpinBox = QSpinBox()
        self.selectionSpinBox.setKeyboardTracking(False)
        self.selectionSpinBox.setSingleStep(1)
        self.selectionSpinBox.setMinimum(0)
        self.selectionSpinBox.setMaximum(2147483647)
        self.selectionSpinBox.valueChanged.connect(self.changeSelection)
        self.selectionSpinBox.setAlignment(Qt.AlignCenter)
        self._on_selection_change()

        sld = QSlider(Qt.Horizontal)
        sld.setFocusPolicy(Qt.NoFocus)
        sld.setMinimum(1)
        sld.setMaximum(40)
        sld.setSingleStep(1)
        sld.valueChanged.connect(self.changeSize)
        self.brushSizeSlider = sld
        self._on_brush_size_change()

        contig_cb = QCheckBox()
        contig_cb.setToolTip('contiguous editing')
        contig_cb.stateChanged.connect(self.change_contig)
        self.contigCheckBox = contig_cb
        self._on_contig_change()

        ndim_cb = QCheckBox()
        ndim_cb.setToolTip('n-dimensional editing')
        ndim_cb.stateChanged.connect(self.change_ndim)
        self.ndimCheckBox = ndim_cb
        self._on_n_dim_change()

        self.panzoom_button = QtModeRadioButton(
            layer, 'zoom', Mode.PAN_ZOOM, tooltip='Pan/zoom mode', checked=True
        )
        self.pick_button = QtModeRadioButton(
            layer, 'picker', Mode.PICKER, tooltip='Pick mode'
        )
        self.paint_button = QtModeRadioButton(
            layer, 'paint', Mode.PAINT, tooltip='Paint mode'
        )
        self.fill_button = QtModeRadioButton(
            layer, 'fill', Mode.FILL, tooltip='Fill mode'
        )

        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.panzoom_button)
        self.button_group.addButton(self.paint_button)
        self.button_group.addButton(self.pick_button)
        self.button_group.addButton(self.fill_button)
        self._on_editable_change()

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self.pick_button)
        button_row.addWidget(self.fill_button)
        button_row.addWidget(self.paint_button)
        button_row.addWidget(self.panzoom_button)
        button_row.setSpacing(4)
        button_row.setContentsMargins(0, 0, 0, 5)

        color_layout = QHBoxLayout()
        color_layout.addWidget(QtColorBox(layer))
        color_layout.addWidget(self.selectionSpinBox)

        # grid_layout created in QtLayerControls
        # addWidget(widget, row, column, [row_span, column_span])
        self.grid_layout.addLayout(button_row, 0, 1)
        self.grid_layout.addWidget(self.colormapUpdate, 0, 0)
        self.grid_layout.addWidget(QLabel('label:'), 1, 0)
        self.grid_layout.addLayout(color_layout, 1, 1)
        self.grid_layout.addWidget(QLabel('opacity:'), 2, 0)
        self.grid_layout.addWidget(self.opacitySlider, 2, 1)
        self.grid_layout.addWidget(QLabel('brush size:'), 3, 0)
        self.grid_layout.addWidget(self.brushSizeSlider, 3, 1)
        self.grid_layout.addWidget(QLabel('blending:'), 4, 0)
        self.grid_layout.addWidget(self.blendComboBox, 4, 1)
        self.grid_layout.addWidget(QLabel('contiguous:'), 5, 0)
        self.grid_layout.addWidget(self.contigCheckBox, 5, 1)
        self.grid_layout.addWidget(QLabel('n-dim:'), 6, 0)
        self.grid_layout.addWidget(self.ndimCheckBox, 6, 1)
        self.grid_layout.setRowStretch(7, 1)
        self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.setSpacing(4)

    def mouseMoveEvent(self, event):
        """On mouse move, set layer status equal to the current selected mode.

        Available mode options are: PAN_ZOOM, PICKER, PAINT, or FILL

        Parameters
        ----------
        event : qtpy.QtCore.QEvent
            Event from the Qt context.
        """
        self.layer.status = str(self.layer.mode)

    def _on_mode_change(self, event):
        """Receive layer model mode change event and update checkbox ticks.

        Parameters
        ----------
        event : qtpy.QtCore.QEvent
            Event from the Qt context.

        Raises
        ------
        ValueError
            Raise error if event.mode is not PAN_ZOOM, PICKER, PAINT, or FILL
        """
        mode = event.mode
        if mode == Mode.PAN_ZOOM:
            self.panzoom_button.setChecked(True)
        elif mode == Mode.PICKER:
            self.pick_button.setChecked(True)
        elif mode == Mode.PAINT:
            self.paint_button.setChecked(True)
        elif mode == Mode.FILL:
            self.fill_button.setChecked(True)
        else:
            raise ValueError("Mode not recognized")

    def changeColor(self):
        """Change colormap of the label layer."""
        self.layer.new_colormap()

    def changeSelection(self, value):
        """Change currently selected label.

        Parameters
        ----------
        value : int
            Index of label to select.
        """
        self.layer.selected_label = value
        self.selectionSpinBox.clearFocus()
        self.setFocus()

    def changeSize(self, value):
        """Change paint brush size.

        Parameters
        ----------
        value : float
            Size of the paint brush.
        """
        self.layer.brush_size = value

    def change_contig(self, state):
        """Toggle contiguous state of label layer.

        Parameters
        ----------
        state : QCheckBox
            Checkbox indicating if labels are contiguous.
        """
        if state == Qt.Checked:
            self.layer.contiguous = True
        else:
            self.layer.contiguous = False

    def change_ndim(self, state):
        """Toggle n-dimensional state of label layer.

        Parameters
        ----------
        state : QCheckBox
            Checkbox indicating if label layer is n-dimensional.
        """
        if state == Qt.Checked:
            self.layer.n_dimensional = True
        else:
            self.layer.n_dimensional = False

    def _on_selection_change(self, event=None):
        """Receive layer model label selection change event and update spinbox.

        Parameters
        ----------
        event : qtpy.QtCore.QEvent, optional.
            Event from the Qt context.
        """
        with self.layer.events.selected_label.blocker():
            value = self.layer.selected_label
            self.selectionSpinBox.setValue(int(value))

    def _on_brush_size_change(self, event=None):
        """Receive layer model brush size change event and update the slider.

        Parameters
        ----------
        event : qtpy.QtCore.QEvent, optional.
            Event from the Qt context.
        """
        with self.layer.events.brush_size.blocker():
            value = self.layer.brush_size
            value = np.clip(int(value), 1, 40)
            self.brushSizeSlider.setValue(value)

    def _on_n_dim_change(self, event=None):
        """Receive layer model n-dim mode change event and update the checkbox.

        Parameters
        ----------
        event : qtpy.QtCore.QEvent, optional.
            Event from the Qt context.
        """
        with self.layer.events.n_dimensional.blocker():
            self.ndimCheckBox.setChecked(self.layer.n_dimensional)

    def _on_contig_change(self, event=None):
        """Receive layer model contiguous change event and update the checkbox.

        Parameters
        ----------
        event : qtpy.QtCore.QEvent, optional.
            Event from the Qt context.
        """
        with self.layer.events.contiguous.blocker():
            self.contigCheckBox.setChecked(self.layer.contiguous)

    def _on_editable_change(self, event=None):
        """Receive layer model editable change event & enable/disable buttons.

        Parameters
        ----------
        event : qtpy.QtCore.QEvent, optional.
            Event from the Qt context.
        """
        disable_with_opacity(
            self,
            ['pick_button', 'paint_button', 'fill_button'],
            self.layer.editable,
        )


class QtColorBox(QWidget):
    """A widget that shows a square with the current label color.

    Parameters
    ----------
    layer : napari.layers.Layer
        An instance of a napari layer.
    """

    def __init__(self, layer):
        super().__init__()

        self.layer = layer
        self._height = 24
        self.setFixedWidth(self._height)
        self.setFixedHeight(self._height)
        self.setToolTip('Selected label color')

        self.layer.events.selected_label.connect(self.update_color)

    def update_color(self, event):
        """Receive layer model label selection change event & update colorbox.

        Parameters
        ----------
        event : qtpy.QtCore.QEvent
            Event from the Qt context.
        """
        self.update()

    def paintEvent(self, event):
        """Paint the colorbox.  If no color, display a checkerboard pattern.

        Parameters
        ----------
        event : qtpy.QtCore.QEvent
            Event from the Qt context.
        """
        painter = QPainter(self)
        if self.layer._selected_color is None:
            for i in range(self._height // 4):
                for j in range(self._height // 4):
                    if (i % 2 == 0 and j % 2 == 0) or (
                        i % 2 == 1 and j % 2 == 1
                    ):
                        painter.setPen(QColor(230, 230, 230))
                        painter.setBrush(QColor(230, 230, 230))
                    else:
                        painter.setPen(QColor(25, 25, 25))
                        painter.setBrush(QColor(25, 25, 25))
                    painter.drawRect(i * 4, j * 4, 5, 5)
        else:
            color = 255 * self.layer._selected_color
            color = color.astype(int)
            painter.setPen(QColor(*list(color)))
            painter.setBrush(QColor(*list(color)))
            painter.drawRect(0, 0, self._height, self._height)
