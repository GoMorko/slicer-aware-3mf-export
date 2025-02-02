import xml.etree.ElementTree as ET

__all__ = [
    'ET',
    'ns',
]

ET.register_namespace('', 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02')
ET.register_namespace('m', 'http://schemas.microsoft.com/3dmanufacturing/material/2015/02')
ET.register_namespace('p', 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06')

ns = {
    'core': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02',
    'material': 'http://schemas.microsoft.com/3dmanufacturing/material/2015/02',
    'production': 'http://schemas.microsoft.com/3dmanufacturing/production/2015/06',
}
