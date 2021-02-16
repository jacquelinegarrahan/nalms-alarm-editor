import xml.etree.ElementTree as ET
import os
import copy
from treelib import Node, Tree


# TODO: ADD HANDLING OF SEVRCOMMAND, STATCOMMAND, ALARMCOUNTERFILETER, BEEPSEVERITY, BEEPSEVR
# TODO: Fix path handling for include files

class HeartbeatPV:
    def __init__(self, name, value=None, seconds=None):
        self.name = name

class AckPV:
    def __init__(self, name, ack_value):
        self.name = name
        self.ack_value = ack_value

class SevrPV:
    def __init__(self, name):
        self.name = name

class ForcePV:
    def __init__(self, force_mask, force_value, reset_value):
        self.force_mask=force_mask
        self.force_value = force_value
        self.reset_value = reset_value
        self.name = None 
        self.is_calc = False
        self.calc_expressions = []
        self.base_calc = ""

    def add_calc(self, expression):
        self.calc_expressions.append(expression)

class AlarmNode:
    def __init__(self, group_name, filename=None):
        self.name = group_name
        self.alias = ""
        self.commands = []
        self.sevr_pv = None
        self.force_pv = None
        self.parent = None
        self.node_children = []
        self.guidance = []
        self.guidance_url = ""
        self.main_calc = ""
        self.calcs = {}
        self.filename = filename

    def add_child(self, child):
        if child in self.node_children:
            print(f"DUPLICATE CHILD FOR GROUP {self.name}: {child}")

        else:
            self.node_children.append(child)


class AlarmLeaf:
    node_children = None
    def __init__(self, channel_name, filename=None):
        self.name = channel_name
        self.mask = None
        self.alias = ""
        self.commands = []
        self.sevr_pv = None
        self.force_pv = None
        self.guidance = []
        self.guidance_url = []
        self.main_calc = ""
        self.calcs = {}
        self.filename = ""


def build_tree(items, top_level_node):
    tree = Tree()

    # create root
    tree.create_node(top_level_node, top_level_node, data=items[top_level_node])
    processed = []

    to_process = [top_level_node]

    while len(to_process) > 0:
        node = to_process.pop(0)
        children = items[node].node_children

        if children:
            for child in children:
                print(items[child].name)
                tree.create_node(items[child].name, child, parent=node, data=items[child])

            # add children to process
            to_process += children
        
        processed.append(node)

    return tree


