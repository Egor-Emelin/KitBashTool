import os

import hou
from collections import defaultdict

class KitBashTool:

    def __init__(self):
        self.asset_name = None
        self.stage_path = '/stage'
        self.grouped_assets_map = None
        self.textures_hash_map = None
        self.named_locators = None
        self.all_usds_rops = []
        self.last_node = None

    def getData(self):
        # self.stage_path = '/stage'

        for sub in hou.selectedNodes():
            n_material_network = hou.node(sub.path()+ '/materials')

            # hash map for all materials in pack
            self.textures_hash_map = {}
            for child in n_material_network.children():
                self.textures_hash_map[child.name()] = child

            # print(len(self.textures_hash_map))
            # print(len(n_material_network.children()))
            self.grouped_assets_map = defaultdict(list)
            self.named_locators = {}
            for geo_node in sub.children():
                if geo_node.type().name() == 'geo':
                    if geo_node.input(0) is not None:
                        locator = geo_node.input(0)
                        locator_name = "_".join(locator.name().split('_')[2:])
                        if locator_name in self.named_locators.keys():
                            # merge assets
                            self.grouped_assets_map[locator_name].append(geo_node)
                        else:
                            self.named_locators[locator_name] = locator
                            self.grouped_assets_map[locator_name].append(geo_node)
                elif geo_node.type().name() == 'subnet':
                    locator = geo_node
                    locator_name = "_".join(locator.name().split('_')[2:5])
                    self.grouped_assets_map[locator_name].append(geo_node)

            self.createTemplate()


    def createTemplate(self):
        for locator, nodes in self.grouped_assets_map.items():
            # proper naming structure
            n_primitive = hou.node(self.stage_path).createNode('primitive')
            n_primitive.parm('primpath').set(f'/{locator}')
            n_primitive.parm('primkind').set('component')

            if locator in self.named_locators.keys():
                n_global_transform = n_primitive.createOutputNode('xform')
                n_global_transform.parmTuple('t').set(self.named_locators[locator].parmTuple('t'))
                n_global_transform.parmTuple('r').set(self.named_locators[locator].parmTuple('r'))
                n_global_transform.parmTuple('s').set(self.named_locators[locator].parmTuple('s'))
                n_global_transform.parm('scale').set(self.named_locators[locator].parm('scale'))
                n_graftstages = n_global_transform.createOutputNode('graftstages')
            else:
                print("Locator name not found")
                n_graftstages = n_primitive.createOutputNode('graftstages')

            n_graftstages.parm('primkind').set('subcomponent')
            self.last_node = n_graftstages

            for node in nodes:
                sopcreates = self.cleanGeo(node, locator)
                for n_sopcreate in sopcreates:
                    n_graftstages.setNextInput(n_sopcreate)

            # export nodes
            n_usd_rop = self.last_node.createOutputNode('usd_rop')
            n_usd_rop.parm('lopoutput').set(locator + '.usd')
            self.all_usds_rops.append(n_usd_rop)

        n_usd_rop.setSelected(True)
        hou.node(self.stage_path).layoutChildren()


    def cleanGeo(self, node, locator=None):
        sopcreates = []
        for file_node in node.children():
            if file_node.type().name() == 'file':
                self.asset_name = "_".join(file_node.name().split('_')[2:])

                # SOP create node
                n_sopcreate = hou.node(self.stage_path).createNode('sopcreate', self.asset_name)
                n_sopcreate.parm('enable_partitionattribs').set(0)
                sopcreates.append(n_sopcreate)

                # SOP cleaning geo
                n_file = hou.copyNodesTo((file_node,), hou.node(n_sopcreate.path() + '/sopnet/create'))[0]

                if node.type().name() != 'subnet':
                    transform = node
                elif node.type().name() == 'subnet':
                    transform = file_node.outputs()[0]
                n_transform = n_file.createOutputNode('xform')
                n_transform.parmTuple('t').set(transform.parmTuple('t'))
                n_transform.parmTuple('r').set(transform.parmTuple('r'))
                n_transform.parmTuple('s').set(transform.parmTuple('s'))
                # n_transform.parmTuple('shear').set(node.parmTuple('shear'))
                n_transform.parm('scale').set(transform.parm('scale'))

                n_block_begin = n_transform.createOutputNode('block_begin', 'foreach_begin1')
                n_block_begin.parm('method').set(1)
                n_block_begin.parm('blockpath').set('../foreach_end1')
                n_block_begin.parm('createmetablock').pressButton()

                n_metadata = hou.node(n_block_begin.parent().path() + '/foreach_begin1_metadata1')
                n_metadata.parm('method').set(2)
                n_metadata.parm('blockpath').set('../foreach_end1')

                n_attribwrangle = n_block_begin.createOutputNode('attribwrangle')
                n_attribwrangle.setInput(1, n_metadata)
                n_attribwrangle.parm('class').set(1)
                n_attribwrangle.parm('snippet').set(
                    'string names = s@shop_materialpath;\nstring result = "";\nstring parts[] = split(names, "/");\n'
                    'if (len(parts)>1) {\n    s@shop_materialpath = parts[3];\n    parts = split(parts[3], "_");\n'
                    '    }\nelse {\n    parts = split(parts[0], "_");\n'
                    '    }\n\nif (len(parts)>2) {\n    result = parts[2];\n}\nelse{\n'
                    '    //printf(names);\n    result = parts[1];\n    }\ns@path = "/" + result;\n')

                n_block_end = n_attribwrangle.createOutputNode('block_end', 'foreach_end1')
                n_block_end.parm('itermethod').set(1)
                n_block_end.parm('method').set(1)
                n_block_end.parm('class').set(0)
                n_block_end.parm('useattrib').set(1)
                n_block_end.parm('attrib').set('shop_materialpath')
                n_block_end.parm('blockpath').set('../foreach_begin1')
                n_block_end.parm('templatepath').set('../foreach_begin1')

                numiterations = n_metadata.geometry().attribValue('numiterations')
                n_block_end.parm('dosinglepass').set(1)

                materials = []
                for i in range(0, numiterations):
                    n_block_end.parm('singlepass').set(i)
                    geometry = n_block_end.geometry()
                    materials.append(geometry.prim(0).stringAttribValue('shop_materialpath'))

                # print(materials)
                n_block_end.parm('dosinglepass').set(0)

                n_attribdelete = n_block_end.createOutputNode('attribdelete')
                n_attribdelete.parm('ptdel').set('* ^P')
                n_attribdelete.parm('primdel').set('* ^path')

                n_output = n_attribdelete.createOutputNode('output')
                n_output.setGenericFlag(hou.nodeFlag.Display, True)
                n_output.setGenericFlag(hou.nodeFlag.Render, True)

                self.createMaterials(materials, locator)

        return sopcreates


    def createMaterials(self, materials, locator='/'):
        # materials
        n_materiallibrary = self.last_node.createOutputNode('materiallibrary', self.asset_name+'_mat')
        n_materiallibrary.parm('materials').set(len(materials))
        self.last_node = n_materiallibrary
        for i, material in enumerate(materials):
            short_material_name = material.split('_')[2]
            n_materiallibrary.parm(f"matnode{i + 1}").set(short_material_name)
            n_materiallibrary.parm(f"matpath{i + 1}").set(
                f'/{locator}/{self.asset_name}/materials/{short_material_name}_mat')
            n_materiallibrary.parm(f"assign{i + 1}").set(1)
            n_materiallibrary.parm(f"geopath{i + 1}").set(
                f'/{locator}/{self.asset_name}/{short_material_name}')

            n_subnet = n_materiallibrary.createNode('subnet', short_material_name)
            # take texture from hashmap
            if material in self.textures_hash_map:
                n_shader = hou.copyNodesTo((self.textures_hash_map[material],), n_subnet)[0]
                n_suboutput = hou.node(n_subnet.path() + '/suboutput1')
                shader_output = n_shader.outputIndex('surface')
                n_suboutput.setNextInput(n_shader, shader_output)
                # print("name is in hash-map")

            else:
                print(material + ' not found')

            n_subnet.layoutChildren()
            n_subnet.setMaterialFlag(True)

            n_materiallibrary.layoutChildren()


    def USDexport(self, path: str):
        for n_usd_rop in self.all_usds_rops:
            n_usd_rop.parm('lopoutput').set(path +  n_usd_rop.parm('lopoutput').eval())
            n_usd_rop.parm('execute').pressButton()

    def refImport(self, dirpath: str):
        # import all USD assets as reference
        n_reference = hou.node(self.stage_path).createNode('reference::2.0')
        n_reference.parm('num_files').set(len(os.listdir(dirpath)))
        for index, file in enumerate(os.listdir(dirpath)):
            n_reference.parm(f'filepath{index+1}').set(dirpath+file)

        n_reference.setSelected(True)
        hou.node(self.stage_path).layoutChildren()