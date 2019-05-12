import os


class Dict(dict):
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__


def dict_to_object(dictObj):
    if not isinstance(dictObj, dict):
        return dictObj
    inst = Dict()
    for k, v in dictObj.items():
        inst[k] = dict_to_object(v)
    return inst


def get_mysql_package():
    file = os.listdir("./MDBMP/mysql_related/mysql_package")
    mysql_package_list = []
    for i in file:
        dict = {}
        dict['pack_name'] = i
        dict_to_object(dict)
        mysql_package_list.append(dict)
    return mysql_package_list


if __name__ == "__main__":
    file = get_mysql_package()
    print(file)
