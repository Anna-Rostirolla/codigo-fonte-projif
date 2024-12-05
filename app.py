from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from sqlite3 import Error
import base64
import re
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'An1003*Rj1205_'

# Método que conecta com o BD
def conectar():
    conexao = mysql.connector.connect(
        host="localhost",
        user="root",
        password="An1205_Rj1003*",
        database="projifdb"
    )
    return conexao

# Método que identifica o coordenador a partir do email passado na sessao
def identificar_coordenador():
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT id_coordenador, nome, email, telefone, data_nascimento FROM coordenadores WHERE email = %s", (session.get("usuario"),))
        coordenador = cursor.fetchone()
    return coordenador

def identificar_tipo(id_tipo):
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM tipos WHERE id_tipo = %s", (id_tipo,))
        tipo = cursor.fetchone()
    return tipo

def identificar_proj(id_proj):
    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT * FROM projetos WHERE id_projeto = %s", (id_proj,))
        proj = cursor.fetchone()

    return proj

def calculo_idade(data):
    if not data:
        return None

    hoje = datetime.today().date()  # Obtém a data de hoje
    
    # Calcula a idade
    idade = hoje.year - data.year - ((hoje.month, hoje.day) < (data.month, data.day))
    return idade

def nomear_coordenador(): # especificamente direcionado para a identificação do coordenador na navbar
    if session.get("usuario"):
        nome_coordenador = identificar_coordenador()
        nome_coordenador = nome_coordenador[1]
        nome_coordenador = nome_coordenador.split()
        nome_coordenador = nome_coordenador[0].title()
        return nome_coordenador
    else:
        return ""
app.jinja_env.globals.update(nomear_coordenador=nomear_coordenador) # métdo para que jinja reconheca nomear_coordenador como um metodo

def mostrar_dia_semana(dia_semana):
    dia = 'Dia da semana não informado.'
    if dia_semana == 'seg':
        dia = 'Segunda-feira'
    elif dia_semana == 'ter':
        dia = 'Terça-feira'
    elif dia_semana == 'qua':
        dia = 'Quarta-feira'
    elif dia_semana == 'qui':
        dia = 'Quinta-feira'
    elif dia_semana == 'sex':
        dia = 'Sexta-feira'

    return dia  

def formatar_data(dia, mes, ano):
    # Convertendo os valores para int
    dia = int(dia)
    mes = int(mes)
    ano = int(ano)

    # Verificando se há data adicionada
    if ano or mes or dia: # validando o ano inserido
        if dia < 1 or dia > 31 or mes < 1 or mes > 12 or ano < 1900 or ano > 2010: # 2010 por ora, consideran uso p data de nasc
            flash("Insira uma data válida.", "error")
            print("A data é inválida")
            return "Data inválida"
        
        if len(f"{dia}") == 1: # formatando o dia
            dia = f"0{dia}"

        if len(f"{mes}") == 1:  # formatando o mes
            mes = f"0{mes}"

        data = f"{ano}-{mes}-{dia}" # formatando a entrada para inserção da data no bd
        # print(data)
        return data
        
    else: # caso a data não tenha sido informada
        return None

@app.route("/")
def index(): # rota padrao do site
    return redirect(url_for("projetos"))

@app.route("/sobre") # exibe informações sobre o site
def sobre():
    return render_template("tela_sobre.html")

