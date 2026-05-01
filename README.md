# projeto-akcit-2026
Projeto final do curso [ESP T1 ES C4]: Listar tempo para execução de tarefas

## Pré-requisitos

- Python 3.8+
- make
  - **Linux:** já incluso na maioria das distribuições (`sudo apt install make` se necessário)
  - **macOS:** instalar via Xcode Command Line Tools (`xcode-select --install`)
  - **Windows:** instalar via [Chocolatey](https://chocolatey.org/) (`choco install make`) ou usar o `make` do Git Bash / MSYS2

## Comandos Make

| Comando            | Descrição                                                                 |
|--------------------|---------------------------------------------------------------------------|
| `make venv`        | Cria o ambiente virtual Python em `.venv/`                                |
| `make install`     | Cria o ambiente virtual (se necessário) e instala as dependências         |
| `make install-dev` | Cria o ambiente virtual e instala dependências + ferramentas de teste     |
| `make run`         | Instala o projeto em modo editável e exibe instruções de uso              |
| `make test`        | Instala dependências de desenvolvimento e executa os testes com pytest    |
| `make clean`       | Remove o ambiente virtual, caches e artefatos de build                   |

> O Makefile detecta automaticamente o sistema operacional (Linux, macOS ou Windows) e ajusta os caminhos e comandos de acordo.

## Início rápido

```bash
# Instalar e executar a aplicação
make run

# Ativar o ambiente virtual
# Linux/macOS:
source .venv/bin/activate
# Windows (cmd):
.venv\Scripts\activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Usar a aplicação
tracker start "minha tarefa"
```

## Uso do Tracker

Após ativar o ambiente virtual, o comando `tracker` fica disponível no terminal. Abaixo estão todos os comandos disponíveis.

### `tracker start`

Inicia o rastreamento de uma tarefa. Se houver outra tarefa ativa, ela será pausada automaticamente.

```bash
tracker start "nome da tarefa"

# Com tags
tracker start "nome da tarefa" -t bug -t urgente
```

| Argumento / Opção | Descrição |
|---|---|
| `NAME` | Nome da tarefa (obrigatório) |
| `--tag`, `-t` | Tag para associar à tarefa (pode ser usada múltiplas vezes) |

### `tracker stop`

Para/pausa a tarefa que está ativa no momento.

```bash
tracker stop
```

### `tracker resume`

Retoma uma tarefa pausada. Sem argumentos, exibe a lista de tarefas pausadas para escolha interativa.

```bash
# Escolher interativamente
tracker resume

# Retomar diretamente pelo ID
tracker resume 3
```

| Argumento | Descrição |
|---|---|
| `TASK_ID` | ID da tarefa a retomar (opcional — se omitido, exibe lista para seleção) |

### `tracker list`

Exibe todas as tarefas com status, tags e tempo acumulado.

```bash
tracker list
```

### `tracker report`

Gera um relatório de tempo. Por padrão, exibe o resumo do dia atual.

```bash
# Relatório do dia
tracker report

# Filtrar por período
tracker report --from 2026-01-01 --to 2026-01-31

# Filtrar por tag
tracker report -t bug
```

| Opção | Descrição |
|---|---|
| `--from` | Data inicial no formato `YYYY-MM-DD` |
| `--to` | Data final no formato `YYYY-MM-DD` |
| `--tag`, `-t` | Filtrar por nome de tag |

### `tracker tag`

Adiciona uma tag a uma tarefa existente.

```bash
tracker tag 1 --add "urgente"
```

| Argumento / Opção | Descrição |
|---|---|
| `TASK_ID` | ID da tarefa (obrigatório) |
| `--add` | Nome da tag a adicionar (obrigatório) |
