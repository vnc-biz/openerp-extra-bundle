# -*- encoding: utf-8 -*-
##############################################################################
#
#    ETL system- Extract Transfer Load system
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
"""
 To read data from dbf file.

 Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
 GNU General Public License.
"""
from etl.component import component

class dbf_in(component):
    """
    This is an ETL Component that is used to read data from csv file. Its type is data component.
    Its computing peformance is streamline.
    It has two flows
        Input Flows    : 0.
        * .*           : Nothing.
        Output Flows   : 0-x.
        * .*           : Returns the main flow with data from csv file.
    """

    def __init__(self, dbfconnector, name='component.input.dbf_in', transformer=None,):
        """
        Required  Parameters
        fileconnector   : Localfile connector.

        Extra Parameters
        name            : Name of Component.
        transformer     : Transformer object to transform string data into  particular object.
        row_limit       : Limited records are sent to destination if row limit is specified. If row limit is 0, all records are sent.
        csv_param       : To specify other csv parameter like fieldnames , restkey , restval etc.
        """
        super(dbf_in, self).__init__(name=name, connector=dbfconnector, transformer=transformer,)
        self.dbf_connector = dbfconnector
        self._type = 'component.input.dbf_in'


    def process(self):
        fields = []
        for field in self.dbf_connector.conn.fieldDefs:
            fields.append(field.name)
        for rec in self.dbf_connector.conn:
            data = {}
            for f in fields:
                data[f] = rec[f]
            yield data, 'main'

