{
    'name': 'Deboning Process',
    'version': '16.0',
    'category': 'Inventory',
    'summary': 'Custom module for deboning process with multi-warehouse support',
    'author': 'Amare Tilaye',
    'website': 'www.ktstech.com',
    'depends': ['stock', 'product', 'inventory_pb','mail'],
    'data': [
        'views/custom_bom_views.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/deboning_order_views.xml',
        'views/menu_items.xml',
        'data/sequence_data.xml',

    ],
    'installable': True,
    'application': False,
}
