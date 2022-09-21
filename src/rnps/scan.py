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

from ipaddress import IPv4Address
from pickle import LIST
from random import randint
import socket
import struct
from threading import Thread
from time import time
from typing import Any, Callable, Iterable, Mapping
from rnps.host import Host
from rnps.port import Port, PortService
import concurrent.futures
######################################################################################################
class ScanException(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

######################################################################################################
class ScanResult:

    def __init__(self) -> None:
        self.__result = {
            "timestamps":{
                "start":0,
                "end":0,
                "elapsed":0
            },
            "hosts":{},
            "errors":{
                "main":[],
                "task":[],
                "timeout":[]
            }
        }

    def setStartTimestamp(self,timestamp):
        self.__result["timestamps"]["start"] = timestamp

    def setEndTimestamp(self,timestamp):
        self.__result["timestamps"]["end"] = timestamp

    def setElapsedTimestamp(self,timestamp):
        self.__result["timestamps"]["elapsed"] = timestamp

    def addHostResult(self,host,result=None):
        if host not in self.__result["hosts"]:
            self.__result["hosts"][host] = []
        if result is not None:
            self.__result["hosts"][host].append(result)

    def getStartTimestamp(self) -> float:
        return self.__result["timestamps"]["start"]
    
    def getEndTimestamp(self) -> float:
        return self.__result["timestamps"]["end"]

    def getElapsedTimestamp(self) -> float:
        return self.__result["timestamps"]["elapsed"]

    def getHosts(self):
        return self.__result["hosts"]

    def getResults(self):
            return self.__result
    
    def addMainError(self,e):
        self.__result["errors"]["main"].append({
            "timestamp": time(),
            "description": str(e)
        })

    def addTaskError(self,e):
        self.__result["errors"]["task"].append({
            "timestamp": time(),
            "description": str(e)
        })

    def addTimeoutError(self,e):
         self.__result["errors"]["timeout"].append({
            "timestamp": time(),
            "description": str(e)
        })

    def getMainErrors(self):
        return self.__result["errors"]["main"]

    def getTaskErrors(self):
        return self.__result["errors"]["task"]

    def getTimeoutErrors(self):
        return self.__result["errors"]["timeout"]

######################################################################################################
class Scan(Thread):

    def __init__(   self, 
                    group: None = None, 
                    target: Callable = None, 
                    name: str = "RNPS-Scan-Thread", 
                    args: Iterable[Any] = None, 
                    kwargs: Mapping[str, Any] = None, 
                    *, 
                    daemon: bool = True,
                    host: Host = None,
                    port: Port = None,
                    verbose: bool = False,
                    maxThreads: int = None,
                    ) -> None:
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        if host is None :
            raise ScanException("Host is required")
        if port is None:
            raise ScanException("Port is required")
        self.host = host
        self.port = port
        self.verbose = verbose
        self.maxThreads = maxThreads
        self.results = ScanResult()

    def getMaxWorkers(self):
        max_workers = sum(1 for n in self.host.address.network.hosts()) * len(self.port.range)
        if self.maxThreads is not None:
            max_workers = min(self.maxThreads,max_workers)
        return max_workers

    def run(self):
        try:
            self.results.setStartTimestamp(time())
            futures = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.getMaxWorkers()) as executor:
                for address in self.host.address.network.hosts():
                        for port in self.port.range:
                            futures.append(executor.submit(self.task,address,port,self.port.type))
                for d in concurrent.futures.as_completed(futures):
                    try:
                        item = d.result()
                        host = item.pop("host")
                        if item["result"] != 0 and not self.verbose:
                            self.results.addHostResult(host,None)
                        else:
                            self.results.addHostResult(host,item)
                    except Exception as e:
                        self.results.addTaskError(e)
        except concurrent.futures.TimeoutError as e:
            self.results.addTimeoutError(e)
        except Exception as e:
            self.results.addMainError(e)
        finally:
            self.results.setEndTimestamp(time())
            self.results.setElapsedTimestamp(self.results.getEndTimestamp() - self.results.getStartTimestamp())
        
    def task(self,address,port,port_type):
        socket_type = socket.SOCK_STREAM if port_type == Port.TCP else socket.SOCK_DGRAM
        socket_family = socket.AF_INET if type(address) is IPv4Address else socket.AF_INET6
        with socket.socket(socket_family, socket_type) as sock:
            sock.settimeout(1)
            r = -1
            try:
                if port_type == Port.TCP:
                    r = sock.connect_ex((str(address),port))
                else:
                    sock.sendto(bytes(self.getDataPacket(str(address),port)),(str(address),port))
                    sock.recvfrom(1024)
                    r = 0
            except socket.error as e:
                 r = -1
            finally:
                sock.close()
                service = PortService.getServiceName(port)
                return {"host":str(address),"port":port,"port_type":port_type,"service":service,"result":r}

    def getDataPacket(self,host,port):
        packet = struct.pack(">H",port)
        packet += struct.pack(">H", 0x0100)
        packet += struct.pack(">H", 1)
        packet += struct.pack(">H", 0)
        packet += struct.pack(">H", 0)
        packet += struct.pack(">H", 0)
        for h in host.split("."):
            packet += struct.pack("B", len(h))
            for s in h:
                packet += struct.pack('c',s.encode())
        packet += struct.pack("B", 0)
        packet += struct.pack(">H", 1)
        packet += struct.pack(">H", 1)
        return packet

    def result(self):
        return self.results.getResults()

    def getStartTimestamp(self):
        return self.results.getStartTimestamp()