import base64
from io import BytesIO
import qrcode
from flask import url_for, current_app

def get_qrcode(id, visita=False, docs=False):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    if visita:
        qr.add_data(f'{ url_for("base.dashboard", _external=True) }?visita={id}')
    elif docs:
        int_url = url_for("base.index", _external=True, service_docs=id)
        int_dom = int_url.split('://')[1].split('/')[0]
        ext_url = int_url.replace(int_dom, current_app.config['DOMAIN'])

        print(ext_url)

        qr.add_data(ext_url)
    else:
        return False

    qr.make(fit=True)
    img = qr.make_image()
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str 

    img = qr.make_image(fill_color="black", back_color="white")

    b64 = base64.b64encode(img.get_image().tobytes()).decode("utf-8")
    return b64
    # content = base64.b64decode(files[0]['data'])



# from PIL import Image
# stamp = Image.open('../static/img/stamp.jpg')
# basewidth = 100
# wpercent = (basewidth/float(logo.size[0]))
# hsize = int((float(logo.size[1])*float(wpercent)))
# logo = logo.resize((basewidth, hsize), Image.ANTIALIAS)
# QRcode = qrcode.QRCode(
#     error_correction=qrcode.constants.ERROR_CORRECT_H
# )
# # adding color to QR code
# QRimg = QRcode.make_image(
#     fill_color=QRcolor, back_color="white").convert('RGB')
#  # set size of QR code
# pos = ((QRimg.size[0] - logo.size[0]) // 2,
#        (QRimg.size[1] - logo.size[1]) // 2)
# QRimg.paste(logo, pos)
 
# # save the QR code generated
# QRimg.save('gfg_QR.png')
 
# .decode()
