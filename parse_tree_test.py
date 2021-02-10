import xml.etree.ElementTree as ET




class PhoebusConfigTool:

    def __init__(self):
        self._nodes = []

    def parse_config(self, filename):
        """
        Parses a configuration file
        """
        self._tree = ET.parse(filename)
        self._root = self._tree.getroot()

        # add root item to tree
        parent = None
        self._nodes.append(self._root)

        if self._root.tag == "config":
            self._config_name = self._root.tag
            
            for child in self._root:
                if child.tag == "component":
                    self._handle_group(child, 0)

                elif child.tag == "pv":
                    self._handle_pv(child, 0)

        return self._nodes


    def build_config(self):
        pass


    def _handle_pv(self, pv, parent_idx):
        data = {}
        self._nodes.append([data, parent_idx])

    
    def _handle_group(self, group, parent_idx):
        # add group
        data = {}
        self._nodes.append([data, parent_idx])
        group_idx = len(self._nodes) - 1 

        for child in group:
            if child.tag == "component":
                self._handle_group(child, group_idx)

            elif child.tag == "pv":
                self._handle_pv(child, group_idx)

    



if __name__ == "__main__":
    config = PhoebusConfig()
    config.parse_config("test_config.xml")