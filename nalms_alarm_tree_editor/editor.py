import os
import json
from qtpy import QtCore
from pydm import Display
from pydm.widgets import PyDMEmbeddedDisplay, PyDMAlarmTree
from pydm.utilities import connection

from qtpy.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeView, QTableWidgetItem, QCheckBox,
                            QAbstractItemView, QSpacerItem, QSizePolicy, QLineEdit, QToolBar, QAction,
                            QDialogButtonBox, QPushButton, QMenu, QGridLayout, QTableWidget, QLabel, QApplication, QFileDialog)
from qtpy.QtCore import Qt, Slot, QModelIndex, QItemSelection
from qtpy import QtCore, QtGui
from qtpy.QtDesigner import QDesignerFormWindowInterface
from collections import OrderedDict
import xml.etree.ElementTree as ET



class PhoebusConfigTool:
    """
    Tool for building and parsing Phoebus configuration files

    """

    def __init__(self):
        self._nodes = []

    def parse_config(self, filename):
        """
        Parses a configuration file
        """
        self._tree = ET.parse(filename)
        self._root = self._tree.getroot()

        if self._root.tag == "config":
            self._config_name = self._root.attrib["name"]

            # add root item to tree
            self._nodes.append([{"label": self._config_name}, None])
            
            for child in self._root:
                if child.tag == "component":
                    self._handle_group_parse(child, 0)

                elif child.tag == "pv":
                    self._handle_pv_parse(child, 0)

        return self._nodes


    def _build_data(self, elem):
        data = {"label": elem.attrib.get("name")}

        for child in elem:
            if child.tag == "description":
                data["description"] = child.text
            
            elif child.tag == "enabled":
                data["enabled"] = child.text

            elif child.tag == "latching":
                data["latching"] = child.text

            elif child.tag == "annunciating":
                data["annunciating"] = child.text

            elif child.tag == "delay":
                data["delay"] = child.text

            elif child.tag == "count":
                data["count"] = child.text

            elif child.tag == "filter":
                data["filter"] = child.text

            elif child.tag == "command":
                pass # TODO

            elif child.tag == "automated_action":
                pass # TODO 

        return data


    def _handle_pv_parse(self, pv, parent_idx):
        data = self._build_data(pv)
        self._nodes.append([data, parent_idx])

    
    def _handle_group_parse(self, group, parent_idx):
        # add group
        data = self._build_data(group)
        self._nodes.append([data, parent_idx])
        group_idx = len(self._nodes) - 1 

        for child in group:
            if child.tag == "component":
                self._handle_group(child, group_idx)

            elif child.tag == "pv":
                self._handle_pv(child, group_idx)


    def save_configuration(self, nodes, config_name, filename):
        self._build_config(nodes, config_name)
        
        with open (filename, "wb") as f : 
            file_str = ET.tostring(self._tree, encoding='utf8') 
            f.write(file_str)

    
    def _build_config(self, nodes, config_name):
        self._tree = ET.Element("config", name=config_name)

        for node in nodes:
            
            #if children, is a group
            if node.child_count():
                self._handle_group_add(node, self._tree)

            else:
                self._handle_pv_add(node, self._tree)

    def _handle_property_add(self, elem, alarm_tree_item):

        if alarm_tree_item.enabled is not None:
            enabled = ET.SubElement(elem, "enabled")
           
            if alarm_tree_item.enabled:
                enabled.text = 'true'

            else:
                enabled.text = 'false'

        if alarm_tree_item.latching is not None:
            latching = ET.SubElement(elem, "latching")

            if alarm_tree_item.latching:
                latching.text = 'true'

            else:
                latching.text = 'false'

        if alarm_tree_item.annunciating is not None:
            annunciating = ET.SubElement(elem, "annunciating")

            if alarm_tree_item.annunciating:
                annunciating.text = 'true'

            else:
                annunciating.text = 'false'


        if alarm_tree_item.description:
            description = ET.SubElement(elem, "description")
            description.text = alarm_tree_item.description


        if alarm_tree_item.delay:
            delay = ET.SubElement(elem, "delay")
            delay.text = alarm_tree_item.delay

        if alarm_tree_item.count:
            count = ET.SubElement(elem, "count")
            count.text = alarm_tree_item.count


    def _handle_group_add(self, group, parent):
        group_comp = ET.SubElement(parent, 'component', name=group.label)
        self._handle_property_add(group_comp, group)

        for child in self.group.children:

            if child.child_count():
                self._handle_group_add(child, group)

            else:
                self._handle_pv_add(child, group)


    def _handle_pv_add(self, pv, parent):
        pv_comp = ET.SubElement(parent, 'pv', name=pv.label)
        self._handle_property_add(group_comp, pv)


        



