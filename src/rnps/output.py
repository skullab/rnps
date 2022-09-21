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

from datetime import datetime
import json
import sys
from typing import Any
from rnps.validator import Validator
from rnps.version import Version

class Output:

    def __init__(   self,
                    validator: Validator
                ) -> None:
        self.validator = validator
        self.result = None

    def setResult(self,result):
        self.result = result

    def header(self) -> str:
        return f"RNPS ver {Version.MAJOR}.{Version.MINOR}.{Version.PATCH}\n"
    
    def startTimestamp(self,timestamp) -> str:
        return f"Scan started at {datetime.fromtimestamp(timestamp)}\n"

    def elapsedTimestamp(self,timestamp) -> str:
        return f"Scan performed in {round(timestamp,2)} seconds\n"

    def hostHeader(self,host,total_of,total,tot_done,tot_not_done):
        return f"\nHost {host}\nTotal ports scanned {total} (of {total_of}), not open {tot_not_done}, open {tot_done}\n"

    def line(self,length:int):
        return "-" * length + "\n"

    def stats(self):
        content = self.startTimestamp(self.result["timestamps"]["start"])
        content += self.elapsedTimestamp(self.result["timestamps"]["elapsed"])
        for host in self.result["hosts"]:
            total_of = len(self.validator.getArgs().getPorts())
            total = total_of - len(self.result["errors"]["task"])
            tot_done = 0
            tot_not_done = total
            for port in self.result["hosts"][host]:
                if port["result"] == 0:
                    tot_done += 1
                    tot_not_done -= 1
            content += self.hostHeader(host,total_of,total,tot_done,tot_not_done)
            if tot_done == 0 and not self.validator.verbose():
                continue
            content += self.portTable(host)
        if len(self.result["hosts"]) == 0:
            content += "No results !\n"
        return content

    def portTableTabulation(self):
        return "{:<7} {:<5} {:<6} {:<7}\n"

    def portTableHeader(self):
        header = self.portTableTabulation().format("PORT","TYPE","STATE","SERVICE")
        line = self.line(len(header))
        return line + header + line

    def portTableRow(self,port):
        return self.portTableTabulation().format(port["port"],port["port_type"],"open" if port["result"] == 0 else port["result"],port["service"])

    def portTable(self,host):
        ports = self.result["hosts"][host]
        table = self.portTableHeader()
        for port in ports:
            if port["result"] != 0 and not self.validator.verbose():
                continue
            table += self.portTableRow(port)
        return table

    def toJSON(self):
        content = self.result
        content["name"] = "RNPS (Rapid Network Port Scan)"
        content["version"] = f"{Version.MAJOR}.{Version.MINOR}.{Version.PATCH}"
        content["cmdline"] = self.validator.getArgs().getCmdLine()
        return json.dumps(content,indent=4)

    def checkForErrors(self):
        tot_main_errs = len(self.result["errors"]["main"])
        tot_task_errs = len(self.result["errors"]["task"])
        tot_timeout_errs = len(self.result["errors"]["timeout"])

        content = "\n"
        if tot_timeout_errs > 0:
            content += "WARNING ! The scan is incomplete !\n"
            content += f"Timeout Error were found while running the scan.\n"
            err = self.result["errors"]["timeout"][0]["description"]
            content += f"{err}"
        if  tot_main_errs > 0:
            content += f"ALERT ! Errors were found while running the scan. Total errors found {tot_main_errs}\n"
            err = self.result["errors"]["main"][0]["description"]
            content += f"{err}"
        if tot_task_errs > 0:
            content += "WARNING ! The scan is incomplete !\n"
            content += f"Errors were encountered during the execution of individual tasks. Total errors found {tot_task_errs}\n"
            content += "Try rescan with the -t parameter, or increase the number of system processes.\nType -h for more information.\n"
        return content

    def send(self):
        if self.result is None:
            return
        content = self.toJSON() if self.validator.json() else self.stats()
        if self.validator.filename() is not None:
            with open(self.validator.filename(),"w") as f:
                if not self.validator.json():
                    f.write(self.header())
                f.write(content)
            sys.stdout.write(f"Done ! See results in file {self.validator.filename()}")
        else:
            sys.stdout.write(content)
        sys.stdout.write("\n")
        sys.stdout.write(self.checkForErrors())