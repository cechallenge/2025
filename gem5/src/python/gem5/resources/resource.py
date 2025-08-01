# Copyright (c) 2021-2023 The Regents of the University of California
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import inspect
import os
from abc import ABCMeta
from functools import partial
from pathlib import Path
from typing import (
    Any,
    Dict,
    Generator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
)

from m5.util import (
    fatal,
    warn,
)

from _m5 import core

from ..isas import (
    ISA,
    get_isa_from_str,
)
from .client import (
    get_multiple_resource_json_obj,
    get_resource_json_obj,
)
from .client_api.client_query import ClientQuery
from .downloader import get_resource
from .elfie import ELFieInfo
from .looppoint import (
    LooppointCsvLoader,
    LooppointJsonLoader,
)

"""
Resources are items needed to run a simulation, such as a disk image, kernel,
or binary. The gem5 project provides pre-built resources, with sources, at
<resources.gem5.org>. Here we provide the AbstractResource class and its
various implementations which are designed to encapsulate a resource for use
in the gem5 Standard Library.

These classes may be contructed directly. E.g.:

.. code-block:: python

	binary = BinaryResource(local_path="/path/to/binary")


or obtained via the gem5-resources infrastructure with the ``obtain_resource``
function:

.. code-block:: python

	binary = obtain_resource("resource name here")

"""


class AbstractResource:
    """
    An abstract class which all Resource classes inherit from.
    """

    __metaclass__ = ABCMeta

    def __init__(
        self,
        id: Optional[str] = None,
        resource_version: Optional[str] = None,
        local_path: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        downloader: Optional[partial] = None,
    ):
        """
        :param local_path: The path on the host system where this resource is
                           located.
        :param description: Description describing this resource. Not a
                            required parameter. By default is ``None``.
        :param source: The source (as in "source code") for this resource. This
                       string should navigate users to where the source for this
                       resource may be found. Not a required parameter. By default
                       is ``None``.
        :param resource_version: Version of the resource itself.
        :param downloader: A partial function which is used to download the
        resource. If set, this is called if the resource is not present at the
        specified `local_path`.
        """

        self._id = id
        self._local_path = local_path
        self._description = description
        self._source = source
        self._version = resource_version
        self._downloader = downloader

    def get_id(self) -> str:
        """Returns the ID of the resource."""
        return self._id

    def get_category_name(cls) -> str:
        raise NotImplementedError

    def __str__(self):
        message = (
            f"{self.get_category_name()}({self._id}, {self._version})\n"
            "For more information, please visit "
            f"https://resources.gem5.org/resources/{self._id}?"
            f"version={self._version}"
        )
        return message

    def get_resource_version(self) -> str:
        """Returns the version of the resource."""
        return self._version

    def get_local_path(self) -> Optional[str]:
        """Returns the local path of the resource.

        If specified the `downloader` partial function is called to download
        the resource if it is not present or up-to-date at the specified
        `local_path`.
        """
        if self._downloader:
            self._downloader()
        if self._local_path and not os.path.exists(self._local_path):
            raise Exception(
                f"Local path specified for resource, '{self._local_path}', "
                "does not exist."
            )
        return self._local_path

    def get_description(self) -> Optional[str]:
        """Returns description associated with this resource."""
        return self._description

    def get_source(self) -> Optional[str]:
        """Returns information as to where the source for this resource may be
        found.
        """
        return self._source


class FileResource(AbstractResource):
    """A resource consisting of a single file."""

    def __init__(
        self,
        local_path: str,
        id: Optional[str] = None,
        resource_version: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        downloader: Optional[partial] = None,
        **kwargs,
    ):
        super().__init__(
            local_path=local_path,
            id=id,
            description=description,
            source=source,
            resource_version=resource_version,
            downloader=downloader,
        )

    def get_category_name(cls) -> str:
        return "FileResource"

    def get_local_path(self) -> Optional[str]:
        # Here we override get_local_path to ensure the file exists.
        file_path = super().get_local_path()

        if not file_path:
            raise Exception("FileResource path not specified.")

        if not os.path.isfile(file_path):
            raise Exception(
                f"FileResource path specified, '{file_path}', is not a file."
            )
        return file_path


class DirectoryResource(AbstractResource):
    """A resource consisting of a directory."""

    def __init__(
        self,
        local_path: str,
        id: Optional[str] = None,
        resource_version: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        downloader: Optional[partial] = None,
        **kwargs,
    ):
        super().__init__(
            local_path=local_path,
            id=id,
            description=description,
            source=source,
            resource_version=resource_version,
            downloader=downloader,
        )

    def get_category_name(cls) -> str:
        return "DirectoryResource"

    def get_local_path(self) -> Optional[str]:
        # Here we override get_local_path to ensure the directory exists.
        dir_path = super().get_local_path()

        if not dir_path:
            raise Exception("DirectoryResource path not specified.")

        if not os.path.isdir(dir_path):
            raise Exception(
                f"DirectoryResource path specified, {dir_path}, is not a "
                "directory."
            )
        return dir_path


class DiskImageResource(FileResource):
    """A Disk Image resource."""

    def __init__(
        self,
        local_path: str,
        id: Optional[str] = None,
        resource_version: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        downloader: Optional[partial] = None,
        root_partition: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            local_path=local_path,
            id=id,
            description=description,
            source=source,
            resource_version=resource_version,
            downloader=downloader,
        )
        self._root_partition = root_partition

    def get_root_partition(self) -> Optional[str]:
        """Returns, if applicable, the Root Partition of the disk image."""
        return self._root_partition

    def get_category_name(cls) -> str:
        return "DiskImageResource"


