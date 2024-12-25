window.addEventListener('load', (event) => {
    // show_req.show()
})

let show_req = new bootstrap.Modal(document.getElementById('requerimento'))

const req_proc = $('req_info_proc')
const req_proc_form = document.forms.req_info_proc

console.log(req_proc_form)


// vend_name = req_proc_form.vend_name.value
// vend_email = req_proc_form.vend_email.value
// vend_tel = req_proc_form.vend_tel.value
// vend_file = req_proc_form.vend_file

// comp_name = req_proc_form.comp_name.value
// comp_email = req_proc_form.comp_email.value
// comp_tel = req_proc_form.comp_tel.value
// comp_file = req_proc_form.comp_file

// placa = req_proc_form.placa.value


const req_send_pedido = async (that) => {
    if (confirm("Deseja realmente Solicitar o atendimento?")) {
        let btn_html = that.innerHTML
        that.innerHTML = spinner_w

        if (req_proc_form.vend_name.value && req_proc_form.vend_name.value.length < 10 ) {
            alert("Informar nome completo do vendedor")
            that.innerHTML = btn_html
            return
        }

        if (req_proc_form.vend_email.value && ! req_proc_form.vend_email.value.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
            alert("Informe um email válido do vendedor")
            that.innerHTML = btn_html
            return
        }

        if (req_proc_form.vend_tel.value && req_proc_form.vend_tel.value.replace(/\D/g, "").length < 10) {
            alert("Informe um telefone válido do vendedor")
            that.innerHTML = btn_html
            return
        }

        if (! req_proc_form.vend_file.files.length) {
            alert("Anexar o PDF com a CNH do Vendedor")
            that.innerHTML = btn_html
            return
        }

        if (req_proc_form.comp_name.value && req_proc_form.comp_name.value.length < 10 ) {
            alert("Informar nome completo do comprador")
            that.innerHTML = btn_html
            return
        }

        if (req_proc_form.comp_email.value && ! req_proc_form.comp_email.value.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
            alert("Informe um email válido do comprador")
            that.innerHTML = btn_html
            return
        }

        if (req_proc_form.comp_tel.value && req_proc_form.comp_tel.value.replace(/\D/g, "").length < 10) {
            alert("Informe um telefone válido do comprador")
            that.innerHTML = btn_html
            return
        }

        if (! req_proc_form.comp_file.files.length) {
            alert("Anexar o PDF com a CNH do Comprador")
            that.innerHTML = btn_html
            return
        }

        if (req_proc_form.placa.value && req_proc_form.placa.value.replace(/[^A-Z0-9]/g, "").length < 6) {
            alert("Informe uma placa válida")
            that.innerHTML = btn_html
            return
        }

        if (req_proc_form.proc_estab.value && req_proc_form.proc_estab.value === '0') {
            alert("Informe uma opção 'SUBSTABELECER' válida")
            that.innerHTML = btn_html
            return
        }

        if (req_proc_form.proc_irrev.value && req_proc_form.proc_irrev.value === '0') {
            alert("Informe uma opção 'IRREVOGÁVEL/IRRETRATÁVEL' válida")
            that.innerHTML = btn_html
            return
        }

        if (req_proc_form.proc_valid.value && req_proc_form.proc_valid.value === '0') {
            alert("Informe uma opção 'PRAZO DE VALIDADE' válida")
            that.innerHTML = btn_html
            return
        }

        if (! req_proc_form.crlv_file.files.length) {
            alert("Anexar o PDF com o Documento CRLV do Veículo")
            that.innerHTML = btn_html
            return
        }


        to_send = {
            'vend_name' : req_proc_form.vend_name.value,
            'vend_email' : req_proc_form.vend_email.value,
            'vend_tel' : req_proc_form.vend_tel.value.replace(/\D/g, ""),
            'comp_name' : req_proc_form.comp_name.value,
            'comp_email' : req_proc_form.comp_email.value,
            'comp_tel' : req_proc_form.comp_tel.value.replace(/\D/g, ""),
            'placa' : req_proc_form.placa.value.replace(/[^A-Z0-9]/g, ""),
            'proc_estab' : req_proc_form.proc_estab.value,
            'proc_irrev' : req_proc_form.proc_irrev.value,
            'proc_valid' : req_proc_form.proc_valid.value,
        }

        let vend_file = req_proc_form.vend_file

        if (vend_file.files.length) {
            // Para cada arquivo do input criar um item na lista uploads
            let uploads = []
            for (var i = 0; i < vend_file.files.length; i++) {
                let reader = new FileReader()
                reader.fileName = vend_file.files[i].name
                reader.fileType = vend_file.files[i].type
                reader.fileIndex = i
                reader.readAsDataURL(vend_file.files[i])
                reader.onload = () => {
                    reader['data'] = reader.result
                        .replace('data:', '')
                        .replace(/^.+,/, '')
                }
                uploads.push(reader)
            } 
            const load_dili_files = await loop_files(uploads)
            to_send['vend_file'] = uploads
        } 

        let comp_file = req_proc_form.comp_file

        if (comp_file.files.length) {
            // Para cada arquivo do input criar um item na lista uploads
            let uploads = []
            for (var i = 0; i < comp_file.files.length; i++) {
                let reader = new FileReader()
                reader.fileName = comp_file.files[i].name
                reader.fileType = comp_file.files[i].type
                reader.fileIndex = i
                reader.readAsDataURL(comp_file.files[i])
                reader.onload = () => {
                    reader['data'] = reader.result
                        .replace('data:', '')
                        .replace(/^.+,/, '')
                }
                uploads.push(reader)
            } 
            const load_dili_files = await loop_files(uploads)
            to_send['comp_file'] = uploads
        } 

        let crlv_file = req_proc_form.crlv_file

        if (crlv_file.files.length) {
            // Para cada arquivo do input criar um item na lista uploads
            let uploads = []
            for (var i = 0; i < crlv_file.files.length; i++) {
                let reader = new FileReader()
                reader.fileName = crlv_file.files[i].name
                reader.fileType = crlv_file.files[i].type
                reader.fileIndex = i
                reader.readAsDataURL(crlv_file.files[i])
                reader.onload = () => {
                    reader['data'] = reader.result
                        .replace('data:', '')
                        .replace(/^.+,/, '')
                }
                uploads.push(reader)
            } 
            const load_dili_files = await loop_files(uploads)
            to_send['crlv_file'] = uploads
        } 

        console.log(to_send)
        let api_url = `{{ url_for('attend.new') }}`
        fetch(api_url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', "X-CSRFToken": csrf_token },
            body: JSON.stringify( to_send ) })
        .then(response => response.json()).then(data => {
            if (data['result']) {
                console.log(data['result'])
                alert('Pedido enviado com sucesso')
                that.innerHTML = btn_html
                req_proc_form.reset()
            } else { 
                data['error'] ? alert(data['error']) : console.error('Unknown data:', data)
                that.innerHTML = btn_html
            }
        })
        .catch(error => { 
            alert(`{{ _('Error in API') }} attend.new | ${error}`) 
            that.innerHTML = btn_html
        })
    }
}



// Check Form
function check_form(formId) {
    var Form = document.getElementById(formId)
    var invalidList = Form.querySelectorAll(':invalid')
    if ( typeof invalidList !== 'undefined' && invalidList.length > 0 ) {
        for (var item of invalidList) {
          if (item.label) {alert("Preencha o campo "+item.label.innerHTML)}
          else {alert(item.validationMessage)}
        } return false
    }
    return true
}