@app.route("/cadastro", methods=["GET", "POST"]) # cria uma conta
def cadastro():

    if request.method == "POST":
        # Pegar os dados do formulário
        nome = request.form.get("nome").strip().title()
        telefone = request.form.get("telefone").strip() or None
        dia_nasc = request.form.get("dia_nascimento") or None
        mes_nasc = request.form.get("mes_nascimento") or None
        ano_nasc = request.form.get("ano_nascimento") or None
        email = request.form.get("email").strip().lower()
        senha = request.form.get("senha")
        confirmar_senha = request.form.get("confirmar_senha")

        # Validar o e-mail
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Email inválido!", "danger")
            print("O email não é valido")
            return redirect(url_for("cadastro"))

        # Verificar as senhas
        if senha != confirmar_senha:
            flash("As senhas não conferem!", "danger")
            print("Senhas não estao iguais'")
            return redirect(url_for("cadastro"))
        
        # # Criptografand a senha
        senha_bd = generate_password_hash(senha)

        # Validar e formatar a data
        data_nasc = formatar_data(dia_nasc, mes_nasc, ano_nasc)
        if data_nasc == "Data inválida":
            return redirect(url_for("cadastro"))

        # Verificar se a conta existe
        try:
            with conectar() as conexao:
                cursor = conexao.cursor()
                cursor.execute("""
                    SELECT COUNT(email) FROM coordenadores WHERE email = %s
                    """, (email,)
                )
                email_igual = cursor.fetchone()
                
            if email_igual[0] != 0: # caso o comando anterior retorne um ou mais itens com o email inseridp
                flash(f"O e-mail já existe.", "danger")
                print("O email já existe no bd")
                return redirect(url_for("cadastro"))

            else:
                # Cadastro do usuário
                with conectar() as conexao:
                    cursor = conexao.cursor()
                    cursor.execute("""
                        INSERT INTO coordenadores (nome, email, senha, telefone, data_nascimento) 
                        VALUES (%s, %s, %s, %s, %s);
                        """, (nome, email, senha_bd, telefone, data_nasc)
                    )
                    conexao.commit()
                flash("Cadastro realizado com sucesso!", "sucess")
                print("Usuario cadastrado")
                session["usuario"] = email

                return redirect(url_for("perfil"))
        
        except Error as e:
            print(f"Ocorreu um erro ao validar o e-mail: {e}")
            flash("Algo deu errado ao validar o e-mail.", "danger")   

    return render_template("tela_cadastro.html")

@app.route("/acesso", methods=["GET", "POST"]) # acessa uma conta ja criada
def acesso():

    if request.method == "POST":

        # Pegas os dados inseridos
        email = request.form.get("email").strip().lower()
        senha = request.form.get("senha")

        try:
            with conectar() as conexao:
                cursor = conexao.cursor()

                # Verificar se o e-mail existe
                cursor.execute("SELECT * FROM coordenadores WHERE email = %s", (email,))
                existe = cursor.fetchone() # método que retorna uma linha a partir de uma consulta feita
        
                if existe: # caso a conta exista
                    if check_password_hash(existe[3], senha): # validando se as senhas conferem
                        session["usuario"] = email
                        flash("Autenticação realizada com sucesso!", "sucess")
                        return redirect(url_for("perfil"))
                
                    else:
                        flash("Senha incorreta.", "danger")
                        return redirect(url_for("acesso"))
            
        except Error as e:
            print(f"Ocorreu um erro ao validar o acesso: {e}.")
    
    return render_template("tela_acesso.html")

