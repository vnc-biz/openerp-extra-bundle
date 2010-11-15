# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
#
##############################################################################
{
    'name' : 'Better zip management data for CH',
    'version' : '0.1',
    'depends' : [
                 'better_zip',
                 ],
    'author' : 'Camptocamp',
    'description': """better zip data for Switzerland""",
    'website': 'http://www.camptocamp.com',
    'init_xml': [],
    'update_xml': [
                    'l10n_ch_better_zip.xml',
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}