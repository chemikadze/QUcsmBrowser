#!/usr/bin/python


from pyucsm import UcsmObject


def dict_to_mo(dct):
    try:
        obj = UcsmObject(dct.pop('__class'))
        children = dct.pop('__children', [])
        obj.attributes.update(dct)
        for child in children:
            obj.children.append(dict_to_mo(child))
        return obj
    except KeyError:
        return None

def create_tree():
    TREE =  \
        {
            "__class": "topRoot",
            "dn": "",
            "__children": [
                {
                    "__class": "systemRoot",
                    "dn": "sys",
                    "rn": "sys",
                    "comment": "This is system root",
                    "__children": [
                        {
                            "__class": "computeChassis",
                            "dn": "sys/chassis-1",
                            "rn": "chassis-1"
                        }
                    ]
                }
            ]
        }
    return dict_to_mo(TREE)