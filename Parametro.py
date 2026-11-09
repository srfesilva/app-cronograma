import pandas as pd# Exemplo de atividades corrigido
dados = {
    'Atividade': [
        'CENSO ESCOLAR 2026 - Segunda Etapa',             #CENSO ESCOLAR 2026
        'Atualização Cadastro de Escolas',                #1
        'Quadro Resumo e Coleta de Classes e Matrícula',  #2
        'Matriz Curricular e Funcional outras Redes',     #3
        'Associação do Professor na Classe',              #4
        'Transporte Escolar',                             #5
        'Declaração do Censo Escolar',                    #6
        'Revisão dos Dados',                              #7
        'Migração dos Dados do Censo Escolar',            #MIGRAÇÃO PRIMEIRA ETAPA
        'Preparação do material Evento Censo',            #8
        'Evento do Censo Escolar MI',                     #EVENTO PRIMEIRA ETAPA
        'Retificação do Censo Escolar',                   #RETIFICAÇÃO DO CENSO ESCOLAR
        'Rendimento Escolar',                             #10
        'Migração da Situação do Aluno',                  #11
        'Orientação Técnica Situação do Aluno',           #EVENTO SEGUNDA ETAPA
        'Retificação da Situação do Aluno',               #13
        'Publicação dos dados do Censo Escolar',          #14
        'CENSO ESCOLAR 2028',                             #Censo Escolar 2028,

    ],
    'Início': ['2026-12-01',                              #CENSO ESCOLAR 2026
               '2027-01-01',                              #1
               '2027-01-01',                              #2
               '2027-01-01',                              #3
               '2027-02-01',                              #4
               '2027-03-01',                              #5
               '2027-05-01',                              #6
               '2027-04-01',                              #7
               '2027-06-01',                              #MIGRAÇÃO PRIMEIRA ETAPA
               '2027-07-01',                              #8
               '2027-09-13',                              #EVENTO PRIMEIRA ETAPA
               '2027-09-15',                              #RETIFICAÇÃO DO CENSO ESCOLAR
               '2027-12-15',                              #10
               '2028-02-01',                              #11
               '2028-03-22',                              #EVENTO SEGUNDA ETAPA
               '2028-04-01',                              #13
               '2028-01-31',                              #14
               '2027-12-01'                               #Censo Escolar 2028

               ],
    'Fim': ['2027-04-15',                                 #CENSO ESCOLAR 2026
            '2027-03-31',                                 #1
            '2027-03-31',                                 #2
            '2027-05-26',                                 #3
            '2027-05-26',                                 #4
            '2027-05-26',                                 #5
            '2027-05-26',                                 #6
            '2027-05-26',                                 #7
            '2027-07-31',                                 #MIGRAÇÃO PRIMEIRA ETAPA
            '2027-08-30',                                 #8
            '2027-09-15',                                 #EVENTO PRIMEIRA ETAPA
            '2027-10-15',                                 #RETIFICAÇÃO DO CENSO ESCOLAR
            '2028-01-20',                                 #10
            '2028-03-15',                                 #11
            '2028-03-26',                                 #EVENTO SEGUNDA ETAPA
            '2028-04-15',                                 #13
            '2028-05-31',                                 #14
            '2028-05-31'                                  #Censo Escolar 2028
            ],
    'Responsável': ['CENSO ESCOLAR 2026 - SEGUNDA ETAPA',               #CENSO ESCOLAR 2026
                    'GESTÃO ESCOLAR, SEGRE/SEOM, COPLAG/COINFO',        #1
                    'GESTÃO ESCOLAR. SEGRE/SEMAT, DIMAV/COINFO',        #2
                    'GESTÃO ESCOLAR OUTRAS REDES, SEGRE/SEMAT, COINFO', #3
                    'GESTÃO ESCOLAR OUTRAS REDES, SEGRE/SEMAT, COINFO', #4
                    'GESTÃO ESCOLAR, SEGRE/SEOM, SUCOR/COINFO',         #5
                    'GESTÃO ESCOLAR, SEGRE/SEMAT, COINFO',                    #6
                    'COINFO',                                           #7
                    'COINFO',                                           #MIGRAÇÃO PRIMEIRA ETAPA
                    'COINFO',                                           #8
                    'COINFO',                                           #EVENTO PRIMEIRA ETAPA
                    'GESTÃO ESCOLAR, SEGRE, COINFO',                    #RETIFICAÇÃO DO CENSO ESCOLAR
                    'GESTÃO ESCOLAR, SEGRE/SEVESC, COINFO/COVESC',      #10
                    'COINFO/PRODESP',                                   #11
                    'COINFO',                                           #EVENTO SEGUNDA ETAPA
                    'COINFO',                                           #13
                    'INEP',                                             #14
                    'CENSO ESCOLAR 2028'                                #Censo Escolar 2028

]}

df = pd.DataFrame(dados)
df['Início'] = pd.to_datetime(df['Início'])
df['Fim'] = pd.to_datetime(df['Fim'])
