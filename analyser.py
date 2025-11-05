import csv
import datetime as dt
import io
import re
import zipfile
from pathlib import Path
import locale
import sys
import os
import requests
import shutil

import numpy as np
import pandas as pd
from tqdm import tqdm

# --- Configuração do Locale para Português ---
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    print("Locale 'pt_BR.UTF-8' não encontrado. Tentando 'Portuguese_Brazil' (Windows).", file=sys.stderr)
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
    except locale.Error:
        print("Locale em português não encontrado. Os nomes dos meses podem aparecer em inglês.", file=sys.stderr)


# =============================================================================
# FUNÇÕES DE PROCESSAMENTO
# =============================================================================

def read_metadata(filepath: Path | zipfile.ZipExtFile) -> dict[str, str]:
    """Lê os metadados (cabeçalho) de um arquivo CSV do INMET."""
    if isinstance(filepath, zipfile.ZipExtFile):
        f = io.TextIOWrapper(filepath, encoding="latin-1")
    else:
        f = open(filepath, "r", encoding="latin-1")
    
    reader = csv.reader(f, delimiter=";")
    
    try:
        _, regiao = next(reader)
        _, uf = next(reader)
        _, estacao = next(reader)
        _, codigo_wmo = next(reader)
        _, latitude = next(reader)
        try:
            latitude = float(latitude.replace(",", "."))
        except:
            latitude = np.nan
        _, longitude = next(reader)
        try:
            longitude = float(longitude.replace(",", "."))
        except:
            longitude = np.nan
        _, altitude = next(reader)
        try:
            altitude = float(altitude.replace(",", "."))
        except:
            altitude = np.nan
        _, data_fundacao = next(reader)
        if re.match("[0-9]{4}-[0-9]{2}-[0-9]{2}", data_fundacao):
            data_fundacao = dt.datetime.strptime(data_fundacao, "%Y-%m-%d")
        elif re.match("[0-9]{2}/[0-9]{2}/[0-9]{2}", data_fundacao):
            data_fundacao = dt.datetime.strptime(data_fundacao, "%d/%m/%y")
    except Exception as e:
        print(f"Erro ao ler metadados: {e}", file=sys.stderr)
        f.close()
        return {}

    f.close()
    return {
        "regiao": regiao,
        "uf": uf,
        "estacao": estacao,
        "codigo_wmo": codigo_wmo,
        "latitude": latitude,
        "longitude": longitude,
        "altitude": altitude,
        "data_fundacao": data_fundacao,
    }

def columns_renamer(name: str) -> str:
    """Renomeia colunas para um formato padronizado."""
    name = name.lower()
    if re.match(r"data", name): return "data"
    if re.match(r"hora", name): return "hora"
    if re.match(r"precipita[çc][ãa]o", name): return "precipitacao"
    if re.match(r"press[ãa]o atmosf[ée]rica ao n[íi]vel", name): return "pressao_atmosferica"
    if re.match(r"press[ãa]o atmosf[ée]rica m[áa]x", name): return "pressao_atmosferica_maxima"
    if re.match(r"press[ãa]o atmosf[ée]rica m[íi]n", name): return "pressao_atmosferica_minima"
    if re.match(r"radia[çc][ãa]o", name): return "radiacao"
    if re.match(r"temperatura do ar", name): return "temperatura_ar"
    if re.match(r"temperatura do ponto de orvalho", name): return "temperatura_orvalho"
    if re.match(r"temperatura m[áa]x", name): return "temperatura_maxima"
    if re.match(r"temperatura m[íi]n", name): return "temperatura_minima"
    if re.match(r"temperatura orvalho m[áa]x", name): return "temperatura_orvalho_maxima"
    if re.match(r"temperatura orvalho m[íi]n", name): return "temperatura_orvalho_minima"
    if re.match(r"umidade rel\. m[áa]x", name): return "umidade_relativa_maxima"
    if re.match(r"umidade rel\. m[íi]n", name): return "umidade_relativa_minima"
    if re.match(r"umidade relativa do ar", name): return "umidade_relativa"
    if re.match(r"vento, dire[çc][ãa]o", name): return "vento_direcao"
    if re.match(r"vento, rajada", name): return "vento_rajada"
    if re.match(r"vento, velocidade", name): return "vento_velocidade"
    return name

