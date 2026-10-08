"""Parser do layout observado no texto do projeto, ainda sem manual validado.

Não atribui unidades às coordenadas nem converte horário bruto para UTC.
Cada linha aceita mantém sua identificação física e seu bloco de origem.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from math import isfinite
from pathlib import Path


@dataclass
class Diagnostic:
    arquivo: str
    linha: int
    tipo_problema: str
    conteudo_original: str
    acao_tomada: str


@dataclass
class Observation:
    source_file: str
    line_number: int
    block_id: int
    time_raw_hhmm: str
    datetime_raw: str
    block_aux_raw: str
    prn: int
    x_sat_raw: float
    y_sat_raw: float
    z_sat_raw: float
    raw_5: str
    signal_power_raw: float
    raw_7: str
    s4: float
    raw_9: str
    raw_10: str
    original_line: str
    s4_valid: bool
    s4_above_one: bool
    exact_duplicate: bool


@dataclass
class ParseResult:
    source_file: str
    station: str
    description: str
    station_xyz_raw: tuple[float, float, float]
    header_datetime_raw: str
    header_aux_raw: str
    observations: list[Observation] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)


def parse_sum(path: str | Path) -> ParseResult:
    """Leia linha por linha; cabeçalho inválido gera erro explícito.

    Duplicatas são apenas marcadas, nunca removidas. Uma diminuição de
    horário só incrementa a data quando passa de 23:xx para 00:xx.
    Outras inversões são registradas sem inventar uma nova noite.
    """
    path = Path(path)
    with path.open(encoding="utf-8-sig") as stream:
        header = [stream.readline().rstrip("\r\n") for _ in range(5)]
        try:
            xyz = tuple(float(v) for v in header[2].split())
            date_values = [int(v) for v in header[3].split()]
            if len(xyz) != 3 or not all(map(isfinite, xyz)) or len(date_values) != 5:
                raise ValueError("Coordenadas ou data malformadas")
            stamp = datetime(*date_values)
            if not header[0] or not header[1] or not header[4]:
                raise ValueError("Cabeçalho incompleto")
        except (ValueError, TypeError) as error:
            raise ValueError(f"{path.name}: cabeçalho inválido: {error}") from error
        result = ParseResult(path.name, header[0], header[1], xyz,
                             stamp.isoformat(), header[4])
        day = stamp.date()
        previous_minutes = None
        block_id = 0
        expected = received = 0
        block_line = 0
        block_original = ""
        current_time = None
        hhmm = aux = ""
        seen = set()

        def issue(line, kind, original, action):
            result.diagnostics.append(Diagnostic(path.name, line, kind, original, action))

        def close_block():
            if block_id and received != expected:
                issue(block_line, "contagem_bloco", block_original,
                      f"Preservado: declarados={expected}, linhas_satélite={received}")

        for number, raw in enumerate(stream, 6):
            original = raw.rstrip("\r\n")
            tokens = original.split()
            if not tokens:
                issue(number, "linha_vazia", original, "Ignorada e registrada")
                continue
            if len(tokens) == 3:
                try:
                    value, count = int(tokens[0]), int(tokens[1])
                    hour, minute = divmod(value, 100)
                    if not 0 <= hour <= 23 or not 0 <= minute <= 59 or count < 0:
                        raise ValueError("Horário ou contagem inválidos")
                except ValueError:
                    close_block()
                    expected = received = 0
                    current_time = None
                    issue(number, "bloco_invalido", original, "Bloco rejeitado; horário desativado")
                    continue
                close_block()
                minutes = hour * 60 + minute
                if previous_minutes is not None and minutes < previous_minutes:
                    if previous_minutes // 60 == 23 and hour == 0:
                        day += timedelta(days=1)
                    else:
                        issue(number, "horario_inconsistente", original,
                              "Preservado na mesma data; revisar sequência")
                previous_minutes = minutes
                current_time = datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute)
                block_id += 1
                expected, received = count, 0
                block_line, block_original = number, original
                hhmm, aux = tokens[0].zfill(4), tokens[2]
                continue
            if current_time is None:
                issue(number, "registro_sem_bloco", original, "Rejeitado")
                continue
            # A contagem inclui linhas candidatas inválidas: o diagnóstico
            # separa integridade estrutural de validade dos valores físicos.
            received += 1
            if len(tokens) != 10:
                issue(number, "numero_campos", original, "Rejeitado; esperados 10 campos")
                continue
            try:
                prn = int(tokens[0])
                x, y, z = map(float, tokens[1:4])
                power, s4 = float(tokens[5]), float(tokens[7])
                if prn <= 0 or not all(map(isfinite, (x, y, z, power))):
                    raise ValueError("PRN ou coordenadas/potência inválidos")
            except ValueError:
                issue(number, "valor_invalido", original, "Rejeitado")
                continue
            valid = isfinite(s4) and s4 >= 0
            above = isfinite(s4) and s4 > 1
            # Inclui data, horário e auxiliar do bloco na identidade.
            identity = (current_time, aux, original)
            duplicate = identity in seen
            seen.add(identity)
            if duplicate:
                issue(number, "duplicata_exata", original, "Preservada")
            if not valid:
                issue(number, "s4_invalido", original, "Preservado e marcado inválido")
            elif above:
                issue(number, "s4_acima_de_um", original, "Preservado para inspeção")
            result.observations.append(Observation(
                path.name, number, block_id, hhmm, current_time.isoformat(), aux,
                prn, x, y, z, tokens[4], power, tokens[6], s4, tokens[8],
                tokens[9], original, valid, above, duplicate))
        close_block()
        return result