class BinaryResource(FileResource):
    """A binary resource."""

    def __init__(
        self,
        local_path: str,
        id: Optional[str] = None,
        resource_version: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        downloader: Optional[partial] = None,
        architecture: Optional[Union[ISA, str]] = None,
        **kwargs,
    ):
        super().__init__(
            local_path=local_path,
            id=id,
            description=description,
            source=source,
            resource_version=resource_version,
            downloader=downloader,
        )

        self._architecture = None
        if architecture:
            if isinstance(architecture, str):
                self._architecture = get_isa_from_str(architecture)
            elif isinstance(architecture, ISA):
                self._architecture = architecture

    def get_category_name(cls) -> str:
        return "BinaryResource"

    def get_architecture(self) -> Optional[ISA]:
        """Returns the ISA this binary is compiled to."""
        return self._architecture


class BootloaderResource(BinaryResource):
    """A bootloader resource."""

    def __init__(
        self,
        local_path: str,
        id: Optional[str] = None,
        resource_version: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        downloader: Optional[partial] = None,
        architecture: Optional[Union[ISA, str]] = None,
        **kwargs,
    ):
        super().__init__(
            local_path=local_path,
            id=id,
            description=description,
            architecture=architecture,
            source=source,
            resource_version=resource_version,
            downloader=downloader,
        )

    def get_category_name(cls) -> str:
        return "BootloaderResource"


class GitResource(DirectoryResource):
    """A git resource."""

    def __init__(
        self,
        local_path: str,
        id: Optional[str] = None,
        resource_version: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        downloader: Optional[partial] = None,
        **kwargs,
    ):
        super().__init__(
            local_path=local_path,
            id=id,
            description=description,
            source=source,
            resource_version=resource_version,
            downloader=downloader,
        )

    def get_category_name(cls) -> str:
        return "GitResource"


class KernelResource(BinaryResource):
    """A kernel resource."""

    def __init__(
        self,
        local_path: str,
        id: Optional[str] = None,
        resource_version: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        downloader: Optional[partial] = None,
        architecture: Optional[Union[ISA, str]] = None,
        **kwargs,
    ):
        super().__init__(
            local_path=local_path,
            id=id,
            description=description,
            source=source,
            architecture=architecture,
            resource_version=resource_version,
            downloader=downloader,
        )

    def get_category_name(cls) -> str:
        return "KernelResource"


class CheckpointResource(DirectoryResource):
    """A checkpoint resource. The following directory structure is expected:

    <local_path>:
       - board.physmem.store0.pmem
       - m5.cpt
    """

    def __init__(
        self,
        local_path: str,
        id: Optional[str] = None,
        resource_version: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        downloader: Optional[partial] = None,
        **kwargs,
    ):
        super().__init__(
            local_path=local_path,
            id=id,
            description=description,
            source=source,
            resource_version=resource_version,
            downloader=downloader,
        )

    def get_category_name(cls) -> str:
        return "CheckpointResource"