def convert_dates(dates: pd.Series) -> pd.Series:
    """Converte datas de 'DD/MM/YYYY' para 'YYYY-MM-DD'."""
    return dates.str.replace("/", "-")

def convert_hours(hours: pd.Series) -> pd.Series:
    """Garante que a string de hora esteja no formato 'HH:MM'."""
    def fix_hour_string(hour: str) -> str:
        hour = str(hour)
        if re.match(r"^\d{2}\:\d{2}$", hour): return hour
        elif re.match(r"^\d{4}$", hour): return hour[:2] + ":" + hour[2:]
        elif re.match(r"^\d{2} UTC$", hour): return hour[:2] + ":00"
        else:
            match = re.match(r"^\d{2}", hour)
            return (match.group(0) + ":00") if match else "00:00"
    return hours.apply(fix_hour_string)

def fix_data_hora(d: pd.DataFrame) -> pd.DataFrame:
    d = d.assign(
        data_hora=pd.to_datetime(
            convert_dates(d["data"]) + " " + convert_hours(d["hora"]),
            format="%Y-%m-%d %H:%M",
        ),
    )
    d = d.drop(columns=["data", "hora"])
    return d

def read_data(filepath: Path | zipfile.ZipExtFile) -> pd.DataFrame:
    d = pd.read_csv(
        filepath, sep=";", decimal=",", na_values=["-9999", "-9999,0"],
        encoding="latin-1", skiprows=8, usecols=range(19), dtype=str
    )
    d = d.rename(columns=columns_renamer)

    numeric_cols = [
        "precipitacao", "pressao_atmosferica", "pressao_atmosferica_maxima",
        "pressao_atmosferica_minima", "radiacao", "temperatura_ar",
        "temperatura_orvalho", "temperatura_maxima", "temperatura_minima",
        "temperatura_orvalho_maxima", "temperatura_orvalho_minima",
        "umidade_relativa_maxima", "umidade_relativa_minima", "umidade_relativa",
        "vento_direcao", "vento_rajada", "vento_velocidade"
    ]
    cols_to_keep = numeric_cols + ['data', 'hora']
    d = d[[col for col in cols_to_keep if col in d.columns]]

    for col in numeric_cols:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col].str.replace(',', '.'), errors='coerce')

    empty_columns = [col for col in numeric_cols if col in d.columns]
    if not d.empty and empty_columns:
        d = d.loc[~d[empty_columns].isnull().all(axis=1)]

    if d.empty:
        return pd.DataFrame()

    return fix_data_hora(d)

def read_zipfile(filepath: Path) -> pd.DataFrame:
    data = pd.DataFrame()
    with zipfile.ZipFile(filepath) as z:
        files = [zf for zf in z.infolist()
                 if not zf.is_dir()
                 and zf.filename.lower().endswith(".csv")
                 and not zf.filename.startswith("__MACOSX")]

        if not files:
            print(f"Nenhum .csv encontrado dentro de {filepath.name}.")
            return data

        for zf in tqdm(files, desc=f"Processando {filepath.name}"):
            try:
                meta = read_metadata(z.open(zf.filename))
                if not meta:
                    continue
                d = read_data(z.open(zf.filename))
                if not d.empty:
                    d = d.assign(**meta)
                    data = pd.concat((data, d), ignore_index=True)
            except Exception as e:
                print(f"Erro ao processar {zf.filename}: {e}", file=sys.stderr)
    return data


# =============================================================================
# SELEÇÃO INTERATIVA DO ANO + DOWNLOAD AUTOMÁTICO
# =============================================================================

def _getch():
    """Leitura de tecla única cross-platform."""
    if os.name == "nt":
        import msvcrt
        ch = msvcrt.getch()
        if ch in {b'\x00', b'\xe0'}:
            ch2 = msvcrt.getch()
            return (ch + ch2).decode(errors='ignore')
        return ch.decode(errors='ignore')
    else:
        import tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                ch2 = sys.stdin.read(2)
                return ch + ch2
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

