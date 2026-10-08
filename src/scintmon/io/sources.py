"""Contrato de fonte: novos formatos não alteram o pipeline científico."""
from abc import ABC, abstractmethod
from scintmon.io.sum_parser import parse_sum


class DataSource(ABC):
    @abstractmethod
    def read(self, path):
        """Retorne metadados, observações e diagnósticos preservados."""


class ScintmonSumSource(DataSource):
    def read(self, path):
        return parse_sum(path)


class RinexSource(DataSource):
    def read(self, path):
        raise NotImplementedError("Fonte RINEX futura; .SUM não é RINEX")