"""
def handle_children(builder, tree, node, parent_group=None):
    children = tree.children(node.identifier)

    if children:
        builder.add_group(node.tag, node.data, parent_group=parent_group)

        for child in children:
            if isinstance(child.data, AlarmLeaf):
                builder.add_pv(child.tag, node.tag, child.data)

            elif isinstance(child.data, AlarmNode):
                handle_children(builder, tree, child, parent_group=node.tag)



    def add_pv(self, pvname, group, data):
        if pvname in self.added_pvs:
            pass

        else:
            self.added_pvs.append(pvname)
            pv = ET.SubElement(self.groups[group], "pv", name=pvname)
        #    description = ET.SubElement(pv, "description")
            enabled = ET.SubElement(pv, "enabled")
            enabled.text = 'true'

            if data.force_pv is not None:
                filter_pv = ET.SubElement(pv, "filter")
                filter_pv.text = self._process_forcepv(data.force_pv)

"""
        

class AlarmTreeEditorDisplay(Display):
    def __init__(self):
        super(AlarmTreeEditorDisplay, self).__init__()

        self.app = QApplication.instance()

        # set up the ui
        self.setup_ui()

        # allow add and remove row
        self.add_button.clicked.connect(self.insertChild)
        self.remove_button.clicked.connect(self.removeItem)
        self.remove_button.setEnabled(True)

        # connect save changes
        self.button_box.accepted.connect(self.save_property_changes)

        # upon tree view selection, change the item view
        self.tree_view.selectionModel().selectionChanged.connect(self.handle_selection)
        self.tree_view.tree_model.dataChanged.connect(self.item_change)

        self.file_dialog = QFileDialog()
        self.open_config_action = QAction("Open", self)
        self.open_config_action.triggered.connect(self.open_file)
        self.toolbar.addAction(self.open_config_action)

        self.save_config_action = QAction("Save", self)
        self.save_config_action.triggered.connect(self.save_configuration)
        self.toolbar.addAction(self.save_config_action)

        # default open size
        self.resize(800, 600)


    def setup_ui(self):
        self.main_layout = QGridLayout()
        self.setLayout(self.main_layout)

        # add toolbar
        self.toolbar = QToolBar()
        self.main_layout.setMenuBar(self.toolbar)

        # create the tree view layout and add/remove buttons
        self.tree_view_layout = QVBoxLayout()
        self.tree_view = PyDMAlarmTree(self)
        self.tree_view.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.tree_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tree_view.setHeaderHidden(True)

        # Drag/drop
        self.tree_view.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree_view.setDragEnabled(True)
        self.tree_view.setAcceptDrops(True)

        # view sizing
        self.tree_view.setColumnWidth(0, 160)
        self.tree_view.setColumnWidth(1, 160)
        self.tree_view.setColumnWidth(2, 160)

        # lable for tree view
        self.tree_label = QLabel("Tree")

        self.tree_view_layout.addWidget(self.tree_label)
        self.tree_view_layout.addWidget(self.tree_view)

        # add/ remove buttons
        self.add_remove_layout = QHBoxLayout()
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding,
                             QSizePolicy.Minimum)
        self.add_remove_layout.addItem(spacer)
        self.add_button = QPushButton("New", self)
        self.add_remove_layout.addWidget(self.add_button)
        self.remove_button = QPushButton("Remove", self)
        self.add_remove_layout.addWidget(self.remove_button)
        self.tree_view_layout.addLayout(self.add_remove_layout)

        # add the tree view to the window
        self.main_layout.addLayout(self.tree_view_layout, 0, 0)


        self.properties_label = QLabel("Alarm Properties")
      

        self.property_view_layout = QGridLayout()

        self.property_view_layout.addWidget(QLabel("Alarm Properties"), 0, 0)

        # add label
        self.label_edit = QLineEdit()
        self.property_view_layout.addWidget(QLabel("LABEL"), 1, 0)
        self.property_view_layout.addWidget(self.label_edit, 1, 1, 1, 3)


        # add description
        self.description_edit = QLineEdit()
        self.property_view_layout.addWidget(QLabel("DESCRIPTION"), 2, 0)
        self.property_view_layout.addWidget(self.description_edit, 2, 1, 1, 3)


        # add delay
        self.delay_edit = QLineEdit()
        self.property_view_layout.addWidget(QLabel("DELAY"), 3, 0)
        self.property_view_layout.addWidget(self.delay_edit, 3, 1, 1, 3)

        # add count
        self.count_edit = QLineEdit()
        self.property_view_layout.addWidget(QLabel("COUNT"), 4, 0)
        self.property_view_layout.addWidget(self.count_edit, 4, 1, 1, 3)

        # enabled, latching, annunciating
        self.enabled_check = QCheckBox("ENABLED")
        self.annunciating_check = QCheckBox("ANNUNCIATING")
        self.latching_check = QCheckBox("LATCHING")
        self.property_view_layout.addWidget(self.enabled_check, 5, 0)
        self.property_view_layout.addWidget(self.annunciating_check, 5, 1)
        self.property_view_layout.addWidget(self.latching_check, 5, 2)


        spacer = QSpacerItem(40, 200, QSizePolicy.Expanding,
                             QSizePolicy.Minimum)

        self.property_view_layout.addItem(spacer, 6, 0)


        #create save button
        self.button_box = QDialogButtonBox(self)
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.addButton("Save Properties", QDialogButtonBox.AcceptRole)
        
        self.property_view_layout.addWidget(self.button_box, 7, 2)


        # TODO: command, automated actions tables

        self.main_layout.addLayout(self.property_view_layout, 0, 1)

        self.setWindowTitle("Alarm Tree Editor")
        self.tree_view.expandAll()

    def minimumSizeHint(self):
        # This is the default recommended size
        # for this screen
        return QtCore.QSize(400, 200)


    def insertChild(self):
        index = self.tree_view.selectionModel().currentIndex()
        model = self.tree_view.model()

        if model.columnCount(index) == 0:
            if not model.insertColumn(0, index):
                return

        if not model.insertRow(0, index):
            return

        for column in range(model.columnCount(index)):
            child = model.index(0, column, index)
            model.set_data(child, label="NEW_PV",
                    role=QtCore.Qt.EditRole)

        self.tree_view.selectionModel().setCurrentIndex(model.index(0, 0, index),
                QtCore.QItemSelectionModel.ClearAndSelect)
                
    def removeItem(self):
        index = self.tree_view.selectionModel().currentIndex()
        self.tree_view.model().removeRow(index.row(), index.parent())

    @Slot()
    def save_property_changes(self):
        index = self.tree_view.selectionModel().currentIndex()
        self.tree_view.model().set_data(index, 
                                    label=self.label_edit.text(),
                                    description=self.description_edit.text(),
                                    delay=self.delay_edit.text(),
                                    count=self.count_edit.text(),
                                    enabled=self.enabled_check.isChecked(),
                                    annunciating=self.annunciating_check.isChecked(),
                                    latching=self.latching_check.isChecked(),
                                    )

    #DEPRECATE
    @Slot()
    def save_configuration(self):
        pass
        #

    @Slot()
    def handle_selection(self):
        self.remove_button.setEnabled(
        self.tree_view.selectionModel().hasSelection())

        index = self.tree_view.selectionModel().currentIndex()
        item = self.tree_view.model().getItem(index)

        self.description_edit.setText(item.description)
        self.label_edit.setText(item.label)
        self.delay_edit.setText(item.delay)
        self.count_edit.setText(item.count)

        if item.enabled:
            self.enabled_check.setChecked(True)
        else:
            self.enabled_check.setChecked(False)


        if item.latching:
            self.latching_check.setChecked(True)
        else:
            self.latching_check.setChecked(False)


        if item.annunciating:
            self.annunciating_check.setChecked(True)
        else:
            self.annunciating_check.setChecked(False)


    @Slot()
    def item_change(self):
        index = self.tree_view.selectionModel().currentIndex()
        item = self.tree_view.model().getItem(index)

        self.description_edit.setText(item.description)
        self.label_edit.setText(item.label)
        self.delay_edit.setText(item.delay)
        self.count_edit.setText(item.count)

        if item.enabled:
            self.enabled_check.setChecked(True)
        else:
            self.enabled_check.setChecked(False)


        if item.latching:
            self.latching_check.setChecked(True)
        else:
            self.latching_check.setChecked(False)


        if item.annunciating:
            self.annunciating_check.setChecked(True)
        else:
            self.annunciating_check.setChecked(False)


    @Slot()
    def item_name_changed(self):
        index = self.tree_view.selectionModel().currentIndex()
        pass

    def ui_filepath(self):
        # No UI file is being used
        return None


    def to_xml(self):
        pass

        #iterate over xml

    @Slot(bool)
    def open_file(self, checked):
        modifiers = QApplication.keyboardModifiers()
        try:
            curr_file = self.current_file()
            folder = os.path.dirname(curr_file)
        except Exception:
            folder = os.getcwd()

        filename = QFileDialog.getOpenFileName(self, 'Open File...', folder, 'Configration files (*.xml)')
        filename = filename[0] if isinstance(filename, (list, tuple)) else filename

        if filename:
            filename = str(filename)
            self.import_configuration(filename)

            # TODO: implement file handler open exception handling
            #except (IOError, OSError, ValueError, ImportError) as e:
            #    self.handle_open_file_error(filename, e)



    def import_configuration(self, filename):

        config_tool = PhoebusConfigTool()
        nodes = config_tool.parse_config("test_config.xml")

        self.tree_view.model().import_hierarchy(nodes)

        




        

    



