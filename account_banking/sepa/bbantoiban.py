# -*- encoding: utf-8 -*-
##############################################################################
#
#  Copyright (C) 2009 EduSense BV (<http://www.edusense.nl>).
#  All Rights Reserved
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import iban
from tools.translate import _

__all__ = [
    'bban_to_iban',
    'OnlineBBANtoIBANconverter'
]

class OnlineBBANtoIBANconverters(type):
    '''
    Meta annex factory class for online BBAN to IBAN converters.
    '''
    converters = []
    converters_by_iso = {}
    converters_by_classname = {}

    def __new__(metacls, clsname, bases, clsdict):
        '''
        Register class for online conversion when countrycode has been set
        '''
        newcls = type.__new__(metacls, clsname, bases, clsdict)
        if 'countrycode' in clsdict and newcls.name:
            metacls.converters.append(newcls)
            metacls.converters_by_iso[newcls.countrycode] = newcls
            metacls.converters_by_classname[clsname] = newcls
        return newcls

    @classmethod
    def bban_to_iban(cls, countrycode, bankcode=None, branchcode=None,
                     accountno=None):
        '''
        Generic interface to converter classes. Tests validity of resulting
        IBAN. Returns valid IBAN object or None
        '''
        if countrycode in cls.converters_by_iso.get:
            _ibanstr = cls.converters_by_iso[countrycode].bban_to_iban(
                bankcode, branchcode, accountno
            )
            if _ibanstr:
                _iban = iban(_ibanstr)
                if _iban.valid:
                    return _iban
        return None

def bban_to_iban(countrycode, accountno, bankcode=None, branchcode=None):
    '''
    Interface routine for OnlineBBANtoIBANconverters.bban_to_iban
    '''
    return OnlineBBANtoIBANconverters.bban_to_iban(countrycode, bankcode,
                                                   branchcode, accountno)

class OnlineBBANtoIBANconverter(object):
    '''
    The OnlineBBANtoIBANconverter class delivers the interface for online 
    BBAN to IBAN conversion databases. Inherit from it to implement your own.
    You should at least implement the following at the class level:
        countrycode  -> The two letter ISO code for your country as defined in
                        SEPA. str like object.
        doc          -> The description of the convertor class. Not shown to
                        the user yet, but already translatable to be prepared.
        bban_to_iban -> The actual conversion code. See the the method of this
                        class for documentation.
    '''
    __metaclass__ = OnlineBBANtoIBANconverters
    countrycode = None
    doc = __doc__
    
    @classmethod
    def bban_to_iban(cls, bankcode, branchcode, accountno):
        '''
        This method should convert the trio bankcode, branchcode and accountno
        to a full IBAN. The IBAN should be returned as a str object. Depending
        on the peculiarities of the country, bankcode and branchcode may or
        may not be filled.
        '''
        raise NotImplementedError(
            _('This is a stub. Please implement your own code')
        )