class SimpointResource(AbstractResource):
    """A SimPoint resource. This resource stores all information required to
    perform a SimPoint creation and restore. It contains the SimPoint, the
    SimPoint interval, the weight for each SimPoint, the full warmup length,
    and the warmup length for each SimPoint.
    """

    def __init__(
        self,
        resource_version: Optional[str] = None,
        simpoint_interval: int = None,
        simpoint_list: List[int] = None,
        weight_list: List[float] = None,
        warmup_interval: int = 0,
        id: Optional[str] = None,
        workload_name: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        downloader: Optional[partial] = None,
        local_path: Optional[str] = None,
        **kwargs,
    ):
        """
        :param simpoint_interval: The SimPoint interval.
        :param simpoint_list: The SimPoint list.
        :param weight_list: The weight list.
        :param warmup_interval: The warmup interval. Default to zero (a value
                                of zero means effectively not set).
        :param workload_name: SimPoints are typically associated with a
                              particular workload due to their dependency on
                              chosen input parameters.
                              This field helps backtrack to that resource if
                              required. This should relate to a workload "name"
                              field in the ``resource.json`` file.
        """

        super().__init__(
            local_path=local_path,
            id=id,
            description=description,
            source=source,
            resource_version=resource_version,
            downloader=downloader,
        )

        self._weight_list = weight_list
        self._simpoint_list = simpoint_list
        self._simpoint_interval = simpoint_interval
        self._warmup_interval = warmup_interval
        self._workload_name = workload_name

        self._simpoint_start_insts = None

    def _load_simpoints(self) -> None:
        """As we cache downloading of resources until we require it, we may
        not pass the simpoint data in the constructor. In this case we enforce
        that the simpoint data is loaded via ths `_load_simpoints` function.
        Ergo when functions like `get_simpoint_list` are called, the data is
        loaded.
        """
        self._simpoint_start_insts = list(
            inst * self.get_simpoint_interval()
            for inst in self.get_simpoint_list()
        )

        if self.get_warmup_interval() != 0:
            self._warmup_list = self._set_warmup_list()
        else:
            self._warmup_list = [0] * len(self.get_simpoint_start_insts)

    def get_simpoint_list(self) -> List[int]:
        """Returns the a list containing all the SimPoints for the workload."""
        if self._simpoint_list is None:
            self._load_simpoints()
        assert self._simpoint_list is not None, "SimPoint list is None"
        return self._simpoint_list

    def get_simpoint_start_insts(self) -> List[int]:
        """Returns a lst containing all the SimPoint starting instrunction
        points for the workload. This was calculated by multiplying the
        SimPoint with the SimPoint interval when it was generated."""
        if self._simpoint_start_insts is None:
            self._load_simpoints()
        assert (
            self._simpoint_start_insts is not None
        ), "SimPoint start insts is None"
        return self._simpoint_start_insts

    def get_warmup_interval(self) -> int:
        """Returns the instruction length of the warmup interval."""
        if self._warmup_interval is None:
            self._load_simpoints()
        assert self._warmup_interval is not None, "Warmup interval is None"
        return self._warmup_interval

    def get_weight_list(self) -> List[float]:
        """Returns the list that contains the weight for each SimPoint. The
        order of the weights matches that of the list returned by
        ``get_simpoint_list()``. I.e. ``get_weight_list()[3]`` is the weight for
        SimPoint ``get_simpoint_list()[3]``."""
        if self._weight_list is None:
            self._load_simpoints()
        assert self._weight_list is not None, "Weight list is None"
        return self._weight_list

    def get_simpoint_interval(self) -> int:
        """Returns the SimPoint interval value."""
        return self._simpoint_interval

    def get_warmup_list(self) -> List[int]:
        """Returns the a list containing the warmup length for each SimPoint.
        Each warmup length in this list corresponds to the SimPoint at the same
        index in ``get_simpoint_list()``. I.e., ``get_warmup_list()[4]`` is the
        warmup length for SimPoint ``get_simpoint_list()[4]``."""
        if self._warmup_list is None:
            self._load_simpoints()
        assert self._warmup_list is not None, "Warmup list is None"
        return self._warmup_list

    def get_workload_name(self) -> Optional[str]:
        """Return the workload name this SimPoint is associated with."""
        return self._workload_name

    def _set_warmup_list(self) -> List[int]:
        """
        This function uses the ``warmup_interval``, fits it into the
        ``simpoint_start_insts``, and outputs a list of warmup instruction lengths
        for each SimPoint.

        The warmup instruction length is calculated using the starting
        instruction of a SimPoint to minus the ``warmup_interval`` and the ending
        instruction of the last SimPoint. If it is less than 0, then the warmup
        instruction length is the gap between the starting instruction of a
        SimPoint and the ending instruction of the last SimPoint.
        """
        warmup_list = []
        for index, start_inst in enumerate(self.get_simpoint_start_insts()):
            warmup_inst = start_inst - self.get_warmup_interval()
            if warmup_inst < 0:
                warmup_inst = start_inst
            else:
                warmup_inst = self.get_warmup_interval()
            warmup_list.append(warmup_inst)
            # change the starting instruction of a SimPoint to include the
            # warmup instruction length
            self._simpoint_start_insts[index] = start_inst - warmup_inst
        return warmup_list

    def get_category_name(cls) -> str:
        return "SimpointResource"


class LooppointCsvResource(FileResource, LooppointCsvLoader):
    """This LoopPoint resource used to create a LoopPoint resource from a
    pinpoints CSV file."""

    def __init__(
        self,
        local_path: str,
        id: Optional[str] = None,
        resource_version: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        downloader: Optional[partial] = None,
        **kwargs,
    ):
        FileResource.__init__(
            self,
            local_path=local_path,
            id=id,
            description=description,
            source=source,
            resource_version=resource_version,
            downloader=downloader,
        )
        LooppointCsvLoader.__init__(
            self, pinpoints_file=Path(self.get_local_path())
        )

    def get_category_name(cls) -> str:
        return "LooppointCsvResource"


class LooppointJsonResource(FileResource, LooppointJsonLoader):
    def __init__(
        self,
        local_path: str,
        id: Optional[str] = None,
        resource_version: Optional[str] = None,
        region_id: Optional[Union[str, int]] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        downloader: Optional[partial] = None,
        **kwargs,
    ):
        FileResource.__init__(
            self,
            local_path=local_path,
            id=id,
            description=description,
            source=source,
            resource_version=resource_version,
            downloader=downloader,
        )
        LooppointJsonLoader.__init__(
            self, looppoint_file=self.get_local_path(), region_id=region_id
        )

    def get_category_name(cls) -> str:
        return "LooppointJsonResource"


