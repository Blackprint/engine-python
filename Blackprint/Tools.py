import json
from .Types import Types
from .Internal import Internal
from .Utils import Utils
from .Port.PortFeature import Port

class Tools:
    @staticmethod
    def extractSkeleton():
        # docs = getattr(Blackprint, '_docs', {})
        nodes = {}
        virtualType = []

        def vType(type_):
            if hasattr(type_, 'virtualType'):
                return ','.join([v.name for v in type_.virtualType])

            if isinstance(type_, dict) and 'type' in type_:
                type_ = type_['type']

            if type_ == int or type_ == float: return 'Number'
            elif type_ == str: return 'String'
            elif type_ == dict: return 'Object'
            elif type_ == list: return 'Array'
            elif type_ == bool: return 'Boolean'
            elif type_ == Types.Any: return 'BP.Any'
            elif type_ == Types.Trigger: return 'BP.Trigger'
            elif type_ == Types.Route: return 'BP.Route'

            if isinstance(type_, list):
                types = []
                for i in range(len(type_)):
                    types.append(vType(type_[i]))
                return ','.join(types)

            try:
                existIndex = virtualType.index(type_)
            except ValueError:
                existIndex = len(virtualType)
                virtualType.append(type_)

            return f"{type_}.{existIndex}"

        def deep(nest, save, first=False):
            """Recursively process nested structure"""
            for key, ref in nest.items():
                if hasattr(ref, 'hidden') and ref.hidden: continue
                if first and key.startswith('BP'): continue

                #if isinstance(ref, (dict, list)):
                #    if key not in save:
                #        save[key] = {}
                #    deep(ref, save[key])
                #    continue
                # else .. ref == class

                temp = Utils.getDeepProperty(save, key.split('/'))
                if not temp:
                    temp = {}
                    Utils.setDeepProperty(save, key.split('/'), temp)

                temp['input'] = {}
                temp['output'] = {}

                for which in temp:
                    target = getattr(ref, which)
                    if not target: continue

                    for name, type_ in target.items():
                        savePort = temp[which]

                        if isinstance(type_, dict) and 'feature' in type_:
                            if type_['feature'] == Port.ArrayOf:
                                savePort[name] = f'BP.ArrayOf<{vType(type_)}>'
                            elif type_['feature'] == Port.StructOf:
                                savePort[name] = f'BP.StructOf<{vType(type_)}>'
                            elif type_['feature'] == Port.Trigger:
                                savePort[name] = 'BP.Trigger'
                            elif type_['feature'] == Port.Union:
                                savePort[name] = f'BP.Union<{vType(type_)}>'
                            elif type_['feature'] == Port.VirtualType:
                                savePort[name] = f'VirtualType<{vType(type_)}>'
                        elif type_ == int or type_ == float: savePort[name] = 'Number'
                        elif type_ == str: savePort[name] = 'String'
                        elif type_ == dict: savePort[name] = 'Object'
                        elif type_ == list: savePort[name] = 'Array'
                        elif type_ == bool: savePort[name] = 'Boolean'
                        elif type_ == Types.Any: savePort[name] = 'BP.Any'
                        elif type_ == Types.Trigger: savePort[name] = 'BP.Trigger'
                        elif type_ == Types.Route: savePort[name] = 'BP.Route'
                        else: savePort[name] = f'VirtualType<{vType(type_)}>'

                # Rename
                temp['$input'] = temp['input']
                temp['$output'] = temp['output']

                del temp['input']
                del temp['output']

        # Get nodes from Blackprint module
        try:
            nodes_dict = Internal.nodes
        except AttributeError:
            nodes_dict = {}

        deep(nodes_dict, nodes, True)

        return json.dumps({
            'nodes': nodes,
            # 'docs': docs,
        })