# __init__.py

def classFactory(iface):
    from .table_compare_plugin import TableComparePlugin
    return TableComparePlugin(iface)