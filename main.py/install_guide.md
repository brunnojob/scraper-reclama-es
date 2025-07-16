# Guia de Instalação - Scraper de Reclamações de TI

## Problema: pip não reconhecido

Este erro indica que o Python não está instalado ou não está configurado corretamente no PATH do Windows.

## Soluções

### Opção 1: Instalar Python (Recomendado)

1. **Baixe o Python**:
   - Acesse: https://www.python.org/downloads/
   - Baixe a versão mais recente do Python 3.x

2. **Instale o Python**:
   - Execute o instalador baixado
   - **IMPORTANTE**: Marque a opção "Add Python to PATH" durante a instalação
   - Clique em "Install Now"

3. **Verifique a instalação**:
   ```cmd
   python --version
   pip --version
   ```

4. **Instale as dependências**:
   ```cmd
   pip install -r requirements.txt
   ```

### Opção 2: Usar Python via Microsoft Store

1. Abra a Microsoft Store
2. Procure por "Python 3.11" ou "Python 3.12"
3. Instale a versão mais recente
4. Reinicie o terminal e tente novamente

### Opção 3: Usar py launcher (se Python já estiver instalado)

```cmd
py -m pip install -r requirements.txt
py main.py
```

## Verificação Rápida

Para verificar se o Python está funcionando:

```cmd
python -c "print('Python funcionando!')"
```

## Próximos Passos

Após instalar o Python:

1. Navegue até a pasta do projeto
2. Execute: `pip install -r requirements.txt`
3. Execute: `python main.py`