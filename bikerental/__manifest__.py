# -*- coding: utf-8 -*-
{
    'name': 'Bike Rental',
    'version': '1.0',
    'summary': 'Simple Bike Rental module with Website',
    'description': 'A simple Odoo 18 module for managing bikes for rent with frontend website.',
    'author': 'Kamal',
    'category': 'Sales',
    'depends': ['base', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/bike_view.xml',
        'views/website_templates.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