def select_from_list(options: list[str], title: str = "Escolha:") -> str | None:
    if not options:
        return None
    if not sys.stdin.isatty():
        print(title)
        choice = input("> ").strip()
        return choice if choice in options else None
    idx = 0
    visible = 10
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print(title)
            start = max(0, idx - visible//2)
            end = min(len(options), start + visible)
            start = max(0, end - visible)
            for i in range(start, end):
                prefix = ">" if i == idx else " "
                print(f"{prefix} {options[i]}")
            print("\nUse ↑/↓ ou k/j para navegar, Enter para confirmar, q para sair.")
            ch = _getch()
            if ch in ('\x1b[A', '\x00H', '\xe0H'): idx = (idx - 1) % len(options)
            elif ch in ('\x1b[B', '\x00P', '\xe0P'): idx = (idx + 1) % len(options)
            elif ch in ('k', 'K'): idx = (idx - 1) % len(options)
            elif ch in ('j', 'J'): idx = (idx + 1) % len(options)
            elif ch in ('\r', '\n'): return options[idx]
            elif ch in ('q', 'Q'): return None
    except Exception:
        print("\nEntrada interativa falhou — use entrada manual")
        choice = input("Digite o ano desejado: ").strip()
        return choice if choice in options else None


def download_zip_for_year(year: str, datadir: Path, overwrite: bool = False) -> Path:
    """Baixa https://portal.inmet.gov.br/uploads/dadoshistoricos/{year}.zip"""
    datadir.mkdir(parents=True, exist_ok=True)
    local_name = datadir / f"{year}.zip"
    url = f"https://portal.inmet.gov.br/uploads/dadoshistoricos/{year}.zip"

    if local_name.exists() and not overwrite:
        print(f"Arquivo local já existe: {local_name}. Reutilizando.")
        return local_name

    print(f"Tentando baixar: {url}")
    try:
        with requests.get(url, stream=True, timeout=30, allow_redirects=True) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            with open(local_name, "wb") as f:
                if total:
                    with tqdm(total=total, unit="B", unit_scale=True, desc=f"Baixando {year}.zip") as pbar:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                else:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
        print(f"Download concluído: {local_name}")
        return local_name
    except requests.RequestException as e:
        if local_name.exists():
            try:
                local_name.unlink()
            except Exception:
                pass
        raise RuntimeError(f"Falha ao baixar {url}: {e}")


# --- Seleção e download ---
years = [str(y) for y in range(2000, 2026)]
selected_year = select_from_list(years, title="Escolha o ano do dataset:")

if not selected_year:
    print("Nenhum ano selecionado. Saindo.")
    sys.exit(0)

datadir = Path("data")
zip_path = None
try:
    zip_path = download_zip_for_year(selected_year, datadir)
except Exception as e:
    print(f"Aviso: falha ao baixar ZIP remoto: {e}", file=sys.stderr)
    fallback = datadir / f"{selected_year}.zip"
    if fallback.exists():
        zip_path = fallback
        print(f"Usando fallback local: {fallback}")
    else:
        print(f"Erro: Nenhum arquivo ZIP encontrado para {selected_year}.", file=sys.stderr)
        sys.exit(1)

print(f"Analisando o arquivo: {zip_path} (Isso pode levar alguns minutos)...")

# =============================================================================
# LEITURA, AGRUPAMENTO E MÉDIAS
# =============================================================================

try:
    df_ano = read_zipfile(zip_path)
    if df_ano.empty:
        print("Erro: DataFrame vazio após leitura.")
        sys.exit(1)
except Exception as e:
    print(f"Erro crítico ao ler o ZIP: {e}")
    sys.exit(1)

print("Processamento concluído. Calculando médias...")

df_ano['mes_num'] = df_ano['data_hora'].dt.month
df_ano['mes_nome'] = df_ano['data_hora'].dt.strftime('%B')

media_regional_mensal = df_ano.groupby(
    ['regiao', 'mes_num', 'mes_nome']
).agg(
    temperatura_media=('temperatura_ar', 'mean'),
    umidade_media=('umidade_relativa', 'mean')
).reset_index().sort_values(by=['regiao', 'mes_num'])

print(f"\n--- Médias de Temperatura e Umidade para {selected_year} ---")
for regiao in media_regional_mensal['regiao'].unique():
    print(f"\n{regiao}:")
    dados_regiao = media_regional_mensal[media_regional_mensal['regiao'] == regiao]
    for _, linha in dados_regiao.iterrows():
        mes = linha['mes_nome'].capitalize()
        temp = linha['temperatura_media']
        umid = linha['umidade_media']
        print(f"  {mes} (temperatura {temp:.1f}°C / umidade {umid:.1f}%)")
