servidor-monitor/
│
├── app/                  # Pasta principal da sua aplicação Flask
│   │
│   ├── static/           # Pasta para arquivos estáticos (CSS, JS, Imagens)
│   │   └── screenshots/  # Onde os prints dos colaboradores são salvos
│   │
│   ├── templates/        # Pasta para os arquivos HTML
│   │   ├── base.html             # O template base com o menu e layout principal
│   │   ├── dashboard.html        # A página principal do painel de administradores
│   │   ├── edit_employee.html    # Página para editar um colaborador
│   │   ├── employee_details.html # Página com o relatório de um colaborador
│   │   ├── login.html            # A tela de login do administrador
│   │   └── session_details.html  # Página com os detalhes de uma sessão de trabalho
│   │
│   ├── __init__.py       # Inicializa a aplicação Flask (fábrica de aplicação)
│   ├── models.py         # Define as tabelas do banco de dados (User, WorkSession, etc.)
│   ├── routes.py         # Define todas as rotas e a lógica das páginas e da API
│   └── app.db            # O arquivo do banco de dados SQLite
│
├── venv/                 # Pasta do ambiente virtual do Python (gerenciada automaticamente)
│
├── config.py             # Arquivo de configuração (chaves secretas, caminho do DB)
├── run.py                # Ponto de entrada para iniciar o servidor com Gunicorn
├── requirements.txt      # Lista de todas as bibliotecas Python necessárias para o servidor
└── cleanup.py            # Script agendado (cron job) para apagar prints antigos


cliente-monitor/
│
├── build/                # Pasta de trabalho do PyInstaller (pode ser ignorada)
│
├── dist/                 # Onde o PyInstaller salva o resultado final
│   └── main.exe          # O seu programa executável pronto para distribuir!
│
├── venv/                 # Pasta do ambiente virtual do Python para o cliente
│
├── api_client.py         # Centraliza toda a comunicação com a API do servidor
├── config.py             # Configuração simples que armazena a URL do servidor
├── icone.ico             # O ícone utilizado no arquivo .exe
├── main.py               # Arquivo principal que cria a interface gráfica (login, etc.)
├── tracker.py            # O coração do monitor, com toda a lógica de rastreamento
└── requirements.txt      # Lista das bibliotecas Python necessárias para o cliente
