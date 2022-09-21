# ----------------------------------------------------------------------------------------
# RNPS aka Rapid Network Port Scan
# Copyright (C) 2022 Ivan Maruca <ivan>DOT<maruca>AT<gmail>DOT<com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see https://www.gnu.org/licenses/agpl-3.0.en.html
# ----------------------------------------------------------------------------------------

from rnps.args import Args
from rnps.host import Host
from rnps.port import Port
from rnps.scan import Scan

class Validator:
    def __init__(self) -> None:
        self.__args = Args()
        self.__errors = []

    def validate(self) -> list:
        try:
            self.host = Host(self.__args.getHost())
            self.port = Port(self.__args.getPorts(),self.__args.getPortType())
            self.scan = Scan(host=self.host,port=self.port,verbose=self.verbose(),maxThreads=self.__args.getMaxThreads())
        except Exception as e:
            self.__errors.append(e)

        return self.__errors

    def getErrors(self) -> list:
        return self.__errors

    def getArgs(self) -> Args:
        return self.__args

    def getScan(self) -> Scan:
        return self.scan

    def verbose(self) -> bool:
        return self.__args.isVerbose()

    def json(self) -> bool:
        return self.__args.isJSON()

    def filename(self) -> str :
        return self.__args.filename()