import hou


class KitBashTool:

    def __init__(self):
        self.asset_name = None

    def createTemplate(self):
        stage_path = '/stage'

        for sub in hou.selectedNodes():
            n_material_network = hou.node(sub.path()+ '/materials')
            # hash map for all materials in pack
            textures_hash_map = {}
            for child in n_material_network.children():
                textures_hash_map[child.name()] = child

            # print(len(textures_hash_map))
            # print(len(n_material_network.children()))

            for geo_node in sub.children():
                if geo_node.type().name()=='geo':
                    for file_node in geo_node.children():
                        if file_node.type().name()=='file':
                            self.asset_name = "_".join(file_node.name().split('_')[2:])

                            # SOP create node
                            n_sopcreate = hou.node(stage_path).createNode('sopcreate', self.asset_name)
                            n_sopcreate.parm('enable_partitionattribs').set(0)

                            # SOP cleaning geo
                            n_file = hou.copyNodesTo((file_node,), hou.node(n_sopcreate.path() + '/sopnet/create'))[0]

                            # n_file = hou.node(n_sopcreate.path() + '/sopnet/create/').createNode('file')
                            # n_file.parm('file').set(dirpath + '/' + fbx_file)

                            n_block_begin = n_file.createOutputNode('block_begin', 'foreach_begin1')
                            n_block_begin.parm('method').set(1)
                            n_block_begin.parm('blockpath').set('../foreach_end1')
                            n_block_begin.parm('createmetablock').pressButton()

                            n_metadata = hou.node(n_block_begin.parent().path() + '/foreach_begin1_metadata1')
                            n_metadata.parm('method').set(2)
                            n_metadata.parm('blockpath').set('../foreach_end1')

                            n_attribwrangle = n_block_begin.createOutputNode('attribwrangle')
                            n_attribwrangle.setInput(1, n_metadata)
                            n_attribwrangle.parm('class').set(1)
                            # n_attribwrangle.parm('snippet').set(
                            #     'string assets[] = {"Body","Eye", "Glasses", "Hair", "Bottom", "Footwear", "Top", "Skin", '
                            #     '"Teeth"};\ns@path = "/" + assets[detail(1,"iteration")];')
                            n_attribwrangle.parm('snippet').set(
                                'string names = s@shop_materialpath;\nstring parts[] = split(names, '
                                '"_");\nstring result = "";\nif (len(parts)>2) {\n    result = parts[2];'
                                '\n}\nelse{\n    printf(names);\n    '
                                '}\ns@path = "/" + result;')




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
                            materials=[]
                            for i in range(0, numiterations):
                                n_block_end.parm('singlepass').set(i)
                                geometry = n_block_end.geometry()
                                materials.append(geometry.prim(0).stringAttribValue('shop_materialpath'))

                            # print(materials)
                            n_block_end.parm('dosinglepass').set(0)

                            n_attribdelete = n_block_end.createOutputNode('attribdelete')
                            n_attribdelete.parm('ptdel').set('* ^P')
                            # n_attribdelete.parm('primdel').set('* ^path')

                            n_output = n_attribdelete.createOutputNode('output')
                            n_output.setGenericFlag(hou.nodeFlag.Display, True)
                            n_output.setGenericFlag(hou.nodeFlag.Render, True)

                            # proper naming structure
                            n_primitive = hou.node(stage_path).createNode('primitive')
                            n_primitive.parm('primpath').set(f'/{self.asset_name}')
                            n_primitive.parm('primkind').set('component')

                            n_graftstages = n_primitive.createOutputNode('graftstages')
                            n_graftstages.parm('primkind').set('subcomponent')
                            n_graftstages.setNextInput(n_sopcreate)

                            # materials
                            n_materiallibrary = n_graftstages.createOutputNode('materiallibrary')
                            n_materiallibrary.parm('materials').set(len(materials))


                            for i, material in enumerate(materials):
                                short_material_name = material.split('_')[2]
                                n_materiallibrary.parm(f"matnode{i + 1}").set(short_material_name)
                                n_materiallibrary.parm(f"matpath{i + 1}").set(
                                    f'/{self.asset_name}/materials/{short_material_name}_mat')
                                n_materiallibrary.parm(f"assign{i + 1}").set(1)
                                n_materiallibrary.parm(f"geopath{i + 1}").set(
                                    f'/{self.asset_name}/{self.asset_name}/{short_material_name}')

                                n_subnet = n_materiallibrary.createNode('subnet', short_material_name)
                                # take texture from hashmap
                                if material in textures_hash_map:
                                    n_shader = hou.copyNodesTo((textures_hash_map[material],), n_subnet)[0]
                                    n_suboutput = hou.node(n_subnet.path() + '/suboutput1')
                                    shader_output = n_shader.outputIndex('surface')
                                    n_suboutput.setNextInput(n_shader, shader_output)

                                    # print("name is in hash-map")
                                else:
                                    print(material + ' not found')

                                n_subnet.layoutChildren()
                                n_subnet.setMaterialFlag(True)

                            n_materiallibrary.layoutChildren()
                            n_materiallibrary.setGenericFlag(hou.nodeFlag.Display, True)
                            n_materiallibrary.setGenericFlag(hou.nodeFlag.Render, True)

                            # exporting
                            n_usd_rop = n_materiallibrary.createOutputNode('usd_rop')
                            n_usd_rop.parm('lopoutput').set('D:/Assets/Kitbash3D - Brooklyn' + '/usd_export/' + self.asset_name + '.usd')
                            n_usd_rop.parm('execute').pressButton()
                            n_usd_rop.setSelected(True)
                            hou.node(stage_path).layoutChildren()
