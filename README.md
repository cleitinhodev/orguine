<p align="center">
  <img src="docs/orguine_icon.png" width="140" alt="Orguine">
</p>

<h1 align="center">Orguine</h1>

<p align="center">
  <b>Organize suas pastas com prévia, backup e desfazer — sem sustos.</b><br>
  <i>Tidy up your folders with a preview, backup and undo — no surprises.</i>
</p>

<p align="center">
  <a href="https://github.com/cleitinhodev/orguine/releases/latest"><img src="https://img.shields.io/github/v/release/cleitinhodev/orguine?color=6ff8c8&label=download" alt="Última versão"></a>
  <a href="https://github.com/cleitinhodev/orguine/actions/workflows/ci.yml"><img src="https://github.com/cleitinhodev/orguine/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/Windows%20%7C%20Linux%20%7C%20macOS-7C6CF0" alt="Windows | Linux | macOS">
  <img src="https://img.shields.io/badge/PySide6-Qt%206-7C6CF0" alt="PySide6">
  <img src="https://img.shields.io/badge/licen%C3%A7a-GPL--3.0-6ff8c8" alt="GPL-3.0">
</p>

<p align="center">
  <a href="https://github.com/cleitinhodev/orguine/releases/latest"><b>⬇️ Baixar</b></a> ·
  <a href="https://github.com/cleitinhodev">Meu GitHub</a> ·
  <a href="https://github.com/cleitinhodev/orguine">Projeto</a> ·
  <a href="https://www.bugzinho.com/">bugzinho.com</a> ·
  <a href="https://www.bugzinho.com/donate">💚 Apoiar / Doar</a> ·
  <a href="#-english">🇺🇸 English</a>
</p>

---

O **Orguine** é um organizador de arquivos para desktop, gratuito e de código aberto. Ele arruma pastas bagunçadas
(como **Downloads** ou **Área de Trabalho**) em poucos cliques e **mostra antes como tudo vai ficar**.
Nada é movido sem a sua confirmação, nada é sobrescrito, e dá para **desfazer** tudo com um clique.

![Orguine com efeitos neon animados](docs/screenshots/neon.gif)

| Prévia "como ficará" | Gráfico de tipos de arquivo |
|---|---|
| ![Prévia em árvore](docs/screenshots/01-preview-arvore-light.png) | ![Gráfico de rosca](docs/screenshots/03-grafico-dark-en.png) |
| **Aviso de arquivos sensíveis** | **Sobre** |
| ![Aviso de arquivos sensíveis](docs/screenshots/05-aviso-sensiveis.png) | ![Sobre](docs/screenshots/06-sobre-dark.png) |

## ⬇️ Download