class SimpointDirectoryResource(SimpointResource):
    """A SimPoint diretory resource. This SimPoint Resource assumes the
    existance of a directory containing a SimPoint file and a weight file."""

    def __init__(
        self,
        local_path: str,
        simpoint_file: str,
        weight_file: str,
        simpoint_interval: int,
        warmup_interval: int,
        id: Optional[str] = None,
        resource_version: Optional[str] = None,
        workload_name: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        downloader: Optional[partial] = None,
        **kwargs,
    ):
        """
        :param simpoint_file: The SimPoint file. This file is a list of
                             SimPoints, each on its own line. It should map
                             1-to-1 to the weights file.
        :param weight_file: The SimPoint weights file. This file is a list of
                            weights, each on its own line.
        """
        self._simpoint_file = simpoint_file
        self._weight_file = weight_file

        super().__init__(
            simpoint_interval=simpoint_interval,
            warmup_interval=warmup_interval,
            workload_name=workload_name,
            local_path=local_path,
            id=id,
            description=description,
            source=source,
            downloader=downloader,
            resource_version=resource_version,
        )

    def _load_simpoints(self) -> None:
        (
            simpoint_list,
            weight_list,
        ) = self._get_weights_and_simpoints_from_file()
        self._simpoint_list = simpoint_list
        self._weight_list = weight_list
        super()._load_simpoints()

    def get_simpoint_file(self) -> Path:
        """Return the SimPoint File path."""
        return Path(Path(self.get_local_path()) / self._simpoint_file)

    def get_weight_file(self) -> Path:
        """Returns the Weight File path."""
        return Path(Path(self.get_local_path()) / self._weight_file)

    def _get_weights_and_simpoints_from_file(
        self,
    ) -> Tuple[List[int], List[int]]:
        """This is a helper function to extract the weights and SimPoints from
        the files.
        """
        simpoint_weight_pair = []
        with open(self.get_simpoint_file()) as simpoint_file, open(
            self.get_weight_file()
        ) as weight_file:
            while True:
                line = simpoint_file.readline()
                if not line:
                    break
                interval = int(line.split(" ", 1)[0])
                line = weight_file.readline()
                if not line:
                    fatal("not engough weights")
                weight = float(line.split(" ", 1)[0])
                simpoint_weight_pair.append((interval, weight))
        simpoint_weight_pair.sort(key=lambda obj: obj[0])
        # use simpoint to sort

        weight_list = []
        simpoint_list = []
        for simpoint, weight in simpoint_weight_pair:
            simpoint_list.append(simpoint)
            weight_list.append(weight)
        return simpoint_list, weight_list

    def get_category_name(cls) -> str:
        return "SimpointDirectoryResource"


