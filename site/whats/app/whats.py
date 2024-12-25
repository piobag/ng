import time
import base64
from io import BytesIO







from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from flask import current_app, render_template
from flask_mail import Message

from . import mail

options = webdriver.ChromeOptions()
options.add_argument("--window-size=1920,1080")
options.add_argument("--user-data-dir=./profile")
options.add_argument("--profile-directory=Default")
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")


driver = webdriver.Chrome(options=options, service=ChromeService(ChromeDriverManager().install()))

msg_field = []


# driver.get('https://web.whatsapp.com/')
# time.sleep(5)

# while len(driver.find_elements(By.ID, "side")) < 1:
#     time.sleep(1)
#     print('.')

# print('foi')

def send_msg(msg, dest):
    link = f"https://web.whatsapp.com/send?phone={dest}"
    driver.get(link)
    try:
        msg_field = WebDriverWait(driver, timeout=5).until(lambda d: d.find_element(
            By.XPATH, '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div[1]/div/p'))
        # time.sleep(3)
        # driver.save_screenshot(f'app/teste.png')
    except Exception as e:
        try:
            qrcode = WebDriverWait(driver, timeout=5).until(lambda d: d.find_element(
                By.XPATH, '/html/body/div[1]/div/div/div[3]/div[1]/div/div/div[2]/div[2]')
            )
        except Exception as e:
            invalid = driver.find_elements(By.XPATH, '//*[@id="app"]/div/span[2]/div/span/div/div/div/div/div/div[2]/div/button')
            # invalid = driver.find_elements(By.CLASS_NAME, "f8jlpxt4")
            if len(invalid) > 0:
                print('Número inválido')
                return '402'
                # time.sleep(76)
                # exit(9)
            print(e)
            print('Erro encontrando estado atual')
            driver.save_screenshot(f'app/erro.png')
            return '401'

        time.sleep(3)
        qrcode = driver.get_screenshot_as_base64()
        title = 'Valide o QRCode para o Whatsapp'
        msg = Message(
            title,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[current_app.config['MAIL_ADMIN'][0]]
        )
        msg.body = render_template(
            'mail.txt',
            title=title,
        )
        msg.html = render_template(
            'mail.html',
            title=title,
        )

        # part = MIMEMultipart('image', 'png')
        # part.set_payload(qrcode)
        # part.add_header('Content-Transfer-Encoding', 'base64')
        # part['Content-Disposition'] = f'attachment; filename="qrcode.png"'

        image = BytesIO(base64.b64decode(qrcode))
        msg.attach("qrcode.png", "image/png", image.read())
                
        try:
            mail.send(msg)
        except Exception as e:
            try:
                print(f'Exception sending mail')
                print(e)
            except Exception as e:
                pass
            time.sleep(5)
            mail.send(msg)
        return '403'
    

    msg_field = driver.find_elements(By.XPATH, '//*[@id="main"]/footer/div[1]/div/span[2]/div/div[2]/div[1]/div[1]/div/p')


    print('foi')

    time.sleep(3)
    msg_field[0].click()
    msg_field[0].send_keys(msg)
    print('mensagem escrita')
    time.sleep(5)

    driver.save_screenshot(f'app/msg.png')

    # msg_field[0].send_keys(Keys.ESCAPE)
    # print('Send Escape')

    msg_field[0].send_keys(Keys.ENTER)
    print('Send Enter')
    time.sleep(5)
    
    return '0'

# msg = """Boragora mesmo
# Link: https://bobbyhadz.com/blog/python-attributeerror-webdriver-object-has-no-attribute-find-element-by-id
# Revolucionário
# """

# send_msg(msg, '5561982111180')

# time.sleep(15)
# exit(0)
# campo_pesquisa = driver.find_element_by_xpath('//div[contains(@class,"copyable-text selectable-text")]')

# # //*[@id="app"]/div/span[2]/div/span/div/div/div/div/div/div[1]

# #Contatos/Grupos - Informar o nome(s) de Grupos ou Contatos que serao enviadas as mensagens
# contatos = ['PALMEIRAS FUT','CONDOMINIO AREZZO','FAMILIA 02','FUTEBOL 2020','CLIENTES 02']

# #Mensagem - Mensagem que sera enviada
# mensagem = 'Bom dia grupo '
# mensagem2 = ' ,que o dia de voces seja iluminado'

# #Midia = imagem, pdf, documento, video (caminho do arquivo, lembrando que mesmo no windows o caminho deve ser passado com barra invertida */* ) 
# midia = "/home/pinheirocfc/Imagens/bom-dia.jpg"

# #Funcao que pesquisa o Contato/Grupo
# def buscar_contato(contato):
#     campo_pesquisa = driver.find_element_by_xpath('//div[contains(@class,"copyable-text selectable-text")]')
#     time.sleep(2)
#     campo_pesquisa.click()
#     campo_pesquisa.send_keys(contato)
#     campo_pesquisa.send_keys(Keys.ENTER)

# #Funcao que envia a mensagem
# def enviar_mensagem(mensagem,mensagem2):
#     campo_mensagem = driver.find_elements_by_xpath('//div[contains(@class,"copyable-text selectable-text")]')
#     campo_mensagem[1].click()
#     time.sleep(3)
#     campo_mensagem[1].send_keys(str(mensagem) + str(contato) + str(mensagem2))
#     campo_mensagem[1].send_keys(Keys.ENTER)

# #Funcao que envia midia como mensagem
# def enviar_midia(midia):
#     driver.find_element_by_css_selector("span[data-icon='clip']").click()
#     attach = driver.find_element_by_css_selector("input[type='file']")
#     attach.send_keys(midia)
#     time.sleep(3)
#     send = driver.find_element_by_css_selector("span[data-icon='send']")
#     send.click()    

# #Percorre todos os contatos/Grupos e envia as mensagens
# for contato in contatos:
#     buscar_contato(contato)
#     enviar_mensagem(mensagem,mensagem2)       
#     enviar_midia(midia) 
#     time.sleep(1)