Baixe a versão mais recente em **[Releases](https://github.com/cleitinhodev/orguine/releases/latest)**.
Não precisa instalar Python nem nada mais: é um arquivo único.

| Sistema | Arquivo | Como abrir |
|---|---|---|
| **Windows 10/11** (64 bits) | `Orguine-windows-amd64.exe` | Dê dois cliques. Se o SmartScreen avisar "O Windows protegeu o computador", clique em **Mais informações → Executar assim mesmo** (o executável é novo e não é assinado). |
| **Linux** (x86_64) | `Orguine-linux-x86_64` | `chmod +x Orguine-linux-x86_64 && ./Orguine-linux-x86_64` |
| **macOS** | `Orguine-macos-*.zip` | Descompacte e, na primeira vez, abra com **botão direito → Abrir** (app não assinado). |

Cada arquivo tem um `.sha256` ao lado para você conferir a integridade
(`sha256sum -c Orguine-linux-x86_64.sha256`, ou `Get-FileHash` no PowerShell).

## ✨ Funcionalidades

- **Prévia "como ficará"**: uma árvore com as pastas que serão criadas e o que vai para cada uma. A prévia **se atualiza sozinha** quando você muda o modo ou qualquer opção.
- **4 modos de organização**:
  - **Categorias inteligentes**: Imagens, Documentos, Vídeos, Músicas, Compactados, Código, Instaladores…
  - **Por extensão**: uma pasta por formato (PDF, MP3…).
  - **Por data**: Ano/Mês. Para fotos, usa a data **EXIF** quando ela existe.
  - **Alfabética**: A–Z, 0-9 e Outros.
- **Duplicados por conteúdo (SHA-256)**, não só pelo nome. Você escolhe: manter o original e mandar as cópias para a **lixeira**, apenas pular, manter o mais novo ou ignorar. O hash é feito em etapas (tamanho → início → arquivo completo), então é rápido mesmo com muitos arquivos.
- **Proteção de arquivos sensíveis**: chaves, `.env`, cofres de senha, carteiras e bancos de dados ficam no lugar por padrão.
- **Gráfico de tipos de arquivo** (rosca, por quantidade ou tamanho) e **tabela de detalhes** com busca, filtros e o motivo de cada decisão.
- **Subpastas (opcional)**: pastas de projetos (`.git`, `package.json`, `pyproject.toml`…) nunca são desmontadas.
- **Pastas de destino inteligentes**: pastas que já existem são reaproveitadas (mesmo com outra grafia, como `imagens`/`Imagens`). Um sufixo como `A (2)` só aparece quando o nome está ocupado por um arquivo que vai continuar no lugar.
- **Backup opcional** (ZIP ou cópia da pasta) e **desfazer a última organização** com um clique.
- **Trabalho em segundo plano** com barra de progresso e botão **Cancelar**: a janela não trava.
- **Visual neon**: a cor **#6ff8c8** do robozinho com o roxo do tema. Faixas de luz no cabeçalho, na aba ativa e na barra de progresso; reflexo nos botões; cartões que brilham. As animações são leves, pausam com a janela minimizada e podem ser desligadas em **Opções → Animações neon** (ou com `ORGUINE_NO_ANIM=1`).
- **Tema claro/escuro**, **português (Brasil) e inglês**, arrastar e soltar uma pasta e preferências salvas.
- **Linha de comando (CLI)** para scripts e automações.

## 🛡️ Modelo de segurança

O Orguine foi feito para que organizar nunca custe um arquivo:

1. **Prévia primeiro**: nada é movido antes de você ver o resultado e confirmar.
2. **Nunca sobrescreve**: se o destino já existir, o arquivo vira `nome (1).ext`, `nome (2).ext`… (sem diferenciar maiúsculas de minúsculas, como no Windows/macOS). Arquivos alterados entre a prévia e a execução são conferidos de novo.
3. **Pastas perigosas são bloqueadas**: raiz do disco, `C:\Windows`, `Program Files`, `AppData`, `/usr`, `/etc`, `/System`, `~/Library`, `~/.ssh`, `~/.config`… Organizar a **pasta pessoal inteira** exige digitar `ORGANIZAR`.
4. **Arquivos sensíveis ficam no lugar**: chaves (`id_rsa`, `.pem`, `.pfx`), `.env`, `.kdbx`, carteiras, bancos de dados e nomes como "senha" ou "password". Para incluí-los, aparece um **aviso listando cada um**, e eles **nunca vão para a lixeira** como duplicados sem permissão explícita (CLI: `--permitir-lixeira-sensiveis`).
5. **Arquivos de sistema, ocultos e temporários são ignorados**: `desktop.ini`, `.DS_Store`, `Thumbs.db`, downloads incompletos (`.crdownload`, `.part`) e links simbólicos. O próprio executável do Orguine nunca é movido.
6. **Backup opcional** em ZIP ou cópia, guardado na pasta de dados do app.
7. **Diário de desfazer à prova de quedas**: cada passo é gravado em JSON (de forma atômica) **antes** de acontecer. Se o programa fechar no meio, o desfazer ainda devolve tudo aos nomes e lugares originais.
8. **Exclusões só vão para a lixeira do sistema** (Send2Trash), nunca são apagadas direto.
9. **Log detalhado** de tudo, com rotação automática.

## ⌨️ Linha de comando

```bash
# só ver a prévia (não mexe em nada)
orguine-cli ~/Downloads --dry-run

# organizar por categoria, com backup ZIP e duplicados para a lixeira
orguine-cli ~/Downloads --backup zip --duplicados trash

# por data (ano/mês), incluindo subpastas, sem perguntar
orguine-cli ~/Fotos --modo data --recursivo --sim

# desfazer a última organização
orguine-cli --desfazer
```

Modos: `categoria` (padrão), `extensao` (ou `tipo`), `data`, `abc`. Veja todas as opções com `--help`.
Rodando a partir do código-fonte, use `python -m orguine` no lugar de `orguine-cli`.

## 🐍 Rodar a partir do código-fonte (Python 3.10+)

```bash
git clone https://github.com/cleitinhodev/orguine.git
cd orguine
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/macOS: source .venv/bin/activate
pip install -e ".[exif]"        # ou: pip install -r requirements.txt
python -m orguine               # abre a interface
```

Depois do `pip install`, os comandos `orguine` (interface) e `orguine-cli` também ficam disponíveis.

## ⚙️ Personalizar categorias

Copie [`orguine/resources/default_rules.json`](orguine/resources/default_rules.json) para `rules.json` dentro da
**pasta de dados** e edite nomes, cores e extensões. Na CLI, também dá para usar `--regras arquivo.json`.

A **pasta de dados** guarda diários de desfazer, backups, logs e o `rules.json`. O botão "Abrir pasta de dados" abre essa pasta:

| Sistema | Local |
|---|---|
| Windows | `%APPDATA%\Orguine` |
| macOS | `~/Library/Application Support/Orguine` |
| Linux | `~/.local/share/orguine` (ou `$XDG_DATA_HOME`) |

Para trocar o local, defina a variável `ORGUINE_DATA_DIR`.

## 🧑‍💻 Desenvolvimento

```bash
pip install -e ".[dev]"
pytest -q                       # no Linux sem tela: QT_QPA_PLATFORM=offscreen pytest -q
python scripts/build_exe.py     # gera o executável em dist/ (PyInstaller)
```

```
orguine/
├── core/         # lógica sem interface (testável)
│   ├── planner.py     # monta o plano / prévia
│   ├── executor.py    # executa o plano
│   ├── journal.py     # diário de desfazer
│   ├── safety.py      # pastas bloqueadas, sensíveis, ocultos
│   ├── duplicates.py  # SHA-256 em etapas
│   ├── backup.py      # ZIP / cópia
│   └── rules.py, naming.py, dates.py, hashing.py, models.py
├── gui/          # PySide6: janela, prévia, gráfico, tema, efeitos neon, "Sobre", workers (QThread)
├── cli.py        # linha de comando
├── i18n.py       # textos pt-BR / en
└── resources/    # regras padrão e ícones
tests/            # pytest + pytest-qt
```

O **GitHub Actions** roda os testes no Windows, no macOS e no Linux e gera os executáveis com PyInstaller.
Uma tag `v*` publica os executáveis automaticamente na página de [Releases](https://github.com/cleitinhodev/orguine/releases).

Encontrou um problema ou tem uma ideia? Abra uma [issue](https://github.com/cleitinhodev/orguine/issues).

## 💚 Apoie

Se o Orguine te ajudou, considere [apoiar o projeto](https://www.bugzinho.com/donate). Visite também [bugzinho.com](https://www.bugzinho.com/).

## 📄 Licença

[GPL-3.0](LICENSE) © CleitinhoDEV

---

# 🇺🇸 English

**Orguine** is a free, open-source desktop file organizer. It tidies up messy folders (Downloads, Desktop…)
in a few clicks and **shows you the result before anything is moved**. Nothing is overwritten, and everything can be **undone** with one click.
Built with **PySide6 (Qt 6)**, with an English and Brazilian Portuguese UI.

### Download

Get the latest build from **[Releases](https://github.com/cleitinhodev/orguine/releases/latest)**. It is a single file; no Python needed.

- **Windows 10/11 (64-bit)**: `Orguine-windows-amd64.exe`. If SmartScreen warns you, click **More info → Run anyway** (the executable is new and unsigned).
- **Linux (x86_64)**: `Orguine-linux-x86_64`. Run `chmod +x Orguine-linux-x86_64 && ./Orguine-linux-x86_64`.
- **macOS**: `Orguine-macos-*.zip`. Unzip, then right-click → **Open** the first time (unsigned app).

Each file has a `.sha256` checksum next to it.

### Features

- A **"Result preview" tree** that **updates automatically** when you change the mode or any option, plus a details table with filters and a **file-type donut chart**.
- **Modes**: smart categories, by extension, by date (Year/Month, using EXIF for photos) and alphabetical.
- **Duplicate detection by content (SHA-256)**. Copies can go to the **system trash**, be skipped, or keep only the newest file.
- **Sensitive files** (keys, `.env`, password vaults, wallets, databases…) stay in place by default.
- **Smart destination folders**: existing folders are reused (case-insensitively); a suffix like `A (2)` only appears when the name is taken by a file that stays.
- Optional recursion that never breaks apart project folders (`.git`, `package.json`…).
- Optional ZIP/folder **backup** and **one-click undo**. Background work with progress and **Cancel**.
- **Neon look** (#6ff8c8 + purple), light and dark themes, drag and drop. Animations can be turned off under **Options → Neon animations** (or `ORGUINE_NO_ANIM=1`).
- A **CLI**: `orguine-cli <folder> [--dry-run] [--modo categoria|extensao|data|abc] [--recursivo] [--backup zip|folder] [--duplicados trash|skip|newest] [--desfazer]`.

### Safety model

- Preview first: nothing moves until you confirm. Files are never overwritten (`name (1).ext`).
- System and root folders are blocked; organizing your whole home folder requires typed confirmation.
- Sensitive files stay in place by default; including them shows a warning with the full list, and they are never trashed as duplicates unless you explicitly allow it.
- System, hidden, temporary and partial-download files, and symbolic links, are skipped.
- A crash-safe, atomic undo journal: every step is recorded before it happens. Deletions only go to the trash. Rotating logs.

### Run from source (Python 3.10+)

```bash
git clone https://github.com/cleitinhodev/orguine.git && cd orguine
pip install -e ".[exif]"
python -m orguine          # GUI
python -m orguine --help   # CLI
```

Custom categories: copy `orguine/resources/default_rules.json` to `rules.json` in the app data folder
(`%APPDATA%\Orguine`, `~/Library/Application Support/Orguine`, or `~/.local/share/orguine`; override with `ORGUINE_DATA_DIR`).

**Development**: `pip install -e ".[dev]" && pytest -q`. Build: `python scripts/build_exe.py`.
CI runs the tests on Windows, macOS and Linux, builds the executables, and publishes them to Releases on every `v*` tag.

**Links**: [My GitHub](https://github.com/cleitinhodev) · [Project](https://github.com/cleitinhodev/orguine) · [bugzinho.com](https://www.bugzinho.com/) · [Support / Donate](https://www.bugzinho.com/donate)

License: [GPL-3.0](LICENSE) © CleitinhoDEV