class SuiteResource(AbstractResource):
    """
    A suite resource. This resource is used to specify a suite of workloads to
    run on a board. It contains a list of workloads to run, along with their
    IDs and versions.

    Each workload in a suite is used to create a `WorkloadResource` object.
    These objects are stored in a list and can be iterated over.
    """

    def __init__(
        self,
        workloads: Dict["WorkloadResource", Set[str]] = {},
        resource_version: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        id: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        :param workloads: A Dict of Tuples containing the WorkloadResource
                          object as the key and a set of input groups as the
                          value. This Dict is created from the ``_workloads``
                          parameter.
        :param local_path: The path on the host system where this resource is
                           located.
        :param description: Description describing this resource. Not a
                            required parameter. By default is ``None``.
        :param source: The source (as in "source code") for this resource
                       on gem5-resources. Not a required parameter. By default
                       is ``None``.
        :param resource_version: Version of the resource itself.
        """
        self._workloads = workloads
        self._description = description
        self._source = source
        self._resource_version = resource_version

        super().__init__(
            id=id,
            description=description,
            source=source,
            resource_version=resource_version,
        )

    def __iter__(self) -> Generator["WorkloadResource", None, None]:
        """
        Returns a generator that iterates over the workloads in the suite.

        :yields: A generator that iterates over the workloads in the suite.
        """
        yield from self._workloads.keys()

    def __len__(self):
        """
        Returns the number of workloads in the suite.

        :returns: The number of workloads in the suite.
        """
        return len(self._workloads)

    def get_category_name(cls) -> str:
        return "SuiteResource"

    def with_input_group(self, input_group: str) -> "SuiteResource":
        """
        :param input_group: The input group to filter the workloads by.
        :returns: A new SuiteResource object with only the workloads that use
                  the specified input group.
        """

        if input_group not in self.get_input_groups():
            raise Exception(
                f"Input group {input_group} not found in Suite.\n"
                f"Available input groups are {self.get_input_groups()}"
            )

        filtered_workloads = {}

        for workload, input_groups in self._workloads.items():
            if input_group in input_groups:
                filtered_workloads[workload] = input_groups

        return SuiteResource(
            local_path=self._local_path,
            resource_version=self._resource_version,
            description=self._description,
            source=self._source,
            workloads=filtered_workloads,
        )

    def get_input_groups(self) -> Set[str]:
        """
        :returns: A set of all input groups used by the workloads in a suite.
        """
        return {
            input_group
            for input_groups in self._workloads.values()
            for input_group in input_groups
        }


class WorkloadResource(AbstractResource):
    """A workload resource. This resource is used to specify a workload to run
    on a board. It contains the function to call and the parameters to pass to
    that function.
    """

    def __init__(
        self,
        function: str = None,
        id: Optional[str] = None,
        resource_version: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        local_path: Optional[str] = None,
        parameters: Optional[dict] = {},
        **kwargs,
    ):
        """
        :param function: The function to call on the board.
        :param parameters: The parameters to pass to the function.
        """

        super().__init__(
            local_path=local_path,
            id=id,
            description=description,
            source=source,
            resource_version=resource_version,
        )

        self._id = id
        self._func = function
        self._params = parameters

    def get_id(self) -> str:
        """Returns the ID of the workload."""
        return self._id

    def get_function_str(self) -> str:
        """
        Returns the name of the workload function to be run.

        This function is called via the AbstractBoard's ``set_workload``
        function. The parameters from the ``get_parameters`` function are passed
        to this function.
        """
        return self._func

    def get_parameters(self) -> Dict[str, Any]:
        """
        Returns a dictionary mapping the workload parameters to their values.

        These parameters are passed to the function specified by
        ``get_function_str`` via the AbstractBoard's ``set_workload`` function.
        """
        return self._params

    def set_parameter(self, parameter: str, value: Any) -> None:
        """
        Used to set or override a workload parameter

        :param parameter: The parameter of the function to set.
        :param value: The value to set to the parameter.
        """
        self._params[parameter] = value

    def get_category_name(cls) -> str:
        return "WorkloadResource"


def obtain_resource(
    resource_id: str,
    resource_directory: Optional[str] = None,
    download_md5_mismatch: bool = True,
    resource_version: Optional[str] = None,
    clients: Optional[List] = None,
    gem5_version=core.gem5Version,
    to_path: Optional[str] = None,
    quiet: bool = False,
) -> AbstractResource:
    """
    This function primarily serves as a factory for resources. It will return
    the correct AbstractResource implementation based on the resource
    requested.

    :param resource_name: The name of the gem5 resource as it appears under the
                          "id" field in the ``resource.json`` file.
    :param resource_directory: The location of the directory in which the
                               resource is to be stored. If this parameter is not
                               set, it will set to the environment variable
                               ``GEM5_RESOURCE_DIR``. If the environment is not set
                               it will default to ``~/.cache/gem5`` if available,
                               otherwise the CWD. *Note*: This argument is ignored
                               if the ``to_path`` parameter is specified.
    :param download_md5_mismatch: If the resource is present, but does not have
                                  the correct md5 value, the resource will be
                                  deleted and re-downloaded if this value is ``True``.
                                  Otherwise an exception will be thrown. ``True`` by
                                  default.
    :param resource_version: Version of the resource itself.
                             Not a required parameter. ``None`` by default.
    :param clients: A list of clients to search for the resource. If this
                    parameter is not set, it will default search all clients.
    :param gem5_version: The gem5 version to use to filter incompatible
                         resource versions. By default set to the current gem5
                         version. If `None`, this filtering is not performed.
    :param to_path: The path to which the resource is to be downloaded. If
                    ``None``, the resource will be downloaded to the resource directory
                    with the file/directory name equal to the ID of the resource.
                    **Note**: Usage of this parameter will override the
                    ``resource_directory`` parameter.
    :param quiet: If ``True``, suppress output. ``False`` by default.
    """

    # Obtain the resource object entry for this resource
    resource_json = get_resource_json_obj(
        resource_id,
        resource_version=resource_version,
        clients=clients,
        gem5_version=gem5_version,
    )

    # Partial function to get the path to download the resource to and the
    # downloader function to use.
    to_path, downloader = _get_to_path_and_downloader_partial(
        resource_json=resource_json,
        to_path=to_path,
        resource_directory=resource_directory,
        download_md5_mismatch=download_md5_mismatch,
        clients=clients,
        gem5_version=gem5_version,
        quiet=quiet,
    )

    # The 'workload' and 'suite' are special and need some translating into
    # the correct dictionary structure before we can create the object.
    if resource_json.get("category") == "suite":
        resource_json = _get_suite(
            resource_json,
            to_path,
            resource_directory,
            download_md5_mismatch,
            clients,
            gem5_version,
            quiet,
        )

    if resource_json.get("category") == "workload":
        resource_json = _get_workload(
            resource_json,
            to_path,
            resource_directory,
            download_md5_mismatch,
            clients,
            gem5_version,
            quiet,
        )

    # Check the schema of the 'resource_json' object.
    _resources_schema_validator(resource_json)

    # Sanity checks. These should have been caught by the schema validator.
    assert "category" in resource_json
    assert resource_json["category"] in _get_resource_json_type_map

    resources_category = resource_json["category"]

    if resources_category == "resource":
        # This is a stop-gap measure to ensure to work with older versions of
        # the "resource.json" file. These should be replaced with their
        # respective specializations ASAP and this case removed.
        if "root_partition" in resource_json:
            # In this case we should return a DiskImageResource.
            root_partition = resource_json["root_partition"]
            return DiskImageResource(
                local_path=to_path,
                root_partition=root_partition,
                downloader=downloader,
                **resource_json,
            )
        return CustomResource(local_path=to_path, downloader=downloader)

    # Once we know what AbstractResource subclass we are using, we create it.
    # The fields in the JSON object are assumed to map like-for-like to the
    # subclass contructor, so we can pass the resource_json map directly.
    return _get_resource_json_type_map[resources_category](
        local_path=to_path, downloader=downloader, **resource_json
    )


def _resources_schema_validator(resource_json: Dict[str, Any]) -> None:
    """
    This function is used to validate the schema of the resource JSON object
    before creating the resource object. This is to ensure that the resource
    object is created with the correct parameters and types.
    """

    if "category" not in resource_json:
        raise Exception(
            f"Resource JSON parsed for resource '{resource_json.get('id', '<unknown>')}' does not "
            "contain a category field."
        )

    assert "category" in resource_json
    resources_category = resource_json["category"]

    if not isinstance(resources_category, str):
        raise Exception(
            f"Resource category for {resource_json['id']} version "
            f"{resource_json['resource_version']} is not a string."
        )

    if resources_category not in _get_resource_json_type_map:
        raise Exception(
            f"Resource category '{resources_category}' "
            f"for {resource_json['id']} version "
            f"{resource_json['resource_version']} not found.\n"
            f"Valid categories are {', '.join(_get_resource_json_type_map.keys())}."
        )

    assert resources_category in _get_resource_json_type_map
    resource_class = _get_resource_json_type_map[resources_category]

    # Get the constructor parameters for the resource class
    params = inspect.signature(resource_class.__init__).parameters

    # Check required parameters exist, the parameters have the right types,
    # and warn if a parameter is given but not used by this category of
    # resource.
    for param_name, param in params.items():
        if param_name in ("self", "local_path", "downloader", "kwargs"):
            continue

        if (
            param_name not in resource_json
            and param.default == inspect.Parameter.empty
        ):
            # Required parameter missing
            raise Exception(
                f"Resource {resource_json['id']} version {resource_json['resource_version']} "
                f"is missing required parameter '{param_name}' for {resources_category}"
            )

        # Skip type checking if parameter not provided and optional
        if param_name not in resource_json:
            continue

        # Get the expected type annotation
        param_type = param.annotation
        if param_type == inspect.Parameter.empty:
            continue  # Skip type checking if no type annotation

        # Handle Union and Optional types
        if getattr(param_type, "__origin__", None) == Union:
            # Get all possible types from the Union using get_args, excluding None for Optional
            from typing import get_args

            valid_types = tuple(
                t for t in get_args(param_type) if t != type(None)
            )

            # For Union types, we need to check if the value matches any of the valid types
            value = resource_json[param_name]
            # For Optional types, None is always valid
            if value is None and type(None) in get_args(param_type):
                continue
            if not any(
                isinstance(value, t)
                for t in valid_types
                if not hasattr(t, "__origin__")
            ):
                type_names = " or ".join(
                    t.__name__
                    for t in valid_types
                    if not hasattr(t, "__origin__")
                )
                raise Exception(
                    f"Resource {resource_json['id']} version {resource_json['resource_version']} "
                    f"parameter '{param_name}' has incorrect type. "
                    f"Expected {type_names}, got {type(value).__name__}"
                )
        else:
            # Non-Union type checking
            value = resource_json[param_name]
            # Check if param_type is a typing generic (List, Dict, Set, etc)
            if hasattr(param_type, "__origin__"):
                # Skip validation for generic types as they can't be checked with isinstance
                continue
            else:
                if not isinstance(value, param_type):
                    raise Exception(
                        f"Resource {resource_json['id']} version {resource_json['resource_version']} "
                        f"parameter '{param_name}' has incorrect type. "
                        f"Expected {param_type.__name__}, got {type(value).__name__}"
                    )


def _get_suite(
    suite: Dict[str, Any],
    local_path: str,
    resource_directory: str,
    download_md5_mismatch: bool,
    clients: List[str],
    gem5_version: str,
    quiet: bool,
) -> Dict[str, Any]:
    """
    :param suite: The suite JSON object.
    :param local_path: The local path of the suite.
    :param resource_directory: The resource directory.
    :param download_md5_mismatch: If the resource is present, but does not have
                                  the correct md5 value, the resource will be
                                  deleted and re-downloaded if this value is ``True``.
                                  Otherwise an exception will be thrown.
    :param clients: A list of clients to search for the resource. If this
                    parameter is not set, it will default search all clients.
    :param gem5_version: The gem5 version to use to filter incompatible
                         resource versions. By default set to the current gem5
                         version.
    :param quiet: If ``True``, suppress output. ``False`` by default.
    """
    # Mapping input groups to workload IDs
    id_input_group_dict = {}
    if "workloads" not in suite:
        raise Exception(
            f"Suite {suite['id']} version {suite['resource_version']} does not contain a 'workloads' field."
        )

    for workload in suite["workloads"]:
        if "input_group" not in workload:
            raise Exception(
                f"Workload {workload['id']} version {workload['resource_version']} does not contain an 'input_group' field."
            )
        if "id" not in workload:
            raise Exception(
                f"The workload with input groups {workload['input_group']} does not contain an 'id' field."
            )

        id_input_group_dict[workload["id"]] = workload["input_group"]

    # Fetching the workload resources as a list of dicts
    db_query = [
        ClientQuery(
            resource_id=resource_info["id"],
            resource_version=resource_info["resource_version"],
            gem5_version=gem5_version,
        )
        for resource_info in suite["workloads"]
    ]
    workload_json = get_multiple_resource_json_obj(db_query, clients)

    # Creating the workload resource objects for each workload
    # and setting the input group for each workload
    workload_input_group_dict = {}
    for workload in workload_json:
        workload_dict = _get_workload(
            workload,
            local_path,
            resource_directory,
            download_md5_mismatch,
            clients,
            gem5_version,
            quiet,
        )
        _resources_schema_validator(workload_dict)
        workload_input_group_dict[
            WorkloadResource(
                local_path=local_path, downloader=None, **workload_dict
            )
        ] = id_input_group_dict[workload["id"]]

    suite["workloads"] = workload_input_group_dict

    return suite


def _get_workload(
    workload: Dict[str, Any],
    local_path: str,
    resource_directory: str,
    download_md5_mismatch: bool,
    clients: List[str],
    gem5_version: str,
    quiet: bool,
) -> Dict[str, Any]:
    """
    :param workload: The workload JSON object.
    :param local_path: The local path of the workload.
    :param resource_directory: The resource directory.
    :param download_md5_mismatch: If the resource is present, but does not have
                                  the correct md5 value, the resource will be
                                  deleted and re-downloaded if this value is ``True``.
                                  Otherwise an exception will be thrown.
    :param clients: A list of clients to search for the resource. If this
                    parameter is not set, it will default search all clients.
    :param gem5_version: The gem5 version to use to filter incompatible
                         resource versions. By default set to the current gem5
                         version.
    :param quiet: If ``True``, suppress output. ``False`` by default.
    """

    db_query = []

    if "resources" not in workload:
        raise Exception(
            f"Workload {workload['id']} version {workload['resource_version']} does not contain a 'resources' field."
        )

    if not isinstance(workload["resources"], dict):
        raise Exception(
            f"Workload {workload['id']} version {workload['resource_version']} contains a 'resources' field of the wrong type."
            "The 'resources' field should be a dictionary mapping parameter name (str) to another Dictionary of the resources resource ID (str) and version (src).\n"
            "e.g., \"{'disk_image': {'id': 'disk_image_id', 'resource_version': '1.0.0'}}\"'"
        )

    if "parameters" not in workload:
        workload["parameters"] = {}

    for resource in workload["resources"].values():
        db_query.append(
            ClientQuery(
                resource_id=resource["id"],
                resource_version=resource["resource_version"],
                gem5_version=gem5_version,
            )
        )
    # Fetching resources as a list of dicts
    resource_details_list = get_multiple_resource_json_obj(db_query, clients)

    # Creating the resource objects for each resource
    for param_name, param_resource in workload["resources"].items():
        resource_match = None
        for resource in resource_details_list:
            if (
                param_resource["id"] == resource["id"]
                and param_resource["resource_version"]
                == resource["resource_version"]
            ):
                resource_match = resource
                break

        if resource_match is None:
            raise Exception(
                f"Resource {param_resource['id']} with version {param_resource['resource_version']} not found"
            )
        to_path, downloader = _get_to_path_and_downloader_partial(
            resource_json=resource_match,
            to_path=local_path,
            resource_directory=resource_directory,
            download_md5_mismatch=download_md5_mismatch,
            clients=clients,
            gem5_version=gem5_version,
            quiet=quiet,
        )

        _resources_schema_validator(resource_match)

        # Sanity checks. These should have been caught by the schema validator.
        assert "category" in resource_match
        assert isinstance(resource_match["category"], str)
        assert resource_match["category"] in _get_resource_json_type_map

        resource_class = _get_resource_json_type_map[
            resource_match["category"]
        ]

        workload["parameters"][param_name] = resource_class(
            local_path=to_path,
            downloader=downloader,
            **resource_match,
        )

    del workload["resources"]

    # Adding the additional parameters to the workload parameters
    if "additional_params" in workload.keys():
        if workload["additional_params"]:
            assert isinstance(
                workload["additional_params"], dict
            ), f"Additional params should be a dict, not {type(workload['additional_params'])}"
            for key in workload["additional_params"].keys():
                assert isinstance(key, str)
                value = workload["additional_params"][key]
                workload["parameters"][key] = value

            del workload["additional_params"]
        else:
            workload.pop("additional_params", None)

    # Run the validator to make sure the workload JSON is correct
    _resources_schema_validator(workload)

    # By this point the workload dictionary should have merged the "resources"
    # and "additional_params" fields into the "parameters" field.
    assert "parameters" in workload
    assert "resources" not in workload
    assert "additional_params" not in workload

    # Return the workload dictionary.
    return workload


def _get_to_path_and_downloader_partial(
    resource_json: Dict[str, str],
    to_path: str,
    resource_directory: str,
    download_md5_mismatch: bool,
    clients: List[str],
    gem5_version: str,
    quiet: bool,
) -> Tuple[str, Optional[partial]]:

    if "resource_version" not in resource_json:
        raise Exception(
            f"Resource {resource_json['id']} does not contain a resource version"
        )
    if not isinstance(resource_json["resource_version"], str):
        raise Exception(
            f"Resource {resource_json['id']} does not contain a string resource version."
            "Resources version should follow the format 'x.y.z'"
        )

    resource_id = resource_json["id"]
    resource_version = resource_json["resource_version"]
    # This is is used to store the partial function which is used to download
    # the resource when the `get_local_path` function is called.
    downloader: Optional[partial] = None

    # If the "url" field is specified, the resoruce must be downloaded.
    if "url" in resource_json and resource_json["url"]:
        # If the `to_path` parameter is set, we use that as the path to which
        # the resource is to be downloaded. Otherwise, default to the
        # `resource_directory` parameter plus the resource ID.
        if not to_path:
            # If the `resource_directory` parameter is not set via this
            # function, we heck the "GEM5_RESOURCE_DIR" environment variable.
            # If this too is not set we call `_get_default_resource_dir()` to
            # determine where the resource directory is, or should be, located.
            if resource_directory == None:
                resource_directory = os.getenv(
                    "GEM5_RESOURCE_DIR", _get_default_resource_dir()
                )

            # Small checks here to ensure the resource directory is valid.
            if os.path.exists(resource_directory):
                if not os.path.isdir(resource_directory):
                    raise Exception(
                        "gem5 resource directory, "
                        "'{}', exists but is not a directory".format(
                            resource_directory
                        )
                    )

            # This is the path to which the resource is to be stored.
            to_path = os.path.join(resource_directory, resource_id)

        assert to_path

        # Here we ensure the directory in which the resource is to be stored
        # is created.
        #
        # `exist_ok=True` here as, occasionally, if multiple instance of gem5
        # are started simultaneously, a race condition can exist to create the
        # resource directory. Without `exit_ok=True`, threads which lose this
        # race will thrown a `FileExistsError` exception. `exit_ok=True`
        # ensures no exception is thrown.
        try:
            Path(to_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            fatal(
                f"Recursive creation of the directory "
                f"'{Path(to_path).parent.absolute}' failed. \n"
                f"Perhaps the path specified, '{to_path}', is incorrect?\n"
                f"Failed with Exception:\n{e}"
            )

        # Download the resource if it does not already exist.
        downloader = partial(
            get_resource,
            resource_name=resource_id,
            to_path=to_path,
            download_md5_mismatch=download_md5_mismatch,
            resource_version=resource_version,
            clients=clients,
            gem5_version=gem5_version,
            quiet=quiet,
        )
    return to_path, downloader


def _get_default_resource_dir() -> str:
    """
    Obtain the default gem5 resources directory on the host system. This
    function will iterate through sensible targets until it finds one that
    works on the host system.

    :returns: The default gem5 resources directory.
    """
    test_list = [
        # First try `~/.cache/gem5`.
        os.path.join(Path.home(), ".cache", "gem5"),
        # Last resort, just put things in the cwd.
        os.path.join(Path.cwd(), "resources"),
    ]

    for path in test_list:
        if os.path.exists(path):  # If the path already exists...
            if os.path.isdir(path):  # Check to see the path is a directory.
                return path  # If so, the path is valid and can be used.
        else:  # If the path does not exist, try to create it.
            try:
                os.makedirs(path, exist_ok=True)
                return path
            except OSError:
                continue  # If the path cannot be created, then try another.

    raise Exception("Cannot find a valid location to download resources")


# The following classes exist to preserve backwards functionality between the
# API for obtaining resources in v21.1.0 and prior.


class CustomResource(AbstractResource):
    """
    A custom gem5 resource. This can be used to encapsulate a resource provided
    by a gem5 user as opposed to one available within the gem5 resources
    repository.

    .. warning::

        This class is deprecated and will be removed in future releases of gem5.
        Please use the correct AbstractResource subclass instead.
    """

    def __init__(self, local_path: str, metadata: Dict = {}):
        """
        :param local_path: The path of the resource on the host system.
        :param metadata: Add metadata for the custom resource. **Warning:**
                         As of v22.1.1, this parameter is not used.
        """
        warn(
            "The `CustomResource` class is deprecated. Please use an "
            "`AbstractResource` subclass instead."
        )
        if bool(metadata):  # Empty dicts cast to False
            warn(
                "the `metadata` parameter was set via the `CustomResource` "
                "constructor. This parameter is not used."
            )
        super().__init__(local_path=local_path)


class CustomDiskImageResource(DiskImageResource):
    """
    A custom disk image gem5 resource. It can be used to specify a custom,
    local disk image.

    .. warning::

        This class is deprecated and will be removed in future releases of gem5.
        Please use the DiskImageResource class instead. This class is merely
        a wrapper for it.
    """

    def __init__(
        self,
        local_path: str,
        resource_version: Optional[str] = None,
        root_partition: Optional[str] = None,
        metadata: Dict = {},
    ):
        """
        :param local_path: The path of the disk image on the host system.
        :param root_partition: The root disk partition to use.
        :param metadata: Metadata for the resource. **Warning:** As of "
                         "v22.1.1, this parameter is not used.
        :param resource_version: Version of the resource itself.
        """
        warn(
            "The `CustomDiskImageResource` class is deprecated. Please use "
            "`DiskImageResource` instead."
        )
        if bool(metadata):  # Empty dicts cast to False
            warn(
                "the `metadata` parameter was set via the "
                "`CustomDiskImageResource` constructor. This parameter is not "
                "used."
            )
        super().__init__(
            local_path=local_path,
            root_partition=root_partition,
            resource_version=resource_version,
        )


def Resource(
    resource_id: str,
    resource_directory: Optional[str] = None,
    download_md5_mismatch: bool = True,
    resource_version: Optional[str] = None,
    clients: Optional[List[str]] = None,
) -> AbstractResource:
    """
    This function was created to maintain backwards compatibility for v21.1.0
    and prior releases of gem5 where `Resource` was a class.

    In the interests of gem5-resource specialization, the ``Resource`` class
    has been dropped. Instead users are advised to use the ``obtain_resource``
    function which will return the correct AbstractResource implementation.
    This function (disguised as a class) wraps this function.
    """

    warn(
        "`Resource` has been deprecated. Please use the `obtain_resource` "
        "function instead."
    )

    return obtain_resource(
        resource_id=resource_id,
        resource_directory=resource_directory,
        download_md5_mismatch=download_md5_mismatch,
        resource_version=resource_version,
        clients=clients,
    )


_get_resource_json_type_map = {
    "disk-image": DiskImageResource,
    "binary": BinaryResource,
    "kernel": KernelResource,
    "checkpoint": CheckpointResource,
    "git": GitResource,
    "bootloader": BootloaderResource,
    "file": FileResource,
    "directory": DirectoryResource,
    "simpoint": SimpointResource,
    "simpoint-directory": SimpointDirectoryResource,
    "resource": Resource,
    "looppoint-pinpoint-csv": LooppointCsvResource,
    "looppoint-json": LooppointJsonResource,
    "suite": SuiteResource,
    "workload": WorkloadResource,
    "elfie-info": ELFieInfo,
}