def parse_tree(top_level_file):
    items = {}
    # track inclusions
    # map filename to group 
    inclusions = {}

    directory = "/".join(top_level_file.split("/")[:-1])
    top_level_filename = top_level_file.split("/")[-1]
    to_process = [top_level_filename]

    in_top_level = True
    top_level_node = None
    current_level_node = None
    node_path = None
    parent_path = None
    while len(to_process) > 0:

        filename = to_process.pop(0)

        with open(f"{directory}/{filename}") as f:
            lines = f.readlines()

        if not lines:
            print(f.path)

        else:
            filename = f.name.split("/")[-1]
         #   try:
            in_guidance = False
            in_calc = False
            target = None
            parent_group = None
            if not in_top_level:
                current_level_node = inclusions[filename]

            for line in lines:
                split = line.split()

                if len(split) > 0:

                    if in_guidance:
                        if split[0] == "$END":
                            in_guidance = False

                        else: 
                            items[target].guidance.append(line)

                    else:
                        if in_calc:
                            if split[0] == "FORCEPV_CALC":
                                items[target].main_calc = split[1]

                            elif "FORCE_PV_CALC_" in split[0]:
                                identifier = split[0][-1]
                                items[target].calcs[identifier] = split[1]

                            else:
                                in_calc = False


                        # Process group
                        if split[0] == "GROUP":

                            # collect name
                            group_name = split[2]

                            # store top level 
                            if in_top_level:
                                top_level_node = copy.copy(group_name)
                                node_path = copy.copy(group_name)

                            parent = None
                            if split[1] != "NULL":
                                parent = split[1]


                            if not in_top_level:
                                if parent:
                                    parent_path = f"{current_level_node}/{parent}"
                                    node_path = f"{current_level_node}/{parent}/{group_name}"
                                else:
                                    parent_path = current_level_node
                                    node_path = f"{current_level_node}/{group_name}"

                                items[parent_path].add_child(node_path)


                            if node_path not in items:
                                items[node_path] = AlarmNode(group_name, filename=filename)

                            # update target 
                            target = node_path
                            parent_group = parent

                        # process channel
                        elif split[0] == "CHANNEL":
                            channel_name = split[2]
                            parent = split[1]

                            if parent_group and parent_group != parent:
                                parent_path = f"{current_level_node}/{parent_group}/{parent}"
                                node_path = f"{current_level_node}/{parent_group}/{parent}/{channel_name}"

                            else:
                                parent_path = f"{current_level_node}/{parent}"
                                node_path = f"{current_level_node}/{parent}/{channel_name}"

                            items[node_path] = AlarmLeaf(channel_name, filename=filename)
                            items[node_path].parent = parent_path

                            # store parent node
                            if parent_path not in items:
                                items[parent_path] = AlarmNode(parent, filename=filename)
                                items[current_level_node].add_child(parent_path)

                            items[node_path].parent = parent_path
                            items[parent_path].add_child(node_path)

                            #store mask
                            if len(split) == 4:
                                items[node_path].mask = split[3]

                            target = node_path


                        elif split[0] == "$COMMAND":
                            command = " ".join(split[1:])
                            commands = command.split("!")
                            items[target].commands += commands

                        elif split[0] == "$SEVRPV":
                            items[target].sevr_pv = SevrPV(split[1])


                        # CONFIGURE THE FORCEPV
                        elif split[0] == "$FORCEPV":
                            force_mask = split[2]

                            force_value = None
                            reset_value = None

                            if len(split) >= 4:
                                force_value = split[3]

                            if len(split) == 5:
                                reset_value = split[4]

                            items[target].force_pv = ForcePV(force_mask, force_value, reset_value)

                            if split[1] == "CALC":
                                items[target].force_pv.is_calc = True
                            
                            else:
                                force_pv_name = split[1]
                                items[target].force_pv.name = force_pv_name


                        # CONFIGURE GUIDANCE
                        elif split[0] == "$GUIDANCE":
                            if len(split) == 1:
                                in_guidance = True

                            else:
                                urlname = split[1]
                                items[target].guidance_url = urlname


                        elif split[0] == "$ALIAS":
                            items[target].alias = split[1]

                        # track inclusions
                        elif split[0] == "INCLUDE":
                            parent = split[1]

                            #HACK FIX
                            include_filename = split[2]
                            if include_filename[:2] == "./":
                                include_filename = include_filename.replace("./", "")

                            to_process.append(include_filename)

                            if in_top_level:
                                inclusions[include_filename] = parent
                            
                            else:
                                inclusions[include_filename] = f"{current_level_node}/{parent}"

                        # INCOMPLETE HANDLING
                        elif split[0] == "$ACKPV":
                            ack_pv_name = split[1]
                            # value to write when the pv is acknowledged
                            ack_value = split[2]
                            items[target] = AckPV(ack_pv_name, ack_value)

                        # Skip comments
                        elif split[0][0] == "#":
                            pass


                        ### HANDLED INCORRECTLY!!!! ONLY ONE HEARTBEATPV
                        elif split[0] == "$HEARTBEATPV":

                            heartbeat_pv_name = split[1]
                            
                            heartbeat_val = None
                            seconds = None
                            if len(split) >= 3:
                                heartbeat_val = split[2]

                            if len(split) == 4:
                                seconds = split[3]
                            
                            items[target] = HeartbeatPV(heartbeat_pv_name, seconds=seconds, value =heartbeat_val)


                        else:
                            print(f"Not found! {line}")
                            pass

            in_top_level = False

           # except Exception as e:
           #     print(e)
           #     print(f"ERROR PROCESSING FILE {filename}")


    for item_name, value in items.items():
        if not value.parent:
            if value.filename in inclusions:
                items[item_name].parent = inclusions[value.filename]



    return items, top_level_node





class XMLBuilder:
    def __init__(self, config_name, root):
        self.configuration = ET.Element("config", name=config_name)
        self.groups = {}
        self.added_pvs = []
        self.settings_artifacts = []


    def add_group(self, group, data, parent_group = None):
        group_name = group
        if data.alias:
            group_name = data.alias

        if group not in self.groups:
            if not parent_group:
                self.groups[group] = ET.SubElement(self.configuration, 'component', name=group_name)
            else:
                self.groups[group] = ET.SubElement(self.groups[parent_group], 'component', name=group_name)


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


    def _process_forcepv(self, force_pv):

        text = force_pv.name
        if force_pv.is_calc:
            formatting = force_pv.calc_expressions.pop("A")

            for key, value in force_pv.calc_expressions.items():
                formatting.replace(key, value)

        if force_pv.force_value:
            text += f" != {force_pv.force_value}"

        return text
               
    

def handle_children(builder, tree, node, parent_group=None):
    children = tree.children(node.identifier)

    if children:
        builder.add_group(node.tag, node.data, parent_group=parent_group)

        for child in children:
            if isinstance(child.data, AlarmLeaf):
                builder.add_pv(child.tag, node.tag, child.data)

            elif isinstance(child.data, AlarmNode):
                handle_children(builder, tree, child, parent_group=node.tag)



def build_config_file(tree, config_name, output_filename):

    root = tree.root
    builder = XMLBuilder(config_name, root)
    root_node = tree.get_node(root)
    handle_children(builder, tree, root_node)

    with open (output_filename, "wb") as f : 
        file_str = ET.tostring(builder.configuration, encoding='utf8') 
        f.write(file_str)



def convert_alh_to_phoebus(input_filename, output_filename):
    config_name = output_filename.split("/")[-1].replace(".xml", "")
    items, top_level_node = parse_tree(input_filename)
    tree = build_tree(items, top_level_node)
    build_config_file(tree, config_name, output_filename)

    return True