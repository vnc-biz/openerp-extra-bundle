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
        * .*           : Returns the main flow with data from dbf file.
    """

    def __init__(self, dbfconnector, name='component.input.dbf_in', transformer=None,):
        """
        Required  Parameters
        dbfconnector   : dbf file connector.

        Extra Parameters
        name            : Name of Component.
        transformer     : Transformer object to transform string data into  particular object.
        """
        super(dbf_in, self).__init__(name=name, connector=dbfconnector, transformer=transformer)
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

    def __getstate__(self):
        res = super(dbf_in, self).__getstate__()
        return res

    def __setstate__(self, state):
        super(dbf_in, self).__setstate__(state)
        self.__dict__ = state

    def __copy__(self):
        res = dbf_in(self.dbfconnector ,self.name, self.transformer)
        return res

    def end(self):
        super(dbf_in, self).end()
        if self.dbf_connector:
            self.dbf_connector.close()
            self.dbf_connector = False

def test():
    from etl_test import etl_test
    import etl
    file_conn = etl.connector.dbf_connector('../../../demo/input/dbf_file.dbf')# /input/DE000446.dbf
    test = etl_test.etl_component_test(dbf_in(file_conn, name='dbf file test'))
    import datetime
    test.check_output([{'BD': 'MOHORN', 'TITRE_LIB': 'Frau', 'AD4': '', 'DPT': '01', 'AD2': '', 'PRENOM': 'ELISABETH', 'PAYS_CODE': 'DEU', 'AD1': '', 'NOM': 'LORENZ', 'BURDIS': '', 'NUMCLI': 59001, 'DATE2': datetime.date(2009, 11, 2), 'DDN': datetime.date(1934, 11, 23), 'DATE1': datetime.date(2009, 11, 2), 'DMTX': '', 'ACTION': 'DE000446', 'PAYS_NAME': 'ALLEMAGNE', 'CP': '01723', 'REF': 'DE000446-59001-', 'AD3': 'Nossener Str. 16'}, {'BD': 'BANNEWITZ', 'TITRE_LIB': 'Frau', 'AD4': '', 'DPT': '01', 'AD2': '', 'PRENOM': 'INGEBURG', 'PAYS_CODE': 'DEU', 'AD1': '', 'NOM': 'DANNOWSKI', 'BURDIS': '', 'NUMCLI': 79989, 'DATE2': datetime.date(2009, 11, 2), 'DDN': datetime.date(1925, 5, 6), 'DATE1': datetime.date(2009, 11, 2), 'DMTX': '', 'ACTION': 'DE000446', 'PAYS_NAME': 'ALLEMAGNE', 'CP': '01728', 'REF': 'DE000446-79989-', 'AD3': 'Braunlinger Str. 7'}, {'BD': 'POSSENDORF', 'TITRE_LIB': 'Frau', 'AD4': '', 'DPT': '01', 'AD2': '', 'PRENOM': 'Annelies', 'PAYS_CODE': 'DEU', 'AD1': '', 'NOM': 'Swoboda', 'BURDIS': '', 'NUMCLI': 19144, 'DATE2': datetime.date(2009, 11, 2), 'DDN': datetime.date(1927, 7, 16), 'DATE1': datetime.date(2009, 11, 2), 'DMTX': '', 'ACTION': 'DE000446', 'PAYS_NAME': 'ALLEMAGNE', 'CP': '01728', 'REF': 'DE000446-19144-', 'AD3': 'Schulstr. 9'}, {'BD': 'KREISCHA', 'TITRE_LIB': 'Frau', 'AD4': '', 'DPT': '01', 'AD2': '', 'PRENOM': 'IRENE', 'PAYS_CODE': 'DEU', 'AD1': '', 'NOM': 'VOGT', 'BURDIS': '', 'NUMCLI': 50238, 'DATE2': datetime.date(2009, 11, 2), 'DDN': datetime.date(1939, 12, 20), 'DATE1': datetime.date(2009, 11, 2), 'DMTX': '', 'ACTION': 'DE000446', 'PAYS_NAME': 'ALLEMAGNE', 'CP': '01731', 'REF': 'DE000446-50238-', 'AD3': 'Babisnauer Str. 20'}, {'BD': 'THARANDT', 'TITRE_LIB': 'Frau', 'AD4': '', 'DPT': '01', 'AD2': '', 'PRENOM': 'Johanna', 'PAYS_CODE': 'DEU', 'AD1': '', 'NOM': 'Pfeifer', 'BURDIS': '', 'NUMCLI': 236442, 'DATE2': datetime.date(2009, 11, 2), 'DDN': datetime.date(1915, 2, 11), 'DATE1': datetime.date(2009, 11, 2), 'DMTX': '', 'ACTION': 'DE000446', 'PAYS_NAME': 'ALLEMAGNE', 'CP': '01737', 'REF': 'DE000446-236442-', 'AD3': 'Freiberger Str. 8'}, {'BD': 'DIPPOLDISWALDE', 'TITRE_LIB': 'Frau', 'AD4': '', 'DPT': '01', 'AD2': '', 'PRENOM': 'Erika', 'PAYS_CODE': 'DEU', 'AD1': '', 'NOM': 'Nietzold', 'BURDIS': '', 'NUMCLI': 209213, 'DATE2': datetime.date(2009, 11, 2), 'DDN': datetime.date(1942, 6, 5), 'DATE1': datetime.date(2009, 11, 2), 'DMTX': '', 'ACTION': 'DE000446', 'PAYS_NAME': 'ALLEMAGNE', 'CP': '01744', 'REF': 'DE000446-209213-', 'AD3': 'Seifenstr. 2'}, {'BD': 'DIPPOLDISWALDE', 'TITRE_LIB': 'Herr', 'AD4': '', 'DPT': '01', 'AD2': '', 'PRENOM': 'Wilfried', 'PAYS_CODE': 'DEU', 'AD1': '', 'NOM': 'KR\x9aGER', 'BURDIS': '', 'NUMCLI': 235947, 'DATE2': datetime.date(2009, 11, 2), 'DDN': datetime.date(1942, 2, 15), 'DATE1': datetime.date(2009, 11, 2), 'DMTX': '', 'ACTION': 'DE000446', 'PAYS_NAME': 'ALLEMAGNE', 'CP': '01744', 'REF': 'DE000446-235947-', 'AD3': 'Altenberger Str. 34'}, {'BD': 'SCHMIEDEBERG', 'TITRE_LIB': 'Frau', 'AD4': '', 'DPT': '01', 'AD2': '', 'PRENOM': 'Irene', 'PAYS_CODE': 'DEU', 'AD1': '', 'NOM': 'Goldbach', 'BURDIS': '', 'NUMCLI': 236675, 'DATE2': datetime.date(2009, 11, 2), 'DDN': datetime.date(1930, 1, 29), 'DATE1': datetime.date(2009, 11, 2), 'DMTX': '', 'ACTION': 'DE000446', 'PAYS_NAME': 'ALLEMAGNE', 'CP': '01762', 'REF': 'DE000446-236675-', 'AD3': 'Talstr. 14'}, {'BD': 'PIRNA', 'TITRE_LIB': 'Herr', 'AD4': '', 'DPT': '01', 'AD2': '', 'PRENOM': 'Jens', 'PAYS_CODE': 'DEU', 'AD1': '', 'NOM': 'Jacob', 'BURDIS': '', 'NUMCLI': 236361, 'DATE2': datetime.date(2009, 11, 2), 'DDN': datetime.date(1964, 6, 8), 'DATE1': datetime.date(2009, 11, 2), 'DMTX': '', 'ACTION': 'DE000446', 'PAYS_NAME': 'ALLEMAGNE', 'CP': '01796', 'REF': 'DE000446-236361-', 'AD3': 'Geibeltstr. 1'}, {'BD': 'PIRNA', 'TITRE_LIB': 'Frau', 'AD4': '', 'DPT': '01', 'AD2': '', 'PRENOM': 'Isabell', 'PAYS_CODE': 'DEU', 'AD1': '', 'NOM': 'Jahn', 'BURDIS': '', 'NUMCLI': 233780, 'DATE2': datetime.date(2009, 11, 2), 'DDN': datetime.date(1964, 1, 17), 'DATE1': datetime.date(2009, 11, 2), 'DMTX': '', 'ACTION': 'DE000446', 'PAYS_NAME': 'ALLEMAGNE', 'CP': '01796', 'REF': 'DE000446-233780-', 'AD3': 'Erich-Sch\x81tze-Weg 7'}])
    res = test.output()
    print res

if __name__ == '__main__':
    test()
