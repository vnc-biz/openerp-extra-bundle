# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
#
##############################################################################
{
    'name' : 'Better zip management',
    'version' : '0.1',
    'depends' : [
                 'base',
                 ],
    'author' : 'Camptocamp',
    'description': """This introduce a better zip/npa management system""",
    'website': 'http://www.camptocamp.com',
    'init_xml': ['security/security.xml'],
    'update_xml': [
                    'better_zip_view.xml',
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}