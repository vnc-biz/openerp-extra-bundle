# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
#    trouver un nom    for OpenERP                                              #
#    Copyright (C) 2011 Akretion Sébastien BEAU <sebastien.beau@akretion.com>   #
#                                                                               #
#    This program is free software: you can redistribute it and/or modify       #
#    it under the terms of the GNU Affero General Public License as             #
#    published by the Free Software Foundation, either version 3 of the         #
#    License, or (at your option) any later version.                            #
#                                                                               #
#    This program is distributed in the hope that it will be useful,            #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the              #
#    GNU Affero General Public License for more details.                        #
#                                                                               #
#    You should have received a copy of the GNU Affero General Public License   #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.      #
#                                                                               #
#################################################################################

import addons
import os
from tools import osutil

addons.load_module_graph_ori = addons.load_module_graph

def load_module_graph(cr, graph, status=None, perform_checks=True, skip_modules=None, **kwargs):
    for package in graph:
        if package.state  in ('to install', 'to upgrade'):
            mapping_dir = os.path.join(addons.get_module_path(package.name), 'autoload')
            exist = os.path.exists(mapping_dir)
            if exist:
                for mapping_module in osutil.listdir(mapping_dir):    
                    cr.execute("select id from ir_module_module where name = '%s' and state in ('installed', 'to_update');"%mapping_module)
                    res = cr.fetchall()
                    if res:
                        mapping_module_dir = os.path.join(mapping_dir, mapping_module)
                        files = osutil.listdir(mapping_module_dir, recursive=True)
                        for file in files:
                            if file[-4:] in ['.csv', '.xml']:
                                package.data['update_xml'].append('autoload/%s/%s'%(mapping_module,file))
    return addons.load_module_graph_ori(cr, graph, status, perform_checks, skip_modules, **kwargs)

addons.load_module_graph = load_module_graph
