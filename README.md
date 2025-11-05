## 🛰️ INMET Data Analyser

Este projeto realiza a **coleta, análise e tratamento de dados meteorológicos históricos** do **INMET (Instituto Nacional de Meteorologia)**.
A ferramenta permite **selecionar interativamente um ano (2000–2025)**, faz o **download automático** do arquivo `.zip` diretamente do portal do INMET e processa as planilhas contidas nele, gerando uma análise consolidada.

---

### 🚀 Funcionalidades

* Seleção interativa do **ano** (2000 a 2025);
* **Download automático** do arquivo `https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip`;
* Extração e leitura automatizada dos arquivos `.csv` e `.xls` dentro do ZIP;
* **Tratamento e normalização** dos dados de estações meteorológicas;
* Consolidação e exportação para análise;
* Interface simples via terminal, com **setas e menus interativos**;
* Compatível com **Windows, Linux (incluindo WSL)** e **macOS**.

---

### 🧰 Tecnologias Utilizadas

* **Python 3.10+**
* **Bibliotecas principais:**

  * `pandas` – Manipulação e análise de dados
  * `numpy` – Suporte a cálculos numéricos
  * `tqdm` – Barra de progresso no download e processamento
  * `requests` – Requisições HTTP para download automático
  * `rich` ou `inquirer` (opcional) – Interface interativa no terminal

---

### 📦 Estrutura de Diretórios

```
├── analyser.py           # Script principal
├── requirements.txt      # Dependências do projeto
├── LICENSE               # Licença MIT
├── README.md             # Este arquivo
└── data/                 # Diretório onde os arquivos ZIP são salvos
```

---

### ⚙️ Instalação

1. Clone o repositório:

```bash
git clone https://github.com/<seu-usuario>/inmet-data-analyser.git
cd inmet-data-analyser
```

2. Crie um ambiente virtual (opcional, mas recomendado):

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

---

### ▶️ Uso

Execute o script principal:

```bash
python analyser.py
```

O programa abrirá um **menu interativo** para seleção do ano.
Após selecionar, ele:

1. Baixará automaticamente o `.zip` do INMET referente ao ano escolhido;
2. Fará a leitura e o tratamento dos arquivos internos;
3. Exibirá relatórios de progresso e salvará os resultados tratados.

> 💡 Os arquivos baixados são armazenados em `data/{ano}.zip`.
> Se o arquivo já existir localmente, ele será reutilizado (sem novo download).

---

### 📊 Resultados Esperados

Após o processamento, o script exibe:

* Quantidade de arquivos processados por estação;
* Análises de temperatura, umidade e outras variáveis disponíveis;
* Relatórios de eventuais falhas em arquivos corrompidos;
* Tempo total de execução.

---

### 🧪 Exemplo de Saída (Terminal)

```
Escolha o ano do dataset:
> 2024

Baixando 2024.zip: 100%|█████████████████████| 215M/215M [01:42<00:00]
Download concluído: data/2024.zip

Analisando o arquivo: data/2024.zip (Isso pode levar alguns minutos)...
Extraindo planilhas...
Processando dados...
✅ Concluído! Dados prontos para análise.
```

---

### 🛡️ Licença

Este projeto está licenciado sob os termos da **Licença MIT** — consulte o arquivo [`LICENSE`](LICENSE) para mais informações.

---

### 📬 Contato

**Autor:** Jean Carlos Soares Alves Filho
**GitHub:** [@jjeancarlos](https://github.com/jjeancarlos)
**E-mail:** *jeanpastebin@gmail.com*

---