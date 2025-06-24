import os
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Screenshot

# Cria uma instância da aplicação para ter acesso ao contexto e ao banco de dados
app = create_app()

def delete_old_screenshots():
    with app.app_context():
        # Define o tempo limite (3 dias atrás)
        cutoff = datetime.utcnow() - timedelta(days=3)

        # Encontra os prints antigos no banco de dados
        old_screenshots = Screenshot.query.filter(Screenshot.timestamp < cutoff).all()

        if not old_screenshots:
            print(f"{datetime.now()}: Nenhum print com mais de 3 dias para deletar.")
            return

        print(f"{datetime.now()}: Encontrados {len(old_screenshots)} prints antigos para deletar.")

        for screenshot in old_screenshots:
            try:
                # Monta o caminho completo do arquivo
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], screenshot.filepath)

                # Verifica se o arquivo existe e o remove do disco
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"Arquivo deletado: {filepath}")

                # Remove o registro do banco de dados
                db.session.delete(screenshot)

            except Exception as e:
                print(f"Erro ao deletar o print {screenshot.id}: {e}")

        # Salva as mudanças no banco de dados
        db.session.commit()
        print(f"{datetime.now()}: Limpeza concluída.")

if __name__ == '__main__':
    delete_old_screenshots()