@app.route("/cadastro-projeto", methods=["GET", "POST"]) # cadastra projeto
def cadastro_projeto():

    if not session.get("usuario"): # caso usuario nao seja autenticado
        return redirect(url_for('acesso'))

    # CPegar os tipos disponiveis
    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT * FROM tipos")
            tipos = cursor.fetchall() 
    except Error as e:
        print(f"Ocorreu um erro ao buscar os tipos disponiveis: {e}")

    if request.method == "POST":

        coo = identificar_coordenador()
        id_coordenador = coo[0]
        id_tipo = request.form.get("tipo")
        nome = request.form.get("nome").strip().title()
        url_material = request.form.get("url-material").strip()
        local = request.form.get("local").strip()
        horario = request.form.get("hora")
        dia_semana = request.form.get("dia_semana")
        resumo = request.form.get("resumo").strip()
        situacao = "Ativo" # padrão ao ser criado

        try:
            with conectar() as conexao:
                cursor = conexao.cursor()
                cursor.execute("""
                    INSERT INTO projetos (nome, resumo, situacao, local, dia_semana, horario, url_material, id_coordenador, id_tipo) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (nome, resumo, situacao, local, dia_semana, horario, url_material, id_coordenador, id_tipo))
                conexao.commit()
                print("Projeto cadastrado com sucesso!")
                return redirect(url_for("perfil"))

        except Error as e:
            print(f"Ocorreu um erro ao conectar com o BD: {e}.")
    
    return render_template("tela_cadastro_projetos.html", tipos=tipos)

@app.route("/editar-projeto/<int:proj_id>", methods=["GET", "POST"]) # editar um projeto cadastrado
def editar_projeto(proj_id):

    if not session.get("usuario"):
        return redirect(url_for('acesso'))
    
    try:
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute('''
                           SELECT p.*, t.nome AS nome_tipo
                           FROM projetos AS p
                           LEFT JOIN tipos AS t
                           ON p.id_tipo = t.id_tipo
                           WHERE id_projeto = %s
                           ''', (proj_id,))
            proj = cursor.fetchone()

            proj['horario'] = f'{proj["horario"]}'[:5] # formatar a hora p retirar os seg
            dia_s = mostrar_dia_semana(proj["dia_semana"])

        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT * FROM tipos")
            tipos = cursor.fetchall()

    except Error as e:
        print(f"Deu erro ao identificar o projeto: {e}")
        return redirect(url_for('perfil'))
    
    if identificar_coordenador()[0] != proj['id_coordenador']: # caso usuario nao seja o coordenador do proj
        print("O usuario não pode alterar um projeto que não possui.")
        return redirect(url_for('perfil'))

    if request.method == "POST":
        nome = request.form.get("nome").strip().title()
        tipo = request.form.get("tipo")
        material = request.form.get("url-material").strip() or None
        situacao = request.form.get("situacao")
        local = request.form.get("local").strip() or None
        dia = request.form.get("dia-semana") or None # caso dia não tenha sido informado
        hora = f'{request.form.get("hora")}:00' or None
        resumo = request.form.get("resumo").strip()
        
        try:
            with conectar() as conexao:
                cursor = conexao.cursor()

                cursor.execute("""
                    UPDATE projetos 
                    SET nome = %s, resumo = %s, situacao = %s, local = %s, dia_semana = %s, horario = %s, url_material = %s, id_tipo = %s
                    WHERE id_projeto = %s
                """, (nome, resumo, situacao, local, dia, hora, material, tipo, proj_id)) # falta hora, dia...
                conexao.commit()
                
        except Error as e:
            print(f"Ocorreu um erro ao atualizar o projeto: {e}")

        else:
            return redirect(url_for("perfil"))
        
    return render_template("tela_editar_projetos.html", tipos=tipos, proj=proj, dia_s=dia_s)

@app.route("/excluir-projeto/<int:proj_id>", methods=["GET", "POST"])  # excluir um projeto por meio do id
def excluir_projeto(proj_id):
    if not session.get("usuario"):
        print("Usuario não cadastrado")
        return redirect(url_for("acesso"))

    if identificar_coordenador()[0] != identificar_proj(proj_id)[8]:
        print("Usuário não pode excluir um projeto que não é seu")
        return redirect(url_for("perfil"))

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM postagens WHERE id_projeto = %s", (proj_id,))
            cursor.execute("DELETE FROM projetos WHERE id_projeto = %s", (proj_id,))
            conexao.commit()
        
        return redirect(url_for("perfil"))
    
    except Error as e:
        print(f"Ocorreu um erro ao excluir projeto: {e}")
        flash("Não foi possivel excluir o projeto.", "error")
        return redirect(url_for('perfil'))

@app.route("/projetos", methods=["GET"]) # mostra os projetos
def projetos():

    try:
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True) # faz retorno com itens tipo dicionario
            cursor.execute('''
                SELECT p.id_projeto, p.nome, p.situacao, p.resumo, c.nome AS coordenador, t.nome AS tipo 
                FROM projetos AS p
                LEFT JOIN coordenadores AS c 
                    ON p.id_coordenador = c.id_coordenador
                LEFT JOIN tipos AS t
                    ON p.id_tipo = t.id_tipo
            ''') # seleciona os itens a serem exibidos na tela os vinculando por meio do 
            projetos = cursor.fetchall()
        # print(projetos)

    except Error as e:
        print(f"Ocorreu um erro ao abrir projeto: {e}")
        return redirect(url_for("projetos"))

    return render_template("tela_visit_visualizar_projetos.html", projetos=projetos) 

@app.route("/perfil", methods=["GET"]) # mostra as info do coordenador e od projetos associados a ele
def perfil():

    if not session.get("usuario"):
        return redirect(url_for('acesso'))

    coordenador = identificar_coordenador()
    id_coordenador = coordenador[0]    

    idade = calculo_idade(coordenador[4])
    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute('''
                SELECT proj.*, t.nome
                FROM projetos AS proj
                LEFT JOIN tipos AS t
                ON t.id_tipo = proj.id_tipo
                WHERE proj.id_coordenador = %s 
                ORDER BY proj.nome ASC
            ''', (id_coordenador,))
            projs = cursor.fetchall()
            qtd_projs = len(projs)

    except Error as e:
        print(f"Ocorreu um erro ao buscar projetos: {e}")
        return redirect(url_for("perfil"))
    
    return render_template("tela_perfil_visualizar_proj.html", coordenador=coordenador, projs=projs, idade=idade, qtd_projs=qtd_projs) 

@app.route("/efetuar-post", defaults={"proj_id": 0}, methods=["GET", "POST"]) #  # faz uma postagem (sem projeto definido)
@app.route("/efetuar-post/<int:proj_id>", methods=["GET", "POST"]) # faz uma postagem (com o projeto definido)
def efetuar_postagem(proj_id):

    if not session.get("usuario"):
        return redirect(url_for('acesso'))
    coordenador = identificar_coordenador()

    # pre selecionar o projeto para a publicacao
    proj_padrao = None
    if proj_id != 0:
        if coordenador[0] == identificar_proj(proj_id)[8]:
            proj_padrao = identificar_proj(proj_id)
    # print(proj_padrao)

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT * FROM projetos WHERE id_coordenador = %s ORDER BY nome", (coordenador[0],))
            projs = cursor.fetchall()

    except Error as e:
        print(f"Ocorreu um erro ao encontrar os projetos: {e}")

    if request.method == "POST":
        id_proj = request.form.get("proj")
        descricao = request.form.get("descricao")
        img = request.files.get("img")

        img_bin = img.read()

        try:
            with conectar() as conexao:
                cursor = conexao.cursor()
                cursor.execute("""
                               INSERT INTO postagens(data_publicacao, imagem, texto, id_projeto)
                               VALUES (CURRENT_TIMESTAMP(), %s, %s, %s)
                               """, (img_bin, descricao, id_proj))
                conexao.commit()
            
            return redirect(url_for("atualizacoes"))

        except Error as e:
            print(f"Algo deu errado ao cadastrar a publicação: {e}")

    return render_template("tela_efetuar_postagem.html", proj_padrao=proj_padrao, projs=projs)

@app.route("/excluir-post/<int:proj_id>/<int:post_id>", methods=["GET"]) # exclui uma postagem
def excluir_postagem(proj_id, post_id):

    with conectar() as conexao:
        cursor = conexao.cursor()
        cursor.execute("SELECT email FROM coordenadores WHERE id_coordenador = %s",(identificar_proj(proj_id)[8],))
        coo = cursor.fetchone()[0]

    if session.get("usuario") != coo:
        print(f"Usuario não pode excluir uma postagem de um projeto que não é seu. ")
        return redirect(url_for('perfil'))

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM postagens WHERE id_postagem = %s", (post_id,))
            conexao.commit()
        flash("Postagem excluída com sucesso.", "success")
    except Exception as e:
        print(f"Erro ao excluir postagem: {e}")
        flash("Erro ao excluir postagem.", "error")
    return redirect(url_for('consultar_projeto', proj_id=proj_id))

@app.route("/atualizacoes", methods=["GET"]) # exibir um mural com as postagens de projetos feitas
def atualizacoes():
    situacao = request.args.get("situacao")
    if not situacao:
        situacao = "Ativo"
    
    posts = []

    try:
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True)
            
            # Consulta SQL com aliases para facilitar acesso no dicionário
            cursor.execute("""
                SELECT 
                    p.id_postagem AS id, p.data_publicacao AS data, p.imagem AS imagem, p.texto AS texto, 
                    proj.id_projeto AS proj_id, proj.nome AS proj_nome, proj.id_coordenador AS proj_id_coo
                FROM postagens AS p
                INNER JOIN projetos AS proj
                        ON p.id_projeto = proj.id_projeto
                WHERE proj.situacao = %s
                ORDER BY p.data_publicacao DESC
            """, (situacao,))
            posts_bd = cursor.fetchall()

        for post_bd in posts_bd:
            imagem_blob = post_bd["imagem"]
            imagem_base64 = base64.b64encode(imagem_blob).decode("utf-8")

            data_bd = post_bd["data"].strftime("%Y-%m-%d %H:%M:%S")
            data = f"{data_bd[8:10]}/{data_bd[5:7]}/{data_bd[:4]} - {data_bd[11:16]}"  # Formato: dd/mm/aaaa - hh:mm

            post = {
                "id": post_bd["id"],
                "data": data,
                "imagem": f"data:image/jpg;base64,{imagem_base64}",
                "texto": post_bd["texto"],
                "id_projeto": post_bd["proj_id"],
                "projeto": post_bd["proj_nome"],
                "coordenador": post_bd["proj_id_coo"]
            }
            posts.append(post)

    except Error as e:
        print(f"Algo deu errado ao buscar os posts cadastrados: {e}")
    
    return render_template("tela_postagens.html", posts=posts, situacao=situacao)

@app.route("/projeto/<int:proj_id>", methods=["GET"]) # mostra informacoes de um projeto
def consultar_projeto(proj_id):

    coo_bl = False # boolean para validar se usuario tera a opcao de add postagem ao projeto
    if session.get("usuario"): # verifica se usuario está cadastrado
        if identificar_coordenador()[0] == identificar_proj(proj_id)[8]: # verifica se usuario é coordenador do projeto em questao
            coo_bl = True

    with conectar() as conexao:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute('''
                       SELECT proj.*, c.nome AS nome_coordenador, t.nome AS nome_tipo
                       FROM projetos AS proj 
                       LEFT JOIN coordenadores AS c
                       ON c.id_coordenador = proj.id_coordenador
                       LEFT JOIN tipos AS t
                       ON t.id_tipo = proj.id_tipo
                       WHERE id_projeto = %s
                       ''', (proj_id,))
        proj = cursor.fetchone()

    posts = []

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT * FROM postagens WHERE id_projeto = %s ORDER BY data_publicacao DESC", (proj_id,))
            posts_bd = cursor.fetchall()
        
        for post_bd in posts_bd:

            imagem_blob = post_bd[2]
            imagem_base64 = base64.b64encode(imagem_blob).decode("utf-8")

            data_bd = f"{post_bd[1]}"
            data = f"{data_bd[8:10]}/{data_bd[5:7]}/{data_bd[:4]} - {data_bd[11:16]}" # aaaa-mm-dd hh:mm:ss

            post = {
                "id": post_bd[0],
                "data": data,
                "imagem": f"data:image/jpg;base64,{imagem_base64}", # configurar dps para mais extensões
                "texto": post_bd[3],
            }
            posts.append(post)
        print(f"Quantidade de posts: {len(posts)}")

        projeto = {
            "id": proj["id_projeto"],
            "nome": proj["nome"],
            "resumo": proj["resumo"],
            "situacao": proj["situacao"],
            "local": proj["local"],
            "dia_semana": mostrar_dia_semana(proj["dia_semana"]),
            "horario": f"{proj['horario']}",
            "url_material": proj["url_material"],
            "coordenador": proj["nome_coordenador"],
            "tipo": proj["nome_tipo"],
            "posts": posts
        }

    except Error as e:
        print(f"Ocorreu um erro ao retornar as informações do projeto: {e}")
        return redirect(url_for("projetos"))

    return render_template('tela_consultar_proj.html', projeto=projeto, coo_bl=coo_bl)

@app.route("/editar-perfil", methods=["GET", 'POST']) # edita os dados do cadastro
def editar_perfil():
    if not session.get("usuario"):
        return redirect(url_for("acesso"))

    conta = identificar_coordenador()
    data_bd = f"{conta[4]}".split("-") # yyyy-mm-dd

    if request.method == "POST":
        nome = request.form.get("nome").strip().title()
        telefone = request.form.get("telefone").strip()
        dia = request.form.get("dia_nasc")
        mes = request.form.get("mes_nasc")
        ano = request.form.get("ano_nasc")

        # Validar e formatar data
        data = formatar_data(dia, mes, ano)
        if data == "Data inválida":
            return redirect(url_for("editar_perfil"))
    
        try:
            with conectar() as conexao:
                cursor = conexao.cursor()
                cursor.execute('''
                    UPDATE coordenadores
                    SET nome = %s, telefone = %s, data_nascimento = %s
                    WHERE email = %s
                ''', (nome, telefone, data, session.get("usuario")))
                conexao.commit()
            return redirect(url_for("perfil"))

        except Error as e:
            flash("Não foi possível editar as informações.", "error")
            print(f"Ocorreu um erro ao editar: {e}")
            return redirect(url_for("editar_perfil"))

    return render_template("tela_editar_perfil.html", conta=conta, data_bd=data_bd)

@app.route("/sair", methods=["GET", "POST"]) # opcao p usuario fazer logout de sua conta
def sair():
    try:
        if session.get("usuario"):
            print("Usuario pode sair da conta")
            session["usuario"] = None
            return redirect(url_for('acesso')) # recarrega a pag
        else:
            print("Usuario não logado")
        
    except:
        print("Não foi possivel sair da conta")

    return render_template("tela_acesso.html")

## Rotas do ADM
@app.route("/tipos", methods=["GET", "POST"])
def tipos():

    # print("Chegou")
    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("SELECT * FROM tipos")
            tipos = cursor.fetchall()

    except Error as e:
        print(f"Ocorreu um erro ao buscar os tipos: {e}")
        tipos = []

    return render_template("tela_adm_tipos.html", tipos=tipos)

@app.route("/tipos/renomear", methods=["POST"])
def renomear_tipo():
    tipo_id = request.form.get("id")
    novo_nome = request.form.get("novo_nome")

    if not tipo_id or not novo_nome:
        return "Erro: Dados inválidos.", 400

    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                "UPDATE tipos SET nome = %s WHERE id_tipo = %s",
                (novo_nome, tipo_id)
            )
            conexao.commit()
        return redirect(url_for("tipos"))  # Recarrega a página com os dados atualizados
    except Error as e:
        print(f"Ocorreu um erro ao atualizar o tipo: {e}")
        return "Erro ao atualizar o tipo.", 500

if __name__ == "__main__":
    app.run(debug=True)